"""Synthetic-only coordinator reducer. No external actions or credentials."""
import copy
import hashlib
import json
import time
import uuid

class Rejected(ValueError):
    pass

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

class Coordinator:
    def __init__(self, contract, snapshot=None, clock=time.time):
        self.contract = contract
        self.state = copy.deepcopy(snapshot if snapshot is not None else {'tasks': {}, 'events': {}})
        self.clock = clock

    def add(self, task):
        t = copy.deepcopy(task)
        k = t.get('task_id')
        if not isinstance(k, str) or not k or k in self.state['tasks'] or any(x not in t for x in self.contract['required']):
            raise Rejected('task identity/schema')
        if t['status'] != 'QUEUED' or t['revision'] != 1 or t['priority'] not in ('P0','P1','P2','P3'):
            raise Rejected('initial state')
        if any(t[x] not in self.contract['agents'] for x in ('from_agent','to_agent','reviewer')) or t['reviewer'] == t['to_agent']:
            raise Rejected('roles')
        for field in ('depends_on','input_refs','acceptance','allowed_paths','allowed_actions','resource_locks'):
            if not isinstance(t[field], list):
                raise Rejected(field)
        if not t['acceptance'] or not isinstance(t['action'], str) or not t['action'].strip():
            raise Rejected('acceptance/action')
        if any(d not in self.state['tasks'] for d in t['depends_on']):
            raise Rejected('dependency must exist')
        if t['allowed_paths'] or set(t['allowed_actions']) != {'synthetic'}:
            raise Rejected('pilot only')
        t.update(lease_id=None, lease_until=None, result=None)
        self.state['tasks'][k] = t

    def ready(self):
        tasks = self.state['tasks']
        for t in tasks.values():
            if t['status'] == 'QUEUED' and all(tasks[d]['status'] == 'DONE' for d in t['depends_on']):
                t['status'] = 'READY'
        return sorted((t['task_id'] for t in tasks.values() if t['status'] == 'READY'), key=lambda k: (tasks[k]['priority'], k))

    def claim(self, task_id, actor, seconds=1800):
        t = self.state['tasks'][task_id]
        if actor != t['to_agent'] or t['status'] != 'READY' or not 1 <= seconds <= 3600:
            raise Rejected('claim')
        for other in self.state['tasks'].values():
            if other['status'] in ('CLAIMED','RUNNING','REVIEW_READY') and set(other['resource_locks']) & set(t['resource_locks']):
                raise Rejected('resource locked')
        t.update(status='CLAIMED', lease_id=uuid.uuid4().hex, lease_until=self.clock()+seconds)
        return copy.deepcopy(t)

    def event(self, actor, event, payload):
        # actor must come from trusted transport, never from event alone.
        if any(k not in event for k in self.contract['event_required']) or actor != event['actor'] or event['payload_hash'] != digest(payload):
            raise Rejected('event envelope')
        eid = event['event_id']
        signature = digest([event, payload])
        if eid in self.state['events']:
            if self.state['events'][eid] != signature:
                raise Rejected('event collision')
            return 'DUPLICATE'
        t = self.state['tasks'][event['task_id']]
        if event['revision'] != t['revision'] or not t['lease_id'] or event['lease_id'] != t['lease_id']:
            raise Rejected('stale lease')
        kind = payload.get('kind')
        status = t['status']
        if kind in ('start','heartbeat','result'):
            if actor != t['to_agent'] or self.clock() >= t['lease_until']:
                raise Rejected('executor/expiry')
            if kind == 'start' and status == 'CLAIMED':
                t['status'] = 'RUNNING'
            elif kind == 'heartbeat' and status == 'RUNNING':
                t['lease_until'] = self.clock()+1800
            elif kind == 'result' and status == 'RUNNING' and isinstance(payload.get('result'), str) and payload['result'].strip():
                t.update(status='REVIEW_READY', result=payload['result'])
            else:
                raise Rejected('execution transition')
        elif kind == 'review' and status == 'REVIEW_READY' and actor == t['reviewer']:
            if payload.get('result_hash') != digest(t['result']) or not payload.get('evidence'):
                raise Rejected('review evidence')
            if payload.get('verdict') not in ('PASS','CHANGES_REQUESTED'):
                raise Rejected('review verdict')
            t['status'] = 'DONE' if payload['verdict'] == 'PASS' else 'CHANGES_REQUESTED'
        else:
            raise Rejected('event transition')
        self.state['events'][eid] = signature
        return t['status']

    def recover(self):
        # Only synthetic tasks can be retried here; no side-effecting tasks admitted.
        for t in self.state['tasks'].values():
            if t['status'] in ('CLAIMED','RUNNING') and self.clock() >= t['lease_until']:
                t.update(status='READY', lease_id=None, lease_until=None)
            elif t['status'] == 'CHANGES_REQUESTED':
                t.update(status='READY', revision=t['revision']+1, lease_id=None, lease_until=None, result=None)
        return self.ready()

def make_event(task, actor, payload, event_id=None):
    return dict(event_id=event_id or uuid.uuid4().hex, task_id=task['task_id'], revision=task['revision'], lease_id=task['lease_id'], actor=actor, timestamp=time.time(), payload_hash=digest(payload))
