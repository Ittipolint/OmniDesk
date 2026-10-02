"""Generate ChatDesk API-engine workflows (ai-chat, stt, tts, chatdesk-send)."""
import json
import os
import uuid

PG_CHATDESK = {"id": "iGiNCBmmhZ9xgFn8", "name": "ChatDesk Postgres (chatdesk)"}
GEMINI = {"id": "VuE8YX5cbPUw7Ay8", "name": "Google Gemini(PaLM) Api account"}
GEMINI_KEY = "__GEMINI_API_KEY__"
CRED_ID = "VuE8YX5cbPUw7Ay8"
CRED_NAME = "Google Gemini(PaLM) Api account"
CRED_HOST = "https://generativelanguage.googleapis.com"
GEM_KEY_SQL = "SELECT COALESCE((SELECT value FROM app_settings WHERE key = 'gemini.api_key'), '" + GEMINI_KEY + "') AS value"
N8N_SELF = "http://host.docker.internal:5678"
OLLAMA_HOST = "http://host.docker.internal:11434"
VOICE_MODELS = ["gemini", "qwen3:4b"]

GEM_SYS = ("คุณคือผู้ช่วยจองที่พักของเว็บ TripThai พูดภาษาไทยสุภาพเป็นกันเอง "
           "ตอบสั้นกระชับเหมาะกับการฟังออกเสียง (ไม่เกิน 3-4 ประโยค) ห้ามใช้ markdown ตาราง โค้ด หรืออีโมจิ "
           "ข้อมูลเว็บ: โค้ด TRIPTHAI100 ลด 100 บาท, ที่พักเริ่ม 1,400 บาท/คืน, หลายรายการยกเลิกฟรี, "
           "จังหวัดยอดนิยม: กรุงเทพฯ เชียงใหม่ ภูเก็ต พัทยา กระบี่ หัวหิน เกาะสมุย เชียงราย "
           "ถ้าถูกถามเรื่องที่ไม่มีข้อมูล ให้บอกว่าจะส่งต่อให้เจ้าหน้าที่ช่วยเหลือ")


def nid():
    return str(uuid.uuid4())


def N(name, ntype, x, params=None, creds=None, y=300, tv=2):
    n = {"id": nid(), "name": name, "type": ntype, "typeVersion": tv,
         "position": [x, y], "parameters": params or {}}
    if creds:
        n["credentials"] = creds
    return n


def WH(name, path, x, mode="responseNode"):
    n = N(name, "n8n-nodes-base.webhook", x,
          {"httpMethod": "POST", "path": path, "responseMode": mode, "options": {}})
    n["typeVersion"] = 2.1
    n["webhookId"] = str(uuid.uuid4())
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


def IFB(name, x, left, y=300):
    n = N(name, "n8n-nodes-base.if", x, {
        "conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose"},
                       "conditions": [{"id": nid(), "leftValue": left,
                                       "rightValue": True, "operator": {"type": "boolean", "operation": "true"}}],
                       "combinator": "and"}, "options": {}}, y=y)
    n["typeVersion"] = 2.2
    return n


def RESP(name, x):
    n = N(name, "n8n-nodes-base.respondToWebhook", x,
          {"respondWith": "json", "responseBody": "={{ $json }}", "options": {}})
    n["typeVersion"] = 1.5
    return n


def E(cons, a, b):
    cons.setdefault(a["name"], {}).setdefault("main", []).append(
        [{"node": b["name"], "type": "main", "index": 0}])
    return cons


def E2(cons, a, b_true, b_false):
    cons[a["name"]] = {"main": [
        [{"node": b_true["name"], "type": "main", "index": 0}],
        [{"node": b_false["name"], "type": "main", "index": 0}]]}
    return cons


# ================= API-01 AI CHAT (unified brain) =================
def build_aichat():
    wh = WH("Webhook AI Chat", "api-ai-chat", 200)
    prep = CODE("Prep", 420,
                "const b = $input.first().json.body || $input.first().json || {};\n"
                "const hist = Array.isArray(b.history) ? b.history.filter(h => h && h.text).slice(-10) : [];\n"
                "return [{ json: { text: (b.text || '').toString().slice(0, 2000),\n"
                "  userId: (b.userId || '').toString(),\n"
                "  group_id: b.group_id ? parseInt(b.group_id) : null,\n"
                "  session_id: (b.session_id || 'ai-' + Date.now()).toString(),\n"
                "  history: hist } }];")
    getvoice = PGQ("Get Voice Model", 520, "SELECT COALESCE((SELECT value FROM app_settings WHERE key = 'llm.qa'), (SELECT value FROM app_settings WHERE key = 'voice.llm_model'), 'gemini') AS value", {"postgres": PG_CHATDESK})
    getpersona = CODE("Get Persona", 580,
                "const g = $('Prep').first().json;\n"
                "const gid = g.group_id ? parseInt(g.group_id) || 0 : 0;\n"
                "return [{ json: { gid: gid, sql: `SELECT COALESCE((SELECT persona_system FROM rag_groups WHERE id = ${gid}), '') AS persona` } }];")
    runpersona = PGQ("Run Persona", 580, "={{ $json.sql }}", {"postgres": PG_CHATDESK}, y=480)
    ragcall = HTTP("RAG Lookup", 640,
                   "POST", N8N_SELF + "/webhook/rag-answer",
                   "={\"question\": {{ $('Prep').first().json.text.toJsonString() }}, \"top_k\": 4, "
                   "\"group_id\": {{ $('Prep').first().json.group_id === null ? 'null' : $('Prep').first().json.group_id }}, "
                   "\"session_id\": {{ $('Prep').first().json.session_id.toJsonString() }}}")
    # onError continue -> empty rag
    ragcall["onError"] = "continueRegularOutput"
    ragcall["retryOnFail"] = False
    pick = CODE("Pick RAG or Gemini", 860,
                "const orig = $('Prep').first().json;\n"
                "const r = $input.first().json;\n"
                "const FALLBACK = 'ไม่พบข้อมูลนี้ในฐานความรู้';\n"
                "const use_rag = !!(r && r.ok && r.text && r.text.indexOf(FALLBACK) < 0 && (r.sources || []).length);\n"
                "return [{ json: { ...orig, use_rag: use_rag,\n"
                "  rag_text: use_rag ? r.text : '', rag_images: use_rag ? (r.images || []) : [],\n"
                "  rag_sources: use_rag ? (r.sources || []) : [] } }];")
    ifuse = IFB("IF Use RAG?", 1080, "={{ $json.use_rag }}")
    shape_rag = CODE("Shape RAG", 1300,
                     "const j = $input.first().json;\n"
                     "return [{ json: { ok: true, text: j.rag_text, images: j.rag_images || [],\n"
                     "  sources: j.rag_sources || [], via: 'rag' } }];", y=200)
    buildbody = CODE("Build Gemini Body", 1300,
                     "const j = $input.first().json;\n"
                     "const GEM = " + json.dumps(GEM_SYS, ensure_ascii=False) + ";\n"
                     "const sys = (() => { try { const p = ($('Run Persona').first().json.persona || '').trim(); return p ? p : GEM; } catch(e) { return GEM; } })();\n"
                     "const contents = [];\n"
                     "(j.history || []).forEach(h => {\n"
                     "  const t = (h.text || '').toString().trim().slice(0, 1000);\n"
                     "  if (!t) return;\n"
                     "  contents.push({ role: h.role === 'model' ? 'model' : 'user', parts: [{ text: t }] });\n"
                     "});\n"
                     "while (contents.length && contents[0].role !== 'user') contents.shift();\n"
                     "contents.push({ role: 'user', parts: [{ text: j.text }] });\n"
                     "return [{ json: { body: { system_instruction: { parts: [{ text: sys }] }, contents: contents,\n"
                     "  generationConfig: { maxOutputTokens: 1024, temperature: 0.7 } } } }];", y=420)
    gemini = HTTP("Gemini Direct", 1520,
                  "POST", "={{ 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=' + $('Get Gemini Key').first().json.value }}",
                  "={{ $('Build Gemini Body').first().json.body }}",
                  y=420, timeout=90000)
    getkey = PGQ("Get Gemini Key", 1410, GEM_KEY_SQL, {"postgres": PG_CHATDESK}, y=420)
    shape_gem = CODE("Shape Gemini", 1740,
                     "const it = $input.first().json;\n"
                     "let t = '';\n"
                     "try { t = it.candidates[0].content.parts.map(p => p.text || '').join(''); } catch(e) {}\n"
                     "t = t.trim();\n"
                     "if (!t) throw new Error('Gemini ไม่ตอบ');\n"
                     "return [{ json: { ok: true, text: t.slice(0, 2000), images: [], sources: [], via: 'gemini' } }];", y=420)
    iflocal = IFB("IF Use Local LLM?", 1300, "={{ ((() => { try { return $('Get Voice Model').first().json.value; } catch(e) { return 'gemini'; } })() === 'qwen3:4b') }}", y=420)
    buildol = CODE("Build Ollama Body", 1520,
                   "const j = $input.first().json;\n"
                   "const GEM = " + json.dumps(GEM_SYS, ensure_ascii=False) + ";\n"
                   "const per = (() => { try { const p = ($('Run Persona').first().json.persona || '').trim(); return p ? p : GEM; } catch(e) { return GEM; } })();\n"
                   "const msgs = [];\n"
                   "(j.history || []).forEach(h => {\n"
                   "  const t = (h.text || '').toString().trim().slice(0, 1000);\n"
                   "  if (!t) return;\n"
                   "  msgs.push({ role: h.role === 'model' ? 'assistant' : 'user', content: t });\n"
                   "});\n"
                   "while (msgs.length && msgs[0].role !== 'user') msgs.shift();\n"
                   "msgs.push({ role: 'user', content: j.text });\n"
                   "return [{ json: { messages: msgs, system: per + ' /no_think' } }];", y=560)
    ollama = HTTP("Ollama Local", 1740,
                  "POST", OLLAMA_HOST + "/api/chat",
                  "={\"model\": \"qwen3:4b-instruct\", \"stream\": false, "
                  "\"options\": {\"temperature\": 0.7, \"num_predict\": 512}, "
                  "\"system\": {{ $json.system.toJsonString() }}, "
                  "\"messages\": {{ $json.messages.toJsonString() }}}",
                  y=560, timeout=120000)
    shape_ol = CODE("Shape Ollama", 1960,
                    "const it = $input.first().json;\n"
                    "let t = '';\n"
                    "try { t = ((it.message || {}).content || '').toString(); } catch(e) {}\n"
                    "t = t.replace(/^[\\s\\S]*?<\\/think>/, '').replace(/<think>[\\s\\S]*?<\\/think>/g, '').trim();\n"
                    "if (!t) throw new Error('Local LLM ไม่ตอบ');\n"
                    "return [{ json: { ok: true, text: t.slice(0, 2000), images: [], sources: [], via: 'qwen3:4b' } }];", y=560)
    resp = RESP("Respond", 2180)
    nodes = [wh, prep, getvoice, getpersona, runpersona, ragcall, pick, ifuse, shape_rag, iflocal,
             buildbody, getkey, gemini, shape_gem, buildol, ollama, shape_ol, resp]
    cons = {}
    E(cons, wh, prep)
    E(cons, prep, getvoice)
    E(cons, getvoice, getpersona)
    E(cons, getpersona, runpersona)
    E(cons, runpersona, ragcall)
    E(cons, ragcall, pick)
    # NOTE: pick outputs use_rag flag; IF routes. ifuse true->shape_rag, false->iflocal
    # fix: pick->ifuse edge, ifuse branches:
    cons[ifuse["name"]] = {"main": [[{"node": shape_rag["name"], "type": "main", "index": 0}],
                                    [{"node": iflocal["name"], "type": "main", "index": 0}]]}
    E(cons, shape_rag, resp)
    E2(cons, iflocal, buildol, buildbody)
    E(cons, buildol, ollama)
    E(cons, ollama, shape_ol)
    E(cons, shape_ol, resp)
    E(cons, buildbody, getkey)
    E(cons, getkey, gemini)
    E(cons, gemini, shape_gem)
    E(cons, shape_gem, resp)
    # remove wrong pick edges (E2 created pick->[ifuse,buildbody] but we want pick->ifuse only):
    cons[pick["name"]] = {"main": [[{"node": ifuse["name"], "type": "main", "index": 0}]]}
    return {"name": "ChatDesk API-01 AI Chat (unified brain)", "nodes": nodes,
            "connections": cons, "settings": {"executionOrder": "v1"}, "pinData": {}}


