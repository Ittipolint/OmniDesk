#!/usr/bin/env python3
import urllib.request, json, http.cookiejar, io

BASE = 'http://127.0.0.1:5678'
CJ = r'C:\Users\pol\AppData\Local\Temp\n8n-local-cookies.txt'
JOBS = [
    (r'C:\Users\pol\Desktop\OpenCode Project\ChatDesk\local\n8n\rag-04-answer.json', 'ChatDesk RAG-04 Answer (Gemini + PGVector + Postgres)'),
    (r'C:\Users\pol\Desktop\OpenCode Project\ChatDesk\local\n8n\api-01-aichat.json', 'ChatDesk API-01 AI Chat (unified brain)'),
    (r'C:\Users\pol\Desktop\OpenCode Project\ChatDesk\local\n8n\api-11-channels.json', 'ChatDesk API-11 Channels (routing map)'),
]

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

lst = call('GET', '/rest/workflows')
byname = {w.get('name'): w.get('id') for w in (lst.get('data', []) or [])}
for fn, want in JOBS:
    wid = byname.get(want)
    print(want, '->', wid)
    assert wid, 'not found: ' + want
    with io.open(fn, 'r', encoding='utf-8') as f:
        wf = json.load(f)
    call('POST', '/rest/workflows/%s/deactivate' % wid)
    r = call('PATCH', '/rest/workflows/' + wid,
             {'name': want, 'nodes': wf['nodes'],
              'connections': wf['connections'], 'settings': wf.get('settings', {})})
    print('  patched err:', r.get('_err'))
    g = call('GET', '/rest/workflows/' + wid).get('data', {})
    a = call('POST', '/rest/workflows/%s/activate' % wid, {'versionId': g.get('versionId')})
    print('  active:', a.get('data', a).get('active'))
print('all imported')
