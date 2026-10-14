import argparse
import json
import sys
from pathlib import Path

from .meeting.core import extract


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='Transcript → diễn biến → dữ liệu có evidence')
    parser.add_argument('transcript', type=Path)
    parser.add_argument('--engine', choices=['local', 'openai', 'ollama'], default='local')
    parser.add_argument('--model')
    parser.add_argument('--output', type=Path, help='Nên lưu transcript riêng tư vào runtime/ (được gitignore).')
    args = parser.parse_args()
    try:
        result = extract(args.transcript.read_text(encoding='utf-8-sig'), args.engine, args.model)
    except (ValueError, OSError) as error:
        parser.exit(1, f'Lỗi: {error}\n')
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding='utf-8')
        print(f'Đã lưu {len(result["items"])} mục, {len(result["review_queue"])} mục cần kiểm tra: {args.output}')
    else:
        print(rendered)


if __name__ == '__main__':
    main()
