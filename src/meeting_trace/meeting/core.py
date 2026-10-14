import copy
import hashlib
import re
import unicodedata
from collections import OrderedDict

from .schema import ITEM, STAGE_ONE, schema_errors

MAX_CHARS = 24000
MAX_TURNS = 300
SELF_ASSIGN = re.compile(r'\b(?:em|anh|chị|tôi|mình)\s+(?:nhận|sẽ làm|sẽ sửa|sẽ cập nhật)|\bđể\s+(?:em|anh|chị|tôi)\s+(?:làm|sửa|cập nhật)\s+\S+', re.I)
FINAL = re.compile(r'^(?:chốt|quyết định|thống nhất)\s+\S+', re.I)
DEFER = re.compile(r'^(?:chưa chốt|chưa thống nhất|hoãn|tạm hoãn|hủy quyết định|không chốt)\b', re.I)
DUE = re.compile(r'\b(?:trước|hạn là|hạn:|hạn)\s+(.+?)[.!;]?$', re.I)


def parse_transcript(raw):
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError('Transcript đang trống.')
    if len(raw) > MAX_CHARS:
        raise ValueError(f'Tối đa {MAX_CHARS:,} ký tự; hãy chia transcript theo cuộc họp.')
    turns = []
    for line_number, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        line = unicodedata.normalize('NFC', line.strip())
        prefix, sep, rest = line.partition(':')
        # A short capitalized name/diarization label is optional. Sentence colons
        # and URL schemes stay in the utterance, never become invented people.
        label = None
        words = prefix.split()
        is_name = 1 <= len(words) <= 4 and all(w.isalpha() and w[0].isupper() for w in words)
        is_label = bool(re.fullmatch(r'(?:người nói|speaker|s)\s*\d+|unknown|ẩn danh', prefix, re.I))
        if sep and (is_label or is_name) and prefix.casefold() not in ('url', 'api', 'http', 'https', 'chốt'):
            label = prefix
            if not rest.strip():
                raise ValueError(f'Dòng {line_number}: nhãn người nói có nội dung trống.')
        content = rest.strip() if label else line
        anonymous = bool(label and re.fullmatch(r'(?:người nói|speaker|s)\s*\d+|unknown|ẩn danh', label, re.I))
        speaker = label if label and not anonymous else None
        turns.append(dict(id=f'T{len(turns)+1}', line=line_number,
                          speaker=speaker, speaker_label=label, text=content))
    if not turns:
        raise ValueError('Transcript không có lượt nói.')
    if len(turns) > MAX_TURNS:
        raise ValueError(f'Tối đa {MAX_TURNS} lượt nói.')
    return turns


def body_of(text):
    match = re.match(r'^Về\s+([^,;:]+),\s*(.+)$', text, re.I)
    return match.group(2) if match else text


def literal_errors(entries, lookup, label):
    errors = []
    for ev in entries:
        turn = lookup.get(ev['turn_id'])
        if turn is None:
            errors.append(f'{label}: ID {ev["turn_id"]} không tồn tại')
        elif not ev['quote'].strip() or ev['quote'] not in turn['text']:
            errors.append(f'{label}: trích dẫn không khớp nguyên văn tại {ev["turn_id"]}')
    return errors


def validate_topics(topics, turns):
    payload = {'topics': topics}
    errors = schema_errors(payload, STAGE_ONE)
    if errors:
        raise ValueError('Bước 1 sai schema: ' + '; '.join(errors[:3]))
    lookup = {t['id']: t for t in turns}
    for topic in topics:
        errors.extend(literal_errors(topic['events'], lookup, topic['topic']))
    if errors:
        raise ValueError('Bước 1 có evidence không hợp lệ: ' + '; '.join(errors[:3]))


