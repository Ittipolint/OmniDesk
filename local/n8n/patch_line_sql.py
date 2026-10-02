#!/usr/bin/env python3
"""Add Text-to-SQL branch to [LOCAL] ChatDesk Manager - LINE (in place update).

Chain inserted after Attach RAG:
  Attach RAG -> Shop SQL Lookup (HTTP api-shop-sql) -> Merge Shop SQL (code)
  -> SQL Direct Answer? (IF)
      true  -> Shape SQL Reply (code) -> Build Reply
      false -> Get Voice Model (existing edge)
Also: Build Ollama Body gets SQL block w/ grounding; Build Reply merges sql_images.
"""
import urllib.request, json, http.cookiejar, io, uuid

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
with io.open(r'C:\Users\pol\Desktop\OpenCode Project\ChatDesk\line_backup.json', 'w', encoding='utf-8') as f:
    json.dump(w, f, ensure_ascii=False)
print('backup saved, nodes:', len(w.get('nodes', [])))

nodes = {n['name']: n for n in w.get('nodes', [])}
conns = w.get('connections', {})
for need in ('Attach RAG', 'Get Voice Model', 'Build Reply', 'Build Ollama Body', 'RAG Lookup', 'IF Use Local?'):
    assert need in nodes, 'missing node ' + need

# --- verify existing edge Attach RAG -> Get Voice Model ---
edge = (((conns.get('Attach RAG') or {}).get('main') or [[]])[0]) or []
assert any(e.get('node') == 'Get Voice Model' for e in edge), 'edge AttachRAG->GetVoiceModel not found: %s' % json.dumps(edge)[:200]

# --- templates ---
http_tpl = json.loads(json.dumps(nodes['RAG Lookup']))  # clone structure
if_tpl = json.loads(json.dumps(nodes['IF Use Local?']))
ax, ay = nodes['Attach RAG'].get('position', [1000, 500])

def nid():
    return str(uuid.uuid4())

shop_http = {
    'id': nid(), 'name': 'Shop SQL Lookup', 'type': 'n8n-nodes-base.httpRequest',
    'typeVersion': http_tpl.get('typeVersion', 4.2), 'position': [ax + 220, ay],
    'parameters': dict(http_tpl.get('parameters', {})),
    'onError': 'continueRegularOutput', 'retryOnFail': False,
}
shop_http['parameters']['url'] = 'http://host.docker.internal:5678/webhook/api-shop-sql'
shop_http['parameters']['jsonBody'] = '={"text": {{ $json.text.toJsonString() }}, "userId": {{ $json.userId.toJsonString() }}, "history": []}'

MERGE_JS = """/* Merge Attach RAG item with Shop SQL result; decide deterministic SQL reply */
const a = $('Attach RAG').first().json;
let s = {};
try { s = $('Shop SQL Lookup').first().json || {}; } catch (e) { s = {}; }
const sql_rows = parseInt(s.rows) || 0;
const sql_answer = (s.answer || '').toString();
const sql_block = (s.block || '').toString();
let sql_images = [];
try {
  const arr = s.images;
  if (Array.isArray(arr)) sql_images = arr.map(u => (u || '').toString().trim()).filter(u => /^https:\\/\\//i.test(u)).slice(0, 4);
} catch (e2) { sql_images = []; }
const adviceQ = /(\\u0e41\\u0e19\\u0e30\\u0e19\\u0e33|\\u0e40\\u0e1b\\u0e23\\u0e35\\u0e22\\u0e1a\\u0e40\\u0e17\\u0e35\\u0e22\\u0e1a|\\u0e40\\u0e1b\\u0e23\\u0e35\\u0e22\\u0e1a|\\u0e04\\u0e38\\u0e49\\u0e21|\\u0e14\\u0e35\\u0e44\\u0e2b\\u0e21|\\u0e40\\u0e25\\u0e37\\u0e2d\\u0e01|\\u0e15\\u0e31\\u0e27\\u0e44\\u0e2b\\u0e19|\\u0e23\\u0e38\\u0e48\\u0e19\\u0e44\\u0e2b\\u0e19|\\u0e14\\u0e35\\u0e01\\u0e27\\u0e48\\u0e32)/.test(a.text || '');
const sql_direct = sql_rows > 0 && sql_answer !== '' && !adviceQ;
return [{ json: { ...a, sql_block, sql_answer, sql_images, sql_rows, sql_direct } }];"""

