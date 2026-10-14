"""Apply current literal guards to preserved live LLM outputs; never rerun/fake AI.

Only previously accepted candidates can remain accepted. Semantic verdicts and
live inference timing/provenance remain unchanged; no quarantined item promoted.
"""
import argparse
import copy
import hashlib
import json
from datetime import datetime, timezone

from ..config import PATHS
from ..meeting.core import validate_items
from .runner import dump, hashes
from .scoring import score
from .reporting import render_tests


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':')).encode('utf-8')).hexdigest()


def revalidate(result):
    updated=copy.deepcopy(result)
    accepted,queue=validate_items(updated['items'], updated['turns'], semantic_checked=True)
    updated['items']=accepted
    updated['review_queue'].extend(queue)
    checked=bool(updated.get('semantic_checks'))
    updated['metadata']['semantic_verification']=checked
    updated['metadata']['verification_method']='llm_judgment' if checked else 'literal_rules'
    updated['postvalidation']=dict(kind='literal_only_no_new_inference',
        at=datetime.now(timezone.utc).isoformat(), source_canonical_sha256=canonical_hash(result),
        core_hashes=hashes())
    return updated


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    source=PATHS.benchmarks/'baselines/qwen-v2-live/ollama'
    target=PATHS.benchmarks/'results/ollama'
    manifest=json.loads((PATHS.fixtures/'dataset_manifest.json').read_text(encoding='utf-8'))
    scored={}
    for row in manifest:
        fixture=PATHS.fixtures/(row['id']+'.expected.json')
        raw=(PATHS.examples/(row['id']+'.txt')).read_text(encoding='utf-8')
        if hashlib.sha256(fixture.read_bytes()).hexdigest()!=row['expected_sha256'] or hashlib.sha256(raw.encode()).hexdigest()!=row['transcript_sha256']:
            raise ValueError('Input/kỳ vọng v2 đã đổi; dừng hậu kiểm.')
        previous=json.loads((source/(row['id']+'.json')).read_text(encoding='utf-8'))
        if previous['metadata']['transcript_sha256']!=row['transcript_sha256']:
            raise ValueError('Kết quả LLM không khớp transcript.')
        updated=revalidate(previous)
        dump(target/(row['id']+'.json'),updated)
        scored[row['id']]=score(updated,json.loads(fixture.read_text(encoding='utf-8')))
    for split in ['dev','holdout']:
        report=json.loads((source/(split+'_report.json')).read_text(encoding='utf-8'))
        cases=[scored[row['id']] for row in manifest if row['split']==split]
        report['cases']=cases
        report['passed']=sum(c['passed'] for c in cases)
        metrics={key:sum(c['metrics'][key] for c in cases) for key in cases[0]['metrics']}
        tp,fp,fn=[metrics[key] for key in ['decision_tp','decision_fp','decision_fn']]
        metrics.update(decision_precision=round(tp/(tp+fp),4) if tp+fp else None,
            decision_recall=round(tp/(tp+fn),4) if tp+fn else None,
            intermediate_promotion_rate=round(metrics['intermediate_promoted']/metrics['intermediate_total'],4) if metrics['intermediate_total'] else None)
        report['metrics']=metrics
        for field in ['groups','input_formats']:
            key='group' if field=='groups' else 'input_format'
            for value,counts in report[field].items():
                counts['passed']=sum(c['passed'] and c[key]==value for c in cases)
        report['postvalidation']=dict(kind='literal_only_no_new_inference',
            at=datetime.now(timezone.utc).isoformat(), core_hashes=hashes(),
            source='data/benchmarks/baselines/qwen-v2-live/ollama')
        dump(target/(split+'_report.json'),report)
    render_tests('ollama')
    print('Revalidated preserved live outputs; no model calls, gold unchanged.')


if __name__=='__main__': main()
