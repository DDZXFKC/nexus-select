"""GLM Coding Plan adapter: synthetic nonce check only. Python 3.9+, stdlib."""
import json
import os
import urllib.request
import urllib.error
import uuid

URL = 'https://api.z.ai/api/coding/paas/v4/chat/completions'
MODEL = 'glm-5.2'

class BridgeError(RuntimeError):
    pass

def check(opener=urllib.request.urlopen, key=None, nonce=None):
    key = key if key is not None else os.environ.get('GLM_API_KEY')
    if not key:
        raise BridgeError('missing credential')
    nonce = nonce or uuid.uuid4().hex
    body = json.dumps({'model': MODEL, 'messages': [{'role':'user','content':'Return exactly this token, no other text: '+nonce}], 'temperature':0}).encode()
    req = urllib.request.Request(URL, data=body, headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    # A POST whose response was lost may have incurred a charge. Do not retry.
    try:
        with opener(req, timeout=120) as response:
            raw = response.read(1024*1024+1)
        if len(raw)>1024*1024:
            raise BridgeError('oversize response')
        data = json.loads(raw)
        choice = data['choices'][0]
        if choice['finish_reason'] != 'stop' or choice['message']['content'].strip() != nonce:
            raise BridgeError('nonce or completion mismatch')
        return {'status':'CHECK_OK','model':MODEL,'nonce':nonce}
    except urllib.error.HTTPError as exc:
        raise BridgeError('HTTP status '+str(exc.code)) from None
    except BridgeError:
        raise
    except Exception:
        raise BridgeError('response unavailable or invalid; no automatic retry') from None

if __name__ == '__main__':
    import sys
    if sys.argv[1:] != ['--check']:
        sys.exit('usage: glm_bridge.py --check')
    try:
        print(json.dumps(check()))
    except BridgeError as exc:
        sys.exit(str(exc))
