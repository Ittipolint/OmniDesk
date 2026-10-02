#!/usr/bin/env python3
import urllib.request, json, http.cookiejar, io
BASE = 'http://127.0.0.1:5678'
CJ = r'C:\Users\pol\AppData\Local\Temp\n8n-local-cookies.txt'
WID = '5n4GtYDbhf3NPhgU'
FN = r'C:\Users\pol\Desktop\OpenCode Project\ChatDesk\local\n8n\api-11-channels.json'
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

def hook(obj):
    req = urllib.request.Request('http://127.0.0.1:5678/webhook/api-channels',
                                 data=json.dumps(obj).encode('utf-8'),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    try:
        return json.loads(urllib.request.urlopen(req, timeout=60).read().decode('utf-8'))
    except Exception as e:
        try:
            return {'_err': getattr(e, 'code', '?'), '_body': e.read().decode('utf-8', 'replace')[:300]}
        except Exception:
            return {'_err': str(e)[:150]}

with io.open(FN, 'r', encoding='utf-8') as f:
    wf = json.load(f)
call('POST', '/rest/workflows/%s/deactivate' % WID)
call('PATCH', '/rest/workflows/' + WID,
     {'name': 'ChatDesk API-11 Channels (routing map)', 'nodes': wf['nodes'],
      'connections': wf['connections'], 'settings': wf.get('settings', {})})
g = call('GET', '/rest/workflows/' + WID).get('data', {})
a = call('POST', '/rest/workflows/%s/activate' % WID, {'versionId': g.get('versionId')})
print('active:', a.get('data', a).get('active'))

log = []
r = hook({'op': 'get', 'channel': 'shopweb'})
orig = r.get('channel', {})
log.append('orig groups=%s' % orig.get('group_ids'))
r = hook({'op': 'set', 'channel': 'shopweb', 'group_ids': [4, 5], 'persona_system': 'SMOKE-P'})
log.append('set multi: %s' % json.dumps(r, ensure_ascii=False)[:150])
r = hook({'op': 'get', 'channel': 'shopweb'})
ch = r.get('channel', {})
log.append('verify groups=%s persona=%s' % (ch.get('group_ids'), str(ch.get('persona_system', ''))[:15]))
r = hook({'op': 'set', 'channel': 'shopweb', 'label': 'ShopDee Web', 'rag_group_id': 5,
          'line_bot_id': '', 'is_active': 1, 'persona_system': orig.get('persona_system', '')})
log.append('old-style set: %s' % json.dumps(r, ensure_ascii=False)[:150])
r = hook({'op': 'get', 'channel': 'shopweb'})
ch = r.get('channel', {})
log.append('final groups=%s persona=%s label=%s' % (ch.get('group_ids'), str(ch.get('persona_system', ''))[:25], ch.get('label')))
with io.open(r'C:\Users\pol\AppData\Local\Temp\opencode\set_smoke.txt', 'w', encoding='utf-8') as o:
    o.write('\n'.join(log))
print('done')
