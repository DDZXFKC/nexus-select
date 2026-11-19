"""One-command offline pilot plus explicit live nonce roundtrip."""
import argparse
import json
import pathlib
import tempfile
import unittest
from core import make_event, digest
from pilot_store import transaction
from glm_bridge import check
from test_core import task, CONTRACT

def run(live=False):
    with tempfile.TemporaryDirectory() as directory:
        state=pathlib.Path(directory)/'pilot.json'
        with transaction(state,CONTRACT) as c:
            c.add(task('nonce-check'))
            c.ready()
            t=c.claim('nonce-check','glm')
            p={'kind':'start'}
            c.event('glm',make_event(t,'glm',p),p)
        # No lock held across network call. This is an isolated temporary pilot.
        result=check()['nonce'] if live else 'synthetic-local-echo'
        with transaction(state,CONTRACT) as c:
            p={'kind':'result','result':result}
            c.event('glm',make_event(t,'glm',p),p)
        with transaction(state,CONTRACT) as c:
            if c.state['tasks']['nonce-check']['status']!='REVIEW_READY':
                raise RuntimeError('checkpoint restore failed')
            # No independent reviewer authenticated; never mark DONE here.
            print(json.dumps({'status':'REVIEW_READY','mode':'live_nonce' if live else 'mock','result_hash':digest(result),'independent_review_required':True}))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--live-glm',action='store_true')
    args=parser.parse_args()
    suite=unittest.defaultTestLoader.discover(str(pathlib.Path(__file__).parent),pattern='test_*.py')
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful(): raise SystemExit(1)
    run(args.live_glm)
