"""Single iMac dispatcher for explicitly admitted public GLM review tasks."""
import argparse
import fcntl
import json
import pathlib
import time
from core import Coordinator, make_event
from github_store import IssueStore
from glm_bridge import review, BridgeError

def cycle(store, contract, manifest, sources, invoke=review, reviews=()):
    previous=store.read()
    c=Coordinator(contract,previous['state'],enable_readonly=True)
    def persist():
        nonlocal previous
        if c.state!=previous['state']:
            previous=store.write(previous,c.state)
    for task in manifest:
        if task['task_id'] not in c.state['tasks']:
            c.add(task)
    # Review receipts come only from the trusted local admission channel.
    # Muse must independently authenticate the reviewer before placing a receipt.
    for receipt in reviews:
        t=c.state['tasks'].get(receipt['task_id'])
        if not t or t['status']!='REVIEW_READY':
            continue
        if receipt['reviewer']!=t['reviewer'] or receipt['revision']!=t['revision'] or receipt['lease_id']!=t['lease_id']:
            continue
        payload={'kind':'review','result_hash':receipt['result_hash'],'verdict':receipt['verdict'],'evidence':receipt['evidence']}
        c.event(t['reviewer'],make_event(t,t['reviewer'],payload,receipt['event_id']),payload)
    c.recover()
    persist()
    approved={t['task_id']:t for t in manifest}
    for k in c.ready():
        t=c.state['tasks'][k]
        original=approved.get(k)
        if not original or t['to_agent']!='glm' or t['allowed_actions']!=['read_public_review']:
            continue
        if any(t.get(field)!=original.get(field) for field in contract['required'] if field not in ('revision','status')):
            continue
        if t['revision']!=1:
            continue # revised tasks require explicit updated admission
        selected={ref:sources[ref] for ref in t['input_refs']}
        claimed=c.claim(k,'glm')
        p={'kind':'start'}
        c.event('glm',make_event(claimed,'glm',p),p)
        persist() # durable before any external call
        try:
            result=invoke(claimed,selected)
            if len(result.encode())>16000:
                raise BridgeError('review exceeds public state capacity')
            p={'kind':'result','result':result}
        except BridgeError:
            p={'kind':'block','reason':'GLM call failed or response unavailable; reconcile before retry'}
        c.event('glm',make_event(claimed,'glm',p),p)
        persist()
    return {k:t['status'] for k,t in c.state['tasks'].items()}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',required=True)
    parser.add_argument('--issue',required=True,type=int)
    parser.add_argument('--admission',required=True,type=pathlib.Path)
    parser.add_argument('--lock',required=True,type=pathlib.Path)
    parser.add_argument('--loop',action='store_true')
    args=parser.parse_args()
    contract=json.loads(pathlib.Path(__file__).with_name('contract.json').read_text())
    # Admission is a trusted local file prepared by Muse, never an Issue instruction.
    with args.lock.open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        store=IssueStore(args.repo,args.issue)
        while True:
            admission=json.loads(args.admission.read_text())
            print(json.dumps(cycle(store,contract,admission['tasks'],admission['sources'],reviews=admission.get('verified_reviews',[]))),flush=True)
            if not args.loop:
                break
            time.sleep(60)

if __name__=='__main__':
    main()