def validate_items(items, turns, semantic_checked=False):
    """Quarantine, don't erase, invalid candidates. This is NOT entailment checking."""
    lookup = {t['id']: t for t in turns}
    accepted, review, used = [], [], set()
    for original in items:
        row = copy.deepcopy(original)
        errors = schema_errors(row, ITEM)
        if not errors:
            if not row['id'].strip() or row['id'] in used:
                errors.append('ID mục trống hoặc trùng')
            used.add(row['id'])
            for key in ['topic', 'content', 'reason']:
                if not row[key].strip():
                    errors.append(f'{key} đang trống')
            if not row['evidence']:
                errors.append('Không có evidence')
            errors.extend(literal_errors(row['evidence'], lookup, 'Evidence'))
            errors.extend(literal_errors(row['history'], lookup, 'Diễn biến'))
            if row['type'] != 'action' and (row['owner'] is not None or row['due'] is not None):
                errors.append('Chỉ công việc được có người nhận hoặc hạn')
            if row['type'] == 'action':
                if row['owner'] is not None:
                    known = {turn['speaker'] for turn in turns if turn['speaker']}
                    supported = any(
                        (lookup.get(ev['turn_id'], {}).get('speaker') == row['owner'] and SELF_ASSIGN.search(ev['quote']))
                        or re.search(r'(?<!\w)' + re.escape(row['owner']) + r'(?!\w)', ev['quote'], re.I)
                        for ev in row['evidence'])
                    if re.fullmatch(r'(?:người nói|speaker|s)\s*\d+|unknown|ẩn danh', row['owner'], re.I):
                        supported = False
                    if row['owner'].casefold() in ('em', 'anh', 'chị', 'tôi', 'mình', 'bạn', 'chúng tôi') and row['owner'] not in known:
                        supported = False
                    if not supported:
                        errors.append('Người phụ trách thiếu bằng chứng giao việc hoặc tự nhận việc')
                if row['due'] is not None and (not row['due'].strip() or not any(
                        row['due'] in ev['quote'] for ev in row['evidence'])):
                    errors.append('Hạn không xuất hiện nguyên văn trong evidence')
                if row['status'] == 'confirmed' and row['owner'] is None:
                    errors.append('Công việc đã xác định cần người nhận; thiếu người thì cần xác nhận')
            if not semantic_checked and row['type'] == 'decision' and row['status'] == 'confirmed':
                explicit = any(FINAL.search(body_of(ev['quote'])) for ev in row['evidence'])
                agreeing = {lookup.get(ev['turn_id'], {}).get('speaker') for ev in row['evidence']
                            if re.search(r'\bđồng ý\b', ev['quote'], re.I)} - {None}
                if not explicit and len(agreeing) < 2:
                    errors.append('Không có chốt tường minh hoặc đồng thuận từ ít nhất hai người')
                if any(DEFER.search(body_of(ev['quote'])) for ev in row['evidence']):
                    errors.append('Evidence kết luận có tín hiệu hoãn/chưa chốt')
            if row['type'] == 'unresolved' and row['status'] == 'confirmed':
                errors.append('Nội dung chưa chốt không thể có trạng thái đã xác định')
        if errors:
            review.append(dict(item=row, errors=errors))
        else:
            accepted.append(row)
    return accepted, review


def classify(body):
    if DEFER.search(body):
        return 'defer'
    if FINAL.search(body):
        return 'finalize'
    if SELF_ASSIGN.search(body) or re.match(r'^(?:giao\s+\S+\s+|cần làm\s+)', body, re.I):
        return 'assign'
    if re.match(r'^(?:vướng mắc|vấn đề|bị chặn)\b', body, re.I):
        return 'issue'
    if re.match(r'^(?:yêu cầu|phản hồi|đề nghị)\b', body, re.I):
        return 'request_feedback'
    if re.match(r'^đề xuất\b', body, re.I):
        return 'proposal'
    if re.search(r'\bđồng ý\b', body, re.I):
        return 'support'
    if re.search(r'\b(?:phản đối|vượt ngân sách|không đồng ý)\b', body, re.I):
        return 'objection'
    return 'other'


def local_stage_one(turns):
    groups = OrderedDict()
    current = None
    for turn in turns:
        text = turn['text']
        match = re.match(r'^Về\s+([^,;:]+),\s*(.+)$', text, re.I)
        if match:
            current = match.group(1).strip().lower()
        kind = classify(body_of(text))
        if kind == 'other':
            continue
        topic = current or 'chưa xác định chủ đề'
        groups.setdefault(topic, []).append(dict(turn_id=turn['id'], kind=kind, quote=text))
    return [dict(topic=topic, events=events) for topic, events in groups.items()]


