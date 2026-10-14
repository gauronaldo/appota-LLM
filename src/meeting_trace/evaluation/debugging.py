"""Offline boundary diagnostics. Existing gold/results/scorer remain unchanged."""
import argparse
import copy
import hashlib
import json
import re
import sys
from collections import Counter

from ..config import PATHS
from ..meeting.core import parse_transcript, validate_items, extract
from ..meeting.llm import source_quotes
from ..meeting.schema import CHECK_FIELDS
from .runner import dump
from .scoring import score
from .revalidate import canonical_hash

BASE = PATHS.benchmarks / 'debug/2026-10-14'
COMPARISON = PATHS.benchmarks / 'comparisons/qwen2.5-7b'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def cases():
    for suite in ['v2', 'holdout-v3']:
        rows = load(PATHS.fixtures/'dataset_manifest.json') if suite == 'v2' else load(PATHS.root/'data/holdout-v3/manifest.json')
        for row in rows:
            transcript = PATHS.examples/(row['id']+'.txt') if suite == 'v2' else PATHS.root/row['transcript']
            expected = PATHS.fixtures/(row['id']+'.expected.json') if suite == 'v2' else PATHS.root/row['expected']
            yield suite, row, transcript.read_text(encoding='utf-8'), load(expected)


def oracle(gold, turns):
    """Synthetic correct-field inputs to test downstream guards, NOT extraction."""
    items=[]
    for i, label in enumerate(gold['items'], 1):
        text=next(t['text'] for t in turns if t['id']==label['evidence_turn'])
        items.append(dict(id='O'+str(i), topic=label['topic'],type=label['type'],status=label['status'],
            content=text,owner=label['owner'],due=label['due'],
            evidence=source_quotes([dict(turn_id=label['evidence_turn'])],turns),
            reason='Diagnostic oracle: fields from frozen label, content from source; not a model prediction.',
            history=source_quotes([dict(turn_id=id,kind='other') for id in gold['history_turns']],turns)))
    return items


def field_ablation(result, gold):
    """One-field-at-a-time relaxed sensitivity, never a replacement score.

    Each exclusion retains all other checks and operates on copies only.
    Exact topic/content matching is retained for normal reported scores.
    """
    values={}
    for field in ['topic','content_phrase','conditions','status','owner','due','evidence','history','extras','queue']:
        actual, expected=copy.deepcopy(result),copy.deepcopy(gold)
        if field=='topic':
            for item in actual['items']: item['topic']='*'
            for item in expected['items']: item['topic']='*'
        elif field=='content_phrase':
            for item in expected['items']: item['contains']=''
        elif field=='conditions':
            for item in expected['items']: item['conditions']=[]
        elif field=='status':
            for item in actual['items']: item['status']='*'
            for item in expected['items']: item['status']='*'
        elif field in ('owner','due'):
            for item in actual['items']: item[field]=None
            for item in expected['items']: item[field]=None
        elif field=='evidence':
            for item in actual['items']: item['evidence']=[dict(turn_id='*')]
            for item in expected['items']: item['evidence_turn']='*'
        elif field=='history': expected['history_turns']=[]
        elif field=='queue': actual['review_queue']=[]
        elif field=='extras':
            actual['items']=[item for item in actual['items'] if any(
                item['type']==g['type'] and item['topic'].casefold()==g['topic'].casefold()
                and g['contains'].casefold() in item['content'].casefold()
                and all(c.casefold() in item['content'].casefold() for c in g.get('conditions',[]))
                for g in expected['items'])]
        values[field]=score(actual,expected)['passed']
    return values


