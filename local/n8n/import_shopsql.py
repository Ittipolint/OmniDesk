#!/usr/bin/env python3
"""Import local/n8n/api-12-shopsql.json into running n8n (update in place, keep id)."""
import urllib.request, json, http.cookiejar, io, sys

BASE = 'http://127.0.0.1:5678'
CJ = r'C:\Users\pol\AppData\Local\Temp\n8n-local-cookies.txt'
FN = r'C:\Users\pol\Desktop\OpenCode Project\ChatDesk\local\n8n\api-12-shopsql.json'
WANT_NAME = 'ChatDesk API-12 Shop SQL (structured lookup)'

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
            body = e.read().decode('utf-8', 'replace')[:500]
        except Exception:
            body = str(e)[:200]
        return {'_err': getattr(e, 'code', '?'), '_body': body}

# 1. find workflow id by name
lst = call('GET', '/rest/workflows')
items = lst.get('data', lst) if isinstance(lst, dict) else lst
wid = None
if isinstance(items, list):
    for w in items:
        if w.get('name') == WANT_NAME:
            wid = w.get('id')
            print('found:', wid, '| active:', w.get('active'))
            break
if not wid:
    print('WORKFLOW NOT FOUND. names on server:')
    if isinstance(items, list):
        for w in items:
            print(' -', w.get('id'), w.get('name'), w.get('active'))
    sys.exit(1)

with io.open(FN, 'r', encoding='utf-8') as f:
    wf = json.load(f)
print('local file nodes:', len(wf['nodes']))

# 2. deactivate -> patch -> activate
_d = call('POST', '/rest/workflows/%s/deactivate' % wid)
print('deactivated ok:', '_err' not in _d)
r = call('PATCH', '/rest/workflows/' + wid,
         {'name': wf['name'], 'nodes': wf['nodes'],
          'connections': wf['connections'], 'settings': wf.get('settings', {})})
d = r.get('data', r)
print('patched id:', d.get('id'), '| version:', d.get('versionId'), '| err:', d.get('_err'))
print('patch body head:', str(d.get('_body', ''))[:200])
g = call('GET', '/rest/workflows/' + wid).get('data', {})
a = call('POST', '/rest/workflows/%s/activate' % wid, {'versionId': g.get('versionId')})
print('active:', a.get('data', a).get('active'))

# 3. verify route code live
g2 = call('GET', '/rest/workflows/' + wid).get('data', {})
for n in g2.get('nodes', []):
    if n.get('name') == 'Route SQL':
        js = n['parameters'].get('jsCode', '')
        print('live Route has chitchat-gate:', 'chitchat' in js)
    if n.get('name') == 'Build Template SQL':
        print('live Template has numeric-regex:', '(^|[^0-9])' in n['parameters'].get('jsCode', ''))
print('done')