VOICE_GW = "http://host.docker.internal:8080"  # triptthai-gateway (whisper :9000, voiceapi :8001 via Caddy)


# ================= API-02 STT (mic -> whisper) =================
def build_stt():
    wh = WH("Webhook STT", "api-stt", 200)
    valid = CODE("Validate", 420,
                 "const inp = $input.first();\n"
                 "const b = inp.json.body || inp.json || {};\n"
                 "const bin = inp.binary || {};\n"
                 "const f = bin.audio || bin.file || bin.data || Object.values(bin)[0];\n"
                 "const userId = (b.userId || '').toString();\n"
                 "if (!/^WEB_[A-Za-z0-9_-]{1,64}$/.test(userId)) throw new Error('userId ไม่ถูกต้อง');\n"
                 "if (!f) throw new Error('ไม่พบไฟล์เสียง (field audio)');\n"
                 "// ส่ง binary object เดิมทั้งก้อน (ห้ามสร้างใหม่ — reference จะขาดแล้วได้ไฟล์ศูนย์)\n"
                 "return [{ json: { userId: userId }, binary: inp.binary }];")
    # NOTE: whisper gateway expects multipart field audio_file
    to_wh = N("Whisper ASR", "n8n-nodes-base.httpRequest", 640,
              {"method": "POST",
               "url": VOICE_GW + "/asr?task=transcribe&language=th&output=json&vad_filter=true",
               "sendBody": True, "contentType": "multipart-form-data",
               "bodyParameters": {"parameters": [{"parameterType": "formBinaryData",
                                                  "name": "audio_file", "inputDataFieldName": "audio"}]},
               # whisper ส่ง transcript กลับเป็น text/plain -> บังคับ parse JSON
               "options": {"timeout": 120000, "response": {"response": {"responseFormat": "json"}}}}, y=300)
    to_wh["typeVersion"] = 4.2
    to_wh["onError"] = "continueRegularOutput"
    to_wh["retryOnFail"] = False
    shape = CODE("Shape Transcript", 860,
                 "const j = $input.first().json;\n"
                 "const t = ((j && j.text) || '').toString().trim().slice(0, 2000);\n"
                 "if (!t) return [{ json: { ok: False, error: 'ไม่ได้ยินเสียงพูด (ลองพูดใกล้ไมค์และดังขึ้น)' } }];\n"
                 "return [{ json: { ok: True, text: t } }];".replace('False', 'false').replace('True', 'true'))
    resp = RESP("Respond", 1060)
    nodes = [wh, valid, to_wh, shape, resp]
    cons = {}
    E(cons, wh, valid)
    E(cons, valid, to_wh)
    E(cons, to_wh, shape)
    E(cons, shape, resp)
    return {"name": "ChatDesk API-02 STT (whisper)", "nodes": nodes,
            "connections": cons, "settings": {"executionOrder": "v1"}, "pinData": {}}


# ================= API-03 TTS (text -> piper wav base64) =================
def build_tts():
    wh = WH("Webhook TTS", "api-tts", 200)
    valid = CODE("Validate", 420,
                 "const b = $input.first().json.body || $input.first().json || {};\n"
                 "const userId = (b.userId || '').toString();\n"
                 "if (!/^WEB_[A-Za-z0-9_-]{1,64}$/.test(userId)) throw new Error('userId ไม่ถูกต้อง');\n"
                 "let text = (b.text || '').toString().trim().slice(0, 600);\n"
                 "if (!text) throw new Error('ข้อความว่างเปล่า');\n"
                 "let speed = parseFloat(b.speed);\n"
                 "if (!(speed >= 0.7 && speed <= 1.2)) speed = 0.9;\n"
                 "return [{ json: { text: text, speed: speed } }];")
    gettts = PGQ("Get TTS Engine", 520, "SELECT COALESCE((SELECT value FROM app_settings WHERE key = 'tts.engine'), 'auto') AS value", {"postgres": PG_CHATDESK}, y=160)
    synth = HTTP("Piper Synth", 640, "POST", VOICE_GW + "/tts",
                 "={\"text\": {{ $('Validate').first().json.text.toJsonString() }}, \"speed\": {{ $('Validate').first().json.speed }}}",
                 y=480, timeout=90000)
    neural = HTTP("Neural TTS", 640, "POST", VOICE_GW + "/tts-neural",
                 "={\"text\": {{ $('Validate').first().json.text.toJsonString() }}, \"speed\": {{ $('Validate').first().json.speed }}}",
                 y=160, timeout=90000)
    neural["onError"] = "continueRegularOutput"
    neural["retryOnFail"] = False
    picktts = CODE("Pick TTS", 860,
               "const pre = $('Validate').first().json;\n"
               "const mode = (() => { try { return $('Get TTS Engine').first().json.value || 'auto'; } catch(e) { return 'auto'; } })();\n"
               "if (mode === 'piper') {\n"
               "  return [{ json: { ok: false, engine: 'piper', text: pre.text, speed: pre.speed } }];\n"
               "}\n"
               "const bin = $input.first().binary || {};\n"
               "const f = bin.audio || bin.file || bin.data || Object.values(bin)[0];\n"
               "if (f) {\n"
               "  const key = Object.keys(bin).find(k => bin[k] === f) || 'data';\n"
               "  const buf = await this.helpers.getBinaryDataBuffer(0, key);\n"
               "  if (buf && buf.length && buf.length >= 1000) {\n"
               "    return [{ json: { ok: true, audio: buf.toString('base64'), mime: 'audio/wav', engine: 'neural' } }];\n"
               "  }\n"
               "}\n"
               "return [{ json: { ok: false, engine: 'piper', text: pre.text, speed: pre.speed, error: 'neural ล้มเหลว' } }];", y=160)
    ifpiper = IFB("IF Piper Fallback?", 1080, "={{ (($json.ok !== true && $('Get TTS Engine').first().json.value !== 'neural') || $('Get TTS Engine').first().json.value === 'piper') }}", y=160)
    b64 = CODE("To Base64", 860,
               "const bin = $input.first().binary || {};\n"
               "const f = bin.audio || bin.file || bin.data || Object.values(bin)[0];\n"
               "if (!f) return [{ json: { ok: false, error: 'TTS ไม่ตอบเป็นไฟล์เสียง' } }];\n"
               "const buf = await this.helpers.getBinaryDataBuffer(0, Object.keys(bin).find(k => bin[k] === f) || 'data');\n"
               "if (!buf || !buf.length || buf.length < 1000) return [{ json: { ok: false, error: 'ไฟล์เสียงว่างเปล่า' } }];\n"
               "return [{ json: { ok: true, audio: buf.toString('base64'), mime: 'audio/wav', engine: 'piper' } }];")
    resp = RESP("Respond", 1300)
    nodes = [wh, valid, gettts, neural, picktts, ifpiper, synth, b64, resp]
    cons = {}
    E(cons, wh, valid)
    E(cons, valid, gettts)
    E(cons, gettts, neural)
    E(cons, neural, picktts)
    E2(cons, ifpiper, synth, resp)
    cons[picktts["name"]] = {"main": [[{"node": ifpiper["name"], "type": "main", "index": 0}]]}
    # NOTE: picktts single output -> IF; IF true (neural failed) -> piper -> b64 -> resp; false -> resp
    E(cons, synth, b64)
    E(cons, b64, resp)
    return {"name": "ChatDesk API-03 TTS (neural+piper base64)", "nodes": nodes,
            "connections": cons, "settings": {"executionOrder": "v1"}, "pinData": {}}


