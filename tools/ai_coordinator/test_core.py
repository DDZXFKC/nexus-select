import json
import pathlib
import unittest
from core import Coordinator, Rejected, make_event, digest

CONTRACT=json.loads(pathlib.Path(__file__).with_name('contract.json').read_text())
def task(k, deps=()):
    return dict(task_id=k, revision=1, from_agent='gpt', to_agent='glm', reviewer='claude', priority='P1', depends_on=list(deps), input_refs=[], action='synthetic echo', acceptance=['echo'], allowed_paths=[], allowed_actions=['synthetic'], resource_locks=['fixture'], status='QUEUED')

class Tests(unittest.TestCase):
    def setUp(self):
        self.now=100
        self.c=Coordinator(CONTRACT, clock=lambda:self.now)
        self.c.add(task('a'))
        self.c.add(task('b',['a']))
        self.assertEqual(self.c.ready(),['a'])
    def send(self,t,actor,p):
        return self.c.event(actor,make_event(t,actor,p),p)
    def finish(self):
        t=self.c.claim('a','glm')
        self.send(t,'glm',{'kind':'start'})
        p={'kind':'result','result':'echo'}
        e=make_event(t,'glm',p)
        self.assertEqual(self.c.event('glm',e,p),'REVIEW_READY')
        self.assertEqual(self.c.event('glm',e,p),'DUPLICATE')
        return t
    def test_roundtrip(self):
        t=self.finish()
        p={'kind':'review','result_hash':digest('echo'),'verdict':'PASS','evidence':'checked'}
        with self.assertRaises(Rejected): self.send(t,'glm',p)
        self.assertEqual(self.send(t,'claude',p),'DONE')
        self.assertEqual(self.c.ready(),['b'])
    def test_expiry(self):
        t=self.c.claim('a','glm',1)
        self.now+=2
        self.c.recover()
        self.c.claim('a','glm')
        with self.assertRaises(Rejected): self.send(t,'glm',{'kind':'start'})
    def test_revision(self):
        t=self.finish()
        self.send(t,'claude',{'kind':'review','result_hash':digest('echo'),'verdict':'CHANGES_REQUESTED','evidence':'fix'})
        self.c.recover()
        self.assertEqual(self.c.state['tasks']['a']['revision'],2)
        with self.assertRaises(Rejected): self.send(t,'glm',{'kind':'start'})
    def test_restore(self):
        t=self.finish()
        self.c=Coordinator(CONTRACT,json.loads(json.dumps(self.c.state)),clock=lambda:self.now)
        self.assertEqual(self.send(t,'claude',{'kind':'review','result_hash':digest('echo'),'verdict':'PASS','evidence':'checked'}),'DONE')
    def test_pilot_guard(self):
        t=task('c');t['allowed_actions']=['purchase']
        with self.assertRaises(Rejected): self.c.add(t)
    def test_actor(self):
        with self.assertRaises(Rejected): self.c.claim('a','claude')
        t=self.c.claim('a','glm');p={'kind':'start'}
        with self.assertRaises(Rejected): self.c.event('claude',make_event(t,'glm',p),p)

if __name__=='__main__': unittest.main()
