"""Generate ChatDesk RAG n8n workflows (ingest + answer). Run: python gen_rag_wf.py"""
import json
import os
import uuid

PG_CHATDESK = {"id": "iGiNCBmmhZ9xgFn8", "name": "ChatDesk Postgres (chatdesk)"}
PG_RAGDB = {"id": "1d2k0urW1mECDLrE", "name": "RAG Postgres (postgres-rag:5432 / ragdb)"}
GEMINI = {"id": "VuE8YX5cbPUw7Ay8", "name": "Google Gemini(PaLM) Api account"}
GEMINI_KEY = "__GEMINI_API_KEY__"
OLLAMA_HOST = "http://host.docker.internal:11434"
OCR_GW = "http://host.docker.internal:8080"


def nid():
    return str(uuid.uuid4())


def N(name, ntype, x, params=None, creds=None, y=300, tv=2, extra=None):
    n = {"id": nid(), "name": name, "type": ntype, "typeVersion": tv,
         "position": [x, y], "parameters": params or {}}
    if creds:
        n["credentials"] = creds
    if extra:
        n.update(extra)
    return n


def WH(name, path, x):
    n = N(name, "n8n-nodes-base.webhook", x,
          {"httpMethod": "POST", "path": path, "responseMode": "responseNode", "options": {}},
          extra={"webhookId": str(uuid.uuid4())})
    n["typeVersion"] = 2.1
    return n


def CODE(name, x, js, y=300):
    n = N(name, "n8n-nodes-base.code", x, {"mode": "runOnceForAllItems", "jsCode": js}, y=y)
    n["typeVersion"] = 2
    return n


def PGQ(name, x, query, creds, y=300):
    n = N(name, "n8n-nodes-base.postgres", x,
          {"operation": "executeQuery", "query": query, "options": {}}, creds, y)
    n["typeVersion"] = 2.4
    return n


def HTTP(name, x, method, url, json_body=None, y=300, timeout=60000):
    p = {"method": method, "url": url, "options": {"timeout": timeout}}
    if json_body is not None:
        p["sendBody"] = True
        p["specifyBody"] = "json"
        p["jsonBody"] = json_body
    n = N(name, "n8n-nodes-base.httpRequest", x, p, y=y)
    n["typeVersion"] = 4.2
    return n


def IF(name, x, left, y=300):
    n = N(name, "n8n-nodes-base.if", x, {
        "conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose"},
                       "conditions": [{"id": nid(), "leftValue": left,
                                       "rightValue": True, "operator": {"type": "boolean", "operation": "true"}}],
                       "combinator": "and"}, "options": {}}, y=y)
    n["typeVersion"] = 2.2
    return n


def E(cons, a, b, out=0, inp=0):
    cons.setdefault(a["name"], {}).setdefault("main", []).append(
        [{"node": b["name"], "type": "main", "index": inp}] if out == 0 else [])
    # NOTE: n8n connections.main is a 2D array [outputs][targets]; single output -> cons[a].main = [[...]]
    return cons


def E2(cons, a, b_true, b_false):
    cons[a["name"]] = {"main": [
        [{"node": b_true["name"], "type": "main", "index": 0}],
        [{"node": b_false["name"], "type": "main", "index": 0}]]}
    return cons


