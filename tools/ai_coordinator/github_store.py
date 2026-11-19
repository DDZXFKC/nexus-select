"""GitHub issue snapshot transport. Single dispatcher only; no blind write retries."""
import json
import os
import urllib.request
import urllib.error

class StoreError(RuntimeError):
    pass

class IssueStore:
    def __init__(self, repo, number, token=None, opener=urllib.request.urlopen):
        import re
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo) or type(number) is not int or number < 1:
            raise StoreError('invalid issue locator')
        self.url='https://api.github.com/repos/'+repo+'/issues/'+str(number)
        self.token=token or os.environ.get('AHC_GITHUB_TOKEN')
        if not self.token:
            raise StoreError('missing dispatcher credential')
        self.opener=opener

    def request(self, method='GET', data=None):
        req=urllib.request.Request(self.url, method=method,
            data=None if data is None else json.dumps(data).encode(),
            headers={'Authorization':'Bearer '+self.token,'Accept':'application/vnd.github+json',
                     'Content-Type':'application/json','X-GitHub-Api-Version':'2022-11-28'})
        try:
            with self.opener(req, timeout=30) as response:
                raw=response.read(2*1024*1024+1)
            if len(raw)>2*1024*1024:
                raise StoreError('oversize response')
            return json.loads(raw)
        except Exception:
            raise StoreError('GitHub request failed; reconcile before writing again') from None

    def read(self):
        issue=self.request()
        if 'pull_request' in issue or issue.get('state')!='open':
            raise StoreError('not an open task state issue')
        try:
            envelope=json.loads(issue['body'])
            if envelope['format']!='ahc-coordinator-state-v1' or type(envelope['generation']) is not int:
                raise ValueError()
            return envelope
        except (KeyError,TypeError,ValueError):
            raise StoreError('invalid state envelope') from None

    def write(self, previous, state):
        # GitHub Issues PATCH does not provide a guaranteed atomic CAS.
        # Caller must hold the sole dispatcher lock and own all writes.
        if self.read()!=previous:
            raise StoreError('state changed; stop dispatcher')
        desired={'format':'ahc-coordinator-state-v1','generation':previous['generation']+1,'state':state}
        body=json.dumps(desired,ensure_ascii=True,sort_keys=True,separators=(',',':'))
        if len(body)>60000:
            raise StoreError('issue body capacity; stop before losing state')
        try:
            self.request('PATCH',{'body':body})
        except StoreError:
            if self.read()==desired:
                return desired
            raise StoreError('write unresolved; do not retry automatically') from None
        if self.read()!=desired:
            raise StoreError('readback mismatch; stop dispatcher')
        return desired
