"""Optional real OpenAI Responses API adapter; not used by local runs.

No SDK dependency. No key saved, printed, or accepted in browser payloads.
"""
import json
import os
import urllib.error
import urllib.request

from .core import validate_topics, literal_errors
from .prompts import STAGE_ONE_PROMPT, STAGE_TWO_PROMPT, VERIFY_PROMPT
from .schema import MODEL_STAGE_ONE, MODEL_STAGE_TWO, MODEL_SEMANTIC, CHECK_FIELDS, schema_errors


def call_model(prompt, data, schema, name, model):
    key = os.environ.get('OPENAI_API_KEY', '').strip()
    if not key:
        raise ValueError('Chưa có OPENAI_API_KEY. Hãy dùng chế độ local hoặc đặt key ở biến môi trường.')
    payload = dict(model=model, store=False, max_output_tokens=10000,
                   input=[dict(role='system', content=prompt),
                          dict(role='user', content=json.dumps(data, ensure_ascii=False))],
                   text=dict(format=dict(type='json_schema', name=name, strict=True, schema=schema)))
    req = urllib.request.Request('https://api.openai.com/v1/responses',
                                 data=json.dumps(payload).encode(), method='POST',
                                 headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        # Never print response bodies or headers which may contain private data.
        raise ValueError(f'OpenAI HTTP {error.code}: kiểm tra model, key, quota và quyền API.') from None
    except (urllib.error.URLError, TimeoutError):
        raise ValueError('Không kết nối được OpenAI hoặc đã hết thời gian chờ. Không tạo kết quả thay thế.') from None
    if result.get('status') != 'completed':
        raise ValueError('API chưa hoàn tất; không sử dụng JSON bị cắt ngắn.')
    chunks = []
    for output in result.get('output', []):
        for content in output.get('content', []):
            if content.get('type') == 'refusal':
                raise ValueError('Model từ chối xử lý. Không tạo dữ liệu thay thế.')
            if content.get('type') == 'output_text':
                chunks.append(content['text'])
    try:
        return json.loads(''.join(chunks))
    except (ValueError, TypeError):
        raise ValueError('API không trả JSON hợp lệ.') from None


def resolve_model(engine, model=None):
    return model or os.environ.get('OLLAMA_MODEL' if engine == 'ollama' else 'OPENAI_MODEL', '').strip() or ('qwen2.5:7b' if engine == 'ollama' else '')


def call_ollama(prompt, data, schema, name, model):
    """Local-only endpoint; no cloud fallback, no automatic model downloads."""
    payload = dict(model=model, stream=False, keep_alive='10m', format=schema,
                   messages=[dict(role='system', content=prompt),
                             dict(role='user', content=json.dumps(data, ensure_ascii=False))],
                   options=dict(temperature=0, seed=42, num_ctx=8192, num_predict=4000))
    req = urllib.request.Request('http://127.0.0.1:11434/api/chat',
                                 data=json.dumps(payload).encode(), method='POST',
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=600) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        raise ValueError(f'Ollama HTTP {error.code}: kiểm tra model đã cài và server local.') from None
    except (urllib.error.URLError, TimeoutError):
        raise ValueError('Không kết nối được Ollama local hoặc hết thời gian chờ; không tạo kết quả thay thế.') from None
    if result.get('done') is not True or result.get('done_reason') == 'length':
        raise ValueError('Ollama chưa hoàn tất hoặc output bị cắt ngắn.')
    try:
        parsed = json.loads(result['message']['content'])
    except (ValueError, KeyError, TypeError):
        raise ValueError('Ollama không trả JSON hợp lệ.') from None
    errors = schema_errors(parsed, schema)
    if errors:
        raise ValueError('Ollama sai schema: ' + '; '.join(errors[:3]))
    return parsed


def provider_call(engine, *args):
    if engine == 'ollama':
        return call_ollama(*args)
    if engine == 'openai':
        return call_model(*args)
    raise ValueError('Provider không hợp lệ.')


def llm_extract(turns, model=None, engine='openai'):
    model = resolve_model(engine, model)
    if not model:
        raise ValueError('Đặt OPENAI_MODEL thành model tài khoản của bạn được quyền dùng, hỗ trợ Structured Outputs.')
    stage_one = provider_call(engine, STAGE_ONE_PROMPT, {'turns': turns}, MODEL_STAGE_ONE, 'meeting_events', model)
    enforce_schema(stage_one, MODEL_STAGE_ONE)
    if not isinstance(stage_one, dict) or 'topics' not in stage_one:
        raise ValueError('Bước 1 thiếu topics.')
    topics = stage_one['topics']
    for topic in topics:
        topic['events'] = source_quotes(topic['events'], turns)
    validate_topics(topics, turns)
    stage_two = provider_call(engine, STAGE_TWO_PROMPT, {'turns': turns, 'topics': topics}, MODEL_STAGE_TWO, 'meeting_items', model)
    enforce_schema(stage_two, MODEL_STAGE_TWO)
    if not isinstance(stage_two, dict) or not isinstance(stage_two.get('items'), list):
        raise ValueError('Bước 2 thiếu items. Không tạo dữ liệu thay thế.')
    for item in stage_two['items']:
        item['evidence'] = source_quotes(item['evidence'], turns)
        item['history'] = source_quotes(item['history'], turns)
    return topics, stage_two['items'], model


def enforce_schema(value, schema):
    errors = schema_errors(value, schema)
    if errors:
        raise ValueError('LLM sai schema: ' + '; '.join(errors[:3]))


def source_quotes(references, turns):
    lookup = {turn['id']: turn['text'] for turn in turns}
    rows = []
    for ref in references:
        if ref['turn_id'] not in lookup:
            raise ValueError('LLM chọn ID evidence không tồn tại: ' + ref['turn_id'])
        rows.append({**ref, 'quote':lookup[ref['turn_id']]})
    return rows


def verify_semantics(items, turns, engine, model=None):
    model = resolve_model(engine, model)
    result = provider_call(engine, VERIFY_PROMPT, dict(turns=turns, candidates=items),
                           MODEL_SEMANTIC, 'meeting_verification', model)
    errors = schema_errors(result, MODEL_SEMANTIC)
    if errors:
        raise ValueError('Bộ kiểm chứng sai schema: ' + '; '.join(errors[:3]))
    checks = result['checks']
    for check in checks:
        check['evidence'] = source_quotes(check['evidence'], turns)
    if sorted(c['item_id'] for c in checks) != sorted(i['id'] for i in items):
        raise ValueError('Bộ kiểm chứng thiếu/trùng/sai ID; không sử dụng kết quả.')
    lookup = {t['id']: t for t in turns}
    accepted, review = [], []
    for item in items:
        check = next(c for c in checks if c['item_id'] == item['id'])
        issues = literal_errors(check['evidence'], lookup, 'Kiểm chứng')
        if not check['evidence'] or not check['reason'].strip():
            issues.append('Kiểm chứng thiếu evidence hoặc lý do')
        issues.extend(key + ': ' + check[key] for key in CHECK_FIELDS if check[key] != 'pass')
        if issues:
            review.append(dict(item=item, errors=issues + [check['reason']], semantic_check=check))
        else:
            accepted.append(item)
    return accepted, review, checks
