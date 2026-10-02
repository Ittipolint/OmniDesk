# OmniDesk — Technical Specification

> เอกสารนี้อธิบายสถาปัตยกรรมและสัญญา (contract) ของระบบ ณ 2 ต.ค. 2026
> ภาพรวมสำหรับผู้ใช้ดูที่ [README.md](README.md)

## 1. หลักสถาปัตยกรรม

- **PHP เป็น thin forwarder เท่านั้น** — ทำแค่ auth/session/CSRF, validate,
  เสิร์ฟไฟล์ แล้วส่งต่อ n8n ทุกครั้ง **ห้าม query DB ตรงจากโค้ดเว็บ**
  (ข้อยกเว้นเดียว: `upload.php` เก็บไฟล์ที่ดิสก์)
- **n8n คือ API Engine กลาง** — สมอง AI, RAG ทั้งหมด, รับ/ส่งทุกช่องทาง,
  งาน DB ทั้งหมดทำใน workflow ผ่าน Postgres node (credential เดียว `ChatDesk Postgres`)
- **Structured + Vector ค้นใน n8n เท่านั้น** แล้วรวมให้ AI ตอบ (กันบอทแต่งตัวเลข)

### 1.1 เส้นทางขาเข้า (inbound)

```
LINE OA ──POST /webhook/chatdesk-mgr ─▶ [ChatDesk Manager - LINE]
FB Page ──POST /webhook/chatdesk-fb ──▶ [ChatDesk Manager - FB]      (primary)
FB Page ──poll 1 นาที ────────────────▶ [ChatDesk FB Poller] ─POST /webhook/chatdesk-fb
                                         (fallback — ดู §7)
ShopDee ──chat.php ─POST api-ai-chat + api-shop-sql ─▶ รวมคำตอบที่ PHP
IntelTech ─chat.php ─POST api-ai-chat (channel=intelweb, RAG-only)
OmniDesk UI ─incoming.php ─POST /webhook/api-receive ─▶ [API-05] (staff/agent msgs)
```

Manager ทุกตัวใช้โครงเดียวกัน:
`Verify/Parse → Get Profile → Q Channel → Run Channel → Shape Channel →
Send to ChatDesk (เซฟ incoming ผ่าน incoming.php) → Bot Can Reply? →
[RAG Lookup → Shop SQL Lookup → LLM (Gemini | Ollama qwen3:4b)] →
Build Reply → Notify ChatDesk (เซฟ bot reply) → Create Message → Push API`

### 1.2 เส้นทางขาออก (staff reply)
พนักงานพิมพ์ใน OmniDesk → `send.php` → `POST /webhook/api-04-send`
(`api-send`) → route ตาม channel:
`line*` → LINE Push (token รายช่อง, fallback credential),
`fb*` → `POST /webhook/chatdesk-fb-push` (`chatdesk-push-fb`) → Graph API,
`web/intelweb/shopweb` → เซฟเป็น agent + mute บอท (text ล้วน)

## 2. แคตตาล็อก n8n workflows (`local/n8n/*.json`)

ไฟล์คือ export ตรงจาก production (มี `_export.workflowId` + วัน export;
token ถูกแทนด้วย placeholder แล้ว — import แล้วกรอกค่าจริง)