# ================= API-04 CHATDESK SEND (agent reply central) =================
def build_send():
    wh = WH("Webhook Send", "chatdesk-send", 200)
    valid = CODE("Validate", 420,
                 "const b = $input.first().json.body || $input.first().json || {};\n"
                 "const convId = parseInt(b.conversationId) || 0;\n"
                 "if (!convId) throw new Error('missing conversationId');\n"
                 "const type = ['text','image','video','sticker'].includes(b.type) ? b.type : 'text';\n"
                 "const text = (b.text || '').toString().slice(0, 2000);\n"
                 "if (type === 'text' && !text.trim()) throw new Error('กรุณาพิมพ์ข้อความ');\n"
                 "if ((type === 'image' || type === 'video') && !(b.mediaUrl || '').toString().match(/^https?:\\/\\//i)) throw new Error('ไม่พบ URL ของไฟล์');\n"
                 "if (type === 'sticker' && (!(b.stickerPackage || '') || !(b.stickerId || ''))) throw new Error('ข้อมูลสติกเกอร์ไม่ครบ');\n"
                 "return [{ json: { conversationId: convId, type: type, text: text,\n"
                 "  mediaUrl: (b.mediaUrl || '').toString(), mediaPreviewUrl: (b.mediaPreviewUrl || '').toString(),\n"
                 "  stickerPackage: (b.stickerPackage || '').toString(), stickerId: (b.stickerId || '').toString() } }];")
    save = CODE("Build Mute SQL", 640,
                 "const j = $input.first().json;\n"
                 "return [{ json: { ...j, mute_sql: `UPDATE cd_conversations SET bot_enabled = 0 WHERE id = ${j.conversationId} AND bot_enabled = 1` } }];")
    mute = PGQ("Mute Bot", 860, "={{ $json.mute_sql }}", {"postgres": PG_CHATDESK})
    ins = CODE("Build Insert SQL", 1080,
               "const j = $('Build Mute SQL').first().json;\n"
               "const q = (s) => (s || '').toString().replace(/'/g, \"''\");\n"
               "const body = (j.text !== '' && j.text !== undefined) ? j.text : ('[' + j.type + ']');\n"
               "const sql = `INSERT INTO cd_messages (conversation_id, sender, content, message_type, media_url, media_preview_url, sticker_package, sticker_id, status, delivered_at, created_at) VALUES (${j.conversationId}, 'agent', '${q(body)}', '${j.type}', ${j.mediaUrl ? `'${q(j.mediaUrl.slice(0,500))}'` : 'NULL'}, ${j.mediaPreviewUrl ? `'${q(j.mediaPreviewUrl.slice(0,500))}'` : 'NULL'}, ${j.stickerPackage ? `'${q(j.stickerPackage.slice(0,50))}'` : 'NULL'}, ${j.stickerId ? `'${q(j.stickerId.slice(0,50))}'` : 'NULL'}, 'ok', NOW(), NOW()) RETURNING id`;\n"
               "return [{ json: { ...j, sql: sql } }];")
    pgins = PGQ("Insert Agent Msg", 1220, "={{ $json.sql }}", {"postgres": PG_CHATDESK})
    lookup = PGQ("Lookup Conversation", 1400,
                 "=SELECT id, channel, external_user_id AS \"userId\" FROM cd_conversations WHERE id = {{ $('Build Insert SQL').first().json.conversationId }} LIMIT 1",
                 {"postgres": PG_CHATDESK})
    reqconv = CODE("Require Conv", 1540,
                   "const rows = $input.all();\n"
                   "if (!rows.length) throw new Error('ไม่พบห้องแชทนี้');\n"
                   "return rows;")
    qtok = CODE("Q Channel Token", 1680,
                "const c = $('Lookup Conversation').first().json;\n"
                "const ch = (c.channel || 'line').toString().replace(/'/g, \"''\");\n"
                "return [{ json: { sql: `SELECT COALESCE((SELECT line_channel_token FROM channel_map WHERE channel_code = '${ch}'), '') AS line_channel_token` } }];")
    rtok = PGQ("Run Channel Token", 1680, "={{ $json.sql }}", {"postgres": PG_CHATDESK}, y=480)
    gate = IFB("IF LINE Channel?", 1300, "={{ /^line/.test(($('Lookup Conversation').first().json.channel || '')) }}")
    push = HTTP("Push via chatdesk-push", 1740, "POST", N8N_SELF + "/webhook/chatdesk-push",
                "={\"userId\": {{ $('Lookup Conversation').first().json.userId.toJsonString() }}, \"text\": {{ $('Validate').first().json.text.toJsonString() }}, "
                "\"type\": {{ $('Validate').first().json.type.toJsonString() }}, \"mediaUrl\": {{ $('Validate').first().json.mediaUrl.toJsonString() }}, "
                "\"mediaPreviewUrl\": {{ $('Validate').first().json.mediaPreviewUrl.toJsonString() }}, "
                "\"stickerPackage\": {{ $('Validate').first().json.stickerPackage.toJsonString() }}, \"stickerId\": {{ $('Validate').first().json.stickerId.toJsonString() }}, "
                "\"lineToken\": {{ $('Run Channel Token').first().json.line_channel_token.toJsonString() }}}",
                y=200, timeout=60000)
    push["onError"] = "continueRegularOutput"
    push["retryOnFail"] = False
    shape = CODE("Shape Result", 1960,
                 "const msg = $('Insert Agent Msg').first().json;\n"
                 "const conv = $('Lookup Conversation').first().json;\n"
                 "return [{ json: { ok: true, messageId: msg.id || 0, conversationId: conv.id || 0,\n"
                 "  botMuted: true, time: new Date().toISOString().slice(11, 16) } }];")
    resp = RESP("Respond", 1960)
    nodes = [wh, valid, save, mute, ins, pgins, lookup, reqconv, qtok, rtok, gate, push, shape, resp]
    cons = {}
    E(cons, wh, valid)
    E(cons, valid, save)
    E(cons, save, mute)
    E(cons, mute, ins)
    E(cons, ins, pgins)
    E(cons, pgins, lookup)
    E(cons, lookup, reqconv)
    E(cons, reqconv, qtok)
    E(cons, qtok, rtok)
    E2(cons, gate, push, shape)
    # gate input from rtok:
    cons[rtok["name"]] = {"main": [[{"node": gate["name"], "type": "main", "index": 0}]]}
    E(cons, push, shape)
    E(cons, shape, resp)
    return {"name": "ChatDesk API-04 Send (agent reply central)", "nodes": nodes,
            "connections": cons, "settings": {"executionOrder": "v1"}, "pinData": {}}


# ================= API-05 RECEIVE (chat send central: customer/bot) =================
    return {"name": "ChatDesk API-06 Read (inbox/thread/webthread)", "nodes": nodes,
            "connections": cons, "settings": {"executionOrder": "v1"}, "pinData": {}}


# ================= API-05 RECEIVE (chat send central: customer/bot) =================
def build_receive():
    wh = WH("Webhook Receive", "api-receive", 200)
    valid = CODE("Validate", 420,
                 "const b = $input.first().json.body || $input.first().json || {};\n"
                 "const userId = (b.userId || b.externalUserId || b.user_id || '').toString().trim();\n"
                 "if (!userId) throw new Error('ไม่พบ userId ของลูกค้า');\n"
                 "const keys = ['text', 'message', 'reply', 'content'];\n"
                 "let text = '';\n"
                 "for (const k of keys) {\n"
                 "  if (b[k] !== undefined && b[k] !== null && String(b[k]).trim() !== '') { text = String(b[k]).trim(); break; }\n"
                 "}\n"
                 "const type = ((b.messageType || b.message_type || 'text') + '').toLowerCase().replace(/[^a-z]/g, '') || 'text';\n"
                 "if (!text && type === 'text') throw new Error('ไม่พบข้อความ');\n"
                 "const q = (s) => (s === undefined || s === null) ? null : String(s);\n"
                 "const sq = (s) => q(s) === null ? null : q(s).replace(/'/g, \"''\");\n"
                 "const ch = (b.channel || 'line').toString();\n"
                 "const channel = /^[a-z0-9_]{2,32}$/.test(ch) ? ch : 'line';\n"
                 "const sn = (b.sender || 'customer').toString();\n"
                 "const sender = ['customer', 'bot', 'agent', 'system'].includes(sn) ? sn : 'customer';\n"
                 "const disp = b.displayName || b.display_name || null;\n"
                 "const pic = b.pictureUrl || b.picture_url || null;\n"
                 "const med = b.mediaUrl || b.media_url || null;\n"
                 "const prv = b.mediaPreviewUrl || b.media_preview_url || null;\n"
                 "const spk = b.stickerPackage || b.sticker_package || null;\n"
                 "const sti = b.stickerId || b.sticker_id || null;\n"
                 "const mid = b.messageId || b.externalMessageId || b.external_message_id || null;\n"
                 "const Q = (v) => v === null ? 'NULL' : ` '${v}'`;\n"
                 "const NQ = (v, n) => v === null ? 'NULL' : `'${v.slice(0, n)}'`;\n"
                 "const sql = `SELECT * FROM cd_msg_in('${channel}', '${q(userId).replace(/'/g, \"''\")}', '${q(text.slice(0, 8000))}', '${sender}', ${Q(sq(disp ? String(disp).slice(0,150) : null))}, ${Q(sq(pic ? String(pic).slice(0,255) : null))}, '${type}', ${NQ(sq(med ? String(med) : null), 500)}, ${NQ(sq(prv ? String(prv) : null), 500)}, ${NQ(sq(spk ? String(spk) : null), 50)}, ${NQ(sq(sti ? String(sti) : null), 50)}, ${mid ? `'${q(String(mid).slice(0,64))}'` : 'NULL'});`;\n"
                 "return [{ json: { sql: sql } }];")
    call = PGQ("Call cd_msg_in", 640, "={{ $json.sql }}", {"postgres": PG_CHATDESK})
    shape = CODE("Shape", 860,
                 "const r = $input.first().json;\n"
                 "return [{ json: { ok: true, conversationId: r.conversation_id, messageId: r.message_id,\n"
                 "  duplicate: !!r.duplicate, botEnabled: !!r.bot_enabled, displayName: r.display_name } }];")
    resp = RESP("Respond", 1060)
    nodes = [wh, valid, call, shape, resp]
    cons = {}
    E(cons, wh, valid)
    E(cons, valid, call)
    E(cons, call, shape)
    E(cons, shape, resp)
    return {"name": "ChatDesk API-05 Receive (chat send central)", "nodes": nodes,
            "connections": cons, "settings": {"executionOrder": "v1"}, "pinData": {}}