def diagnose():
    rows=[]
    verifier_diagnostics=[]
    for suite, manifest, raw, gold in cases():
        turns=parse_transcript(raw)
        ideal=oracle(gold,turns)
        accepted, blocked=validate_items(ideal,turns,semantic_checked=True)
        # A source-only correct-field synthetic answer also exposes label/scorer
        # demands that are not literally stated in the required evidence turn.
        oracle_result=dict(items=accepted,review_queue=blocked)
        arms={}
        for arm in ['baseline_b','pipeline']:
            result=load(COMPARISON/suite/arm/(gold['id']+'.json'))
            candidates=result['items']+[q['item'] for q in result['review_queue']]
            events=[e for topic in result['topics'] for e in topic['events']]
            event_refs={e['turn_id'] for e in events}
            local_accepted, local_blocked=validate_items(candidates,turns,semantic_checked=True)
            checked={c['item_id']:c for c in result.get('semantic_checks',[])}
            for id, check in checked.items():
                verifier_diagnostics.append(dict(suite=suite,case=gold['id'],item_id=id,
                    all_pass=all(check[k]=='pass' for k in CHECK_FIELDS),
                    reason_chars=len(check['reason']),
                    chinese=bool(re.search('[\u4e00-\u9fff]',check['reason'])),
                    repeats_prompt=any(s in check['reason'] for s in ['Không tự thêm candidate','按照schema','trả JSON theo schema'])))
            sem_rejected=[id for id,c in checked.items() if any(c[k]!='pass' for k in CHECK_FIELDS)
                or not c['evidence'] or not c['reason'].strip()]
            matched={g['evidence_turn'] for g in gold['items'] if any(
                g['evidence_turn'] in {e['turn_id'] for e in c['evidence']} for c in candidates)}
            arms[arm]=dict(source_canonical_sha256=canonical_hash(result),
                strict_pass=score(result,gold)['passed'], ablations=field_ablation(result,gold),
                candidates=len(candidates),accepted=len(result['items']),literal_blocked=local_blocked,
                verifier_rejected_ids=sem_rejected,verifier_all_pass_ids=[id for id,c in checked.items() if all(c[k]=='pass' for k in CHECK_FIELDS)],
                stage_one_topics=[t['topic'] for t in result['topics']],
                expected_evidence_not_in_stage_one=sorted({g['evidence_turn'] for g in gold['items']}-event_refs) if arm=='pipeline' and not result.get('error') else None,
                expected_evidence_not_in_any_candidate=sorted({g['evidence_turn'] for g in gold['items']}-matched),
                error=result.get('error'))
        issues=[]
        for g in gold['items']:
            source=next(t['text'] for t in turns if t['id']==g['evidence_turn'])
            if g['contains'].casefold() not in source.casefold():
                issues.append(dict(kind='required_content_not_in_required_turn',topic=g['topic'],contains=g['contains'],evidence_turn=g['evidence_turn'],source=source))
            if g['type'] in ('issue','request_feedback') and g['status']=='needs_confirmation':
                issues.append(dict(kind='status_policy_not_defined_for_this_type_in_prompt',type=g['type'],status=g['status']))
        rows.append(dict(suite=suite,id=gold['id'],turns=len(turns),
            parser_preserves_text=all(t['text'] in raw for t in turns),
            gold_items=len(gold['items']),gold_source_observations=issues,
            oracle_guard_blocked=blocked,oracle_strict_score=score(oracle_result,gold),arms=arms))
    summary={}
    for suite in ['v2','holdout-v3']:
        subset=[r for r in rows if r['suite']==suite]
        summary[suite]=dict(total=len(subset),parser_text_preserved=sum(r['parser_preserves_text'] for r in subset),
            oracle_guard_blocked_cases=[r['id'] for r in subset if r['oracle_guard_blocked']],
            gold_issue_request_status_cases=[r['id'] for r in subset if any(o['kind']=='status_policy_not_defined_for_this_type_in_prompt' for o in r['gold_source_observations'])],arms={})
        for arm in ['baseline_b','pipeline']:
            a=[r['arms'][arm] for r in subset]
            summary[suite]['arms'][arm]=dict(strict=sum(r['strict_pass'] for r in a),
                single_field_ablation_passed={field:sum(r['ablations'][field] for r in a) for field in a[0]['ablations']},
                candidates=sum(r['candidates'] for r in a),accepted=sum(r['accepted'] for r in a),
                literal_blocked=sum(len(r['literal_blocked']) for r in a),
                verifier_rejected=sum(len(r['verifier_rejected_ids']) for r in a),
                verifier_all_pass=sum(len(r['verifier_all_pass_ids']) for r in a),
                errors=sum(bool(r['error']) for r in a))
    return dict(kind='offline_layer_diagnosis_not_new_benchmark',gold_oracle_not_model=True,
        relaxation_not_quality_score=True,reference_presence_proxy_not_semantics=True,
        summary=summary,cases=rows,verifier_diagnostics=verifier_diagnostics)


