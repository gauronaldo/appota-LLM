"""Read transcript, frozen expectation and output together for author review."""
import argparse
import json
import sys

from ..config import PATHS


def main():
    if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ids',nargs='+')
    parser.add_argument('--arm',choices=['pipeline','baseline_b'],default='pipeline')
    parser.add_argument('--suite',choices=['v2','holdout-v3'],default='v2')
    args=parser.parse_args()
    if args.suite=='v2':
        rows=json.loads((PATHS.fixtures/'dataset_manifest.json').read_text(encoding='utf-8'))
        manifest={r['id']:dict(transcript='data/examples/'+r['id']+'.txt',
            expected='tests/fixtures/'+r['id']+'.expected.json') for r in rows}
    else:
        manifest={r['id']:r for r in json.loads((PATHS.root/'data/holdout-v3/manifest.json').read_text(encoding='utf-8'))}
    for id in args.ids:
        if id not in manifest: raise ValueError('Case không tồn tại: '+id)
        row=manifest[id]
        raw=(PATHS.root/row['transcript']).read_text(encoding='utf-8')
        gold=json.loads((PATHS.root/row['expected']).read_text(encoding='utf-8'))
        base=PATHS.benchmarks/'comparisons/qwen2.5-7b'/args.suite/args.arm
        path=base/(id+'.json')
        if args.suite=='v2' and args.arm=='pipeline': path=PATHS.benchmarks/'results/ollama'/(id+'.json')
        result=json.loads(path.read_text(encoding='utf-8'))
        fields=['id','type','topic','status','content','owner','due']
        def brief(item):
            return {**{key:item.get(key) for key in fields},
                'evidence':[ev['turn_id'] for ev in item.get('evidence',[])],
                'history':[ev['turn_id'] for ev in item.get('history',[])]}
        print('\nCASE '+id)
        print('\n'.join('T'+str(n)+': '+line for n,line in enumerate(raw.splitlines(),1)))
        print('GOLD '+json.dumps(gold['items'],ensure_ascii=False))
        print('OUTPUT '+json.dumps([brief(item) for item in result['items']],ensure_ascii=False))
        print('QUEUE '+json.dumps([dict(item=brief(q['item']),errors=q['errors']) for q in result['review_queue']],ensure_ascii=False))
        if result.get('error'): print('ERROR '+json.dumps(result['error'],ensure_ascii=False))


if __name__=='__main__': main()