# ================= API-06 READ (inbox/thread/webthread) =================
# ================= API-06 READ (inbox/thread/webthread) =================
# Single statement per PG node. Response shapes identical to PHP.
def build_read():
    wh = WH("Webhook Read", "api-read", 200)
    prep = CODE("Prep", 420,
                "const b = $input.first().json.body || $input.first().json || {};\n"
                "const resource = (b.resource || '').toString();\n"
                "if (!['inbox', 'thread', 'webthread'].includes(resource)) throw new Error('unknown resource');\n"
                 "return [{ json: { resource: resource, filter: (b.filter || 'all').toString(),\n"
                 "  q: (b.q || '').toString(), id: parseInt(b.id) || 0,\n"
                 "  since: Math.max(0, parseInt(b.since) || 0), userId: (b.userId || b.externalUserId || '').toString(),\n"
                 "  channel: (b.channel || '').toString() } }];")
    if_inbox = IFB("IF Inbox?", 640, "={{ $json.resource === 'inbox' }}")
    if_thread = IFB("IF Thread?", 640, "={{ $json.resource === 'thread' }}", y=480)
    fmt_js = (
        "const esc = (s) => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');\n"
        "const linkify = (s) => esc(s).replace(/(https?:\\/\\/[^\\s<]+)/g, '<a href=\"$1\" target=\"_blank\" rel=\"noopener noreferrer\">$1</a>').replace(/\\n/g, '<br>');\n"
        "const tz = (ts) => { if (!ts) return null; const d = new Date(new Date(ts).getTime() + 7*3600*1000); const p = (n) => String(n).padStart(2, '0');\n"
        "  return { hm: `${p(d.getUTCHours())}:${p(d.getUTCMinutes())}`, dmy: `${p(d.getUTCDate())}/${p(d.getUTCMonth()+1)}/${d.getUTCFullYear()}` }; };\n"
        "const fmt = (row) => { const t = tz(row.created_at); return { id: row.id, sender: row.sender, type: row.message_type,\n"
        "  content: row.content, html: linkify(row.content || ''),\n"
        "  mediaUrl: row.media_url || null, mediaPreviewUrl: row.media_preview_url || null,\n"
        "  stickerPackage: row.sticker_package || null, stickerId: row.sticker_id || null,\n"
        "  status: row.status || 'ok', error: row.error_message || null,\n"
        "  delivered: !!row.delivered_at, read: !!row.read_at, deleted: false,\n"
        "  deliveredAt: row.delivered_at ? tz(row.delivered_at).hm : null,\n"
        "  readAt: row.read_at ? tz(row.read_at).hm : null,\n"
        "  time: t ? t.hm : '', date: t ? t.dmy : '' }; };\n"
        "const cname = (c) => (c.display_name !== null && c.display_name !== '') ? c.display_name : ('id#' + c.id);\n")
    # ---- inbox: single query ----
    q_inbox = CODE("Q Inbox", 860,
                   "const p = $input.first().json;\n"
                   "const q = (s) => (s || '').toString().replace(/'/g, \"''\");\n"
                   "let where = \"c.status = 'open'\";\n"
                   "if (p.filter === 'unread') where = \"c.unread_count > 0 AND c.status = 'open'\";\n"
                   "else if (p.filter === 'human') where = \"c.bot_enabled = 0 AND c.status = 'open'\";\n"
                   "else if (p.filter === 'closed') where = \"c.status = 'closed'\";\n"
                   "if (p.q) { const like = '%' + q(p.q) + '%'; where += ` AND (c.display_name LIKE '${like}' OR c.external_user_id LIKE '${like}' OR EXISTS (SELECT 1 FROM cd_messages m WHERE m.conversation_id = c.id AND m.content LIKE '${like}'))`; }\n"
                   "const items = `SELECT COALESCE(json_agg(row_to_json(t)), '[]') FROM (SELECT c.id, c.channel, c.external_user_id, c.display_name, c.picture_url, c.status, c.bot_enabled, c.unread_count, c.last_message_at, c.last_message_text FROM cd_conversations c WHERE ${where} ORDER BY c.last_message_at IS NULL, c.last_message_at DESC, c.id DESC LIMIT 100) t`;\n"
                   "return [{ json: { sql: `SELECT (${items}) AS items, (SELECT COUNT(*) FROM cd_conversations WHERE status = 'open') AS open_count, (SELECT COUNT(*) FROM cd_conversations WHERE unread_count > 0 AND status = 'open') AS unread_count, (SELECT COUNT(*) FROM cd_conversations WHERE bot_enabled = 0 AND status = 'open') AS human_count, (SELECT COUNT(*) FROM cd_conversations WHERE status = 'closed') AS closed_count` } }];", y=200)
    r_inbox = PGQ("Run Inbox", 1060, "={{ $json.sql }}", {"postgres": PG_CHATDESK}, y=200)
    sh_inbox = CODE("Shape Inbox", 1260,
                    "const r = $input.first().json;\n"
                    "let items = r.items || [];\n"
                    "if (typeof items === 'string') { try { items = JSON.parse(items); } catch(e) { items = []; } }\n" + fmt_js +
                    "const list = items.map(x => ({ id: x.id, name: cname(x),\n"
                    "  picture: x.picture_url, userId: x.external_user_id, status: x.status,\n"
                    "  botEnabled: parseInt(x.bot_enabled) === 1, unread: parseInt(x.unread_count) || 0,\n"
                    "  preview: x.last_message_text || '',\n"
                    "  time: x.last_message_at ? (() => { const t = tz(x.last_message_at); return t.dmy.slice(0, 5) + ' ' + t.hm; })() : '' }));\n"
                    "return [{ json: { ok: true, items: list, counts: { open: parseInt(r.open_count) || 0,\n"
                    "  unread: parseInt(r.unread_count) || 0, human: parseInt(r.human_count) || 0, closed: parseInt(r.closed_count) || 0 } } }];", y=200)
    # ---- thread branch ----
    q_tconv = CODE("Q TConv", 860,
                   "const p = $input.first().json;\n"
                   "if (!p.id) throw new Error('missing id');\n"
                   "return [{ json: { id: p.id, since: p.since, sql: `SELECT * FROM cd_conversations WHERE id = ${p.id} LIMIT 1` } }];", y=480)
    r_tconv = PGQ("Run TConv", 1060, "={{ $json.sql }}", {"postgres": PG_CHATDESK}, y=480)
    q_tmsgs = CODE("Q TMsgs", 860,
                   "const t = $('Q TConv').first().json;\n"
                   "const id = parseInt(t.id) || 0;\n"
                   "if (!id) throw new Error('missing id');\n"
                   "const since = Math.max(0, parseInt(t.since) || 0);\n"
                   "return [{ json: { id: id, since: since, sql: `SELECT id, sender, content, message_type, media_url, media_preview_url, sticker_package, sticker_id, status, error_message, delivered_at, read_at, created_at FROM cd_messages WHERE conversation_id = ${id} AND deleted_at IS NULL` + (since > 0 ? ` AND id > ${since}` : '') + ` ORDER BY id DESC LIMIT 200` } }];", y=600)
    r_tmsgs = PGQ("Run TMsgs", 1060, "={{ $json.sql }}", {"postgres": PG_CHATDESK}, y=600)
    q_tclear = CODE("Q TClear", 1260,
                    "const p = $('Q TMsgs').first().json;\n"
                    "return [{ json: { sql: `UPDATE cd_conversations SET unread_count = 0 WHERE id = ${p.id} AND unread_count > 0` } }];", y=600)
    r_tclear = PGQ("Run TClear", 1460, "={{ $json.sql }}", {"postgres": PG_CHATDESK}, y=600)
    q_tread = CODE("Q TRead", 1660,
                   "const p = $('Q TMsgs').first().json;\n"
                   "return [{ json: { sql: `UPDATE cd_messages SET read_at = COALESCE(read_at, NOW()) WHERE conversation_id = ${p.id} AND sender = 'customer' AND read_at IS NULL` } }];", y=600)
    r_tread = PGQ("Run TRead", 1860, "={{ $json.sql }}", {"postgres": PG_CHATDESK}, y=600)
    mg_thread = N("Merge Thread", "n8n-nodes-base.merge", 1260, {"mode": "append"}, y=480)
    mg_thread["typeVersion"] = 3.1
    sh_thread = CODE("Shape Thread", 1460,
                     "let conv = null;\n"
                     "try { conv = $('Run TConv').first().json; if (conv.channel === undefined) conv = null; } catch(e) { conv = null; }\n"
                     "if (!conv) return [{ json: { ok: false, error: 'conv-missing' } }];\n" + fmt_js +
                     "const msgs = $('Run TMsgs').all().map(r => r.json).filter(r => r.sender !== undefined).sort((a, b) => a.id - b.id);\n"
                     "const since = (() => { try { return $('Q TMsgs').first().json.since || 0; } catch(e) { return 0; } })();\n"
                     "const lastId = msgs.reduce((m, x) => Math.max(m, x.id), since);\n"
                     "const ct = tz(conv.created_at);\n"
                     "return [{ json: { ok: true,\n"
                     "  conversation: { id: conv.id, name: cname(conv), picture: conv.picture_url, userId: conv.external_user_id,\n"
                     "    channel: conv.channel, status: conv.status, botEnabled: parseInt(conv.bot_enabled) === 1,\n"
                     "    since: ct ? (ct.dmy + ' ' + ct.hm) : '' },\n"
                     "  messages: msgs.map(fmt), lastId: lastId } }];", y=480)
    # ---- webthread branch ----
    q_wconv = CODE("Q WConv", 860,
                    "const p = $input.first().json;\n"
                    "if (!/^WEB_[A-Za-z0-9_-]{1,64}$/.test(p.userId)) throw new Error('bad user');\n"
                    "const q = (s) => (s || '').toString().replace(/'/g, \"''\");\n"
                    "const ch = (p.channel === 'shopweb') ? 'shopweb' : 'web';\n"
                    "return [{ json: { userId: p.userId, since: p.since, channel: ch, sql: `SELECT * FROM cd_conversations WHERE channel = '${ch}' AND external_user_id = '${q(p.userId)}' LIMIT 1` } }];", y=660)
    r_wconv = PGQ("Run WConv", 1060, "={{ $json.sql }}", {"postgres": PG_CHATDESK}, y=660)
    r_wconv["alwaysOutputData"] = True
    q_wmsgs = CODE("Q WMsgs", 860,
                    "const t = $('Q WConv').first().json;\n"
                    "const q = (s) => (s || '').toString().replace(/'/g, \"''\");\n"
                    "const since = Math.max(0, parseInt(t.since) || 0);\n"
                    "const ch = (t.channel === 'shopweb') ? 'shopweb' : 'web';\n"
                    "return [{ json: { since: since, sql: `SELECT id, sender, content, message_type, created_at FROM cd_messages WHERE conversation_id = COALESCE((SELECT id FROM cd_conversations WHERE channel = '${ch}' AND external_user_id = '${q(t.userId)}' LIMIT 1), -1) AND deleted_at IS NULL` + (since > 0 ? ` AND id > ${since}` : '') + ` ORDER BY id DESC LIMIT 100` } }];", y=780)
    r_wmsgs = PGQ("Run WMsgs", 1060, "={{ $json.sql }}", {"postgres": PG_CHATDESK}, y=780)
    r_wmsgs["alwaysOutputData"] = True
    mg_web = N("Merge Web", "n8n-nodes-base.merge", 1260, {"mode": "append"}, y=720)
    mg_web["typeVersion"] = 3.1
    sh_web = CODE("Shape Web", 1460,
                  "let conv = null;\n"
                  "try { conv = $('Run WConv').first().json; if (conv.channel === undefined) conv = null; } catch(e) { conv = null; }\n"
                  "const since = (() => { try { return $('Q WConv').first().json.since || 0; } catch(e) { return 0; } })();\n"
                  "if (!conv) return [{ json: { ok: true, conversationId: 0, messages: [], lastId: since } }];\n" + fmt_js +
                  "const msgs = $('Run WMsgs').all().map(r => r.json).filter(r => r.sender !== undefined).sort((a, b) => a.id - b.id);\n"
                  "const lastId = msgs.reduce((m, x) => Math.max(m, x.id), since);\n"
                  "return [{ json: { ok: true, conversationId: conv.id, botEnabled: parseInt(conv.bot_enabled) === 1,\n"
                  "  status: conv.status, messages: msgs.map(m => { const f = fmt(m); return { id: f.id, sender: f.sender, type: f.type, text: f.content, time: f.time }; }), lastId: lastId } }];", y=720)
    resp = RESP("Respond", 1700)
    nodes = [wh, prep, if_inbox, if_thread,
             q_inbox, r_inbox, sh_inbox,
             q_tconv, r_tconv, q_tmsgs, r_tmsgs, q_tclear, r_tclear, q_tread, r_tread, sh_thread,
             q_wconv, r_wconv, q_wmsgs, r_wmsgs, sh_web, resp]
    cons = {}
    E(cons, wh, prep)
    E(cons, prep, if_inbox)
    E2(cons, if_inbox, q_inbox, if_thread)
    E(cons, q_inbox, r_inbox)
    E(cons, r_inbox, sh_inbox)
    E(cons, sh_inbox, resp)
    E2(cons, if_thread, q_tconv, q_wconv)
    E(cons, q_tconv, r_tconv)
    E(cons, r_tconv, q_tmsgs)
    E(cons, q_tmsgs, r_tmsgs)
    E(cons, r_tmsgs, q_tclear)
    E(cons, q_tclear, r_tclear)
    E(cons, r_tclear, q_tread)
    E(cons, q_tread, r_tread)
    E(cons, r_tread, sh_thread)
    E(cons, sh_thread, resp)
    E(cons, q_wconv, r_wconv)
    E(cons, r_wconv, q_wmsgs)
    E(cons, q_wmsgs, r_wmsgs)
    E(cons, r_wmsgs, sh_web)
    E(cons, sh_web, resp)
    return {"name": "ChatDesk API-06 Read (inbox/thread/webthread)", "nodes": nodes,
            "connections": cons, "settings": {"executionOrder": "v1"}, "pinData": {}}