| ไฟล์ | Workflow | Trigger | หน้าที่ |
|---|---|---|---|
| `api-01-aichat.json` | API-01 AI Chat | `POST api-ai-chat` | สมองกลาง: persona ตาม channel, RAG scoping ตาม group_ids, memory (`n8n_chat_histories`), เลือก Gemini/Ollama |
| `api-02-stt.json` | API-02 STT | `POST api-stt` | proxy Whisper `:8080` |
| `api-03-tts.json` | API-03 TTS | `POST api-tts` | neural (edge-tts) → fallback Piper, คืน base64 |
| `api-04-send.json` | API-04 Send | `POST api-04-send` | ศูนย์กลางตอบกลับ (route ตาม channel) |
| `api-05-receive.json` | API-05 Receive | `POST api-receive` | รับข้อความกลาง เซฟ `cd_conversations`/`cd_messages` |
| `api-06-read.json` | API-06 Read | `POST api-read` | inbox/thread/webthread (`resource=inbox`, `filter`, `q`, `?channel=`) |
| `api-07-users.json` | API-07 Users | `POST api-users` | CRUD user/group + login/pass_hash |
| `api-08-ragmeta.json` | API-08 RAG Meta | `POST api-ragmeta` | groups/sources/stats/persona (`listsources`, `deletesource` …) |
| `api-09-actions.json` | API-09 Actions | `POST api-actions` | room ops (assign/close/mute/lead …) |
| `api-10-voice.json` | API-10 AI Settings | `POST api-voice` | get/set settings ราย key + Gemini key rotation |
| `api-11-channels.json` | API-11 Channels | `POST api-channels` | `cd_channel_add/set/del`, ผูก channel↔groups/persona/token |
| `api-12-shopsql.json` | API-12 Shop SQL | `POST api-shop-sql` | Text-to-SQL ร้าน (ดู §6) + audit |
| `api-13-odolead.json` | API-13 Odoo Lead | `POST api-odoo-lead` | รับ chat/order → upsert Lead/Contact/Sale Order ใน Odoo |
| `api-14-odoo-outbox.json` | API-14 Odoo Outbox | `POST api-odoo-outbox` | ส่งข้อความจาก Odoo Lead กลับเข้าแชท |
| `rag-03-ingest.json` | RAG-03 Ingest | `POST rag-ingest` | ingest text/URL/PDF/image (OCR: Gemini/EasyOCR, embed 768) |
| `rag-04-answer.json` | RAG-04 Answer | `POST rag-answer` | ตอบจาก PGVector (+สาขา Ollama) |
| `chatdesk-line-mgr.json` | Manager - LINE | `POST chatdesk-mgr` (+GET verify) | รับ LINE webhook ครบวงจร (36 nodes) |
| `chatdesk-fb-mgr.json` | Manager - FB | `POST chatdesk-fb` (+GET verify) | รับ FB webhook ครบวงจร (32 nodes) |
| `chatdesk-push.json` | Manager - Push | `POST chatdesk-push` | ส่ง LINE แบบ staff/agent |
| `chatdesk-push-fb.json` | Manager - Push FB | `POST chatdesk-fb-push` | ส่ง FB ผ่าน Graph API |
| `chatdesk-fb-poller.json` | FB Poller | schedule ทุก 1 นาที | fallback ดึง `/me/conversations` → `/messages` → ยิงเข้า `chatdesk-fb` (ดู §7) |

Credentials ที่ต้องมีใน n8n (สร้างเองใน UI — **ไม่มีในไฟล์ export**):
`ChatDesk Postgres (chatdesk)` (postgres), `ChatDesk LINE Push Header`
(httpHeaderAuth — ปัจจุบันเก็บ **FB Page token**, ชื่อเดิมค้างอยู่),
`lineMessagingApi`, `googlePalmApi` (Gemini), `ai_reader` (read-only สำหรับ Shop SQL)

## 3. สัญญา PHP ↔ n8n

- `chatdesk/api/incoming.php` → `POST {userId, text|message|reply|content,
  sender?, displayName?, pictureUrl?, messageType?, mediaUrl?, messageId?, secret?}`
  ตอบ `{ok, botEnabled?, ...}` (forward ไป `api-receive`)
- `chatdesk/api/inbox.php` → `POST {resource:'inbox', filter, q}` ไป `api-read`
- `shopdee/api/chat.php`, `inteltech/api/chat.php` → proxy เรียก `api-ai-chat`
  (+ `api-shop-sql` สำหรับ ShopDee) แล้วรวม `images[]` ให้ frontend แสดง `<img>`
- `shopdee/api/order.php` → สร้างออเดอร์ + ยิง `api-odoo-lead {op:'order', ...}`

## 4. ฐานข้อมูล (`local/sql/`)

รันตามเลขไฟล์บน DB ที่ระบุ (postgres service `postgres-rag`, ต้องมี
extension `vector` + `pg_trgm`):

