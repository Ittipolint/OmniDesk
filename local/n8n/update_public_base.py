#!/usr/bin/env python3
"""Update PUBLIC_WEB_BASE in [LOCAL] ChatDesk Manager - LINE (run after tunnel regen).

Usage: python3 update_public_base.py https://xxxx.trycloudflare.com
"""
import urllib.request, json, http.cookiejar, sys

BASE = 'http://127.0.0.1:5678'
CJ = r'C:\Users\pol\AppData\Local\Temp\n8n-local-cookies.txt'
WID = 'DPXcIEfqSaxmbLV3'

if len(sys.argv) < 2 or not sys.argv[1].startswith('https://'):
    print('usage: update_public_base.py https://<new-web-tunnel-host>')
    sys.exit(2)
pub = sys.argv[1].rstrip('/')

cj = http.cookiejar.MozillaCookieJar(CJ)
cj.load(CJ, ignore_discard=True, ignore_expires=True)
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def call(method, path, obj=None):
    data = json.dumps(obj).encode() if obj is not None else None
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
                                 method=method)
    return json.loads(op.open(req, timeout=120).read())

w = call('GET', '/rest/workflows/' + WID).get('data', {})
nodes = {n['name']: n for n in w.get('nodes', [])}
assigns = nodes['Set Config']['parameters']['assignments']['assignments']
hit = [a for a in assigns if a.get('name') == 'PUBLIC_WEB_BASE']
if not hit:
    print('PUBLIC_WEB_BASE not found in Set Config')
    sys.exit(1)
hit[0]['value'] = pub
call('POST', '/rest/workflows/%s/deactivate' % WID)
r = call('PATCH', '/rest/workflows/' + WID,
         {'name': w['name'], 'nodes': w.get('nodes', []),
          'connections': w.get('connections', {}), 'settings': w.get('settings', {})})
g = call('GET', '/rest/workflows/' + WID).get('data', {})
a = call('POST', '/rest/workflows/%s/activate' % WID, {'versionId': g.get('versionId')})
print('PUBLIC_WEB_BASE =', pub, '| active:', a.get('data', a).get('active'))