# ================= API-07 USERS (admin CRUD) =================
def build_users():
    wh = WH("Webhook Users", "api-users", 200)
    prep = CODE("Build SQL", 420,
                "const b = $input.first().json.body || $input.first().json || {};\n"
                "const op = (b.op || '').toString();\n"
                "const q = (s) => (s || '').toString().replace(/'/g, \"''\");\n"
                "const qi = (v) => { const n = parseInt(v); if (isNaN(n)) throw new Error('bad id'); return n; };\n"
                "let sql = '', sql2 = '';\n"
                "if (op === 'list') {\n"
                "  sql = `SELECT u.id, u.username, u.display_name, u.is_active, u.created_at, COALESCE(string_agg(g.name, ',' ORDER BY g.name), '') AS groups FROM cd_users u LEFT JOIN cd_user_groups ug ON ug.user_id = u.id LEFT JOIN cd_groups g ON g.id = ug.group_id GROUP BY u.id ORDER BY u.id`;\n"
                "} else if (op === 'list-groups') {\n"
                "  sql = `SELECT id, name, description FROM cd_groups ORDER BY id`;\n"
                "} else if (op === 'create') {\n"
                "  const un = (b.username || '').toString().trim();\n"
                "  if (!/^[A-Za-z0-9_.@-]{3,64}$/.test(un)) throw new Error('ชื่อผู้ใช้ไม่ถูกต้อง');\n"
                "  const ph = (b.pass_hash || '').toString();\n"
                "  if (ph.length < 20 || ph[0] !== '$') throw new Error('pass_hash ไม่ถูกต้อง');\n"
                "  const dn = q((b.display_name || '').slice(0, 150));\n"
                "  const gids = Array.isArray(b.groups) ? b.groups.map(g => parseInt(g)).filter(g => g > 0) : [];\n"
                "  sql = `INSERT INTO cd_users (username, pass_hash, display_name) VALUES ('${q(un)}', '${q(ph)}', '${dn}') RETURNING id`;\n"
                "  sql2 = gids.length ? '__GRANTS__:' + gids.join(',') + ':' + q(un) : '';\n"
                "} else if (op === 'setpass') {\n"
                "  const id = qi(b.id);\n"
                "  const ph = (b.pass_hash || '').toString();\n"
                "  if (ph.length < 20 || ph[0] !== '$') throw new Error('pass_hash ไม่ถูกต้อง');\n"
                "  sql = `UPDATE cd_users SET pass_hash = '${q(ph)}' WHERE id = ${id}`;\n"
                "} else if (op === 'active') {\n"
                "  const id = qi(b.id);\n"
                "  sql = `UPDATE cd_users SET is_active = ${parseInt(b.is_active) === 1 ? 1 : 0} WHERE id = ${id}`;\n"
                "} else if (op === 'display') {\n"
                "  const id = qi(b.id);\n"
                "  sql = `UPDATE cd_users SET display_name = '${q((b.display_name || '').slice(0, 150))}' WHERE id = ${id}`;\n"
                "} else if (op === 'groups') {\n"
                "  const id = qi(b.id);\n"
                "  const gids = Array.isArray(b.groups) ? b.groups.map(g => parseInt(g)).filter(g => g > 0) : [];\n"
                "  sql = `DELETE FROM cd_user_groups WHERE user_id = ${id}`;\n"
                "  sql2 = gids.length ? '__GRANTSID__:' + gids.join(',') + ':' + id : '';\n"
                "} else if (op === 'delete') {\n"
                "  const id = qi(b.id);\n"
                "  sql = `DELETE FROM cd_users WHERE id = ${id}`;\n"
                "} else if (op === 'group_add') {\n"
                "  const nm = (b.name || '').toString().trim().toUpperCase();\n"
                "  if (!/^[A-Z0-9_]{2,32}$/.test(nm)) throw new Error('ชื่อกลุ่มไม่ถูกต้อง');\n"
                "  sql = `INSERT INTO cd_groups (name, description) VALUES ('${nm}', '${q((b.description || '').slice(0, 255))}')`;\n"
                "} else if (op === 'group_del') {\n"
                "  const id = qi(b.id);\n"
                "  sql = `DELETE FROM cd_groups WHERE id = ${id} AND name NOT IN ('ADMIN','STAFF')`;\n"
                "} else { throw new Error('unknown op'); }\n"
                "return [{ json: { sql: sql, sql2: sql2, op: op } }];")
    run = PGQ("Run SQL", 640, "={{ $json.sql }}", {"postgres": PG_CHATDESK})
    run2 = PGQ("Run SQL2", 640, "={{ $json.sql2 }}", {"postgres": PG_CHATDESK}, y=480)
    # run2 executes only when sql2 present (IF below); grants need created id -> separate path:
    if2 = IFB("IF Has SQL2?", 860, "={{ (($('Build SQL').first().json.sql2 || '') !== '') }}", y=480)
    grants = CODE("Build Grants", 1080,
                  "const prev = $input.first().json;\n"
                  "const b = $('Build SQL').first().json;\n"
                  "let parts = (b.sql2 || '').split(':');\n"
                  "const kind = parts[0] || '';\n"
                  "const gids = (parts[1] || '').split(',').map(g => parseInt(g)).filter(g => g > 0);\n"
                  "const who = parts.slice(2).join(':');\n"
                  "let sql = '';\n"
                  "if (kind === '__GRANTS__') {\n"
                  "  sql = gids.map(g => `INSERT INTO cd_user_groups (user_id, group_id) SELECT id, ${g} FROM cd_users WHERE username = '${who.replace(/'/g, \"''\")}' ON CONFLICT DO NOTHING;`).join('');\n"
                  "} else if (kind === '__GRANTSID__') {\n"
                  "  sql = gids.map(g => `INSERT INTO cd_user_groups (user_id, group_id) VALUES (${parseInt(who)}, ${g}) ON CONFLICT DO NOTHING;`).join('');\n"
                  "} else { sql = 'SELECT 1'; }\n"
                  "return [{ json: { sql: sql } }];", y=480)
    rungrants = PGQ("Run Grants", 1300, "={{ $json.sql }}", {"postgres": PG_CHATDESK}, y=480)
    mg = N("Merge Out", "n8n-nodes-base.merge", 1080, {"mode": "append"}, y=300)
    mg["typeVersion"] = 3.1
    shape = CODE("Shape", 1520,
                 "const op = $('Build SQL').first().json.op || '';\n"
                 "const rows = $('Run SQL').all().map(r => r.json);\n"
                 "if (op === 'list') {\n"
                 "  const users = rows.map(u => ({ ...u, groups: (u.groups || '').split(',').filter(Boolean) }));\n"
                 "  return [{ json: { ok: true, users: users } }];\n"
                 "}\n"
                 "if (op === 'list-groups') {\n"
                 "  return [{ json: { ok: true, groups: rows } }];\n"
                 "}\n"
                 "if (op === 'create') {\n"
                 "  const r = rows.find(r => r.id !== undefined) || {};\n"
                 "  return [{ json: { ok: true, id: r.id || 0 } }];\n"
                 "}\n"
                 "return [{ json: { ok: true } }];")
    resp = RESP("Respond", 1740)
    nodes = [wh, prep, run, if2, grants, rungrants, shape, resp]
    cons = {}
    E(cons, wh, prep)
    E(cons, prep, run)
    E(cons, run, if2)
    cons[if2["name"]] = {"main": [[{"node": grants["name"], "type": "main", "index": 0}],
                                  [{"node": shape["name"], "type": "main", "index": 0}]]}
    E(cons, grants, rungrants)
    E(cons, rungrants, shape)
    E(cons, shape, resp)
    return {"name": "ChatDesk API-07 Users (admin CRUD)", "nodes": nodes,
            "connections": cons, "settings": {"executionOrder": "v1"}, "pinData": {}}


