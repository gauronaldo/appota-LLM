"""Exercise the real local HTTP handler, no external network or provider."""
import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from meeting_trace.web.server import Handler


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = 'http://127.0.0.1:' + str(cls.server.server_address[1])

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, route, data=None, headers=None):
        payload = None if data is None else json.dumps(data).encode()
        req = urllib.request.Request(self.base + route, data=payload,
                                     headers={'Content-Type':'application/json', **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=3) as response:
                return response.status, response.read(), response.headers
        except urllib.error.HTTPError as error:
            return error.code, error.read(), error.headers

    def test_page_and_assets_serve_with_headers(self):
        for route in ['/', '/app.js', '/style.css']:
            code, body, headers = self.request(route)
            self.assertEqual(code, 200)
            self.assertTrue(body)
            self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')

    def test_all_examples_and_all_five_output_categories(self):
        status, body, _ = self.request('/api/examples')
        samples = json.loads(body)
        self.assertEqual((status, len(samples)), (200, 20))
        sample = next(s for s in samples if s['id'] == '17_clear_assignment')
        status, body, _ = self.request('/api/extract', {'transcript':sample['transcript'], 'engine':'local'})
        result = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual({r['type'] for r in result['items']}, {'decision','action','issue','request_feedback','unresolved'})

    def test_bad_transcript_returns_error_instead_of_result(self):
        status, body, _ = self.request('/api/extract', {'transcript':'Không có speaker'})
        self.assertEqual(status, 400)
        self.assertIn('error', json.loads(body))
        self.assertNotIn('items', json.loads(body))

    def test_replay_id_cannot_read_arbitrary_file(self):
        status, _, _ = self.request('/api/replay?id=../../.env')
        self.assertEqual(status, 404)

    def test_cross_origin_post_rejected(self):
        status, _, _ = self.request('/api/extract', {'transcript':'A: chốt B.'}, {'Origin':'https://unrelated.example'})
        self.assertEqual(status, 403)

    def test_edit_validation_rejects_unsupported_deadline(self):
        raw = 'Lan: Về kiểm thử, em nhận làm kiểm thử trước thứ Sáu.'
        _, body, _ = self.request('/api/extract', {'transcript':raw})
        item = json.loads(body)['items'][0]
        item['due'] = '20/12/2030'
        status, body, _ = self.request('/api/validate', {'transcript':raw, 'items':[item]})
        result = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(result['items'], [])
        self.assertEqual(len(result['review_queue']), 1)


if __name__ == '__main__':
    unittest.main()
