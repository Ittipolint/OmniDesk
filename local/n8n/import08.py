#!/usr/bin/env python3
import urllib.request, json, http.cookiejar, io
BASE = 'http://127.0.0.1:5678'
CJ = r'C:\Users\pol\AppData\Local\Temp\n8n-local-cookies.txt'
WANT = 'ChatDesk API-08 RAG Meta (groups+stats)'
FN = r'C:\Users\pol\Desktop\OpenCode Project\ChatDesk\local\n8n\api-08-ragmeta.json'
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

def hook(url, obj, timeout=120):
    req = urllib.request.Request(url, data=json.dumps(obj).encode('utf-8'),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    try:
        return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode('utf-8'))
    except Exception as e:
        try:
            return {'_err': getattr(e, 'code', '?'), '_body': e.read().decode('utf-8', 'replace')[:300]}
        except Exception:
            return {'_err': str(e)[:150]}

lst = call('GET', '/rest/workflows')
wid = next((w.get('id') for w in (lst.get('data', []) or []) if w.get('name') == WANT), None)
print('ragmeta ->', wid)
assert wid
with io.open(FN, 'r', encoding='utf-8') as f:
    wf = json.load(f)
call('POST', '/rest/workflows/%s/deactivate' % wid)
call('PATCH', '/rest/workflows/' + wid,
     {'name': WANT, 'nodes': wf['nodes'], 'connections': wf['connections'], 'settings': wf.get('settings', {})})
g = call('GET', '/rest/workflows/' + wid).get('data', {})
a = call('POST', '/rest/workflows/%s/activate' % wid, {'versionId': g.get('versionId')})
print('active:', a.get('data', a).get('active'))

log = []
r = hook('http://127.0.0.1:5678/webhook/api-ragmeta', {'op': 'list'})
log.append('groups list ok=%s groups=%s' % (r.get('ok'), [(g.get('name'), g.get('chunks')) for g in r.get('groups', [])]))
r = hook('http://127.0.0.1:5678/webhook/api-shop-sql',
         {'text': 'จอมอนิเตอร์ 27 นิ้ว', 'userId': 'WEB_MULTI', 'history': []})
log.append('shopsql rows=%s images=%d' % (r.get('rows'), len(r.get('images', []))))
r = hook('http://127.0.0.1:8081/shopdee/api/chat.php',
         {'text': 'จอมอนิเตอร์ 27 นิ้ว', 'userId': 'WEB_MULTI', 'history': []})
log.append('shopdee chat ok=%s via=%s text=%s' % (r.get('ok'), r.get('via'), str(r.get('text', ''))[:90]))
with io.open(r'C:\Users\pol\AppData\Local\Temp\opencode\final_smoke.txt', 'w', encoding='utf-8') as o:
    o.write('\n'.join(log))
print('done')