# ================= API-08 RAGMETA (rag groups + stats) =================
def build_ragmeta():
    wh = WH("Webhook RAG Meta", "api-ragmeta", 200)
    prep = CODE("Build SQL", 420,
                "const b = $input.first().json.body || $input.first().json || {};\n"
                "const op = (b.op || '').toString();\n"
                "const q = (s) => (s || '').toString().replace(/'/g, \"''\");\n"
                "const qi = (v) => { const n = parseInt(v); if (isNaN(n)) throw new Error('bad id'); return n; };\n"
                "let sql = '';\n"
                "if (op === 'list') {\n"
                "  sql = `SELECT g.id, g.name, g.description, COALESCE(g.persona_system, '') AS persona_system, COUNT(c.id) AS chunks FROM rag_groups g LEFT JOIN rag_chunks c ON (c.metadata->>'group_id')::int = g.id GROUP BY g.id, g.name, g.description, g.persona_system ORDER BY g.id;`;\n"
                "} else if (op === 'add') {\n"
                "  const nm = (b.name || '').toString().trim();\n"
                "  if (!/^[A-Za-z0-9_ก-ฮ-]{2,64}$/u.test(nm)) throw new Error('ชื่อกลุ่มไม่ถูกต้อง');\n"
                "  sql = `INSERT INTO rag_groups (name, description) VALUES ('${nm}', '${q((b.description || '').slice(0, 255))}');`;\n"
                "} else if (op === 'persona') {\n"
                "  const pid = qi(b.id);\n"
                "  sql = `UPDATE rag_groups SET persona_system = '${q((b.persona || '').slice(0, 4000))}' WHERE id = ${pid}`;\n"
                 "} else if (op === 'delete') {\n"
                 "  sql = `DELETE FROM rag_groups WHERE id = ${qi(b.id)};`;\n"
                 "} else if (op === 'listsources') {\n"
                 "  sql = `SELECT s.id, s.group_id, s.source_type, COALESCE(s.title, '') AS title, COALESCE(s.source_ref, '') AS source_ref, COALESCE(s.image_url, '') AS image_url, s.created_at, (SELECT COUNT(*) FROM rag_chunks c WHERE c.source_id = s.id) AS chunks FROM rag_sources s WHERE s.group_id = ${qi(b.group_id)} ORDER BY s.id DESC;`;\n"
                 "} else if (op === 'deletesource') {\n"
                 "  sql = `WITH d AS (DELETE FROM rag_sources WHERE id = ${qi(b.id)} AND group_id = ${qi(b.group_id)} RETURNING image_url) SELECT (SELECT COUNT(*) FROM d) AS deleted, COALESCE((SELECT image_url FROM d), '') AS image_url;`;\n"
                 "} else if (op === 'stats') {\n"
                "  sql = `SELECT (SELECT COUNT(*) FROM rag_sources) AS sources, (SELECT COUNT(*) FROM rag_chunks) AS chunks, (SELECT COUNT(*) FROM rag_sources WHERE source_type = 'image') AS images, (SELECT COALESCE(json_agg(json_build_object('name', g.name, 'chunks', (SELECT COUNT(*) FROM rag_chunks c WHERE (c.metadata->>'group_id')::int = g.id)) ORDER BY g.id), '[]') FROM rag_groups g) AS groups`;} else { throw new Error('unknown op'); }\n"
                "return [{ json: { sql: sql, op: op } }];")
    run = PGQ("Run SQL", 640, "={{ $json.sql }}", {"postgres": PG_CHATDESK})
    shape = CODE("Shape", 860,
                 "const op = $('Build SQL').first().json.op || '';\n"
                 "const rows = $input.all().map(r => r.json);\n"
                 "if (op === 'list') return [{ json: { ok: true, groups: rows.map(r => ({ ...r, chunks: parseInt(r.chunks) || 0 })) } }];\n"
                 "if (op === 'listsources') return [{ json: { ok: true, sources: rows.map(r => ({ id: parseInt(r.id) || 0, group_id: parseInt(r.group_id) || 0, source_type: (r.source_type || '').toString(), title: (r.title || '').toString(), source_ref: (r.source_ref || '').toString(), image_url: (r.image_url || '').toString(), created_at: (r.created_at || '').toString(), chunks: parseInt(r.chunks) || 0 })) } }];\n"
                 "if (op === 'deletesource') { const r = rows[0] || {}; return [{ json: { ok: true, deleted: (parseInt(r.deleted) || 0) > 0, image_url: (r.image_url || '').toString() } }]; }\n"
                 "if (op === 'stats') {\n"
                 "  const r = rows[0] || {};\n"
                 "  const groups = Array.isArray(r.groups) ? r.groups : [];\n"
                 "  return [{ json: { ok: true, sources: parseInt(r.sources) || 0, chunks: parseInt(r.chunks) || 0, images: parseInt(r.images) || 0,\n"
                 "    groups: groups.map(g => ({ name: g.name, chunks: parseInt(g.chunks) || 0 })) } }];\n"
                 "}\n"
                 "return [{ json: { ok: true } }];")
    resp = RESP("Respond", 1080)
    nodes = [wh, prep, run, shape, resp]
    cons = {}
    E(cons, wh, prep)
    E(cons, prep, run)
    E(cons, run, shape)
    E(cons, shape, resp)
    return {"name": "ChatDesk API-08 RAG Meta (groups+stats)", "nodes": nodes,
            "connections": cons, "settings": {"executionOrder": "v1"}, "pinData": {}}


