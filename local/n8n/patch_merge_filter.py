#!/usr/bin/env python3
"""Merge Shop SQL: allow http(s) image URLs through (Build Reply rewrites+filters for LINE)."""
import urllib.request, json, http.cookiejar

BASE = 'http://127.0.0.1:5678'
CJ = r'C:\Users\pol\AppData\Local\Temp\n8n-local-cookies.txt'
WID = 'DPXcIEfqSaxmbLV3'

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
            body = e.read().decode('utf-8', 'replace')[:400]
        except Exception:
            body = str(e)[:200]
        return {'_err': getattr(e, 'code', '?'), '_body': body}

w = call('GET', '/rest/workflows/' + WID).get('data', {})
nodes = {n['name']: n for n in w.get('nodes', [])}
js = nodes['Merge Shop SQL']['parameters']['jsCode']
old = ".filter(u => /^https:\\/\\//i.test(u)).slice(0, 4);"
assert old in js, 'filter not found'
nodes['Merge Shop SQL']['parameters']['jsCode'] = js.replace(old, ".filter(u => /^https?:\\/\\//i.test(u)).slice(0, 4);", 1)
print('Merge Shop SQL patched')

call('POST', '/rest/workflows/%s/deactivate' % WID)
r = call('PATCH', '/rest/workflows/' + WID,
         {'name': w['name'], 'nodes': w.get('nodes', []),
          'connections': w.get('connections', {}), 'settings': w.get('settings', {})})
d = r.get('data', r)
print('patched:', d.get('id'), '| err:', d.get('_err'))
g = call('GET', '/rest/workflows/' + WID).get('data', {})
a = call('POST', '/rest/workflows/%s/activate' % WID, {'versionId': g.get('versionId')})
print('active:', a.get('data', a).get('active'))
g2 = call('GET', '/rest/workflows/' + WID).get('data', {})
n2 = {n['name']: n for n in g2.get('nodes', [])}
print('live filter:', 'https?:' in n2['Merge Shop SQL']['parameters']['jsCode'])
print('done')
