import multiprocessing
import json
import os
import pathlib
import plistlib
import tempfile
import time
import unittest
import uuid
from unittest.mock import patch
import controller as c

class FakeVPN:
    def __init__(self):
        self.s = {'AHC DE': 'Disconnected', 'AHC US': 'Connected'}
        self.calls = []
        self.fail_start = None
        self.empty = False
    def __call__(self, a, n=None):
        if a == 'list':
            return 'header' if self.empty else '\n'.join('* ('+s+') UUID VPN (IKEv2) "'+k+'"' for k,s in self.s.items())
        if a == 'status':
            return self.s[n]
        self.calls.append((a,n))
        if a == 'start' and n == self.fail_start:
            raise c.Fault('mock failure')
        self.s[n] = 'Connected' if a == 'start' else 'Disconnected'
        return ''

class Tests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); self.fake = FakeVPN()
        self.patches = [patch.object(c,'ROOT',pathlib.Path(self.t.name)/'private'),patch.object(c,'sc',self.fake),patch.object(c,'boot_id',return_value='mock-boot')]
        for p in self.patches: p.start()
        c.setup(); c.write(c.ROOT/'profiles.json',{'DE':'AHC DE','US':'AHC US'}); self.arm()
    def tearDown(self):
        for p in reversed(self.patches): p.stop()
        self.t.cleanup()
    def arm(self):
        c.watchdog_tick(); c.write(c.ROOT/'armed.json',{'boot':'mock-boot','deadline':c.now()+299})
    def q(self,a,**kw):
        t=c.now(); return dict(version=1,request_id=uuid.uuid4().hex,action=a,created_at=c.iso(t),expires_at=c.iso(t+30),**kw)
    def change(self):
        return c.execute(self.q('connect',country='DE',lease_seconds=90))
    def expire(self):
        d=c.pending(); d['deadline']-=100; d['started']-=100; d['mono_deadline']-=100; d['mono_start']-=100; c.write(c.ROOT/'pending.json',d)
    def test_read_only(self):
        self.assertEqual(c.execute(self.q('status'))['status']['US'],'Connected'); self.assertFalse(self.fake.calls)
    def test_header_only(self):
        self.fake.empty=True
        with self.assertRaises(c.Fault): self.change()
        self.assertFalse(self.fake.calls)
    def test_blank_status(self):
        self.fake.s['AHC DE']=''
        with self.assertRaises(c.Fault): self.change()
        self.assertFalse(self.fake.calls)
    def test_unarmed(self):
        c.remove(c.ROOT/'armed.json')
        with self.assertRaises(c.Fault): self.change()
        self.assertFalse(self.fake.calls)
    def test_stale_watchdog(self):
        h=c.read(c.ROOT/'watchdog-heartbeat.json'); h['monotonic']-=10;c.write(c.ROOT/'watchdog-heartbeat.json',h)
        with self.assertRaises(c.Fault): self.change()
        self.assertFalse(self.fake.calls)
    def test_unmanaged(self):
        self.fake.s['Personal']='Connected'
        with self.assertRaises(c.Fault): self.change()
        self.assertFalse(self.fake.calls)
    def test_connect_confirm(self):
        r=self.change(); self.assertEqual(r['state'],'awaiting_confirmation');self.assertFalse((c.ROOT/'armed.json').exists())
        q=self.q('confirm',lease_token=r['lease_token'],verified_country='DE',muse_reachable=True)
        self.assertEqual(c.execute(q)['state'],'confirmed'); self.assertIsNone(c.pending());self.assertEqual(self.fake.s['AHC DE'],'Connected')
    def test_wrong_token(self):
        self.change()
        with self.assertRaises(c.Fault):c.execute(self.q('confirm',lease_token='0'*32,verified_country='DE',muse_reachable=True))
        self.assertIsNotNone(c.pending())
    def test_wrong_country(self):
        r=self.change()
        with self.assertRaises(c.Fault):c.execute(self.q('confirm',lease_token=r['lease_token'],verified_country='US',muse_reachable=True))
        self.assertIsNotNone(c.pending())
    def test_expired_rollback(self):
        self.change();self.expire();c.watchdog_tick();self.assertIsNone(c.pending());self.assertEqual(self.fake.s['AHC US'],'Connected')
    def test_expired_confirm(self):
        r=self.change();self.expire()
        with self.assertRaises(c.Fault):c.execute(self.q('confirm',lease_token=r['lease_token'],verified_country='DE',muse_reachable=True))
        self.assertEqual(self.fake.s['AHC US'],'Connected')
    def test_failure_restores(self):
        self.fake.fail_start='AHC DE'
        with self.assertRaises(c.Fault):self.change()
        self.assertIsNone(c.pending());self.assertEqual(self.fake.s['AHC US'],'Connected')
    def test_failed_recovery_retains(self):
        self.change();self.expire();self.fake.fail_start='AHC US'
        with self.assertRaises(c.Fault):c.watchdog_tick()
        self.assertIsNotNone(c.pending());self.fake.fail_start=None;c.watchdog_tick();self.assertIsNone(c.pending())
    def test_disconnect_rollback(self):
        c.execute(self.q('disconnect',lease_seconds=90));self.assertEqual(self.fake.s['AHC US'],'Disconnected');self.expire();c.watchdog_tick();self.assertEqual(self.fake.s['AHC US'],'Connected')
    def test_from_none_rollback(self):
        self.fake.s['AHC US']='Disconnected';self.change();self.expire();c.watchdog_tick();self.assertTrue(all(v=='Disconnected' for v in self.fake.s.values()))
    def test_queue_dedupe(self):
        q=self.q('connect',country='DE',lease_seconds=90);p=c.ROOT/'requests'/(q['request_id']+'.json');c.write(p,q);c.process(p);r=c.read(c.ROOT/'results'/p.name);self.assertTrue(r['ok']);calls=list(self.fake.calls);c.write(p,q);c.process(p);self.assertEqual(self.fake.calls,calls)
    def test_queue_expired(self):
        q=self.q('connect',country='DE',lease_seconds=90);q.update(created_at=c.iso(c.now()-40),expires_at=c.iso(c.now()-10));p=c.ROOT/'requests'/(q['request_id']+'.json');c.write(p,q);c.process(p);self.assertFalse(c.read(c.ROOT/'results'/p.name)['ok']);self.assertFalse(self.fake.calls)
    def test_queue_rejects_shell(self):
        q=self.q('connect',country='DE; whoami',lease_seconds=90);p=c.ROOT/'requests'/(q['request_id']+'.json');c.write(p,q);c.process(p);self.assertFalse(c.read(c.ROOT/'results'/p.name)['ok']);self.assertFalse(self.fake.calls)
    def test_symlink(self):
        q=self.q('status');p=c.ROOT/'requests'/(q['request_id']+'.json');p.symlink_to(c.ROOT/'profiles.json');c.process(p);self.assertFalse(c.read(c.ROOT/'results'/p.name)['ok'])
    def test_lock_contention(self):
        with c.locked():
            with self.assertRaises(c.Fault):
                with c.locked(seconds=.1):pass
    def test_boot_change(self):
        self.change()
        with patch.object(c,'boot_id',return_value='another-boot'):c.watchdog_tick()
        self.assertIsNone(c.pending());self.assertEqual(self.fake.s['AHC US'],'Connected')
    def test_independent_recovery_after_worker_death(self):
        ctx=multiprocessing.get_context('fork')
        with ctx.Manager() as manager:
            self.fake.s=manager.dict(dict(self.fake.s));self.fake.calls=manager.list()
            ready=ctx.Event(); old_sc=self.fake
            def blocking_sc(a,n=None):
                r=old_sc(a,n)
                if a=='start' and n=='AHC DE':
                    ready.set();time.sleep(60)
                return r
            q=self.q('connect',country='DE',lease_seconds=90)
            p=c.ROOT/'requests'/(q['request_id']+'.json');c.write(p,q)
            def worker():
                with patch.object(c,'sc',blocking_sc):c.process(p)
            w=ctx.Process(target=worker);w.start()
            try:
                self.assertTrue(ready.wait(5));self.assertTrue((c.ROOT/'pending.json').exists())
            finally:
                w.terminate();w.join(5)
            self.assertEqual(self.fake.s['AHC DE'],'Connected');self.expire()
            watcher=ctx.Process(target=c.watchdog_tick);watcher.start();watcher.join(5)
            self.assertEqual(watcher.exitcode,0);self.assertIsNone(c.pending());self.assertEqual(self.fake.s['AHC US'],'Connected')
    def test_queue_process_separate_worker(self):
        ctx=multiprocessing.get_context('fork')
        q=self.q('status');p=c.ROOT/'requests'/(q['request_id']+'.json');c.write(p,q)
        w=ctx.Process(target=c.process,args=(p,));w.start();w.join(5)
        self.assertEqual(w.exitcode,0);self.assertTrue(c.read(c.ROOT/'results'/p.name)['ok'])
    def test_plists(self):
        for k in ('agent','watchdog'):
            with open(pathlib.Path(__file__).parent/f'com.ahc.vpn.{k}.plist','rb') as f:d=plistlib.load(f)
            self.assertEqual(d['LimitLoadToSessionType'],'Aqua');self.assertTrue(d['KeepAlive']);self.assertEqual(d['ProgramArguments'][1],k+'.py')

if __name__=='__main__': unittest.main(verbosity=2)