def item(type='action',status='confirmed',owner='Mai',due='thứ Sáu',content=None,raw=None):
    raw=raw or 'Mai: Em sẽ gửi báo cáo trước thứ Sáu.'
    turns=parse_transcript(raw)
    return dict(id='P1',topic='báo cáo',type=type,status=status,
        content=content or turns[0]['text'],owner=owner,due=due,
        evidence=source_quotes([dict(turn_id='T1')],turns),reason='Boundary probe',history=[]),turns


def boundary_probes():
    experiments=[]
    # Source text is identical except the commitment phrase.
    for label, raw in [('self_will_send','Mai: Em sẽ gửi báo cáo trước thứ Sáu.'),
                       ('self_accept_send','Mai: Em nhận gửi báo cáo trước thứ Sáu.')]:
        row, turns=item(raw=raw)
        kept,blocked=validate_items([row],turns,semantic_checked=True)
        experiments.append(dict(id=label,expected='accept known-speaker commitment',accepted=bool(kept),blocked=blocked))
    for label,raw,content,owner,due in [
        ('named_but_not_assigned','Huy: Mai đang nghỉ, chưa có ai nhận gửi báo cáo trước thứ Sáu.','Mai gửi báo cáo trước thứ Sáu.','Mai','thứ Sáu'),
        ('drop_condition','Huy: Ngọc gửi CSV đã mã hóa sau khi pháp chế xác nhận, trước thứ Năm.','Ngọc gửi CSV cho đối tác.','Ngọc','thứ Năm')]:
        row,turns=item(raw=raw,content=content,owner=owner,due=due)
        kept,blocked=validate_items([row],turns,semantic_checked=True)
        experiments.append(dict(id=label,expected='reject unsupported/unconditional action',accepted=bool(kept),blocked=blocked))
    row,turns=item(type='decision',owner=None,due=None,
        raw='Minh: Chốt dùng B.\nMinh: Hủy B, hôm nay chưa chọn phương án nào.',content='Chốt dùng B.')
    kept,blocked=validate_items([row],turns,semantic_checked=True)
    experiments.append(dict(id='overridden_decision',expected='reject cancelled decision',accepted=bool(kept),blocked=blocked))
    row,turns=item(type='unresolved',status='needs_confirmation',owner=None,due=None,
        raw='Minh: Hôm nay chưa chốt lựa chọn.',content='Hôm nay chưa chốt lựa chọn.')
    kept,blocked=validate_items([row],turns,semantic_checked=True)
    experiments.append(dict(id='unresolved_status_ambiguity',expected='schema permits status that disagrees with gold policy',accepted=bool(kept),blocked=blocked))
    return dict(kind='code_boundary_probes_no_model',not_benchmark=True,probes=experiments)


def scoring_probes():
    probes=[]
    for id, contradiction in [
        ('05_unnamed_reversal','Không chuyển sang cổng B cho đợt thử tiếp theo.'),
        ('03_switch_condition','Không chọn gói B nếu pháp chế duyệt điều khoản lưu dữ liệu.')]:
        gold=load(PATHS.fixtures/(id+'.expected.json'))
        raw=(PATHS.examples/(id+'.txt')).read_text(encoding='utf-8')
        rows=oracle(gold,parse_transcript(raw))
        rows[0]['content']=contradiction
        scored=score(dict(items=rows,review_queue=[]),gold)
        probes.append(dict(id='negated_'+id,expected='fail contradictory conclusion',
            actual_passed=scored['passed'],content=contradiction,score=scored))
    id='20_explicit_name_in_content'
    gold=load(PATHS.fixtures/(id+'.expected.json'))
    result=load(COMPARISON/'v2/baseline_b'/(id+'.json'))
    probes.append(dict(id='legitimate_fields_counted_invented',
        expected='owner Mai and due thứ Sáu have source; neither is invented',
        metric=score(result,gold)['metrics']['invented_owner_due'],
        source_canonical_sha256=canonical_hash(result)))
    return dict(kind='scorer_boundary_probes_not_quality_score',probes=probes)


def main():
    if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    data=diagnose()
    dump(BASE/'offline.json',data)
    dump(BASE/'boundary_probes.json',boundary_probes())
    dump(BASE/'scoring_probes.json',scoring_probes())
    print(json.dumps(data['summary'],ensure_ascii=False,indent=2))


if __name__=='__main__': main()