# ================= API-09 ACTIONS (room ops: bot/close/read/delete) =================
# Linear chain. Single statement per PG node (CTE). Shapes identical to PHP action.php.
def build_actions():
    wh = WH("Webhook Actions", "api-actions", 200)
    prep = CODE("Build SQL", 420,
                "const b = $input.first().json.body || $input.first().json || {};\n"
                "const op = (b.action || b.op || '').toString();\n"
                "if (!['bot_on', 'bot_off', 'close', 'reopen', 'mark_read', 'delete_message', 'delete'].includes(op)) throw new Error('unknown action');\n"
                "const id = parseInt(b.conversationId || b.id) || 0;\n"
                "if (!id) throw new Error('missing conversation');\n"
                "const mid = parseInt(b.messageId) || 0;\n"
                "if (op === 'delete_message' && !mid) throw new Error('missing message');\n"
                "let sql = '';\n"
                "if (op === 'bot_on' || op === 'bot_off') {\n"
                "  const v = op === 'bot_on' ? 1 : 0;\n"
                "  const txt = op === 'bot_on' ? 'เปิดให้บอทตอบห้องนี้อีกครั้ง' : 'ปิดบอทห้องนี้ — พนักงานดูแลเอง';\n"
                "  sql = `WITH u AS (UPDATE cd_conversations SET bot_enabled = ${v} WHERE id = ${id} RETURNING 1), ins AS (INSERT INTO cd_messages (conversation_id, sender, content, message_type, status) SELECT ${id}, 'system', '${txt}', 'text', 'ok' WHERE EXISTS (SELECT 1 FROM u) RETURNING 1) SELECT EXISTS(SELECT 1 FROM cd_conversations WHERE id = ${id}) AS found`;\n"
                "} else if (op === 'close' || op === 'reopen') {\n"
                "  const st = op === 'close' ? 'closed' : 'open';\n"
                "  const txt = op === 'close' ? 'ปิดเคสนี้แล้ว' : 'เปิดเคสนี้ขึ้นมาใหม่';\n"
                "  const extra = op === 'close' ? ', unread_count = 0' : '';\n"
                "  sql = `WITH u AS (UPDATE cd_conversations SET status = '${st}'${extra} WHERE id = ${id} RETURNING 1), ins AS (INSERT INTO cd_messages (conversation_id, sender, content, message_type, status) SELECT ${id}, 'system', '${txt}', 'text', 'ok' WHERE EXISTS (SELECT 1 FROM u) RETURNING 1) SELECT EXISTS(SELECT 1 FROM cd_conversations WHERE id = ${id}) AS found`;\n"
                "} else if (op === 'mark_read') {\n"
                "  sql = `WITH a AS (UPDATE cd_conversations SET unread_count = 0 WHERE id = ${id} AND unread_count > 0 RETURNING 1), b AS (UPDATE cd_messages SET read_at = COALESCE(read_at, NOW()) WHERE conversation_id = ${id} AND sender = 'customer' AND read_at IS NULL RETURNING 1) SELECT EXISTS(SELECT 1 FROM cd_conversations WHERE id = ${id}) AS found`;\n"
                "} else if (op === 'delete_message') {\n"
                "  sql = `WITH d AS (DELETE FROM cd_messages WHERE id = ${mid} AND conversation_id = ${id} AND sender IN ('bot', 'agent') RETURNING 1) SELECT (SELECT COUNT(*) FROM d) AS deleted, EXISTS(SELECT 1 FROM cd_conversations WHERE id = ${id}) AS found`;\n"
                "} else if (op === 'delete') {\n"
                "  sql = `WITH d AS (DELETE FROM cd_conversations WHERE id = ${id} RETURNING 1) SELECT (SELECT COUNT(*) FROM d) AS deleted`;\n"
                "}\n"
                "return [{ json: { op: op, id: id, mid: mid, sql: sql } }];")
    run = PGQ("Run SQL", 640, "={{ $json.sql }}", {"postgres": PG_CHATDESK})
    shape = CODE("Shape", 860,
                 "const t = $('Build SQL').first().json;\n"
                 "const op = t.op || '';\n"
                 "const r = $input.first().json;\n"
                 "const found = !(r.found === false || r.found === 0 || r.found === '0' || r.found === null || r.found === undefined);\n"
                 "const delN = parseInt(r.deleted) || 0;\n"
                 "const missing = { ok: false, error: 'ไม่พบห้องแชทนี้' };\n"
                 "if (op === 'delete_message') {\n"
                 "  if (!found && delN === 0) return [{ json: missing }];\n"
                 "  if (delN === 0) return [{ json: { ok: false, error: 'ลบข้อความนี้ไม่ได้ (ลบได้เฉพาะข้อความของบอทหรือเจ้าหน้าที่)' } }];\n"
                 "  return [{ json: { ok: true, deleted: true, messageId: t.mid, message: 'ลบข้อความแล้ว' } }];\n"
                 "}\n"
                 "if (op === 'delete') {\n"
                 "  if (delN === 0) return [{ json: missing }];\n"
                 "  return [{ json: { ok: true, deleted: true, message: 'ลบห้องแชทนี้แล้ว' } }];\n"
                 "}\n"
                 "if (!found) return [{ json: missing }];\n"
                 "if (op === 'bot_on') return [{ json: { ok: true, botEnabled: true, message: 'บอทกลับมาตอบห้องนี้แล้ว' } }];\n"
                 "if (op === 'bot_off') return [{ json: { ok: true, botEnabled: false, message: 'ปิดบอทแล้ว พนักงานดูแลเอง' } }];\n"
                 "if (op === 'close') return [{ json: { ok: true, status: 'closed', message: 'ปิดเคสแล้ว' } }];\n"
                 "if (op === 'reopen') return [{ json: { ok: true, status: 'open', message: 'เปิดเคสใหม่แล้ว' } }];\n"
                 "return [{ json: { ok: true, message: 'ทำเครื่องหมายว่าอ่านแล้ว' } }];")
    resp = RESP("Respond", 1060)
    nodes = [wh, prep, run, shape, resp]
    cons = {}
    E(cons, wh, prep)
    E(cons, prep, run)
    E(cons, run, shape)
    E(cons, shape, resp)
    return {"name": "ChatDesk API-09 Actions (room ops)", "nodes": nodes,
            "connections": cons, "settings": {"executionOrder": "v1"}, "pinData": {}}


