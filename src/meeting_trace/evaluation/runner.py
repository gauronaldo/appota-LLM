"""Frozen, deterministic checks. Does not use expected output in extraction.

Pass means fixture assertions passed, not semantic correctness on real meetings.
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
import os
import time

from ..config import PATHS
from ..meeting.core import extract, parse_transcript
from ..meeting.prompts import VERSION
from .scoring import score
from .reporting import render_tests

ROOT = PATHS.root
FROZEN = ['src/meeting_trace/meeting/core.py', 'src/meeting_trace/meeting/schema.py',
          'src/meeting_trace/meeting/prompts.py', 'src/meeting_trace/meeting/llm.py',
          'src/meeting_trace/meeting/review.py']


def hashes():
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in FROZEN}


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def benchmark_extract(raw, engine='local', model=None):
    """An unsupported transcript is a recorded failure, not a passing empty output."""
    try:
        parse_transcript(raw)
    except ValueError as error:
        return dict(schema_version='1.0', metadata=dict(engine=engine, model=model,
                    transcript_sha256=hashlib.sha256(raw.encode('utf-8')).hexdigest(),
                    automated=True, semantic_verification=False),
                    turns=[], topics=[], items=[], review_queue=[],
                    error=dict(stage='input', type=type(error).__name__, message=str(error)))
    try:
        return extract(raw, engine, model)
    except (ValueError, OSError) as error:
        if engine == 'local':
            raise
        return dict(schema_version='1.0', metadata=dict(engine=engine, model=model,
                    transcript_sha256=hashlib.sha256(raw.encode('utf-8')).hexdigest(),
                    automated=True, semantic_verification=False),
                    turns=parse_transcript(raw), topics=[], items=[], review_queue=[],
                    error=dict(stage='pipeline', type=type(error).__name__, message=str(error)))


def verify_freeze():
    """Check original bytes after path-only migration; never replace the old freeze."""
    freeze_path = PATHS.benchmarks / 'freeze-v2.json'
    if not freeze_path.exists():
        raise ValueError('Chưa có freeze trước lượt chạy kín.')
    frozen = json.loads(freeze_path.read_text(encoding='utf-8'))['hashes']
    mapping_path = PATHS.benchmarks / 'path_migration.json'
    mapping = json.loads(mapping_path.read_text(encoding='utf-8')) if mapping_path.exists() else {}
    migrated = {mapping.get(path, path): sha for path, sha in frozen.items()}
    if migrated != hashes():
        raise ValueError('Các file lõi đã thay đổi sau freeze; cần tạo revision mới, giữ baseline cũ.')


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine', choices=['local', 'openai', 'ollama'], default='local')
    parser.add_argument('--model')
    parser.add_argument('--split', choices=['dev', 'holdout'], default='dev')
    parser.add_argument('--freeze', action='store_true')
    parser.add_argument('--verify-only', action='store_true',
                        help='So với kết quả đã lưu; không ghi đè báo cáo hoặc timestamp lịch sử.')
    args = parser.parse_args()
    if args.engine == 'ollama':
        from ..meeting.llm import resolve_model
        args.model = resolve_model('ollama', args.model)
    if args.engine == 'openai' and (not os.environ.get('OPENAI_API_KEY') or not (args.model or os.environ.get('OPENAI_MODEL'))):
        parser.exit(1, 'Chưa cấu hình API key/model; không tạo báo cáo LLM giả.\n')
    freeze_path = PATHS.benchmarks / 'freeze-v2.json'
    if args.freeze:
        if freeze_path.exists():
            parser.exit(1, 'Freeze đã tồn tại; không ghi đè lịch sử tập kín.\n')
        dump(freeze_path, dict(frozen_at=datetime.now(timezone.utc).isoformat(), hashes=hashes(), prompt_version=VERSION))
        print('Frozen revision before v2 re-evaluation (previously observed dataset).')
        return
    if args.split == 'holdout':
        try:
            verify_freeze()
        except ValueError as error:
            parser.exit(1, str(error) + '\n')
    manifest = json.loads((PATHS.fixtures / 'dataset_manifest.json').read_text(encoding='utf-8'))
    cases = []
    base = PATHS.benchmarks / 'results' / args.engine
    for row in manifest:
        transcript_path = PATHS.examples / (row['id'] + '.txt')
        expected_path = PATHS.fixtures / (row['id'] + '.expected.json')
        if hashlib.sha256(expected_path.read_bytes()).hexdigest() != row['expected_sha256']:
            parser.exit(1, f'Kỳ vọng đã bị thay đổi: {row["id"]}\n')
        # Normalize platform line endings for transcript hash; expectations hashed as bytes.
        transcript = transcript_path.read_text(encoding='utf-8')
        if hashlib.sha256(transcript.encode()).hexdigest() != row['transcript_sha256']:
            parser.exit(1, f'Transcript đã bị thay đổi: {row["id"]}\n')
        if row['split'] != args.split:
            continue
        started = time.perf_counter()
        print(f'Running {args.engine}: {row["id"]}', flush=True)
        try:
            result = benchmark_extract(transcript, args.engine, args.model)
        except (ValueError, OSError) as error:
            parser.exit(1, f'{row["id"]}: {error}. Không ghi báo cáo giả.\n')
        result_path = base / (row['id'] + '.json')
        if args.verify_only:
            if not result_path.exists():
                parser.exit(1, f'Chưa có kết quả để đối chiếu: {row["id"]}\n')
            saved = json.loads(result_path.read_text(encoding='utf-8'))
            saved.pop('run_seconds', None)
            if result != saved:
                parser.exit(1, f'Kết quả sau restructure khác baseline: {row["id"]}\n')
        else:
            result['run_seconds'] = round(time.perf_counter() - started, 3)
            dump(result_path, result)
        expected = json.loads(expected_path.read_text(encoding='utf-8'))
        cases.append(score(result, expected))
    metrics = {key: sum(c['metrics'][key] for c in cases) for key in cases[0]['metrics']}
    tp, fp, fn = (metrics[k] for k in ['decision_tp', 'decision_fp', 'decision_fn'])
    metrics.update(decision_precision=round(tp/(tp+fp), 4) if tp+fp else None,
                   decision_recall=round(tp/(tp+fn), 4) if tp+fn else None,
                   intermediate_promotion_rate=round(metrics['intermediate_promoted']/metrics['intermediate_total'], 4) if metrics['intermediate_total'] else None)
    versions = {row.get('dataset_version', '1.0') for row in manifest}
    report = dict(dataset_version=','.join(sorted(versions)), engine=args.engine,
                  model=(args.model or os.environ.get('OPENAI_MODEL')) if args.engine != 'local' else None,
                  prompt_version=VERSION, split=args.split, run_at=datetime.now(timezone.utc).isoformat(),
                  core_hashes=hashes(), evaluation_kind='recheck_observed_v2',
                  total=len(cases), passed=sum(c['passed'] for c in cases),
                  metrics=metrics, cases=cases,
                  groups={group: dict(total=sum(c['group']==group for c in cases),
                                      passed=sum(c['group']==group and c['passed'] for c in cases))
                          for group in sorted({c['group'] for c in cases})},
                  input_formats={fmt: dict(total=sum(c['input_format']==fmt for c in cases),
                                           passed=sum(c['input_format']==fmt and c['passed'] for c in cases))
                                 for fmt in sorted({c['input_format'] for c in cases})})
    if args.verify_only:
        old_report = json.loads((base / (args.split + '_report.json')).read_text(encoding='utf-8'))
        if metrics != old_report['metrics'] or cases != old_report['cases']:
            parser.exit(1, 'Kết quả chấm khác báo cáo lịch sử.\n')
        print('Verified baseline outputs and scores; historical reports were not overwritten.')
    else:
        dump(base / (args.split + '_report.json'), report)
        render_tests(args.engine)
    print(json.dumps({k: report[k] for k in ['engine', 'split', 'total', 'passed', 'metrics']}, ensure_ascii=False, indent=2))
    for c in cases:
        if not c['passed']:
            print(c['id'] + ': ' + '; '.join(c['errors']))
    # Semantic failures remain recorded and don't masquerade as infrastructure failures.


if __name__ == '__main__':
    main()