def local_stage_two(topics, turns):
    lookup = {t['id']: t for t in turns}
    items = []

    def emit(topic, ev, kind, status, history=None):
        owner, due = None, None
        body = body_of(ev['quote'])
        if kind == 'action':
            if SELF_ASSIGN.search(body):
                owner = lookup[ev['turn_id']]['speaker']
            else:
                assignment = re.match(r'^giao\s+(.+?)\s+(?:làm|sửa|cập nhật|kiểm tra)\b', body, re.I)
                if assignment:
                    owner = assignment.group(1).strip()
            date = DUE.search(body)
            if date:
                due = date.group(1).rstrip('.!;').strip()
            status = 'confirmed' if owner else 'needs_confirmation'
        reason = {
            'decision': 'Có câu chốt tường minh; đây là kết luận cuối được nhận diện của chủ đề.',
            'action': 'Giữ người nhận và hạn chỉ khi có bằng chứng nguyên văn; thiếu trường thì để null.',
            'issue': 'Có phát biểu nêu vướng mắc; cần người dùng kiểm tra ý nghĩa và tình trạng.',
            'request_feedback': 'Có yêu cầu/phản hồi; chưa tự chuyển thành công việc hoặc quyết định.',
            'unresolved': 'Không có kết luận tường minh cuối cùng hoặc đã hoãn/mở lại.',
        }[kind]
        items.append(dict(id=f'I{len(items)+1}', topic=topic, type=kind, status=status,
                          content=body, owner=owner, due=due,
                          evidence=[dict(turn_id=ev['turn_id'], quote=ev['quote'])],
                          reason=reason, history=copy.deepcopy(history or [])))

    for group in topics:
        events = group['events']
        timeline = [ev for ev in events if ev['kind'] in ('proposal', 'finalize', 'defer', 'change')]
        if timeline:
            binding = [ev for ev in timeline if ev['kind'] in ('finalize', 'defer')]
            final = binding[-1] if binding else timeline[-1]
            emit(group['topic'], final,
                 'decision' if final['kind'] == 'finalize' else 'unresolved',
                 'confirmed' if final['kind'] == 'finalize' else 'unresolved', timeline)
        for ev in events:
            kind = {'assign': 'action', 'issue': 'issue', 'request_feedback': 'request_feedback'}.get(ev['kind'])
            if kind:
                emit(group['topic'], ev, kind, 'needs_confirmation')
    return items


def check_candidates(candidates, turns, engine='local', model=None):
    """Literal validation followed by a separate model review, never gold labels."""
    items, review = validate_items(candidates, turns, semantic_checked=engine != 'local')
    verification = []
    if engine != 'local' and items:
        from .llm import verify_semantics
        items, semantic_review, verification = verify_semantics(items, turns, engine, model)
        review.extend(semantic_review)
    elif engine == 'local':
        # Local rules cannot certify paraphrases/entailment. Only unchanged
        # source utterances pass this narrow guard; manual rephrasing is blocked.
        kept = []
        for item in items:
            if any(item['content'] == body_of(ev['quote']) for ev in item['evidence']):
                kept.append(item)
            else:
                review.append(dict(item=item, errors=['Local không kiểm chứng được nội dung sửa; dùng LLM để kiểm tra ý nghĩa.']))
        items = kept
    return items, review, verification


def extract(raw, engine='local', model=None):
    turns = parse_transcript(raw)
    if engine == 'local':
        topics = local_stage_one(turns)
        validate_topics(topics, turns)
        candidates = local_stage_two(topics, turns)
        meta_model = None
    elif engine in ('openai', 'ollama'):
        from .llm import llm_extract
        topics, candidates, meta_model = llm_extract(turns, model=model, engine=engine)
    else:
        raise ValueError('Bộ trích xuất không hợp lệ.')
    items, review, verification = check_candidates(candidates, turns, engine, meta_model)
    return dict(schema_version='1.0', metadata=dict(engine=engine, model=meta_model,
                transcript_sha256=hashlib.sha256(raw.encode('utf-8')).hexdigest(),
                automated=True, semantic_verification=bool(verification),
                verification_method='llm_judgment' if verification else 'literal_rules',
                approval_required=True),
                turns=turns, topics=topics, items=items, review_queue=review,
                semantic_checks=verification)