merge_node = {
    'id': nid(), 'name': 'Merge Shop SQL', 'type': 'n8n-nodes-base.code',
    'typeVersion': 2, 'position': [ax + 440, ay],
    'parameters': {'mode': 'runOnceForAllItems', 'jsCode': MERGE_JS},
}

if_node = json.loads(json.dumps(if_tpl))
if_node['id'] = nid()
if_node['name'] = 'SQL Direct Answer?'
if_node['position'] = [ax + 660, ay]
conds = if_node['parameters']['conditions']
conds['conditions'] = [{
    'id': nid(), 'leftValue': '={{ $json.sql_direct }}', 'rightValue': True,
    'operator': {'type': 'boolean', 'operation': 'true'},
}]

REPLY_JS = """/* Deterministic product answer from Shop SQL (skip LLM) */
const m = $('Merge Shop SQL').first().json;
return [{ json: { output: (m.sql_answer || '').toString().slice(0, 2000) } }];"""
reply_node = {
    'id': nid(), 'name': 'Shape SQL Reply', 'type': 'n8n-nodes-base.code',
    'typeVersion': 2, 'position': [ax + 880, ay - 140],
    'parameters': {'mode': 'runOnceForAllItems', 'jsCode': REPLY_JS},
}

# --- patch Build Ollama Body: append SQL block ---
ob = nodes['Build Ollama Body']['parameters']['jsCode']
old_content = "const content = (a.text || '') + '\\n\\n[\u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25\u0e08\u0e32\u0e01\u0e10\u0e32\u0e19\u0e04\u0e27\u0e32\u0e21\u0e23\u0e39\u0e49 RAG \u2014 \u0e43\u0e0a\u0e49\u0e1b\u0e23\u0e30\u0e01\u0e2d\u0e1a\u0e01\u0e32\u0e23\u0e15\u0e2d\u0e1a \u0e16\u0e49\u0e32\u0e44\u0e21\u0e48\u0e40\u0e01\u0e35\u0e48\u0e22\u0e27\u0e43\u0e2b\u0e49\u0e15\u0e2d\u0e1a\u0e15\u0e32\u0e21\u0e1b\u0e01\u0e15\u0e34]:\\n' + (a.rag_context || '');"
assert old_content in ob, 'Build Ollama Body content line not found'
new_content = ("const sqlBlock = (a.sql_block || '');\n"
"const content = (a.text || '') + '\\n\\n[\u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25\u0e08\u0e32\u0e01\u0e10\u0e32\u0e19\u0e04\u0e27\u0e32\u0e21\u0e23\u0e39\u0e49 RAG \u2014 \u0e43\u0e0a\u0e49\u0e1b\u0e23\u0e30\u0e01\u0e2d\u0e1a\u0e01\u0e32\u0e23\u0e15\u0e2d\u0e1a \u0e16\u0e49\u0e32\u0e44\u0e21\u0e48\u0e40\u0e01\u0e35\u0e48\u0e22\u0e27\u0e43\u0e2b\u0e49\u0e15\u0e2d\u0e1a\u0e15\u0e32\u0e21\u0e1b\u0e01\u0e15\u0e34]:\\n' + (a.rag_context || '')\n"
"  + (sqlBlock ? '\\n\\n[\u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25\u0e2a\u0e14\u0e08\u0e32\u0e01\u0e10\u0e32\u0e19\u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25\u0e23\u0e49\u0e32\u0e19 \u2014 \u0e02\u0e49\u0e2d\u0e40\u0e17\u0e47\u0e08\u0e08\u0e23\u0e34\u0e07 \u0e15\u0e49\u0e2d\u0e07\u0e22\u0e36\u0e14\u0e15\u0e31\u0e27\u0e40\u0e25\u0e02\u0e23\u0e32\u0e04\u0e32/\u0e2a\u0e15\u0e47\u0e2d\u0e01/\u0e0a\u0e37\u0e48\u0e2d\u0e23\u0e49\u0e32\u0e19\u0e15\u0e32\u0e21\u0e19\u0e35\u0e49\u0e40\u0e17\u0e48\u0e32\u0e19\u0e31\u0e49\u0e19 \u0e2b\u0e49\u0e32\u0e21\u0e14\u0e36\u0e07\u0e15\u0e31\u0e27\u0e40\u0e25\u0e02\u0e08\u0e32\u0e01\u0e41\u0e16\u0e27\u0e2d\u0e37\u0e48\u0e19\u0e2b\u0e23\u0e37\u0e2d\u0e41\u0e15\u0e48\u0e07 spec \u0e40\u0e1e\u0e34\u0e48\u0e21]:\\n' + sqlBlock : '');")
nodes['Build Ollama Body']['parameters']['jsCode'] = ob.replace(old_content, new_content, 1)
print('Build Ollama Body patched')

