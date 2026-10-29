import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app import make_server
from storage import today


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.server = make_server(Path(cls.tmp.name) / 'test.db', 0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.tmp.cleanup()

    def request(self, path, method='GET', data=None, headers=None):
        request = Request(self.base + path, data=json.dumps(data).encode() if data is not None else None,
                          headers={'Content-Type': 'application/json', **(headers or {})}, method=method)
        try:
            with urlopen(request, timeout=5) as response:
                return response.status, response.read(), response.headers
        except HTTPError as error:
            return error.code, error.read(), error.headers

    def test_static_and_all_vendored_assets_serve(self):
        for path in ['/', '/app.js', '/style.css', '/vendor/codemirror.js', '/vendor/python.js', '/vendor/marked.js', '/vendor/purify.js']:
            code, body, _ = self.request(path)
            self.assertEqual(code, 200, path)
            self.assertTrue(body)

    def test_roundtrip_record_and_history(self):
        code, body, _ = self.request('/api/state')
        self.assertEqual(code, 200)
        self.assertEqual(len(json.loads(body)['problems']), 100)
        code, _, _ = self.request('/api/problems/2/record', 'PUT', dict(day=today(), result='fail', code='print(1)', tags=['边界遗漏'], note='空输入'))
        self.assertEqual(code, 200)
        code, body, _ = self.request('/api/problems/2/history')
        self.assertEqual(json.loads(body)[0]['note'], '空输入')

    def test_private_paths_are_not_exposed(self):
        for path in ['/app.py', '/data/review.db', '/.git/config', '/../storage.py']:
            self.assertEqual(self.request(path)[0], 404)

    def test_foreign_origin_and_host_are_rejected(self):
        self.assertEqual(self.request('/api/tags', 'POST', {'name': 'x'}, {'Origin': 'https://example.com'})[0], 403)
        self.assertEqual(self.request('/api/state', headers={'Host': 'evil.example'})[0], 403)

    def test_no_backfill_and_missing_problem(self):
        self.assertEqual(self.request('/api/problems/1/record', 'PUT', dict(day='2000-01-01', result='pass'))[0], 400)
        self.assertEqual(self.request('/api/problems/999999')[0], 404)


if __name__ == '__main__':
    unittest.main()