| ไฟล์ | DB | สาระ |
|---|---|---|
| `01_chatdesk_pg.sql` | chatdesk | `cd_conversations` (UNIQUE channel+external_user_id), `cd_messages` (`external_message_id` UNIQUE — ใช้กันซ้ำ), `cd_groups/users/user_groups`, `rag_groups/sources/chunks` (embedding vector(768), HNSW) |
| `02_msg_function.sql` | chatdesk | functions ช่วยงานข้อความ |
| `03–07` | chatdesk | voice/ai/ocr settings, gemini key |
| `04, 12–14` | chatdesk | `channel_map` (channel_code, label, persona_system, line token…), `channel_rag_groups`, fn `cd_channel_add/set/del` |
| `08_shopdee.sql` + `seed_products.sql` | shopdee | `shop_products` 100 รายการ, `shop_orders`, `shop_order_items` |
| `10_shop_sql_audit.sql` | shopdee | `ai_sql_audit` (log ทุก query ที่ Text-to-SQL สร้าง) |
| `11_product_images.sql` | shopdee | `image_url` local 100 รูป (`/shopdee/images/products/SD-XXXX.jpg`) |

`seed_admin.php` สร้าง user เริ่มต้น (ดูรหัสใน `local/README.md` — เปลี่ยนทันทีที่ใช้งานจริง)

## 5. กติกา channel / RAG / persona

- Route ทุกคำถาม (ยกเว้นทักทาย) ผ่าน SQL lookup ก่อนตอบ (ShopDee)
- ตัวเลขต้อง deterministic จาก SQL (ห้าม LLM เบลนด์ เว้นแต่คำถามเชิงแนะนำ/เปรียบเทียบ)
- จับเลขแบบ whole-word (`27` ต้องไม่โดน `270`) — regex ใน api-12
- 1 channel : N groups ผ่าน `channel_rag_groups`; น้ำเสียงผูก `channel_map.persona_system`
- ชื่อ group: `A-Za-z0-9_ก-ฮ-` ยาว 2–64; metadata `group_name` ต้อง sync ตามชื่อ
- ป้ายช่องทางใน inbox มาจาก `channel_map.label` (`source` ใน api-06)

## 6. Shop SQL Text-to-SQL (`api-12-shopsql`)

`Prep → Route SQL (intent) → Build Template SQL → Validate → Run Shop SQL →
Shape → Save Audit → Respond`
- Validate: เฉพาะ `SELECT`, allowlist 3 ตาราง (`shop_products/orders/order_items`),
  ออเดอร์ต้องมี code/phone, สินค้าต้อง `is_active`, `LIMIT≤50`
- Shape: mask เบอร์/ที่อยู่, lookup ตอบ deterministic, คืน `image_url_display`/`image_urls`
- Credential `ai_reader` (read-only) + `statement_timeout 10s`
- ทุก query ลง `ai_sql_audit`

## 7. Facebook integration (สถานะ 2 ต.ค. 2026)

- **Primary (webhook)**: `GET/POST /webhook/chatdesk-fb` —
  verify ด้วย `VERIFY_TOKEN=726737d094ddc4039b5b92f41681dad9`,
  `Parse FB Events` รับ `entry[].messaging[]` (ข้าม `is_echo`),
  ได้ Page token แล้วแต่ **Meta ไม่ส่ง event มาเลย** (verify ผ่าน,
  `messages` subscribed, ไม่มี error) — สาเหตุฝั่ง Meta ยังไม่พบ
- **Fallback ที่ใช้จริง (Poller)**: `chatdesk-fb-poller` ทุก 1 นาที
  `GET /me/conversations → /{thread}/messages` กรอง `from != PAGE_ID`,
  ข้อความใหม่ (`created_time > lastCheck`, กันซ้ำด้วย `seen` mids ใน staticData)
  → ยิงเข้า `/webhook/chatdesk-fb` รูปแบบเดียวกับ webhook จริง
  - ในไฟล์: token = `__FB_PAGE_TOKEN__` (แทนค่าจริงก่อน import)
  - เรียกผ่าน query `?access_token=` (credential store ผ่าน API มีปัญหา header —
    ดูข้อควรระวังใน local/README ถ้าจะกลับไปใช้ credential)
  - ⚠️ ถ้าวันไหน webhook ฟื้น จะ**ตอบซ้ำ** (mid เดียวกันมาสองทาง) — ต้องใส่ guard
    กัน mid ซ้ำก่อนถึง Send FB
