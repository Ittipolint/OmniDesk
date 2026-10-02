"""Throwaway test: exact LINE image JS + push expression against httpbin echo. Creates, runs, deletes."""
import urllib.request, json, http.cookiejar

BASE = 'http://127.0.0.1:5678'
CJ = r'C:\Users\pol\AppData\Local\Temp\n8n-local-cookies.txt'
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


live = call('GET', '/rest/workflows/DPXcIEfqSaxmbLV3').get('data', {})
ln = {n['name']: n for n in live.get('nodes', [])}
attach_js = ln['Attach RAG']['parameters']['jsCode']
reply_js = ln['Build Reply']['parameters']['jsCode']
push_body = ln['Push LINE']['parameters']['jsonBody']
print('live code lengths:', len(attach_js), len(reply_js), len(push_body))

import uuid
def N(name, ntype, x, params, y=300):
    return {"id": str(uuid.uuid4()), "name": name, "type": ntype, "typeVersion": 2,
            "position": [x, y], "parameters": params}

fake = N('Fake Merge', 'n8n-nodes-base.code', 200,
         {"mode": "runOnceForAllItems",
          "jsCode": "return [{ json: { text: 'ป้ายเส้นทางลัดเขียนว่าอะไร' } }, { json: { ok: true, text: 'ctx', images: ['https://raw.githubusercontent.com/JaidedAI/EasyOCR/master/examples/thai.jpg', 'http://127.0.0.1:8081/chatdesk/uploads/rag_x.jpg'], sources: ['pm/URL-TEST-thai-sign'] } }];"})
attach = N('Attach RAG', 'n8n-nodes-base.code', 400, {"mode": "runOnceForAllItems", "jsCode": attach_js})
agent = N('Fake Agent', 'n8n-nodes-base.code', 600,
          {"mode": "runOnceForAllItems", "jsCode": "return [{ json: { output: 'ป้ายเขียนว่าเส้นทางลัด เพชรบุรี' } }];"})
stub = N('Send to ChatDesk', 'n8n-nodes-base.code', 800,
         {"mode": "runOnceForAllItems",
          "jsCode": "const a = $input.first().json; return [{ json: { output: a.output, userId: 'Utest123' } }];"})
reply = N('Build Reply', 'n8n-nodes-base.code', 1000, {"mode": "runOnceForAllItems", "jsCode": reply_js})
push = N('Push Probe', 'n8n-nodes-base.httpRequest', 1200,
         {"method": "POST", "url": "https://httpbin.org/post", "sendBody": True,
          "specifyBody": "json", "jsonBody": push_body, "options": {"timeout": 30000}})
push["typeVersion"] = 4.2
resp = N('Resp', 'n8n-nodes-base.respondToWebhook', 1400,
         {"respondWith": "json", "responseBody": "={{ $json }}", "options": {}})
resp["typeVersion"] = 1.5

nodes = [fake, attach, agent, stub, reply, push, resp]
E = lambda c, a, b: c.setdefault(a["name"], {}).setdefault("main", []).append([{"node": b["name"], "type": "main", "index": 0}])
cons = {}
for a, b in [(fake, attach), (attach, agent), (agent, stub), (stub, reply), (reply, push), (push, resp)]:
    E(cons, a, b)
wh = N('WH', 'n8n-nodes-base.webhook', 100, {"httpMethod": "POST", "path": "probe-img", "responseMode": "responseNode", "options": {}})
wh["typeVersion"] = 2.1
wh["webhookId"] = str(uuid.uuid4())
nodes.insert(0, wh)
E(cons, wh, fake)

wf = {"name": "THROWAWAY probe-img", "nodes": nodes, "connections": cons,
      "settings": {"executionOrder": "v1"}, "pinData": {}}
r = call('POST', '/rest/workflows', wf)
wid = r.get('data', r).get('id')
print('created:', wid)
a = call('POST', '/rest/workflows/%s/activate' % wid,
         {'versionId': call('GET', '/rest/workflows/' + wid).get('data', {}).get('versionId')})
print('active:', a.get('data', a).get('active'))
open(r'C:\Users\pol\AppData\Local\Temp\opencode\probe_wid.txt', 'w').write(wid or '')
