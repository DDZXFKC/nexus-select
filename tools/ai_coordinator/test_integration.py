import json
import pathlib
import tempfile
import unittest
import urllib.error
from glm_bridge import check, BridgeError
from pilot_store import transaction
from test_core import CONTRACT, task

class Response:
    def __init__(self, content, finish='stop'):
        self.raw=json.dumps({'choices':[{'finish_reason':finish,'message':{'content':content}}]}).encode()
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def read(self,n): return self.raw[:n]

class IntegrationTests(unittest.TestCase):
    def test_nonce(self):
        def opener(req,timeout):
            self.assertEqual(json.loads(req.data)['model'],'glm-5.2')
            return Response('token')
        self.assertEqual(check(opener,key='mock',nonce='token')['status'],'CHECK_OK')
    def test_bad_response(self):
        for response in (Response('wrong'),Response('token','length')):
            with self.assertRaises(BridgeError):
                check(lambda *a,**kw:response,key='mock',nonce='token')
    def test_no_retry(self):
        calls=[]
        def opener(*a,**kw):
            calls.append(1)
            raise urllib.error.URLError('lost response')
        with self.assertRaises(BridgeError):
            check(opener,key='mock',nonce='token')
        self.assertEqual(len(calls),1)
    def test_persistence_and_rollback(self):
        with tempfile.TemporaryDirectory() as d:
            path=pathlib.Path(d)/'state.json'
            with transaction(path,CONTRACT) as c: c.add(task('a'))
            with self.assertRaises(RuntimeError):
                with transaction(path,CONTRACT) as c:
                    c.add(task('b'))
                    raise RuntimeError('abort')
            with transaction(path,CONTRACT) as c:
                self.assertEqual(list(c.state['tasks']),['a'])
    def test_lock(self):
        with tempfile.TemporaryDirectory() as d:
            path=pathlib.Path(d)/'state.json'
            with transaction(path,CONTRACT):
                with self.assertRaises(BlockingIOError):
                    with transaction(path,CONTRACT): pass
