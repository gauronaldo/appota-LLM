"""Local MVP server. Python 3.10+, no pip dependencies."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from ..meeting.core import extract, parse_transcript, check_candidates
from ..meeting.review import ReviewStore
from ..config import PATHS, STATIC_DIR
REVIEWS = ReviewStore()

def examples():
    rows = []
    index = PATHS.examples / 'index.json'
    if not index.exists():
        return rows
    for row in json.loads(index.read_text(encoding='utf-8')):
        path = PATHS.examples / (row['id'] + '.txt')
        rows.append(dict(id=row['id'], title=row['title'], split=row['split'],
                         transcript=path.read_text(encoding='utf-8')))
    return rows


class Handler(BaseHTTPRequestHandler):
    def send(self, status, payload, content_type='application/json; charset=utf-8'):
        data = payload.encode('utf-8') if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlsplit(self.path)
        assets = {'/': ('index.html', 'text/html; charset=utf-8'),
                  '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                  '/style.css': ('style.css', 'text/css; charset=utf-8')}
        if parsed.path in assets:
            name, kind = assets[parsed.path]
            return self.send(200, (STATIC_DIR / name).read_text(encoding='utf-8'), kind)
        if parsed.path == '/api/examples':
            return self.send(200, examples())
        if parsed.path == '/api/config':
            import os
            return self.send(200, dict(openai_configured=bool(os.environ.get('OPENAI_API_KEY') and os.environ.get('OPENAI_MODEL'))))
        if parsed.path == '/api/replay':
            case_id = parse_qs(parsed.query).get('id', [''])[0]
            if case_id not in {r['id'] for r in examples()}:
                return self.send(404, dict(error='Không có test case này.'))
            engine = parse_qs(parsed.query).get('engine', ['local'])[0]
            if engine not in ('local', 'openai', 'ollama'):
                return self.send(400, dict(error='Bộ trích xuất không hợp lệ.'))
            path = PATHS.benchmarks / 'results' / engine / (case_id + '.json')
            if not path.exists():
                return self.send(404, dict(error='Chưa có kết quả đã chạy. Chạy python src evaluate --split dev rồi --split holdout.'))
            return self.send(200, REVIEWS.create(json.loads(path.read_text(encoding='utf-8'))))
        if parsed.path == '/api/tests':
            engine = parse_qs(parsed.query).get('engine', ['local'])[0]
            if engine not in ('local', 'openai', 'ollama'):
                return self.send(400, dict(error='Bộ trích xuất không hợp lệ.'))
            reports = []
            for split in ['dev', 'holdout']:
                path = PATHS.benchmarks / 'results' / engine / (split + '_report.json')
                if path.exists():
                    reports.append(json.loads(path.read_text(encoding='utf-8')))
            return self.send(200, reports)
        self.send(404, dict(error='Không tìm thấy.'))

    def do_POST(self):
        # Bound to loopback; reject cross-origin browser requests, no CORS permission.
        origin = self.headers.get('Origin')
        host = self.headers.get('Host')
        if origin and origin not in (f'http://{host}', f'https://{host}'):
            return self.send(403, dict(error='Chỉ nhận yêu cầu cùng ứng dụng local.'))
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length < 1 or length > 160000:
                return self.send(413, dict(error='Dữ liệu gửi quá lớn hoặc trống.'))
            data = json.loads(self.rfile.read(length).decode('utf-8'))
            if not isinstance(data, dict):
                raise ValueError('Cần JSON object.')
            if self.path == '/api/extract':
                engine = data.get('engine', 'local')
                return self.send(200, REVIEWS.create(extract(data.get('transcript', ''), engine=engine, model=data.get('model'))))
            if self.path == '/api/validate':
                turns = parse_transcript(data.get('transcript', ''))
                candidates = data.get('items')
                if not isinstance(candidates, list) or len(candidates) > 300:
                    raise ValueError('Danh sách items không hợp lệ.')
                items, review, checks = check_candidates(candidates, turns, data.get('engine', 'local'), data.get('model'))
                return self.send(200, dict(items=items, review_queue=review, semantic_checks=checks))
            if self.path == '/api/review':
                return self.send(200, REVIEWS.act(data.get('session_id'), data.get('revision'),
                    data.get('review_key'), data.get('action'), data.get('changes'), data.get('reason', '')))
            if self.path == '/api/export':
                return self.send(200, REVIEWS.export(data.get('session_id'), data.get('revision')))
            return self.send(404, dict(error='Không tìm thấy.'))
        except (ValueError, TypeError) as error:
            return self.send(400, dict(error=str(error)))
        except Exception:
            # Never expose exception internals or secrets to browser.
            return self.send(500, dict(error='Lỗi xử lý nội bộ. Không tạo kết quả thay thế.'))

    def log_message(self, format, *args):
        # No transcript, response contents, or credentials written to disk/log.
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8501)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Meeting Trace: http://127.0.0.1:{args.port}', flush=True)
    print('Local rules enabled. Press Ctrl+C to stop.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
