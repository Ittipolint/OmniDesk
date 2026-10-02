"""Patch local LINE workflow: add RAG context lookup before AI Agent."""
import urllib.request, json, uuid
BASE = 'http://127.0.0.1:5678'
CJ = r'C:\Users\pol\AppData\Local\Temp\n8n-local-cookies.txt'
import http.cookiejar
cj = http.cookiejar.MozillaCookieJar(CJ)
cj.load(CJ, ignore_discard=True, ignore_expires=True)
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
WID = 'DPXcIEfqSaxmbLV3'

def call(method, path, obj=None):
    data = json.dumps(obj).encode() if obj is not None else None
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
                                 method=method)
    return json.loads(op.open(req, timeout=120).read())

d = call('GET', '/rest/workflows/' + WID)['data']
nodes = {n['name']: n for n in d['nodes']}

rag = {"id": str(uuid.uuid4()), "name": "RAG Lookup", "type": "n8n-nodes-base.httpRequest",
       "typeVersion": 4.2, "position": [700, 120],
       "parameters": {"method": "POST", "url": "http://host.docker.internal:5678/webhook/rag-answer",
                      "sendBody": True, "specifyBody": "json",
                      "jsonBody": "={\"question\": {{ $json.text.toJsonString() }}, \"top_k\": 3}",
                      "options": {"timeout": 90000}},
       "onError": "continueRegularOutput", "retryOnFail": False}
merger = {"id": str(uuid.uuid4()), "name": "Merge RAG", "type": "n8n-nodes-base.merge",
          "typeVersion": 3.1, "position": [900, 200], "parameters": {"mode": "append"}}
attach = {"id": str(uuid.uuid4()), "name": "Attach RAG", "type": "n8n-nodes-base.code",
          "typeVersion": 2, "position": [1100, 200],
          "parameters": {"mode": "runOnceForAllItems",
                         "jsCode": ("const items = $input.all().map(r => r.json);\n"
                                    "const orig = items.find(r => r.text !== undefined && r.ok === undefined) || {};\n"
                                    "const rag = items.find(r => r.ok !== undefined) || {};\n"
                                    "const rc = (rag.text || '').toString();\n"
                                    "return [{ json: { ...orig, rag_context: rc, rag_sources: rag.sources || [] } }];")}}

agent = nodes['AI Agent']
old_text = agent['parameters']['text']
agent['parameters']['text'] = old_text + "\n\n[ข้อมูลจากฐานความรู้ RAG — ใช้ประกอบการตอบ ถ้าไม่เกี่ยวให้ตอบตามปกติ]:\n{{ $json.rag_context }}"
sysmsg = agent['parameters']['options']['systemMessage']
if 'rag_context' not in sysmsg:
    agent['parameters']['options']['systemMessage'] = sysmsg + "\nเพิ่มเติม: ถ้ามี [ข้อมูลจากฐานความรู้] แนบมา ให้ใช้ข้อมูลนั้นตอบเป็นหลัก (อ้างอิงสั้น ๆ ได้)"

d['nodes'].extend([rag, merger, attach])
cons = d['connections']
# Bot Can Reply true-branch currently -> AI Agent ; reroute: true -> RAG Lookup AND MergeRAG(in1)
cons['Bot Can Reply']['main'][0] = [{"node": "RAG Lookup", "type": "main", "index": 0},
                                    {"node": "Merge RAG", "type": "main", "index": 1}]
cons['RAG Lookup'] = {"main": [[{"node": "Merge RAG", "type": "main", "index": 0}]]}
cons['Merge RAG'] = {"main": [[{"node": "Attach RAG", "type": "main", "index": 0}]]}
cons['Attach RAG'] = {"main": [[{"node": "AI Agent", "type": "main", "index": 0}]]}

r = call('PATCH', '/rest/workflows/' + WID,
         {'name': d['name'], 'nodes': d['nodes'], 'connections': cons, 'settings': d.get('settings', {})})
print('patched version:', r.get('data', r).get('versionId'))
