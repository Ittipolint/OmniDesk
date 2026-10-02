#!/usr/bin/env python3
import urllib.request, json, http.cookiejar, io

BASE = 'http://127.0.0.1:5678'
CJ = r'C:\Users\pol\AppData\Local\Temp\n8n-local-cookies.txt'
FN = r'C:\Users\pol\Desktop\OpenCode Project\ChatDesk\local\n8n\api-06-read.json'
WANT = 'ChatDesk API-06 Read (inbox/thread/webthread)'

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
wid = None
for w in (lst.get('data', []) or []):
    if w.get('name') == WANT:
        wid = w.get('id')
        print('found:', wid, '| active:', w.get('active'))
        break
assert wid, 'workflow not found'

with io.open(FN, 'r', encoding='utf-8') as f:
    wf = json.load(f)
call('POST', '/rest/workflows/%s/deactivate' % wid)
r = call('PATCH', '/rest/workflows/' + wid,
         {'name': wf['name'], 'nodes': wf['nodes'],
          'connections': wf['connections'], 'settings': wf.get('settings', {})})
d = r.get('data', r)
print('patched:', d.get('id'), '| err:', d.get('_err'))
g = call('GET', '/rest/workflows/' + wid).get('data', {})
a = call('POST', '/rest/workflows/%s/activate' % wid, {'versionId': g.get('versionId')})
print('active:', a.get('data', a).get('active'))

# smoke: inbox webhook direct
req = urllib.request.Request('http://127.0.0.1:5678/webhook/api-read',
                             data=json.dumps({'resource': 'inbox', 'filter': 'all', 'q': ''}).encode('utf-8'),
                             headers={'Content-Type': 'application/json'}, method='POST')
res = json.loads(urllib.request.urlopen(req, timeout=60).read().decode('utf-8'))
items = res.get('items', [])
with io.open(r'C:\Users\pol\AppData\Local\Temp\opencode\inbox_smoke.txt', 'w', encoding='utf-8') as o:
    for it in items[:8]:
        o.write('%s | %s | source=%s\n' % (it.get('id'), it.get('name'), it.get('source')))
print('inbox items:', len(items))
print('done')