# --- patch Build Reply: merge sql_images ---
br = nodes['Build Reply']['parameters']['jsCode']
old_imgs = "try { imgs = ($('Attach RAG').first().json.rag_images || []); } catch (err) { imgs = []; }"
assert old_imgs in br, 'Build Reply imgs line not found'
new_imgs = (old_imgs + "\ntry { const sq = ($('Merge Shop SQL').first().json.sql_images || []);"
            " if (Array.isArray(sq)) imgs = imgs.concat(sq); } catch (err2) {}")
nodes['Build Reply']['parameters']['jsCode'] = br.replace(old_imgs, new_imgs, 1)
print('Build Reply patched')

# --- add nodes & rewire ---
w['nodes'].extend([shop_http, merge_node, if_node, reply_node])
conns['Attach RAG']['main'][0] = [{'node': 'Shop SQL Lookup', 'type': 'main', 'index': 0}]
conns['Shop SQL Lookup'] = {'main': [[{'node': 'Merge Shop SQL', 'type': 'main', 'index': 0}]]}
conns['Merge Shop SQL'] = {'main': [[{'node': 'SQL Direct Answer?', 'type': 'main', 'index': 0}]]}
conns['SQL Direct Answer?'] = {'main': [
    [{'node': 'Shape SQL Reply', 'type': 'main', 'index': 0}],
    [{'node': 'Get Voice Model', 'type': 'main', 'index': 0}],
]}
conns['Shape SQL Reply'] = {'main': [[{'node': 'Build Reply', 'type': 'main', 'index': 0}]]}

call('POST', '/rest/workflows/%s/deactivate' % WID)
r = call('PATCH', '/rest/workflows/' + WID,
         {'name': w['name'], 'nodes': w['nodes'], 'connections': conns, 'settings': w.get('settings', {})})
d = r.get('data', r)
print('patched:', d.get('id'), '| version:', d.get('versionId'), '| err:', d.get('_err'))
g = call('GET', '/rest/workflows/' + WID).get('data', {})
a = call('POST', '/rest/workflows/%s/activate' % WID, {'versionId': g.get('versionId')})
print('active:', a.get('data', a).get('active'))

# --- verify live ---
g2 = call('GET', '/rest/workflows/' + WID).get('data', {})
names = [n.get('name') for n in g2.get('nodes', [])]
print('nodes now:', len(names))
for nn in ('Shop SQL Lookup', 'Merge Shop SQL', 'SQL Direct Answer?', 'Shape SQL Reply'):
    print(nn, ':', nn in names)
print('done')
