"""One-off local verifier probes; isolate candidate-reason anchoring."""
import argparse
import copy
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from unittest.mock import patch

from ..meeting import llm
from ..meeting.core import parse_transcript
from .comparison import current_hashes
from .debugging import BASE, item, load
from .debug_live import Recorder
from .runner import dump


def probes():
    row,turns=item(raw='Huy: Mai đang nghỉ, chưa có ai nhận gửi báo cáo trước thứ Sáu.',
        content='Mai gửi báo cáo trước thứ Sáu.',owner='Mai',due='thứ Sáu')
    first=dict(id='V01_negated_assignment',turns=turns,candidate=row,
        expected='reject fabricated assignment; named mention is not an assignment')
    raw='Huy: Pháp chế chưa xác nhận quyền chia sẻ.\nHuy: Ngọc gửi CSV đã mã hóa sau khi pháp chế xác nhận, trước thứ Năm.\nNgọc: Nếu chưa được duyệt thì em chưa gửi.'
    turns=parse_transcript(raw)
    second=dict(id='V02_condition_neutral_reason',turns=turns,
        candidate=dict(id='P1',topic='xuất dữ liệu',type='action',status='confirmed',
            content='Ngọc gửi CSV cho đối tác.',owner='Ngọc',due='thứ Năm',
            evidence=llm.source_quotes([dict(turn_id='T2')],turns),history=[],
            reason='Có câu giao việc trong transcript.'),expected='reject: encryption and legal condition missing, not unconditionally confirmed')
    third=copy.deepcopy(second)
    third['id']='V03_condition_false_reason'
    third['candidate']['reason']='Pháp chế đã xác nhận quyền chia sẻ nên Ngọc được gửi ngay.'
    return [first,second,third]


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    base=BASE/'verifier'
    protocol=base/'protocol.json'
    plan=probes()
    if protocol.exists(): parser.exit(1,'Verifier diagnostic already claimed; no retry.\n')
    dump(protocol,dict(at=datetime.now(timezone.utc).isoformat(),plan=plan,
        hashes=current_hashes(),model='qwen2.5:7b',not_benchmark=True,no_retry=True))
    for probe in plan:
        recorder=Recorder()
        result=dict(probe=probe,calls=recorder.calls)
        print('Running '+probe['id'],flush=True)
        try:
            with patch.object(llm,'provider_call',recorder.call):
                kept,blocked,checks=llm.verify_semantics([probe['candidate']],probe['turns'],'ollama','qwen2.5:7b')
            result.update(items=kept,review_queue=blocked,semantic_checks=checks)
        except Exception as error: result['error']=dict(type=type(error).__name__,message=str(error))
        dump(base/(probe['id']+'.json'),result)
        print(probe['id']+': '+('error' if result.get('error') else 'accepted' if result['items'] else 'rejected'),flush=True)
    runtime={}
    for route in ['version','tags','ps']:
        runtime[route]=json.load(urllib.request.urlopen('http://127.0.0.1:11434/api/'+route,timeout=10))
    dump(BASE/'runtime.json',runtime)


if __name__=='__main__': main()
