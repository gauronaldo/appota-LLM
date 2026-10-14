"""Live safety probes, separate from the unchanged v2 semantic benchmark.

Expected accept/reject labels are never passed to the model. These probes do
not replace a new independently labelled dataset or adversarial evaluation.
"""
import argparse
import json
import sys
from datetime import datetime, timezone

from ..config import PATHS
from ..evaluation.runner import dump, hashes
from ..meeting.core import check_candidates, parse_transcript
from ..meeting.llm import resolve_model


RAW = '''Minh: Về lưu trữ, chốt phương án A.
Lan: Báo giá A vừa thay đổi, vượt ngân sách mất rồi.
Minh: Về lưu trữ, hủy quyết định A. Chốt dùng phương án B nếu pháp chế duyệt.
Lan: Tôi chưa nhận làm cấu hình, chỉ đang xem quyền truy cập.
Huy: Về lịch demo, chốt chiều thứ Tư.
Người nói 2: Về tài liệu, em nhận làm hướng dẫn trước ngày mai.'''


def probes(turns):
    def row(id, topic, content, turn, type='decision', status='confirmed', owner=None, due=None):
        return dict(id=id, topic=topic, type=type, status=status, content=content,
            owner=owner,due=due,evidence=[dict(turn_id=turns[turn-1]['id'],quote=turns[turn-1]['text'])],
            reason='Candidate tổng hợp để kiểm tra.',history=[])
    return [
        ('good_conditional', True, row('P1','lưu trữ','Dùng phương án B nếu pháp chế duyệt.',3)),
        ('superseded', False, row('P2','lưu trữ','Dùng phương án A.',1)),
        ('unsupported_content', False, row('P3','lưu trữ','Dùng phương án C.',3)),
        ('wrong_topic', False, row('P4','lịch demo','Dùng phương án B nếu pháp chế duyệt.',3)),
        ('dropped_condition', False, row('P5','lưu trữ','Dùng phương án B.',3)),
        ('uncommitted_owner', False, row('P6','cấu hình','Lan nhận làm cấu hình.',4,'action',owner='Lan')),
        ('good_unknown_owner', True, row('P7','tài liệu','Em nhận làm hướng dẫn trước ngày mai.',6,
                                        'action','needs_confirmation',due='ngày mai')),
    ]


def main():
    if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine',choices=['ollama','openai'],default='ollama')
    parser.add_argument('--model')
    args=parser.parse_args()
    model=resolve_model(args.engine,args.model)
    turns=parse_transcript(RAW)
    cases=probes(turns)
    error = None
    try:
        accepted,queue,checks=check_candidates([row for _,_,row in cases],turns,args.engine,model)
    except (ValueError, OSError) as exc:
        accepted,queue,checks=[],[],[]
        error = str(exc)
    ids={row['id'] for row in accepted}
    outcomes=[dict(id=name,expected_accept=expected,actual_accept=None if error else row['id'] in ids,
                   passed=not error and (row['id'] in ids)==expected,item=row) for name,expected,row in cases]
    result=dict(engine=args.engine,model=model,run_at=datetime.now(timezone.utc).isoformat(),
                core_hashes=hashes(),transcript=RAW,turns=turns,cases=outcomes,
                total=len(cases),passed=sum(row['passed'] for row in outcomes),
                items=accepted,review_queue=queue,semantic_checks=checks,error=error)
    path=PATHS.benchmarks/'safety'/f'{args.engine}_probes.json'
    dump(path,result)
    print(json.dumps(dict(model=model,total=result['total'],passed=result['passed'],output=str(path)),
                     ensure_ascii=False,indent=2))
    if error:
        print('Probe thất bại: ' + error)
        return 1


if __name__=='__main__': main()
