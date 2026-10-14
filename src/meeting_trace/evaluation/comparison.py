"""One-pass B versus the existing pipeline on the same data/model.

v2 reuses preserved pipeline outputs and runs B once. Fresh holdout runs both
arms once, with exclusive claims and no provider retry or prompt tuning.
"""
import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from ..config import PATHS
from ..meeting.baseline import extract_baseline, BASELINE_VERSION
from ..meeting.core import extract, parse_transcript
from ..meeting.llm import resolve_model
from .runner import dump, FROZEN
from .scoring import score
from .revalidate import canonical_hash

FILES=FROZEN+['src/meeting_trace/meeting/baseline.py',
    'src/meeting_trace/evaluation/comparison.py','src/meeting_trace/evaluation/scoring.py']


def current_hashes():
    return {name:hashlib.sha256((PATHS.root/name).read_bytes()).hexdigest() for name in FILES}


def execute(raw, arm, engine, model):
    try:
        return extract_baseline(raw,engine,model) if arm=='baseline_b' else extract(raw,engine,model)
    except (ValueError,OSError) as error:
        return dict(schema_version='1.0',metadata=dict(engine=engine,model=model,arm=arm,
            transcript_sha256=hashlib.sha256(raw.encode()).hexdigest(),automated=True,
            semantic_verification=False),turns=parse_transcript(raw),topics=[],items=[],
            review_queue=[],semantic_checks=[],error=dict(stage='pipeline',message=str(error)))


def write_report(base, manifest, suite):
    reports={}
    for arm in ['baseline_b','pipeline']:
        cases=[]
        for row in manifest:
            path=base/arm/(row['id']+'.json')
            if not path.exists(): continue
            result=json.loads(path.read_text(encoding='utf-8'))
            gold=json.loads((PATHS.root/row['expected']).read_text(encoding='utf-8'))
            cases.append(score(result,gold))
        report=dict(suite=suite,arm=arm,total=len(cases),expected_total=len(manifest),
            passed=sum(c['passed'] for c in cases),cases=cases,
            review_independent=False,completed=len(cases)==len(manifest))
        dump(base/(arm+'_report.json'),report)
        reports[arm]=report
    print(json.dumps({arm:dict(passed=r['passed'],total=r['total']) for arm,r in reports.items()},ensure_ascii=False),flush=True)


def main():
    if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite',choices=['v2','holdout-v3'],default='v2')
    parser.add_argument('--engine',choices=['ollama','openai'],default='ollama')
    parser.add_argument('--model')
    parser.add_argument('--freeze',action='store_true')
    parser.add_argument('--report-only',action='store_true')
    args=parser.parse_args()
    model=resolve_model(args.engine,args.model)
    if not model: parser.exit(1,'Chưa cấu hình model; không tạo kết quả thay thế.\n')
    if args.suite=='v2':
        old=json.loads((PATHS.fixtures/'dataset_manifest.json').read_text(encoding='utf-8'))
        manifest=[{**row,'transcript':'data/examples/'+row['id']+'.txt',
            'expected':'tests/fixtures/'+row['id']+'.expected.json'} for row in old]
    else:
        manifest=json.loads((PATHS.root/'data/holdout-v3/manifest.json').read_text(encoding='utf-8'))
    base=PATHS.benchmarks/'comparisons'/model.replace(':','-').replace('/','-')/args.suite
    freeze=base/'protocol.json'
    if args.freeze:
        if freeze.exists(): parser.exit(1,'Protocol đã tồn tại; không ghi đè.\n')
        dump(freeze,dict(at=datetime.now(timezone.utc).isoformat(),engine=args.engine,model=model,
            hashes=current_hashes(),manifest_sha256=canonical_hash(manifest),
            arms=['baseline_b','pipeline'],baseline_version=BASELINE_VERSION,
            dataset_independent=False,no_retry=True,provider_options=dict(temperature=0,seed=42,num_ctx=8192,num_predict=4000)))
        print('Frozen comparison protocol.'); return
    if args.report_only:
        write_report(base,manifest,args.suite); return
    if not freeze.exists(): parser.exit(1,'Cần --freeze trước khi gọi model.\n')
    protocol=json.loads(freeze.read_text(encoding='utf-8'))
    if protocol['hashes']!=current_hashes() or protocol['manifest_sha256']!=canonical_hash(manifest) or protocol['engine']!=args.engine or protocol['model']!=model:
        parser.exit(1,'Protocol/data/model đã đổi sau freeze; dừng.\n')
    for row in manifest:
        raw=(PATHS.root/row['transcript']).read_text(encoding='utf-8')
        expected=PATHS.root/row['expected']
        if hashlib.sha256(raw.encode()).hexdigest()!=row['transcript_sha256'] or hashlib.sha256(expected.read_bytes()).hexdigest()!=row['expected_sha256']:
            parser.exit(1,'Input/kỳ vọng đã đổi: '+row['id']+'\n')
        for arm in ['baseline_b','pipeline']:
            path=base/arm/(row['id']+'.json')
            claim=base/'claims'/(arm+'-'+row['id']+'.json')
            if path.exists(): continue
            claim.parent.mkdir(parents=True,exist_ok=True)
            try:
                with claim.open('x',encoding='utf-8') as handle:
                    json.dump(dict(started_at=datetime.now(timezone.utc).isoformat(),arm=arm,id=row['id']),handle)
            except FileExistsError:
                parser.exit(1,'Case đã bắt đầu nhưng chưa hoàn tất; không tự gọi lại: '+row['id']+' / '+arm+'\n')
            if args.suite=='v2' and arm=='pipeline' and args.engine=='ollama' and model=='qwen2.5:7b':
                source=PATHS.benchmarks/'results/ollama'/(row['id']+'.json')
                result=json.loads(source.read_text(encoding='utf-8'))
                result['comparison_execution']=dict(kind='preserved_live_pipeline',
                    source=source.relative_to(PATHS.root).as_posix(),source_sha256=canonical_hash(result))
            else:
                print('Running '+args.suite+' / '+arm+' / '+row['id'],flush=True)
                started=time.perf_counter()
                result=execute(raw,arm,args.engine,model)
                result['run_seconds']=round(time.perf_counter()-started,3)
                result['comparison_execution']=dict(kind='live_once_no_retry')
            dump(path,result)
    write_report(base,manifest,args.suite)


if __name__=='__main__': main()
