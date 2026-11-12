import http.cookiejar
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import Request, build_opener
from http.server import ThreadingHTTPServer
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


class MarketplaceAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        server.DB_PATH = Path(cls.tmp.name) / 'test.sqlite3'
        server.init_db()
        cls.http = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.http.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.tmp.cleanup()

    def client(self):
        return build_opener(__import__('urllib.request').request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def call(self, client, path, method='GET', data=None):
        req = Request(self.base + '/api' + path, data=json.dumps(data).encode() if data is not None else None,
                      headers={'Content-Type': 'application/json'}, method=method)
        try:
            response = client.open(req)
        except Exception as e:
            response = e
        return response.code, json.loads(response.read() or b'{}')

    def signup(self, email, name):
        client = self.client()
        code, _ = self.call(client, '/signup', 'POST', {'email': email, 'name': name, 'password': 'campus-pass-123'})
        self.assertEqual(code, 200)
        return client

    def test_profile_and_listing_owner_checks(self):
        alice = self.signup('alice@test.edu', 'Alice Student')
        bob = self.signup('bob@test.edu', 'Bob Student')
        code, profile = self.call(alice, '/profile', 'POST', {'name':'Alice Student','bio': 'Design student', 'skills': 'Design, Figma', 'links': ['https://example.edu/work']})
        self.assertEqual(code, 200)
        self.assertEqual(profile['user']['bio'], 'Design student')
        code, _ = self.call(alice, '/services', 'POST', {'title': 'Flyer design', 'category': 'Design', 'description': 'A campus event flyer.', 'price': 25, 'unit': 'per flyer'})
        self.assertEqual(code, 201)
        code, listings = self.call(alice, '/services')
        sid = next(x['id'] for x in listings['services'] if x['title'] == 'Flyer design')
        code, _ = self.call(bob, f'/services/{sid}', 'PUT', {'title':'Hijacked','category':'Design','description':'No','price':1,'unit':'each'})
        self.assertEqual(code, 403)

    def test_job_proposal_selection_and_review_permissions(self):
        client = self.signup('poster@test.edu', 'Poster Student')
        worker = self.signup('worker@test.edu', 'Worker Student')
        code, _ = self.call(client, '/jobs', 'POST', {'title':'Need a poster','category':'Design','description':'Design a club poster','budget':80,'deadline':'2026-12-15'})
        self.assertEqual(code, 201)
        _, jobs = self.call(client, '/jobs')
        job = next(x for x in jobs['jobs'] if x['title'] == 'Need a poster')
        jid = job['id']
        code, _ = self.call(worker, f'/jobs/{jid}/proposals', 'POST', {'message':'I can help with this','quote':70})
        self.assertEqual(code, 201)
        code, _ = self.call(worker, f'/jobs/{jid}/proposals')
        self.assertEqual(code, 403)
        _, props = self.call(client, f'/jobs/{jid}/proposals')
        pid = props['proposals'][0]['id']
        code, _ = self.call(worker, f'/jobs/{jid}/choose', 'POST', {'proposal_id':pid})
        self.assertEqual(code, 403)
        code, _ = self.call(client, f'/jobs/{jid}/choose', 'POST', {'proposal_id':pid})
        self.assertEqual(code, 200)
        code, _ = self.call(worker, f'/jobs/{jid}/status', 'POST', {'status':'completed'})
        self.assertEqual(code, 403)
        code, _ = self.call(client, f'/jobs/{jid}/status', 'POST', {'status':'completed'})
        self.assertEqual(code, 200)
        code, _ = self.call(client, f'/jobs/{jid}/review', 'POST', {'rating':5,'text':'Great collaboration.'})
        self.assertEqual(code, 201)

    def test_signup_validation_and_category_filter(self):
        anonymous = self.client()
        code, error = self.call(anonymous, '/signup', 'POST', {'email':'bad','name':'A','password':'short'})
        self.assertEqual(code, 400)
        code, result = self.call(anonymous, '/services?category=Tutoring')
        self.assertEqual(code, 200)
        self.assertTrue(all(item['category'] == 'Tutoring' for item in result['services']))


if __name__ == '__main__':
    unittest.main()
