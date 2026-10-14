"""Local diagnostic interventions, isolated from frozen benchmark outputs.

Records real Ollama request/response and token counters. One call per declared
experiment/stage, no hidden retries. No output replaces benchmark data.
"""
import argparse
import copy
import hashlib
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from unittest.mock import patch

from ..config import PATHS
from ..meeting import llm, baseline
from ..meeting.core import extract, parse_transcript, validate_items
from ..meeting.schema import MODEL_STAGE_TWO, schema_errors
from .comparison import current_hashes
from .debugging import BASE, load
from .runner import dump

CONTRACT_ADDENDUM = '''
For this diagnostic product contract, statuses are defined exactly as follows:
decision: confirmed when the conditional or unconditional final choice is agreed;
keep any condition in content. Reopened/cancelled choice becomes unresolved.
action: confirmed only with a known assignee and no unsatisfied prerequisite;
otherwise needs_confirmation, including anonymous assignees and conditional work.
issue and request_feedback: needs_confirmation (human follow-up still required),
even if the problem/request is clearly reported. This is a workflow policy.
unresolved: unresolved for an explicitly unsettled choice; needs_confirmation
for an ambiguous intention that was never accepted as an assignment.
Information being reported reliably is not the same as follow-up being settled.
Extract each valuable request/problem/task independently; no need to promote
requests to tasks. A task owner must be stored in owner, not only in content.
'''

PLAN = [
    dict(id='L01_topic_control',kind='stage_two',case='03_switch_condition',intervention='saved topics unchanged'),
    dict(id='L02_topic_rename',kind='stage_two',case='03_switch_condition',intervention='ONLY first topic name changed from lưu trữ to email; no event or transcript changes'),
    dict(id='L03_contract_control',kind='baseline',case='17_clear_assignment',intervention='existing B prompt'),
    dict(id='L04_contract_defined',kind='baseline',case='17_clear_assignment',intervention='same B prompt + explicit general status/workflow contract'),
    dict(id='L05_truncation_trace',kind='pipeline',case='05_unnamed_reversal',intervention='unchanged production pipeline, record every API stage'),
    dict(id='L06_clear_self_commit',kind='micro',case=None,intervention='single explicit known-speaker commitment, existing B/schema/guard'),
]


class Recorder:
    def __init__(self): self.calls=[]

    def call(self, engine, prompt, data, schema, name, model):
        if engine!='ollama': raise ValueError('Diagnostics must stay local.')
        payload=dict(model=model,stream=False,keep_alive='10m',format=schema,
            messages=[dict(role='system',content=prompt),dict(role='user',content=json.dumps(data,ensure_ascii=False))],
            options=dict(temperature=0,seed=42,num_ctx=8192,num_predict=4000))
        call=dict(stage=name,request=payload,started_at=datetime.now(timezone.utc).isoformat())
        self.calls.append(call)
        started=time.perf_counter()
        try:
            req=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(payload).encode(),
                method='POST',headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=600) as response: result=json.load(response)
            call['response']=result
            if result.get('done') is not True or result.get('done_reason')=='length':
                raise ValueError('Ollama incomplete or output length limit reached.')
            parsed=json.loads(result['message']['content'])
            errors=schema_errors(parsed,schema)
            if errors: raise ValueError('Ollama schema: '+'; '.join(errors[:3]))
            return parsed
        except Exception as error:
            call['error']=dict(type=type(error).__name__,message=str(error))
            raise
        finally:
            call['run_seconds']=round(time.perf_counter()-started,3)


def main():
    if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze',action='store_true')
    parser.add_argument('--model',default='qwen2.5:7b')
    args=parser.parse_args()
    base=BASE/'live'
    protocol_path=base/'protocol.json'
    hashes={**current_hashes(),'src/meeting_trace/evaluation/debug_live.py':hashlib.sha256(Path_source().read_bytes()).hexdigest()}
    data=dict(at=datetime.now(timezone.utc).isoformat(),model=args.model,plan=PLAN,hashes=hashes,
        purpose='diagnosis on already observed v2; no new holdout or quality claim',no_retry=True,
        options=dict(temperature=0,seed=42,num_ctx=8192,num_predict=4000))
    if args.freeze:
        if protocol_path.exists(): parser.exit(1,'Diagnostic protocol already exists.\n')
        dump(protocol_path,data); print('Frozen diagnostic plan.'); return
    if not protocol_path.exists(): parser.exit(1,'Freeze diagnostic plan first.\n')
    protocol=load(protocol_path)
    if protocol['hashes']!=hashes or protocol['model']!=args.model or protocol['plan']!=PLAN:
        parser.exit(1,'Diagnostic code/model/plan changed.\n')
    for experiment in PLAN:
        target=base/(experiment['id']+'.json')
        if target.exists(): continue
        claim=base/'claims'/(experiment['id']+'.json')
        claim.parent.mkdir(parents=True,exist_ok=True)
        try:
            with claim.open('x',encoding='utf-8') as handle: json.dump(dict(at=datetime.now(timezone.utc).isoformat(),id=experiment['id']),handle)
        except FileExistsError: parser.exit(1,'Experiment started but no output; do not silently retry.\n')
        print('Running '+experiment['id'],flush=True)
        recorder=Recorder()
        record=dict(experiment=experiment,benchmark=False,calls=recorder.calls)
        raw=(PATHS.examples/(experiment['case']+'.txt')).read_text(encoding='utf-8') if experiment['case'] else 'Mai: Em sẽ gửi báo cáo trước thứ Sáu.'
        record['input_sha256']=hashlib.sha256(raw.encode()).hexdigest()
        try:
            with patch.object(llm,'provider_call',recorder.call), patch.object(baseline,'provider_call',recorder.call):
                if experiment['kind']=='pipeline':
                    result=extract(raw,'ollama',args.model)
                    record['result']=result
                elif experiment['kind'] in ('baseline','micro'):
                    prompt=baseline.BASELINE_PROMPT
                    if experiment['id']=='L04_contract_defined': prompt+='\n'+CONTRACT_ADDENDUM
                    with patch.object(baseline,'BASELINE_PROMPT',prompt):
                        record['result']=baseline.extract_baseline(raw,'ollama',args.model)
                else:
                    turns=parse_transcript(raw)
                    topics=copy.deepcopy(load(PATHS.benchmarks/'results/ollama/03_switch_condition.json')['topics'])
                    if experiment['id']=='L02_topic_rename': topics[0]['topic']='email'
                    candidates=recorder.call('ollama',llm.STAGE_TWO_PROMPT,dict(turns=turns,topics=topics),MODEL_STAGE_TWO,'meeting_items',args.model)['items']
                    for item in candidates:
                        item['evidence']=llm.source_quotes(item['evidence'],turns)
                        item['history']=llm.source_quotes(item['history'],turns)
                    kept,blocked=validate_items(candidates,turns,semantic_checked=True)
                    record['result']=dict(turns=turns,topics=topics,items=kept,review_queue=blocked,semantic_checks=[])
        except Exception as error:
            record['error']=dict(type=type(error).__name__,message=str(error))
        dump(target,record)
        print(experiment['id']+': '+('error' if record.get('error') else 'complete')+
            '; calls='+str(len(recorder.calls)),flush=True)


def Path_source():
    from pathlib import Path
    return Path(__file__)


if __name__=='__main__': main()