# ================= RAG-03 INGEST =================
def build_ingest():
    wh = WH("Webhook Ingest", "rag-ingest", 200)
    route = CODE("Route + Flags", 420,
                 "const inp = $input.first();\n"
                 "const b = inp.json.body || inp.json || {};\n"
                 "const kind = ['text','pdf','image','url'].includes(b.type) ? b.type : 'text';\n"
                 "const bin = inp.binary || {};\n"
                 "const hasFile = Object.keys(bin).length > 0;\n"
                 "const sq = (s) => (s || '').toString().replace(/'/g, \"''\");\n"
                 "const group_id = parseInt(b.group_id) || 0;\n"
                 "if (!group_id) throw new Error('missing group_id');\n"
                 "return [{ json: {\n"
                 "  kind: kind, group_id: group_id,\n"
                 "  group_name: (b.group_name || '').toString(),\n"
                 "  title: (b.title || '').toString().slice(0, 255),\n"
                 "  title_q: sq(b.title).slice(0, 255),\n"
                 "  text: (b.text || '').toString(),\n"
                 "  url: (b.url || '').toString(),\n"
                 "  image_url: (b.image_url || '').toString(),\n"
                 "  url_q: sq(b.url).slice(0, 2000),\n"
                 "  imgurl_q: sq(b.image_url).slice(0, 2000),\n"
                 "  is_url: kind === 'url', has_file: hasFile,\n"
                 "  has_imgurl: /^https?:\\/\\//i.test((b.image_url || '').toString())\n"
                 "}, binary: bin }];")
    if_url = IF("IF Is URL?", 640, "={{ $json.is_url }}")
    fetch = HTTP("Fetch URL", 860, "GET", "={{ $json.url }}", y=200)
    fetch["parameters"]["options"] = {"timeout": 30000, "response": {"response": {"responseFormat": "text"}}}
    set_url = CODE("Strip Tags", 1060,
                   "const it = $input.first().json;\n"
                   "const flags = $('Route + Flags').first().json;\n"
                   "let t = ((it.data || it.text || '')).toString();\n"
                   "t = t.replace(/<script[\\s\\S]*?<\\/script>/gi, ' ').replace(/<style[\\s\\S]*?<\\/style>/gi, ' ');\n"
                   "t = t.replace(/<[^>]+>/g, ' ').replace(/\\s+/g, ' ').trim();\n"
                   "return [{ json: { ...flags, text: t.slice(0, 60000) } }];", y=200)
    if_file = IF("IF Has File?", 860, "={{ $json.has_file }}", y=420)
    if_img = IF("IF Has Image URL?", 1060, "={{ $json.has_imgurl }}", y=540)
    dl_img = HTTP("Download Image", 1260, "GET", "={{ $json.image_url }}", y=540)
    dl_img["parameters"]["options"] = {"timeout": 60000, "response": {"response": {"responseFormat": "file"}}}
    reattach = CODE("Reattach Flags", 1460,
                    "const inp = $input.first();\n"
                    "const flags = $('Route + Flags').first().json;\n"
                    "return [{ json: { ...flags }, binary: inp.binary }];", y=540)
    gem_prep = CODE("Build Gemini OCR", 1460,
                    "const it = $input.first().json;\n"
                    "const bin = $input.first().binary || {};\n"
                    "const fname = bin.file ? 'file' : (bin.data ? 'data' : Object.keys(bin)[0]);\n"
                    "if (!fname) throw new Error('no file binary (field name must be file)');\n"
                    "const buf = await this.helpers.getBinaryDataBuffer(0, fname);\n"
                    "const f = bin[fname] || {};\n"
                    "const prompt = it.kind === 'image'\n"
                    "  ? 'พากย์ภาพนี้เป็นภาษาไทย 1-2 ประโยค แล้วถอดข้อความตัวอักษรที่เห็นในภาพทั้งหมด (OCR) ตอบเป็นข้อความล้วน'\n"
                    "  : 'ถอดข้อความทั้งหมดในเอกสาร PDF นี้เป็นภาษาไทย คงโครงสร้างหัวข้อและตัวเลขไว้ครบ ตอบเป็นข้อความล้วน';\n"
                    "return [{ json: { ...it, _mime: f.mimeType || 'application/octet-stream', _data: buf.toString('base64'),\n"
                    "  _prompt: (it.kind === 'image' && it.text) ? (it.text + '\\n\\n' + prompt) : prompt } }];", y=420)
    gem_ocr = HTTP("Gemini OCR", 1660,
                  "POST", "={{ 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=' + $('Get Gemini Key').first().json.value }}",
                  "={\"contents\": [{\"parts\": [{\"text\": {{ $('Build Gemini OCR').first().json._prompt.toJsonString() }}}, {\"inline_data\": {\"mime_type\": {{ $('Build Gemini OCR').first().json._mime.toJsonString() }}, \"data\": {{ $('Build Gemini OCR').first().json._data.toJsonString() }} }}]}]}",
                  y=420, timeout=120000)
    getkey = PGQ("Get Gemini Key", 1560,
                 "SELECT COALESCE((SELECT value FROM app_settings WHERE key = 'gemini.api_key'), '" + GEMINI_KEY + "') AS value",
                 {"postgres": PG_CHATDESK}, y=540)
    getocr = PGQ("Get OCR Engine", 1560,
                 "SELECT COALESCE((SELECT value FROM app_settings WHERE key = 'ocr.engine'), 'gemini') AS value",
                 {"postgres": PG_CHATDESK}, y=300)
    ifocr = IF("IF Local OCR?", 1720,
               "={{ ((() => { try { return $('Get OCR Engine').first().json.value; } catch(e) { return 'gemini'; } })() === 'easyocr') }}", y=300)
    local_ocr = HTTP("EasyOCR Local", 1920, "POST", OCR_GW + "/ocr-file",
                     "={\"file_b64\": {{ $('Build Gemini OCR').first().json._data.toJsonString() }}, "
                     "\"mime\": {{ $('Build Gemini OCR').first().json._mime.toJsonString() }}, "
                     "\"kind\": {{ $('Build Gemini OCR').first().json.kind.toJsonString() }}}",
                     y=300, timeout=600000)
    shlocal = CODE("Shape Local OCR", 2120,
                    "const it = $input.first().json;\n"
                    "const flags = $('Build Gemini OCR').first().json;\n"
                    "const cap = (flags.kind === 'image' && flags.text) ? flags.text.toString().trim() : '';\n"
                    "let t = cap ? (cap + '\\n\\n') : '';\n"
                    "try { t += (it.text || '').toString(); } catch(e) {}\n"
                    "if (!t.trim()) throw new Error('OCR ว่างเปล่า');\n"
                    "return [{ json: { kind: flags.kind, group_id: flags.group_id, group_name: flags.group_name,\n"
                    "  title: flags.title, image_url: flags.image_url, text: t.slice(0, 60000) } }];", y=300)
    ocr_text = CODE("Set OCR Text", 1860,
                     "const it = $input.first().json;\n"
                     "const flags = $('Build Gemini OCR').first().json;\n"
                     "const cap = (flags.kind === 'image' && flags.text) ? flags.text.toString().trim() : '';\n"
                     "let t = cap ? (cap + '\\n\\n') : '';\n"
                     "try { t += it.candidates[0].content.parts.map(p => p.text || '').join('\\n'); } catch(e) {}\n"
                     "if (!t.trim()) throw new Error('OCR ว่างเปล่า');\n"
                     "return [{ json: { kind: flags.kind, group_id: flags.group_id, group_name: flags.group_name,\n"
                     "  title: flags.title, image_url: flags.image_url, text: t.slice(0, 60000) } }];", y=420)
    merge_note = "NO-MERGE: branches converge via direct edges (OR semantics); Merge-append would stall waiting for unfired branches"
    srcq = CODE("Build Source SQL", 2260,
                 "const j = $input.first().json;\n"
                 "const q = (s) => (s || '').toString().replace(/'/g, \"''\");\n"
                 "const gid = parseInt(j.group_id) || 0;\n"
                 "if (!gid) throw new Error('missing group_id');\n"
                 "const img = (j.image_url || '').toString();\n"
                 "const ins = `INSERT INTO rag_sources (group_id, source_type, title, source_ref, image_url) VALUES (${gid}, '${q(j.kind) || 'text'}', '${q((j.title || '').slice(0, 255))}', 'webhook', ${img ? `'${q(img.slice(0, 2000))}'` : 'NULL'}) RETURNING id`;\n"
                 "const sql = `WITH gk AS (SELECT COALESCE((SELECT value FROM app_settings WHERE key = 'gemini.api_key'), '" + GEMINI_KEY + "') AS gkey), ins AS (${ins}) SELECT (SELECT id FROM ins) AS id, (SELECT gkey FROM gk) AS gkey`;\n"
                 "return [{ json: { sql: sql } }];")
    src = PGQ("Save Source Row", 2360, "={{ $json.sql }}", {"postgres": PG_CHATDESK})
    chunk = CODE("Chunk + Attach Meta", 2460,
                 "const src = $input.first().json;\n"
                 "const srcId = src.id || null;\n"
                 "const gkey = (src.gkey || '').toString();\n"
                 "// text/flags come from whichever branch fired (direct edges = OR semantics)\n"
                 "let m = null;\n"
                 "for (const nm of ['Set URL Text', 'Set OCR Text', 'Shape Local OCR']) {\n"
                 "  try { const c = $(nm).first().json; if (c && c.text) { m = c; break; } } catch(e) {}\n"
                 "}\n"
                 "if (!m) { m = $('Route + Flags').first().json; }\n"
                 "const text = (m.text || '').toString();\n"
                 "if (!text.trim()) throw new Error('ไม่มีข้อความให้ embedding');\n"
                 "const SIZE = 1000, OVER = 200;\n"
                 "const chunks = text.length <= SIZE ? [text] : [];\n"
                 "if (!chunks.length) { let s = 0; while (s < text.length) { chunks.push(text.slice(s, s + SIZE)); s += SIZE - OVER; } }\n"
                 "const meta = { source_id: srcId, group_id: m.group_id, group_name: m.group_name, title: m.title,\n"
                 "  image_url: m.image_url || null, source_type: m.kind };\n"
                 "return chunks.map((c, i) => ({ json: { text: c, gkey: gkey, metadata: { ...meta, chunk_no: i } } }));")
    vec = None  # NOTE: ไม่ใช้ PGVector insert node (ต้องการ metadata/source_id เต็ม + deterministic) — ใช้ HTTP embed + SQL insert แทน
    emb = HTTP("Embed Chunk (Gemini 768)", 2660,
               "POST", "={{ 'https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key=' + $json.gkey }}",
               "={\"content\": {\"parts\": [{\"text\": {{ $json.text.toJsonString() }} }]}, \"taskType\": \"RETRIEVAL_DOCUMENT\", \"outputDimensionality\": 768}",
               timeout=60000)
    mg2 = CODE("Join Emb+Chunk", 2660,
               "const chunks = ($('Chunk + Attach Meta').all() || []).map(r => r.json);\n"
               "const embs = ($('Embed Chunk (Gemini 768)').all() || []).map(r => r.json);\n"
               "if (!chunks.length || chunks.length !== embs.length) throw new Error('chunk/embed mismatch');\n"
               "return chunks.map((c, i) => ({ json: { ...c, embedding: embs[i].embedding } }));",
               y=480)
    buildsql = CODE("Build Insert SQL", 2860,
                    "const q = (s) => (s || '').toString().replace(/'/g, \"''\");\n"
                    "const mk = (m) => {\n"
                    "  if (!m.embedding || !m.embedding.values) throw new Error('embed ล้มเหลว');\n"
                    "  const meta = { source_id: (m.metadata||{}).source_id ?? null, group_id: (m.metadata||{}).group_id,\n"
                    "    group_name: (m.metadata||{}).group_name || '', title: (m.metadata||{}).title || '',\n"
                    "    image_url: (m.metadata||{}).image_url || null, source_type: (m.metadata||{}).source_type || '',\n"
                    "    chunk_no: (m.metadata||{}).chunk_no ?? 0 };\n"
                    "  const vec = '[' + m.embedding.values.join(',') + ']';\n"
                    "  const sql = `INSERT INTO rag_chunks (source_id, group_id, chunk_no, content, embedding, metadata) VALUES (${meta.source_id ?? 'NULL'}, ${meta.group_id}, ${meta.chunk_no}, '${q(m.text)}', '${vec}'::vector, '${q(JSON.stringify(meta))}'::jsonb)`;\n"
                    "  return { json: { sql: sql } };\n"
                    "};\n"
                    "return $input.all().map(r => mk(r.json));")
    pgins = PGQ("Insert Chunk", 3060, "={{ $json.sql }}", {"postgres": PG_CHATDESK})
    done = CODE("Result", 2860,
                "return [{ json: { ok: true, message: 'นำเข้า + Embedding สำเร็จ', chunks: $('Build Insert SQL').all().length } }];")
    resp = N("Respond", "n8n-nodes-base.respondToWebhook", 3060,
             {"respondWith": "json", "responseBody": "={{ $json }}", "options": {}})
    resp["typeVersion"] = 1.5

    nodes = [wh, route, if_url, fetch, set_url, if_file, if_img, dl_img, reattach,
             gem_prep, getocr, ifocr, getkey, gem_ocr, local_ocr, shlocal, ocr_text, srcq, src, chunk, emb, mg2, buildsql, pgins, done, resp]
    cons = {}
    E(cons, wh, route)
    E2(cons, if_url, fetch, if_file)
    E(cons, fetch, set_url)
    E(cons, set_url, srcq)
    E2(cons, if_file, gem_prep, if_img)
    E2(cons, if_img, dl_img, srcq)
    E(cons, dl_img, reattach)
    E(cons, reattach, gem_prep)
    E(cons, gem_prep, getocr)
    E(cons, getocr, ifocr)
    cons[ifocr["name"]] = {"main": [[{"node": local_ocr["name"], "type": "main", "index": 0}],
                                    [{"node": getkey["name"], "type": "main", "index": 0}]]}
    E(cons, getkey, gem_ocr)
    E(cons, local_ocr, shlocal)
    E(cons, shlocal, srcq)
    E(cons, gem_ocr, ocr_text)
    E(cons, ocr_text, srcq)
    E(cons, srcq, src)
    E(cons, src, chunk)
    E(cons, chunk, emb)
    E(cons, emb, mg2)
    E(cons, emb, mg2)
    cons[mg2["name"]] = {"main": [[{"node": buildsql["name"], "type": "main", "index": 0}]]}
    E(cons, buildsql, pgins)
    E(cons, pgins, done)
    E(cons, done, resp)
    # route -> if_url edge:
    cons[route["name"]] = {"main": [[{"node": if_url["name"], "type": "main", "index": 0}]]}
    return {"name": "ChatDesk RAG-03 Ingest (Gemini embed 768 + OCR)", "nodes": nodes,
            "connections": cons, "settings": {"executionOrder": "v1"}, "pinData": {}}


