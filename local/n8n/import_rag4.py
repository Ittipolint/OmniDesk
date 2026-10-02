#!/usr/bin/env python3
"""Import local rag-04-answer.json (preserves server workflow name)."""
import urllib.request, json, http.cookiejar, io
BASE = 'http://127.0.0.1:5678'
CJ = r'C:\Users\pol\AppData\Local\Temp\n8n-local-cookies.txt'
WID = 'RKrBD4TtzMNsRtEk'
FN = r'C:\Users\pol\Desktop\OpenCode Project\ChatDesk\local\n8n\rag-04-answer.json'
WANT = 'ChatDesk RAG-04 Answer (Gemini + PGVector + Postgres)'
cj = http.cookiejar.MozillaCookieJar(CJ)
cj.load(CJ, ignore_discard=True, ignore_expires=True)
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def call(method, path, obj=None):
    data = json.dumps(obj).encode() if obj is not None else None
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
                                 method=method)
    return json.loads(op.open(req, timeout=120).read())

with io.open(FN, 'r', encoding='utf-8') as f:
    wf = json.load(f)
call('POST', '/rest/workflows/%s/deactivate' % WID)
call('PATCH', '/rest/workflows/' + WID,
     {'name': WANT, 'nodes': wf['nodes'], 'connections': wf['connections'], 'settings': wf.get('settings', {})})
g = call('GET', '/rest/workflows/' + WID).get('data', {})
a = call('POST', '/rest/workflows/%s/activate' % WID, {'versionId': g.get('versionId')})
print('active:', a.get('data', a).get('active'))
