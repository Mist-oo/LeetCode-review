"""Local-only application. Run with Python 3.11+; no pip packages required."""
import argparse
import json
import mimetypes
import sqlite3
import socket
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from storage import Store, ValidationError
from judge.jobs import Jobs,specification
from completion import complete

ROOT = Path(__file__).resolve().parent


def make_server(db_path=None, port=8765):
    store = Store(db_path or ROOT / 'data/review.db', ROOT / 'data/statements.json')
    jobs = None

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
                    return self.send(200, {'ok': True,'version':2})
                if path == '/api/state':
                    return self.send(200, store.state())
                parts = path.strip('/').split('/')
                if len(parts) in (3, 4) and parts[:2] == ['api', 'problems'] and parts[2].isdigit():
                    pid = int(parts[2])
                    if len(parts) == 3:
                        problem=store.problem(pid)
                        problem['acm']=specification(problem['number'])
                        return self.send(200, problem)
                    if parts[3] == 'history':
                        return self.send(200, store.history(pid))
                    if parts[3] == 'submissions':
                        return self.send(200,jobs.history(pid))
                if len(parts)==3 and parts[:2]==['api','jobs']:
                    return self.send(200,jobs.get(parts[2]))
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
                if not 0 < length <= 12_000_000:
                    return self.send(413, {'error': '请求内容为空或过大'})
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValidationError('请求格式不正确')
                path = urlparse(self.path).path
                if self.command == 'POST':
                    if path == '/api/complete':
                        return self.send(200,complete(data))
                    if path == '/api/mark-done':
                        store.mark_done(data)
                        return self.send(200, {'ok': True})
                    if path == '/api/tags':
                        store.add_tag(data)
                        return self.send(200, {'ok': True})
                parts = path.strip('/').split('/')
                if self.command=='POST' and len(parts)==4 and parts[:2]==['api','problems'] and parts[2].isdigit():
                    if parts[3] in ('run','submit'):
                        mode='run' if parts[3]=='run' else data.get('mode','submit')
                        if parts[3]=='submit' and mode not in ('submit','strengthen'):
                            raise ValidationError('提交模式无效')
                        return self.send(202,jobs.create(int(parts[2]),data,mode))
                if self.command=='POST' and len(parts)==4 and parts[:2]==['api','jobs']:
                    if parts[3]=='cancel':return self.send(200,jobs.cancel(parts[2]))
                    if parts[3]=='reveal':return self.send(200,jobs.reveal(parts[2]))
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

    class LocalServer(ThreadingHTTPServer):
        allow_reuse_address=False

        def server_bind(self):
            if hasattr(socket,'SO_EXCLUSIVEADDRUSE'):
                self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
            super().server_bind()

        def server_close(self):
            if jobs:jobs.close()
            super().server_close()
    server=LocalServer(('127.0.0.1',port),Handler)
    try:
        jobs=Jobs(store)
        return server
    except Exception:
        server.server_close()
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='LeetCode Review 本地刷题记录')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--db', type=Path, default=ROOT / 'data/review.db')
    parser.add_argument('--open', action='store_true', help='启动后打开默认浏览器')
    args = parser.parse_args()
    try:
        server = make_server(args.db, args.port)
    except OSError:
        parser.exit(1, f'无法使用端口 {args.port}。服务可能已经启动，请先打开 http://127.0.0.1:{args.port} ，或使用 --port 8766。\n')
    print(f'LeetCode Review: http://127.0.0.1:{server.server_port}', flush=True)
    print('数据保存在本机。按 Ctrl+C 停止服务。', flush=True)
    if args.open:
        threading.Timer(0.5, lambda: webbrowser.open(f'http://127.0.0.1:{server.server_port}')).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