AGENT_SYS = """You are the knowledge assistant of TripThai/ChatDesk (Thai hotel & org QA).
STRICT RULES:
1) Answer ONLY from the provided <context>. Reply in Thai, concise (2-5 sentences for chat).
2) If the context has nothing relevant, say exactly: "ไม่พบข้อมูลนี้ในฐานความรู้ กรุณาติดต่อเจ้าหน้าที่ค่ะ" — never invent prices, policies, dates, names or contacts.
3) Never hallucinate numbers. Quote exactly as in context.
4) IMAGES: context rows may include [image: URL]. When the user asks to see a picture AND a row has one, mention it briefly; put each URL on its own line verbatim (raw URL only) so the UI can render it.
5) Cite the source group/title briefly when useful."""


def build_answer():
    wh = WH("Webhook Answer", "rag-answer", 200)
    prep = CODE("Prep", 420,
                "const b = $input.first().json.body || $input.first().json || {};\n"
                "const topk = Math.max(1, Math.min(10, parseInt(b.top_k) || 4));\n"
                "return [{ json: { question: (b.question || '').toString().slice(0, 2000),\n"
                "  group_id: b.group_id ? parseInt(b.group_id) : null,\n"
                "  session_id: (b.session_id || 'web-' + Date.now()).toString(), top_k: topk } }];")
    embed = HTTP("Embed Query (Gemini 768)", 640,
                 "POST", "={{ 'https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key=' + $('Get Gemini Key').first().json.value }}",
                 "={\"content\": {\"parts\": [{\"text\": {{ $('Prep').first().json.question.toJsonString() }} }]}, \"taskType\": \"RETRIEVAL_QUERY\", \"outputDimensionality\": 768}",
                 timeout=60000)
    getkey2 = PGQ("Get Gemini Key", 520,
                  "SELECT COALESCE((SELECT value FROM app_settings WHERE key = 'gemini.api_key'), '" + GEMINI_KEY + "') AS value",
                  {"postgres": PG_CHATDESK})
    attach = CODE("Attach Params", 830,
                   "const p = $('Prep').first().json;\n"
                   "const e = $input.first().json;\n"
                   "if (!e.embedding || !e.embedding.values) throw new Error('embed ล้มเหลว');\n"
                   "const vec = '[' + e.embedding.values.map(v => Number(v).toFixed(8)).join(',') + ']';\n"
                   "const gid = (p.group_id === null || p.group_id === undefined) ? null : parseInt(p.group_id);\n"
                   "const topk = Math.max(1, Math.min(10, parseInt(p.top_k) || 4));\n"
                   "const where = (gid === null) ? '' : ` AND (c.metadata->>'group_id')::int = ${gid}`;\n"
                   "const sql = `SELECT c.content, c.metadata, 1 - (c.embedding <=> '${vec}'::vector) AS sim FROM rag_chunks c WHERE 1=1${where} ORDER BY c.embedding <=> '${vec}'::vector LIMIT ${topk}`;\n"
                   "return [{ json: { ...p, embedding: e.embedding, sql: sql } }];")
    search = PGQ("Vector Search (group-safe)", 1020,
                 "={{ $json.sql }}",
                 {"postgres": PG_CHATDESK})
    rel = PGQ("Relational Context", 1020,
              "SELECT g.name, COUNT(c.id) AS chunks FROM rag_groups g LEFT JOIN rag_chunks c ON (c.metadata->>'group_id')::int = g.id GROUP BY g.name ORDER BY g.id",
              {"postgres": PG_CHATDESK}, y=480)
    merge = N("Merge Results", "n8n-nodes-base.merge", 1220, {"mode": "append"}, y=390)
    merge["typeVersion"] = 3.1
    prompt = CODE("Build Prompt", 1420,
                  "const items = $input.all().map(r => r.json);\n"
                  "const rows = items.filter(r => r.content !== undefined);\n"
                  "const rel = items.filter(r => r.name !== undefined);\n"
                  "const pre = $('Attach Params').first().json;\n"
                  "const ctx = rows.map((r, i) => `[${i + 1}] (group=${(r.metadata||{}).group_name||''}, src=${(r.metadata||{}).title||''}, sim=${Number(r.sim||0).toFixed(3)})\\n${r.content}${(r.metadata||{}).image_url ? '\\n[image: ' + r.metadata.image_url + ']' : ''}`).join('\\n\\n');\n"
                  "const relTxt = 'groups: ' + rel.map(r => r.name + '(' + r.chunks + ')').join(', ');\n"
                  "return [{ json: { question: pre.question || '', session_id: pre.session_id || '', context: ctx, rel: relTxt } }];")
    agent = {"id": nid(), "name": "RAG Agent (Gemini)", "type": "@n8n/n8n-nodes-langchain.agent",
             "typeVersion": 3.1, "position": [1640, 300],
             "parameters": {
                 "options": {"maxIterations": 3, "systemMessage": AGENT_SYS},
                 "promptType": "define",
                 "text": "=คำถาม: {{ $('Build Prompt').first().json.question }}\n\n<context>\n{{ $('Build Prompt').first().json.context }}\n</context>\n\nข้อมูลเสริม(relational): {{ $('Build Prompt').first().json.rel }}\n\nตอบตามกติกาด้านบนเป็นภาษาไทย"}}
    llm = {"id": nid(), "name": "Gemini 2.5 Flash", "type": "@n8n/n8n-nodes-langchain.lmChatGoogleGemini",
           "typeVersion": 1, "position": [1640, 560],
           "credentials": {"googlePalmApi": GEMINI},
           "parameters": {"modelName": "models/gemini-2.5-flash", "options": {"temperature": 0.2}}}
    mem = {"id": nid(), "name": "Session Memory", "type": "@n8n/n8n-nodes-langchain.memoryPostgresChat",
           "typeVersion": 1.4, "position": [1820, 560],
           "credentials": {"postgres": PG_RAGDB},
             "parameters": {"options": {}, "sessionIdType": "customKey", "sessionKey": "={{ $('Build Prompt').first().json.session_id || 'default-web' }}", "tableName": "n8n_chat_histories"}}
    guard = CODE("Guard Empty", 2020,
                 "const out = (($input.first().json.output ?? '').toString()).trim();\n"
                 "if (!out) { return [{ json: { output: 'ขออภัย ระบบขัดข้องชั่วคราว กรุณาถามใหม่อีกครั้งค่ะ' } }]; }\n"
                 "return $input.all();")
    getqa = PGQ("Get QA Model", 1560,
                "SELECT COALESCE((SELECT value FROM app_settings WHERE key = 'llm.qa'), (SELECT value FROM app_settings WHERE key = 'voice.llm_model'), 'gemini') AS v",
                {"postgres": PG_CHATDESK}, y=160)
    iflocal = IF("IF Use Local LLM?", 1780,
                 "={{ ((() => { try { return $('Get QA Model').first().json.v; } catch(e) { return 'gemini'; } })() === 'qwen3:4b') }}", y=160)
    buildol = CODE("Build Ollama RAG", 2000,
                    "const b = $('Build Prompt').first().json;\n"
                    "let hist = [];\n"
                    "try { const h = $('Read Mem History').first().json.history; hist = Array.isArray(h) ? h.slice().reverse() : []; } catch(e) { hist = []; }\n"
                    "const hlines = hist.filter(m => m && (m.content || '').toString().trim()).slice(-10).map(m => ((m.type === 'ai' ? 'บอท: ' : 'ผู้ใช้: ') + (m.content || '').toString().trim().slice(0, 400)));\n"
                    "const hblock = hlines.length ? ('\\n\\nประวัติการสนทนาก่อนหน้า:\\n' + hlines.join('\\n')) : '';\n"
                    "const content = 'คำถาม: ' + (b.question || '') + hblock + '\\n\\n<context>\\n' + (b.context || '') + '\\n</context>\\n\\nข้อมูลเสริม(relational): ' + (b.rel || '') + '\\n\\nตอบตามกติกาด้านบนเป็นภาษาไทย (ใช้ประวัติประกอบเมื่อคำถามอ้างถึงเรื่องก่อนหน้า)';\n"
                    "return [{ json: { system: " + json.dumps(AGENT_SYS, ensure_ascii=False) + ", messages: [{ role: 'user', content: content }] } }];", y=160)
    memreadcode = CODE("Build Mem Read", 1890,
                    "const b = $('Build Prompt').first().json;\n"
                    "let sid = (b.session_id || '').toString();\n"
                    "if (!/^[A-Za-z0-9:_-]{1,128}$/.test(sid)) sid = 'web-default';\n"
                    "const q = (s) => s.replace(/'/g, \"''\");\n"
                    "return [{ json: { sql: `SELECT COALESCE((SELECT json_agg(message ORDER BY id DESC) FROM (SELECT message, id FROM n8n_chat_histories WHERE session_id = '${q(sid)}' ORDER BY id DESC LIMIT 10) t), '[]'::json) AS history` } }];", y=40)
    runmemread = PGQ("Read Mem History", 1945, "={{ $json.sql }}", {"postgres": PG_RAGDB}, y=40)
    memsavecode = CODE("Build Mem Save", 2550,
                    "const a = $input.first().json;\n"
                    "const b = $('Build Prompt').first().json;\n"
                    "let sid = (b.session_id || '').toString();\n"
                    "if (!/^[A-Za-z0-9:_-]{1,128}$/.test(sid)) sid = 'web-default';\n"
                    "const q = (s) => (s || '').toString().replace(/'/g, \"''\");\n"
                    "const hq = (b.question || '').toString().slice(0, 2000);\n"
                    "const an = ((a.output || '').toString()).slice(0, 2000);\n"
                    "const hj = JSON.stringify({ type: 'human', content: hq });\n"
                    "const aj = JSON.stringify({ type: 'ai', content: an });\n"
                    "const sql = `WITH ins AS (INSERT INTO n8n_chat_histories (session_id, message) VALUES ('${q(sid)}', '${q(hj)}'::jsonb), ('${q(sid)}', '${q(aj)}'::jsonb) RETURNING id), del AS (DELETE FROM n8n_chat_histories WHERE session_id = '${q(sid)}' AND id NOT IN (SELECT id FROM n8n_chat_histories WHERE session_id = '${q(sid)}' ORDER BY id DESC LIMIT 60) RETURNING 1) SELECT (SELECT COUNT(*) FROM ins) AS saved, (SELECT COUNT(*) FROM del) AS pruned`;\n"
                    "return [{ json: { sql: sql } }];", y=40)
    memsaverun = PGQ("Save Mem Turn", 2660, "={{ $json.sql }}", {"postgres": PG_RAGDB}, y=40)
    passanswer = CODE("Pass Answer", 2770,
                    "const t = $('Shape Ollama RAG').first().json;\n"
                    "return [{ json: { output: (t.output || '').toString() } }];", y=40)
    oll = HTTP("Ollama RAG", 2220,
               "POST", OLLAMA_HOST + "/api/chat",
               "={\"model\": \"qwen3:4b-instruct\", \"stream\": false, "
               "\"options\": {\"temperature\": 0.2, \"num_predict\": 512}, "
               "\"system\": {{ $json.system.toJsonString() }}, "
               "\"messages\": {{ $json.messages.toJsonString() }}}",
               y=160, timeout=120000)
    shol = CODE("Shape Ollama RAG", 2440,
                "const it = $input.first().json;\n"
                "let t = '';\n"
                "try { t = ((it.message || {}).content || '').toString(); } catch(e) {}\n"
                "t = t.replace(/^[\\s\\S]*?<\\/think>/, '').replace(/<think>[\\s\\S]*?<\\/think>/g, '').trim();\n"
                "if (!t) throw new Error('Local LLM ไม่ตอบ');\n"
                "return [{ json: { output: t.slice(0, 2000) } }];", y=160)
    shape = CODE("Shape Reply", 2220,
                 "const a = $input.first().json;\n"
                 "const rows = ($('Vector Search (group-safe)').all() || []).map(r => r.json);\n"
                 "return [{ json: { ok: true, text: (a.output || '').toString(),\n"
                 "  images: rows.filter(r => r.metadata && r.metadata.image_url).map(r => r.metadata.image_url).slice(0, 5),\n"
                 "  sources: rows.map(r => ((r.metadata||{}).group_name||'') + '/' + ((r.metadata||{}).title||'')).filter(s => s !== '/').slice(0, 8) } }];")
    resp = N("Respond", "n8n-nodes-base.respondToWebhook", 2420,
             {"respondWith": "json", "responseBody": "={{ $json }}", "options": {}})
    resp["typeVersion"] = 1.5
    mfinal = N("Merge Final", "n8n-nodes-base.merge", 2120, {"mode": "append"}, y=390)
    mfinal["typeVersion"] = 3.1

    nodes = [wh, prep, getkey2, embed, attach, search, rel, merge, prompt, getqa, iflocal,
             memreadcode, runmemread, buildol, oll, shol, memsavecode, memsaverun, passanswer, agent, llm, mem, guard, shape, resp]
    cons = {}
    E(cons, wh, prep)
    cons[prep["name"]] = {"main": [[{"node": getkey2["name"], "type": "main", "index": 0}], [{"node": rel["name"], "type": "main", "index": 0}]]}
    E(cons, getkey2, embed)
    E(cons, embed, attach)
    E(cons, attach, search)
    E(cons, search, merge)
    # rel -> merge second input:
    cons[rel["name"]] = {"main": [[{"node": merge["name"], "type": "main", "index": 1}]]}
    E(cons, merge, prompt)
    E(cons, prompt, getqa)
    E(cons, getqa, iflocal)
    cons[iflocal["name"]] = {"main": [[{"node": memreadcode["name"], "type": "main", "index": 0}],
                                      [{"node": agent["name"], "type": "main", "index": 0}]]}
    E(cons, memreadcode, runmemread)
    E(cons, runmemread, buildol)
    E(cons, buildol, oll)
    E(cons, oll, shol)
    E(cons, shol, memsavecode)
    E(cons, memsavecode, memsaverun)
    E(cons, memsaverun, passanswer)
    E(cons, passanswer, guard)
    cons[llm["name"]] = {"ai_languageModel": [[{"node": agent["name"], "type": "ai_languageModel", "index": 0}]]}
    cons[mem["name"]] = {"ai_memory": [[{"node": agent["name"], "type": "ai_memory", "index": 0}]]}
    E(cons, agent, guard)
    E(cons, guard, shape)
    E(cons, shape, resp)
    return {"name": "ChatDesk RAG-04 Answer (Gemini + PGVector + Postgres)", "nodes": nodes,
            "connections": cons, "settings": {"executionOrder": "v1"}, "pinData": {}}


if __name__ == "__main__":
    out = r"C:\Users\pol\Desktop\OpenCode Project\ChatDesk\local\n8n"
    for name, wf in [("rag-03-ingest.json", build_ingest()), ("rag-04-answer.json", build_answer())]:
        p = os.path.join(out, name)
        json.dump(wf, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("wrote", p, len(json.dumps(wf)), "bytes")