# ================= API-10 AI SETTINGS (per-activity engine settings) =================
# Linear chain. ADMIN gating happens in PHP; engine validates key/value whitelist.
# Keys: llm.qa (gemini|qwen3:4b), tts.engine (auto|neural|piper). voice.llm_model = legacy alias.
def build_voice():
    wh = WH("Webhook Voice", "api-voice", 200)
    prep = CODE("Build SQL", 420,
                "const b = $input.first().json.body || $input.first().json || {};\n"
                "const op = (b.op || 'get').toString();\n"
                "if (!['get', 'set'].includes(op)) throw new Error('unknown op');\n"
                "const ALLOW = { 'llm.qa': ['gemini', 'qwen3:4b'], 'tts.engine': ['auto', 'neural', 'piper'], 'ocr.engine': ['gemini', 'easyocr'] };\n"
                "let sql = '';\n"
                "let key = '';\n"
                "let v = '';\n"
                "let setkey = false;\n"
                "if (op === 'get') {\n"
                "  sql = `SELECT key, value FROM app_settings WHERE key IN ('llm.qa', 'tts.engine', 'ocr.engine', 'voice.llm_model', 'gemini.api_key')`;\n"
                "} else {\n"
                "  key = (b.key || '').toString();\n"
                "  v = (b.value || '').toString();\n"
                "  if (!key && b.model !== undefined) { key = 'llm.qa'; v = b.model.toString(); }\n"
                "  if (key === 'n8n.api_key') throw new Error('forbidden');\n"
                "  if (key === 'gemini.api_key') {\n"
                "    if (!/^[A-Za-z0-9._-]{20,500}$/.test(v)) throw new Error('รูปแบบ API key ไม่ถูกต้อง (20-500 ตัวอักษร: A-Z a-z 0-9 . _ -)');\n"
                "    setkey = true;\n"
                "  } else {\n"
                "    if (!ALLOW[key]) throw new Error('unknown key');\n"
                "    if (!ALLOW[key].includes(v)) throw new Error('unknown value');\n"
                "  }\n"
                "  const q = (s) => s.replace(/'/g, \"''\");\n"
                "  sql = `INSERT INTO app_settings (key, value, updated_at) VALUES ('${key}', '${q(v)}', NOW()) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW() RETURNING value`;\n"
                "}\n"
                "return [{ json: { op: op, key: key, v: v, setkey: setkey, sql: sql } }];")
    run = PGQ("Run SQL", 640, "={{ $json.sql }}", {"postgres": PG_CHATDESK})
    ifkey = IFB("IF Key Rotation?", 800, "={{ ($('Build SQL').first().json.setkey === true) }}")
    getna = PGQ("Get N8N API Key", 960, "SELECT value FROM app_settings WHERE key = 'n8n.api_key'", {"postgres": PG_CHATDESK}, y=180)
    patchcred = HTTP("Rotate Gemini Credential", 1140, "PATCH", N8N_SELF + "/api/v1/credentials/" + CRED_ID,
                     "={\"name\": " + json.dumps(CRED_NAME) + ", \"data\": {\"host\": " + json.dumps(CRED_HOST) + ", \"apiKey\": {{ $('Build SQL').first().json.v.toJsonString() }}}}",
                     y=180, timeout=30000)
    patchcred["onError"] = "continueRegularOutput"
    patchcred["parameters"]["sendHeaders"] = True
    patchcred["parameters"]["headerParameters"] = {"parameters": [{"name": "X-N8N-API-KEY", "value": "={{ $('Get N8N API Key').first().json.value }}"}]}
    shape2 = CODE("Shape Key Rotation", 1320,
                 "const it = $input.first().json;\n"
                 "const t = $('Build SQL').first().json;\n"
                 "const ok = !(it && it.error);\n"
                 "const raw = (t.v || '').toString();\n"
                 "const mask = raw.length >= 8 ? (raw.slice(0, 4) + '••••••' + raw.slice(-3)) : '';\n"
                 "if (!ok) {\n"
                 "  const em = ((it.error && (it.error.message || it.error.description)) || it.error || 'unknown').toString().slice(0, 300);\n"
                 "  return [{ json: { ok: false, key: 'gemini.api_key', value: mask, credential_updated: false, error: 'บันทึก key แล้ว แต่หมุน credential ไม่สำเร็จ: ' + em + ' — กดบันทึกซ้ำได้' } }];\n"
                 "}\n"
                 "return [{ json: { ok: true, key: 'gemini.api_key', value: mask, credential_updated: true } }];", y=180)
    shape = CODE("Shape", 960,
                 "const t = $('Build SQL').first().json;\n"
                 "const ALLOW = { 'llm.qa': ['gemini', 'qwen3:4b'], 'tts.engine': ['auto', 'neural', 'piper'], 'ocr.engine': ['gemini', 'easyocr'] };\n"
                 "const rows = $input.all().map(r => r.json);\n"
                 "if (t.op === 'set') {\n"
                 "  const v = rows.length && rows[0].value !== undefined ? rows[0].value : '';\n"
                 "  return [{ json: { ok: true, key: t.key, value: v } }];\n"
                 "}\n"
                 "const m = {};\n"
                 "rows.forEach(r => { m[r.key] = r.value; });\n"
                 "let qa = m['llm.qa'] || m['voice.llm_model'] || 'gemini';\n"
                 "if (!ALLOW['llm.qa'].includes(qa)) qa = 'gemini';\n"
                 "let te = m['tts.engine'] || 'auto';\n"
                 "if (!ALLOW['tts.engine'].includes(te)) te = 'auto';\n"
                 "let oe = m['ocr.engine'] || 'gemini';\n"
                 "if (!ALLOW['ocr.engine'].includes(oe)) oe = 'gemini';\n"
                 "let gk = (m['gemini.api_key'] || '').toString();\n"
                 "let gmask = gk.length >= 8 ? (gk.slice(0, 4) + '••••••' + gk.slice(-3)) : '';\n"
                 "return [{ json: { ok: true, settings: { 'llm.qa': qa, 'tts.engine': te, 'ocr.engine': oe, 'gemini.api_key_masked': gmask }, model: qa, models: ['gemini', 'qwen3:4b'] } }];", y=420)
    resp = RESP("Respond", 1060)
    nodes = [wh, prep, run, ifkey, getna, patchcred, shape2, shape, resp]
    cons = {}
    E(cons, wh, prep)
    E(cons, prep, run)
    E(cons, run, ifkey)
    E2(cons, ifkey, getna, shape)
    E(cons, getna, patchcred)
    E(cons, patchcred, shape2)
    E(cons, shape2, resp)
    E(cons, shape, resp)
    return {"name": "ChatDesk API-10 AI Settings", "nodes": nodes,
            "connections": cons, "settings": {"executionOrder": "v1"}, "pinData": {}}


# ================= API-11 CHANNELS (channel_map routing CRUD) =================
# Linear chain. ADMIN gating in PHP; engine validates codes/ids.
def build_channels():
    wh = WH("Webhook Channels", "api-channels", 200)
    prep = CODE("Build SQL", 420,
                "const b = $input.first().json.body || $input.first().json || {};\n"
                "const op = (b.op || 'list').toString();\n"
                "if (!['list', 'get', 'set'].includes(op)) throw new Error('unknown op');\n"
                "const q = (s) => (s || '').toString().replace(/'/g, \"''\");\n"
                "const sel = `SELECT m.channel_code, m.label, m.rag_group_id, g.name AS group_name, COALESCE(g.persona_system, '') AS persona_system, m.line_bot_id, (m.line_channel_token IS NOT NULL AND m.line_channel_token <> '') AS has_token, m.is_active FROM channel_map m LEFT JOIN rag_groups g ON g.id = m.rag_group_id`;\n"
                "let sql = '';\n"
                "if (op === 'list') {\n"
                "  sql = `SELECT COALESCE((SELECT json_agg(row_to_json(t)) FROM (${sel} ORDER BY m.channel_code) t), '[]') AS rows`;\n"
                "} else if (op === 'get') {\n"
                "  const code = (b.channel || b.channel_code || '').toString();\n"
                "  const bot = (b.line_bot_id || b.destination || '').toString();\n"
                "  if (bot) {\n"
                "    sql = `SELECT COALESCE((SELECT json_agg(row_to_json(t)) FROM (${sel} WHERE m.line_bot_id = '${q(bot)}') t), '[]') AS rows`;\n"
                "  } else {\n"
                "    if (!/^[a-z0-9_]{2,32}$/.test(code)) throw new Error('bad channel');\n"
                "    sql = `SELECT COALESCE((SELECT json_agg(row_to_json(t)) FROM (${sel} WHERE m.channel_code = '${code}') t), '[]') AS rows`;\n"
                "  }\n"
                "} else if (op === 'set') {\n"
                "  const code = (b.channel || b.channel_code || '').toString();\n"
                "  if (!/^[a-z0-9_]{2,32}$/.test(code)) throw new Error('bad channel');\n"
                "  const sets = [];\n"
                "  if (b.label !== undefined) sets.push(`label = '${q(b.label.toString().slice(0, 100))}'`);\n"
                "  if (b.rag_group_id !== undefined && b.rag_group_id !== null && b.rag_group_id !== '') {\n"
                "    const gid = parseInt(b.rag_group_id); if (!gid) throw new Error('bad group');\n"
                "    sets.push(`rag_group_id = ${gid}`);\n"
                "  }\n"
                "  if (b.line_bot_id !== undefined) {\n"
                "    const v = b.line_bot_id.toString().trim();\n"
                "    sets.push(v ? `line_bot_id = '${q(v.slice(0, 64))}'` : `line_bot_id = NULL`);\n"
                "  }\n"
                "  if (b.line_channel_token !== undefined) sets.push(`line_channel_token = '${q(b.line_channel_token.toString().slice(0, 255))}'`);\n"
                "  if (b.is_active !== undefined) sets.push(`is_active = ${parseInt(b.is_active) === 0 ? 0 : 1}`);\n"
                "  if (!sets.length) throw new Error('nothing to set');\n"
                "  sql = `WITH u AS (UPDATE channel_map SET ${sets.join(', ')} WHERE channel_code = '${code}' RETURNING 1) SELECT (SELECT COUNT(*) FROM u) AS updated`;\n"
                "}\n"
                "return [{ json: { op: op, sql: sql } }];")
    run = PGQ("Run SQL", 640, "={{ $json.sql }}", {"postgres": PG_CHATDESK})
    shape = CODE("Shape", 860,
                 "const op = $('Build SQL').first().json.op || '';\n"
                 "const r0 = $input.first().json;\n"
                 "if (op === 'set') {\n"
                 "  const n = parseInt(r0.updated) || 0;\n"
                 "  if (!n) return [{ json: { ok: false, error: 'ไม่พบช่องทางนี้' } }];\n"
                 "  return [{ json: { ok: true, updated: n } }];\n"
                 "}\n"
                 "let rows = r0.rows || [];\n"
                 "if (typeof rows === 'string') { try { rows = JSON.parse(rows); } catch(e) { rows = []; } }\n"
                 "if (op === 'get') {\n"
                 "  const r = rows[0] || null;\n"
                 "  if (!r) return [{ json: { ok: false, error: 'ไม่พบช่องทางนี้' } }];\n"
                 "  r.is_active = parseInt(r.is_active) || 0;\n"
                 "  r.rag_group_id = r.rag_group_id === null ? null : parseInt(r.rag_group_id);\n"
                 "  return [{ json: { ok: true, channel: r } }];\n"
                 "}\n"
                 "return [{ json: { ok: true, channels: rows.map(r => ({ ...r, is_active: parseInt(r.is_active) || 0 })) } }];")
    resp = RESP("Respond", 1060)
    nodes = [wh, prep, run, shape, resp]
    cons = {}
    E(cons, wh, prep)
    E(cons, prep, run)
    E(cons, run, shape)
    E(cons, shape, resp)
    return {"name": "ChatDesk API-11 Channels (routing map)", "nodes": nodes,
            "connections": cons, "settings": {"executionOrder": "v1"}, "pinData": {}}


if __name__ == "__main__":
    out = r"C:\Users\pol\Desktop\OpenCode Project\ChatDesk\local\n8n"
    for name, wf in [("api-01-aichat.json", build_aichat()),
                     ("api-02-stt.json", build_stt()),
                     ("api-03-tts.json", build_tts()),
                     ("api-04-send.json", build_send()),
                     ("api-05-receive.json", build_receive()),
                     ("api-06-read.json", build_read()),
                     ("api-07-users.json", build_users()),
                     ("api-08-ragmeta.json", build_ragmeta()),
                     ("api-09-actions.json", build_actions()),
                     ("api-10-voice.json", build_voice()),
                     ("api-11-channels.json", build_channels())]:
        p = os.path.join(out, name)
        json.dump(wf, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("wrote", p, len(json.dumps(wf)), "bytes")
