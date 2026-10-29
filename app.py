"""Local-only application. Run with Python 3.11+; no pip packages required."""
import argparse
import json
import mimetypes
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from storage import Store, ValidationError

ROOT = Path(__file__).resolve().parent


def make_server(db_path=None, port=8765):
    store = Store(db_path or ROOT / 'data/review.db', ROOT / 'data/statements.json')

    class Handler(BaseHTTPRequestHandler):
        def send(self, code, data, content_type='application/json; charset=utf-8'):
            if not isinstance(data, bytes):
                data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; img-src 'self' https: data:; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            try:
                if urlparse('http://' + self.headers.get('Host', '')).hostname not in ('127.0.0.1', 'localhost'):
                    return self.send(403, {'error': '只允许本机访问'})
                path = urlparse(self.path).path
                if path == '/api/health':
                    return self.send(200, {'ok': True})
                if path == '/api/state':
                    return self.send(200, store.state())
                parts = path.strip('/').split('/')
                if len(parts) in (3, 4) and parts[:2] == ['api', 'problems'] and parts[2].isdigit():
                    pid = int(parts[2])
                    if len(parts) == 3:
                        return self.send(200, store.problem(pid))
                    if parts[3] == 'history':
                        return self.send(200, store.history(pid))
                # Only the static directory is exposed, never the database or source.
                base = ROOT / 'static'
                file = (base / ('index.html' if path == '/' else path.lstrip('/'))).resolve()
                if not file.is_relative_to(base.resolve()) or not file.is_file():
                    return self.send(404, {'error': '页面不存在'})
                kind = mimetypes.guess_type(file)[0] or 'application/octet-stream'
                if file.suffix in ('.js', '.css', '.html'):
                    kind = {'.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html'}[file.suffix] + '; charset=utf-8'
                self.send(200, file.read_bytes(), kind)
            except LookupError as error:
                self.send(404, {'error': str(error)})

        def mutate(self):
            try:
                expected = f'http://{self.headers.get("Host", "")}'
                if urlparse(expected).hostname not in ('127.0.0.1', 'localhost') or self.headers.get('Origin', expected) != expected:
                    return self.send(403, {'error': '只接受来自本机页面的请求'})
                if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                    return self.send(415, {'error': '需要 JSON 请求'})
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 1_000_000:
                    return self.send(413, {'error': '请求内容为空或过大'})
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValidationError('请求格式不正确')
                path = urlparse(self.path).path
                if self.command == 'POST':
                    if path == '/api/problems':
                        return self.send(201, {'id': store.add_problem(data)})
                    if path == '/api/mark-done':
                        store.mark_done(data)
                        return self.send(200, {'ok': True})
                    if path == '/api/tags':
                        store.add_tag(data)
                        return self.send(200, {'ok': True})
                parts = path.strip('/').split('/')
                actions = {'draft': store.save_draft, 'record': store.save_record,
                           'notes': store.save_notes, 'description': store.save_description}
                if self.command == 'PUT' and len(parts) == 4 and parts[:2] == ['api', 'problems'] and parts[2].isdigit() and parts[3] in actions:
                    actions[parts[3]](int(parts[2]), data)
                    return self.send(200, {'ok': True})
                self.send(404, {'error': '接口不存在'})
            except (ValidationError, json.JSONDecodeError, ValueError) as error:
                self.send(400, {'error': str(error)})
            except LookupError as error:
                self.send(404, {'error': str(error)})
            except sqlite3.Error:
                self.send(503, {'error': '本地数据库暂时无法写入，请保留内容并重试'})

        do_POST = mutate
        do_PUT = mutate

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='LeetCode Review 本地刷题记录')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--db', type=Path, default=ROOT / 'data/review.db')
    args = parser.parse_args()
    server = make_server(args.db, args.port)
    print(f'LeetCode Review: http://127.0.0.1:{server.server_port}', flush=True)
    print('数据保存在本机。按 Ctrl+C 停止服务。', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
