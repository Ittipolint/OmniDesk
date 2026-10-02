#!/usr/bin/env python3
"""Create-or-update api-13-odolead workflow (preserves server name)."""
import urllib.request, json, http.cookiejar, io

BASE = 'http://127.0.0.1:5678'
CJ = r'C:\Users\pol\AppData\Local\Temp\n8n-local-cookies.txt'
import sys as _sys
FN = _sys.argv[1] if len(_sys.argv) > 1 else r'C:\Users\pol\Desktop\OpenCode Project\ChatDesk\local\n8n\api-13-odolead.json'

cj = http.cookiejar.MozillaCookieJar(CJ)
cj.load(CJ, ignore_discard=True, ignore_expires=True)
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def call(method, path, obj=None):
    data = json.dumps(obj).encode() if obj is not None else None
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
                                 method=method)
    try:
        return json.loads(op.open(req, timeout=120).read())
    except Exception as e:
        try:
            body = e.read().decode('utf-8', 'replace')[:300]
        except Exception:
            body = str(e)[:150]
        return {'_err': getattr(e, 'code', '?'), '_body': body}

with io.open(FN, 'r', encoding='utf-8') as f:
    wf = json.load(f)
lst = call('GET', '/rest/workflows')
wid = next((w.get('id') for w in (lst.get('data', []) or []) if w.get('name') == wf['name']), None)
if wid:
    print('exists:', wid, '- updating')
    call('POST', '/rest/workflows/%s/deactivate' % wid)
    r = call('PATCH', '/rest/workflows/' + wid,
             {'name': wf['name'], 'nodes': wf['nodes'],
              'connections': wf['connections'], 'settings': wf.get('settings', {})})
    print('patched err:', r.get('_err'))
else:
    r = call('POST', '/rest/workflows',
             {'name': wf['name'], 'nodes': wf['nodes'],
              'connections': wf['connections'], 'settings': wf.get('settings', {})})
    d = r.get('data', r)
    wid = d.get('id')
    print('created:', wid, '| err:', r.get('_err'))
g = call('GET', '/rest/workflows/' + wid).get('data', {})
a = call('POST', '/rest/workflows/%s/activate' % wid, {'versionId': g.get('versionId')})
print('active:', a.get('data', a).get('active'))