- ส่งออก: `POST /v26.0/me/messages` (`messaging_type: RESPONSE`, text + image ≤3)
- `Get FB Profile` ล้มด้วย `(#3) Application does not have the capability`
  (แอปขาดสิทธิ์) — ระบบทนได้ (ชื่อเป็น `id#N`, รูปว่าง) บอทตอบปกติ

## 8. เสียง (Voice)

- STT: Whisper `:8080` (large-v3-turbo CT2 int8) ผ่าน `api-stt`
- TTS: `api-tts` — neural (edge-tts `th-TH-PremwadeeNeural`) → fallback Piper, คืน base64
- LLM: `voice.llm_model` / `llm.qa` = `gemini` | `qwen3:4b` (Ollama `:11434`)
- OCR: `ocr.engine` = `gemini` | `easyocr` (`:8002`)
- เปลี่ยนได้ใน OmniDesk → ⚙️ AI Setting (ADMIN)

## 9. Odoo connector — **พักงานชั่วคราว**

- `local/odoo/`: `chatdesk-odoo:8069` + addon `chatdesk_connector`
  (`POST /chatdesk/lead`, token ผ่าน env `CHATDESK_ODOO_TOKEN`)
- ขาเข้า: ทุกข้อความ → Lead ต่อห้อง; สั่งซื้อ → Contact + Sale Order + invoice draft
- ขาออก: automation บน Lead → `api-odoo-outbox` → ส่งกลับแชท
- รัน: `local/odoo/docker-compose.yml` (config จาก `odoo.conf.example`)

## 10. Tunnel และรูปภาพ

- `chatdesk-cf-web` → `:8081`, `chatdesk-cf-n8n` → `:5678` (quick tunnel หมดอายุ ~20 ชม.)
- หมดอายุ = รัน `local/regen-tunnels.ps1` + อัปเดต Webhook URL (LINE/Meta) +
  `python3 local/n8n/update_public_base.py <url-web-ใหม่>` (รูป LINE พังถ้าลืม)
- LINE รับเฉพาะ `https://` — โค้ด rewrite รูป local
  `http://127.0.0.1:8081/…` → `PUBLIC_WEB_BASE` ก่อนส่ง (`Build Reply` ทั้ง LINE/FB)

## 11. บทเรียน/กติกาที่ต้องจำ (จากงานจริง)

1. ห้าม fan-out (1 output → หลาย node มีแค่ตัวแรกที่รัน) — ใช้ linear chain + `$('Node')`
2. PG node เปิด `alwaysOutputData` เสมอ (0 แถวแล้ว downstream อดแบบเงียบ ๆ)
3. PG node ละ 1 statement (ใช้ CTE รวม)
4. Code node syntax ผิด = 500 “No Respond to Webhook”
5. PATCH workflow อัปเดตแค่ draft — publish ด้วย `POST /rest/workflows/:id/activate {versionId}`
6. Credential อัปเดตผ่าน API ได้ (`PATCH /rest/credentials/:id` + `type`) แต่ data อ่านกลับไม่ได้
7. Execution detail API เก็บแบบ string-table refs (index อ้างกันเอง) — ต้อง resolve ก่อนอ่าน
8. ห้ามฝังข้อความไทยในพารามิเตอร์โหนด / ห้าม mustache ซ้อนใน array/object ของ HTTP jsonBody

## 12. Placeholders (แทนค่าจริงหลัง import/clone)

| Placeholder | ค่าจริง | ใส่ที่ไหน |
|---|---|---|
| `__FB_PAGE_TOKEN__` | FB Page access token | `chatdesk-fb-poller.json` (2 จุด) + n8n credential `ChatDesk FB Page Token` |
| `__GEMINI_API_KEY__` | Gemini API key (ค่า fallback) | workflow JSON/`gen_*.py`/`config.php`/`07_gemini_key.sql` — ค่าจริงอยู่ใน DB (`app_settings`) และ credential อยู่แล้ว |
| `__ODOO_SHARED_TOKEN__` | token ตรงกันทั้งสองฝั่ง | `api-13/14` + env `CHATDESK_ODOO_TOKEN` ของ Odoo |
| `__ODOO_MASTER_PASSWORD__` / `__POSTGRES_PASSWORD__` | รหัสจริง | `local/odoo/config/odoo.conf` (copy จาก `.example`) |
