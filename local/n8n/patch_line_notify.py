#!/usr/bin/env python3
"""Save bot reply images into ChatDesk inbox (Notify ChatDesk node)."""
import urllib.request, json, http.cookiejar, io

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
assert 'Notify ChatDesk' in nodes, 'node missing'
old = nodes['Notify ChatDesk']['parameters']['jsCode']

anchor = "  if (!res || res.ok !== true) {\n    throw new Error('ChatDesk save failed: ' + JSON.stringify(res));\n  }\n}"
assert anchor in old, 'anchor not found'
add = """  if (!res || res.ok !== true) {
    throw new Error('ChatDesk save failed: ' + JSON.stringify(res));
  }
  const imgs = Array.isArray(j.images) ? j.images : [];
  for (const u of imgs.slice(0, 4)) {
    const url = (u || '').toString().trim();
    if (!/^https:\\/\\//i.test(url)) { continue; }
    const ipayload = { userId: j.userId, text: url, sender: 'bot', channel: $('Shape Channel').first().json.channel_code || 'line', messageType: 'image', mediaUrl: url, mediaPreviewUrl: url };
    if (cfg.CHATDESK_SECRET) { ipayload.secret = cfg.CHATDESK_SECRET; }
    await this.helpers.httpRequest({ method: 'POST', url: cfg.CHATDESK_URL, json: true, timeout: 20000, body: ipayload });
  }
}"""
nodes['Notify ChatDesk']['parameters']['jsCode'] = old.replace(anchor, add, 1)
print('Notify ChatDesk patched')

call('POST', '/rest/workflows/%s/deactivate' % WID)
r = call('PATCH', '/rest/workflows/' + WID,
         {'name': w['name'], 'nodes': w.get('nodes', []),
          'connections': w.get('connections', {}), 'settings': w.get('settings', {})})
d = r.get('data', r)
print('patched:', d.get('id'), '| err:', d.get('_err'))
g = call('GET', '/rest/workflows/' + WID).get('data', {})
a = call('POST', '/rest/workflows/%s/activate' % WID, {'versionId': g.get('versionId')})
print('active:', a.get('data', a).get('active'))
print('done')
