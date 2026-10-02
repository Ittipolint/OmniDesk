# ChatDesk LOCAL Stack (Docker เครื่องนี้) — ระบบหลัก (26 ก.ย. 2026)

**นโยบาย: พัฒนาบน Local Docker เท่านั้น** (26 ก.ย. 2026) — ไม่แตะ veya อีก
(ยกเว้น third-party ข้างนอก: LINE API, Gemini API, Cloudflare Tunnel)

**veya ไม่เกี่ยวข้องกับการทำงานแล้ว** — ChatDesk/TripThai/LINE/RAG/Voice รัน local ทั้งหมด
ของบน veya ถูกแช่แข็งไว้เฉย ๆ (ไฟล์อยู่ครบ แต่ไม่มี traffic) + workflows LINE/Push บน n8n38 **ปิดแล้ว**

ระบบ ChatDesk + TripThai + n8n + RAG รันทั้งหมดบนเครื่องนี้ด้วย Docker
ของบน Cloud (veya) คงไว้เหมือนเดิมทุกอย่าง — rollback ได้ทันที

## Odoo 18 Community (2 ต.ค. 2026)
- `local/odoo/` (`chatdesk-odoo` :8069 + DB `odoo` บน postgres-rag, network `ai-stack_default`)
- เข้าเว็บ: http://127.0.0.1:8069 — admin/admin • master password อยู่ใน `local/odoo/config/odoo.conf` (`admin_passwd`)
- โมดูล CRM + Contacts ติดตั้งแล้ว (ไม่มี demo data) • custom addon `chatdesk_connector` (webhook `POST /chatdesk/lead`, token ใน `controllers/main.py`)
- โฟลว์ขาเข้า: แชททุกข้อความ (LINE/Web) → Lead ต่อห้อง (กันซ้ำ, ข้อความต่อท้ายใบเดิม) • สั่งซื้อสำเร็จ → `order.php` ยิง `op=order` → upsert Contact ตามเบอร์ (+ดึงเบอร์เข้า record แชทเดิม) + สร้าง Sale Order (confirm อัตโนมัติ, สินค้า auto-create แบบ consu ไม่คิด VAT ซ้ำ) + draft invoice + ปิด Lead ที่เปิดอยู่เป็น Won (best-effort ไม่ขวาง checkout)
- โฟลว์ขาออก: พนักงาน Send message บน Lead ใน Odoo → automation ยิง `api-odoo-outbox` (n8n) → LINE push ด้วย token รายช่อง / Web เซฟเป็น agent + mute บอท (text ล้วน)
- รหัสผ่าน admin ของ Odoo ใน `app_settings` (`odoo.admin_password`) — เปลี่ยนรหัสแล้วต้องอัปเดตทั้ง 2 ที่

## ผังระบบ (26 ก.ย. 2026 — n8n เป็น API Engine กลาง)

```
LINE OA ──▶ Tunnel ──▶ n8n-local :5678 ── [LOCAL] LINE/Push (+RAG context)
                                    │
TripThai :8081 ──PHP thin───────────┼──▶ api-ai-chat (สมองกลาง: RAG-first→Gemini)
  (mic/spk/input)   ├─ stt.php ─────┼──▶ api-stt ──▶ Whisper :8080
                    ├─ tts.php ─────┼──▶ api-tts ──▶ Piper :8080 (base64)
                    └─ gemini.php ──┘
ChatDesk :8081 ──PHP (auth/static/inbox-poll)──┼──▶ chatdesk-send (agent+mute+push)
  (login/users/rag UI)                         └──▶ rag-ingest / rag-answer
                                    │
                        Postgres :5432 (chatdesk + ragdb)
PHP ทำแค่: auth/session, เสิร์ฟไฟล์, ตรวจ input, inbox/thread polling ตรง (ถี่ 3-5 วิไม่ผ่าน n8n)
n8n ทำ: สมอง AI, RAG ทั้งหมด, รับ/ส่ง LINE, STT/TTS proxy, บันทึกข้อความ agent
FB: flows อยู่บน cloud (รอ Meta token มากรอก local)
```

(1) `https://autos-barnes-bloggers-ultram.trycloudflare.com` (n8n — อัปเดต 26 ก.ย.)
(2) `https://hindu-ratio-decor-emerald.trycloudflare.com` (ChatDesk — อัปเดต 26 ก.ย.)

## URL ใช้งาน

| อะไร | Local | หมายเหตุ |
|---|---|---|
| ChatDesk | http://127.0.0.1:8081/chatdesk/ | admin / 10203040 (ADMIN) |
| TripThai | http://127.0.0.1:8081/tripthai/ | - |
| RAG System | ปุ่ม 🧠 ใน ChatDesk (ADMIN เท่านั้น) | ingest + ทดสอบถามตอบ |
| จัดการผู้ใช้ | ปุ่ม 👥 ใน ChatDesk (ADMIN เท่านั้น) | staff1 / staff1234 (STAFF ตัวอย่าง) |
| n8n | http://127.0.0.1:5678 | ittipolint@gmail.com |
| pgAdmin | http://localhost:5050 | ดูข้อมูล RAG |

## สั่งรัน / หยุด / รีสตาร์ท

```powershell
$d = 'C:\Users\pol\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe'
& $d compose -f .\docker-compose.yml up -d          # ในโฟลเดอร์ local\
& $D restart chatdesk-web n8n-local                  # รีสตาร์ทหลังแก้โค้ด/PHP
```

## ⚠️ ข้อควรรู้เรื่อง Tunnel (สำคัญ — เจอของจริงแล้ว 26 ก.ย.)
Quick Tunnel **หมดอายุเอง (~20 ชม.)** แบบ `Tunnel not found` — ถ้า LINE ตอบไม่ได้ให้เช็ค log tunnel ก่อน:
`docker logs chatdesk-cf-n8n` / `chatdesk-cf-web`
สร้างใหม่ = รัน `local\regen-tunnels.ps1` (คลิกขวา > Run with PowerShell) — สร้าง 2 ตัว (n8n+web) +
อัปเดต URL ในไฟล์ให้เอง แล้วทำมือแค่: (1) วาง Webhook URL ใน LINE console,
(2) `python3 local/n8n/update_public_base.py <url-web-ใหม่>` (ไม่งั้นรูป LINE หลุด)
ถาวร: เปลี่ยนเป็น **Named Tunnel** (URL นิ่ง, ล็อกอิน Cloudflare ครั้งเดียว)

## veya — ตัดออกแล้ว (1 ต.ค.)
โฮสต์ veya เลิกใช้: ลบ `trip-booking/` (staging), `local/n8n/cloud/`, `export_cloud.py`/`cloud_off.py`/`migrate_cloud.py`,
tunnel `cf-whisper` (gateway เสียง :8080 ภายในยังรันปกติ ไม่ต้องมี tunnel สาธารณะ) และขั้นตอนอัปโหลด FTP ทั้งหมดออกแล้ว
เสียง STT/TTS ใช้ภายในผ่าน `host.docker.internal:8080` อย่างเดียว

## สิ่งที่ยังไม่ย้าย (ตั้งใจค้างไว้)
- **FB flows** (Push FB + FB): ยังรันบน n8n38 — ต้องกรอก Meta token ใน local n8n ก่อนถึงย้ายได้
- **week7/admin (sbu-webchat)**: คนละแอป ไม่ได้ย้าย — รันบน cloud เหมือนเดิม

## การย้าย LINE มา local (cutover — ทำแล้ว 26 ก.ย.)
Webhook ปัจจุบันชี้ local (`https://autos-barnes-bloggers-ultram.trycloudflare.com/webhook/chatdesk-mgr`)
workflows LINE/Push บน n8n38 ปิดแล้ว — ทดสอบโดยส่ง LINE 1 ข้อความ ต้องมีห้องขึ้นใน ChatDesk local

## โครงไฟล์

```
local/
├── docker-compose.yml   # web (php-apache) + cf-web + cf-n8n tunnels
├── php/Dockerfile       # php:8.3-apache + pdo_pgsql
├── sql/01_chatdesk_pg.sql
├── sql/seed_admin.php
├── www/chatdesk/        # โค้ด PHP (port จาก cloud: MySQL->Postgres + multi-user + RAG/Users UI)
├── www/tripthai/        # ก็อปจาก trip-booking (gemini.php เรียก RAG-first)
└── n8n/                 # gen_rag_wf.py, export/migrate/patch scripts, cloud/*.json (backup)
```

## สิ่งที่ยังไม่ทำ (รอของ/รอคน)

- **PDF ingest**: โค้ดพร้อม (ทางเดียวกับรูปที่เทสผ่าน) แต่ยังไม่ได้ทดสอบไฟล์จริง — อัปโหลด PDF ไทยผ่านจอ RAG ได้เลย
- **FB flows** ([LOCAL] Push FB + FB): import แล้วแต่ inactive — ต้องกรอก Meta token ใน UI ก่อนใช้
- **Named Tunnel**: แนะนำทำ (ดูข้างบน)
- **week7/admin (sbu-webchat)**: ไม่ได้ย้าย (คนละแอป) — ยังรันบน cloud เหมือนเดิม

## API Engine กลาง — 100% ผ่าน n8n (ทำแล้ว 26 ก.ย.)

PHP เป็น thin forwarder ทั้งหมด (auth/CSRF/validate ที่ PHP, DB ที่ n8n):
`api-ai-chat (139C66vWSpCv5G2Q)` · `api-stt (af6AkiMrcJupk8E5)` · `api-tts (jmo9rK5TmJPaIQPv)`
`chatdesk-send (CjCI13k1E12J095t)` · `api-receive (AH6wmgP25j8erHEB)` · `api-read (ynBDglW8hWrzEp81)`
`api-users (4C8QHmcAJ02jW7Z9)` · `api-ragmeta (gesxAirJO3NY4gQR)` · `api-actions (aEBTIfxEZFOQAxLt)`
- ต้นแบบ: `local/n8n/gen_api_wf.py` (regen → `update_wf.py` → activate) + `difftest.py` (21 checks ผ่าน)
- กฎเหล็ก: ห้าม fan-out (1 output → หลาย node มีแค่ตัวแรกที่รัน!) — ใช้ linear chain + `$('Node')` refs แทน, ห้าม Merge, PG node ละ 1 statement (ใช้ CTE)
- TripThai `gemini/stt/tts.php` เรียก engine อย่างเดียว (ลบ fallback ตรง + ลบ Gemini key ออกจากโค้ดแล้ว)
- `upload.php` เก็บไฟล์ที่ PHP (ไม่ใช่งาน DB) → `send.php` ส่งต่อ engine

## AI Voice ผ่าน n8n ทั้งหมด (ทำแล้ว 26 ก.ย.)

กฎ: entry ทุกทางเรียก webhook เท่านั้น, AI (STT/TTS/LLM) ถูกเรียกจาก node ใน n8n เท่านั้น

```
Browser ─▶ PHP thin fwd ─▶ [api-ai-chat] ─┬─ RAG ──▶ Respond
                        ─▶ [api-stt] ──▶ whisper:8080 (large-v3-turbo, local CT2 int8)
                        ─▶ [api-tts] ──▶ voiceapi:/tts-neural (edge-tts) ─ok?─▶ base64
                                              │ fail → voiceapi:/tts (Piper fallback)
                        ─▶ [api-voice get/set] ─▶ app_settings.voice.llm_model
LINE ─▶ [chatdesk-mgr] ── RAG + Get Voice Model ── IF ─┬─ AI Agent + Gemini (cloud)
                                                       └── Ollama qwen3:4b-instruct (local)
ChatDesk topbar [🎙️ AI Voice Setting] (ADMIN) ─▶ voice/ ─▶ api-voice
```

- **STT turbo**: `ASR_MODEL=/models/turbo-ct2` (แปลงเอง pt→CT2 int8 820MB เพราะ huggingface.co โดนบล็อก — โหลด turbo.pt จาก Azure + convert ด้วย transformers/ctranslate2; ดู `whisper-server/models/`) • fallback ถ้า image ไม่รู้จักชื่อ: `large-v3`
- **TTS neural**: `voiceapi/app.py:/tts-neural` (edge-tts `th-TH-PremwadeeNeural` → ffmpeg แปลงเป็น wav 16k; ต้องมีเน็ต) • Piper เป็น fallback อัตโนมัติใน `api-03-tts`
- **LLM**: setting `voice.llm_model` default `gemini` • local ใช้ `qwen3:4b-instruct` (ตัว hybrid คิดไม่หยุดแม้ `think:false` — เป็นบั๊ก template ที่แก้ด้วย Modelfile ไม่หายขาด เลยใช้รุ่น instruct) • ลบ `qwen2.5:7b` แล้ว
- Workflows: `api-01-aichat (139C66vWSpCv5G2Q)` +สาขา Ollama, `api-03-tts (jmo9rK5TmJPaIQPv)` +neural, `api-10-voice (ZJQRxPRCyMi6Nszd)` ใหม่, LINE `DPXcIEfqSaxmbLV3` +สาขา Ollama (rollback: v151cc0a0)
- บทเรียน: n8n runner cache ค้างได้ (exec รัน node ที่ไม่มีใน workflow แล้ว) — แก้ด้วย deactivate→activate; `Voice Bot` workflow เก่าไม่มีใครเรียก ไม่แตะ

## RAG แยกตามช่องทาง 1:1 (ทำแล้ว 26 ก.ย.)

- Schema: 1 channel : N groups ผ่าน `channel_rag_groups` + `channel_map.persona_system` (น้ำเสียงผูกช่องทาง) — migration `04_channels.sql` + `13_channel_groups.sql` + `14_channel_save.sql` (+fn `cd_channel_add/set/del`) • 28/9/68: เหลือ 2 กลุ่ม `internal-data`(4, เดิม itsupport) `public-data`(5, เดิม shop) ลบ tourism/law แล้ว • 30/9/68: เปลี่ยนชื่อ `internal-data`→`itil-concept`, `public-data`→`ShopDee-Profile` (id เดิม 4/5) • channels: `line`(itil-concept, active) `shopweb`(ShopDee-Profile, active) `intelweb`(inteltech-data 8, active)
- `api-ai-chat`: lookup persona ตาม channel + RAG scoping ตาม group_ids[] (chat.php ส่ง `channel`) • default persona = GEM_SYS เดิม
- LINE `chatdesk-mgr`: Parse เก็บ `destination` → Lookup Channel (fallback `line` ถ้ายังไม่ผูก) → conv แยก channel code → RAG ส่ง group_id+session(channel:user) → persona ต่อสาขา → ส่ง LINE ผ่าน HTTP push ด้วย token รายช่องทาง (token ว่าง = ใช้ credential เดิม)
- `api-receive` รับ channel ใดๆ ที่ปลอดภัย • `api-04-send` + Push workflow ส่ง token ต่อห้อง (fallback credential เดิม)
- Workflows: `api-11-channels (5n4GtYDbhf3NPhgU)` ใหม่ • `api-ragmeta` +op persona • UI: tab ช่องทาง + น้ำเสียงรายกลุ่มในจอ RAG
- **รอจากคุณ**: (1) Channel access token OA#1 → ใส่ใน tab ช่องทาง (ของเดิมใช้ credential ไปก่อน) (2) `line_bot_id` จะจับจากข้อความจริงครั้งถัดไป (fallback ทำงานแทนได้) (3) เนื้อหา itil-concept/ShopDee-Profile/inteltech-data ingest เองผ่านจอ RAG (ShopDee-Profile มีแค่ Company Profile — บอทสินค้าพึ่ง SQL)
- ระวัง: โควต้า Gemini 429 วันนี้ (RAG agent + direct ใช้คีย์เดียวกัน) — เส้น RAG/LINE จะล้มจนกว่าโควต้ารีเซ็ต แนะนำ P1: fallback Ollama ใน rag-answer

## AI Setting รายกิจกรรม (ทำแล้ว 26 ก.ย.)

- ปุ่ม topbar → **⚙️ AI Setting** (URL `voice/` เดิม) • settings: `llm.qa` (gemini|qwen3:4b ตอบคำถาม: RAG+แชท+LINE) • `tts.engine` (auto|neural|piper) • `ocr.engine` (gemini|easyocr ดูหัวข้อ OCR) • ล็อก: Embedding/STT (engine เดียวที่มี)
- `llm.qa` ไม่มี → fallback `voice.llm_model` → gemini • migration `05_ai_settings.sql`
- Workflows: `api-10 AI Settings (ZJQRxPRCyMi6Nszd)` get/set ราย key • `rag-04` +สาขา Ollama (qwen3:4b-instruct, test ตอบถูกกลุ่มโดยไม่ต้องพึ่ง Gemini) • `api-03-tts` เลือกตาม setting • LINE ใช้ `llm.qa` เหมือนกัน
- กฎเพิ่ม: HTTP jsonBody ห้าม mustache ซ้อนใน array/object (`[{...{{...}}...}]` เสีย) — ส่ง object ทั้งก้อน `={{ $json.body }}` แทน (เจอที่ Gemini Direct + Push LINE)

## OCR เลือก engine: Gemini หรือ EasyOCR ท้องถิ่น (27 ก.ย.)

- Setting ใหม่ `ocr.engine` = `gemini` | `easyocr` (ค่าเริ่ม `gemini`) • เปลี่ยนได้ในจอ **⚙️ AI Setting** → แถว "📄 OCR เอกสาร" หรือ `api-voice` op=set
- **EasyOCR (local)**: service `triptthai-ocrapi` (port 8002 หลัง Caddy path `/ocr*`) — Thai+English, CPU, offline หลังโหลดโมเดล • PDF ≤15MB/≤20 หน้า (200dpi), รูป ≤10MB • เร็ว ~วินาที/รูป, ~4 นาที/PDF 10 หน้า
- Flow `rag-03`: `Get OCR Engine` → `IF Local OCR?` → จริง=`EasyOCR Local` → `Shape Local OCR` / เท็จ=`Gemini OCR` → บรรทัดเดียวกันที่ `Build Source SQL` • ทดสอบแล้ว: ภาพไทย → ข้อความใน DB ผิดแบบ EasyOCR ("ท้องถืน") พิสูจน์ว่าไม่ใช่ Gemini
- สาขา Gemini: แก้บั๊กแล้ว — หลังใส่ IF `$json` ไม่ใช่ output ของ `Build Gemini OCR` อีก → ต้องอ้าง `$('Build Gemini OCR').first().json` ( toJsonString on undefined ) • เส้นเรียก Google สำเร็จแล้ว เหลือแค่โควต้า
- migration `06_ai_ocr.sql` (ค่าเริ่ม gemini) • `api-10` get/set/validate ผ่าน (ค่าผิด = ปฏิเสธ ไม่ลง DB) • PHP `voice/api/setting.php` ใส่ `$allow['ocr.engine']` + CSRF ครบ
- **สถานะตอนนี้**: ค่าในระบบ = `easyocr` (Gemini 429 เป็นระยะ ช่วง limit 20 req/min) — อยากได้แม่นสุดเมื่อโควต้านิ่ง → สลับเป็น gemini ใน AI Setting
- ทดสอบทั้งหมด: EasyOCR branch E2E ผ่าน • `difftest.py` ALL PASS • PHP lint ผ่านทุกไฟล์ • test rows ลบแล้ว

## เปลี่ยน Gemini API Key ในจอ AI Setting (27 ก.ย.)

- แถว "🔑 Gemini API Key" (password input + ปุ่มบันทึก + แสดงแบบ mask `AQ.A••••••RAA`) — มีผลทั้ง 5 จุด: OCR, embed นำเข้า, embed คำถาม, RAG agent, AI chat direct
- กลไก: `gemini.api_key` ใน app_settings เป็น source of truth — HTTP nodes อ่านผ่าน `Get Gemini Key` (ingest ใช้ CTE `gk` แนบมากับ `Save Source Row` เพื่อไม่พัง multi-chunk loop) • RAG agent ใช้ credential `VuE8YX5cbPUw7Ay8` → หมุนผ่าน `PATCH /api/v1/credentials/` ด้วย Personal API key (label `chatdesk-key-rotation`, scope credential:update+read) ที่เก็บใน `n8n.api_key`
- ปลอดภัย: get ไม่ส่ง key เต็ม/`n8n.api_key` ออกมาเลย • set ตรวจ format (20-500 ตัวอักษร `A-Za-z0-9._-`) ทั้ง PHP+n8n • `n8n.api_key` เปลี่ยนผ่าน UI ไม่ได้
- migration `07_gemini_key.sql` • deploy แล้ว 4 workflows (ai-chat/api-10/rag-03/rag-04) + unify key ทั้ง DB+credential
- ทดสอบ: set bogus key → Google 400 ทั้ง embed+direct (พิสูจน์ key ใหม่มีผลทันที ไม่ต้อง restart) → set กลับแล้ว • `difftest.py` ALL PASS • credential PATCH ล้มเหลว = ตอบ ok:false พร้อมบอกให้กดซ้ำ (idempotent)

## ลบเอกสาร RAG รายชิ้น (27 ก.ย.)

- เดิมลบได้ทั้งกลุ่มเท่านั้น (ปุ่มลบข้างกลุ่ม) — FK `ON DELETE CASCADE` ทั้ง `sources.group_id` และ `chunks.source_id` ตรวจแล้วลบเกลี้ยง • 28/9/68: ลบ tourism/law (channel web ตัดทิ้ง, fb ย้ายไป public-data) เหลือ internal-data/public-data (30/9/68 เปลี่ยนชื่อเป็น itil-concept/ShopDee-Profile)
- ใหม่: การ์ด "📄 เอกสารในกลุ่ม" ในจอ RAG — เลือกกลุ่ม → ตารางเอกสาร (หัวข้อ/ชนิด/chunks/วันนำเข้า) + ปุ่มลบรายชิ้น (confirm ก่อน)
- Flow: `api/sources.php` → `api-ragmeta` ops `listsources`/`deletesource` (SQL 1 statement, scope ด้วย group_id กันลบข้ามกลุ่ม) • ลบ source → chunks หายตาม CASCADE • ถ้ามีรูป local (`uploads/rag_*`) เก็บไฟล์ให้ด้วย (URL นอกไม่แตะ)
- ทดสอบ: สร้าง source+chunks ทดสอบ → list เจอ → ลบหายเกลี้ยง • ลบผิดกลุ่ม = deleted:false ของเดิมไม่กระทบ • ไฟล์รูป test โดน unlink จริง • `difftest.py` ALL PASS • PHP lint ผ่าน

## รูปภาพ: ingest เหลือ URL public + LINE ส่งรูปได้ (27 ก.ย.)

- นำเข้ารูปเหลือ **URL public HTTPS อย่างเดียว** (เอาช่องอัปโหลดไฟล์ออก) — PHP ตรวจ `^https://` ก่อนส่ง • n8n ดาวน์โหลดเองแล้ว OCR ตาม `ocr.engine` • แลกกับ OCR รูปถ่ายจากเครื่องทำไม่ได้ (PDF ยังแนบไฟล์ได้ปกติ)
- **LINE แสดงรูปได้แล้ว**: `Attach RAG` ส่ง `rag_images` ต่อ → `Build Reply` กรองเหลือ https ล้วน (ตัด local uploads ทิ้ง) dedupe cap 4 → `Push LINE` ส่ง text + image message (`originalContentUrl`+`previewImageUrl`, รวม ≤5) • เส้น fallback `Send LINE` แปะ URL ต่อท้ายข้อความ (LINE unfurl เป็น preview)
- หมายเหตุ: รูป local เดิม (`http://127.0.0.1:8081/...`) ยังแสดงในแชทเว็บได้ แต่ LINE ดึงไม่ได้ — อยากให้ขึ้น LINE ด้วยต้องเปิด uploads ผ่าน tunnel (ยังไม่ทำ)
- ทดสอบ: ingest `thai.jpg` ผ่าน URL เต็มเส้น (OCR "เส้นทางลัด เพชรบุรี" → 1 chunk, image_url=https) • จำลองแชท LINE ถาม → `rag-answer` คืน images[] → logic เดียวกับ production ยิง httpbin ยืนยัน payload `text+image` ถูกต้อง • push จริงสำเร็จ (LINE รับ) • ลบ source ทดสอบแล้ว • `difftest.py` ALL PASS • workflow ทดสอบชั่วคราวลบแล้ว

## เปลี่ยนชื่อระบบเป็น OmniDesk + โลโก้ (27 ก.ย.)

- ชื่อระบบ `ChatDesk (Local)` → `OmniDesk (Local)` (config `APP_TITLE`, env override ได้) • โลโก้ SVG 2 ไฟล์ใน `chatdesk/assets/` (`omnidesk-logo.svg` แนวนอน + `omnidesk-icon.svg` ไอคอน/favicon)
- ติดแล้ว: หน้า login (โลโก้ใหญ่), topbar ทุกหน้า, หัวข้อจอ RAG/AI Setting/จัดการผู้ใช้, favicon ทุกหน้า • PHP lint ผ่าน + curl ยืนยัน markup ครบ

## TripThai ใช้โรงแรมจริง + รูปสถานที่จริง (27 ก.ย.)

- เปลี่ยน `HOTELS` ใน `app.js` จากชื่อจำลอง 12 แห่ง → โรงแรมจริง (Siam Kempinski, U Nimman, Amari Phuket, Centara Mirage, ShellSea, Centara Hua Hin, Banyan Tree Samui, Le Patta, Mandarin Oriental, Memory at On On, Hilton Pattaya, Four Seasons) — ทำเล/ดาว/ราคาเริ่มต้น/คะแนนรีวิวค้นจากเว็บจอง (KAYAK/HotelsCombined/OTA ก.ย. 2026)
- รูปทั้ง 12 เป็น Wikimedia Commons (verify HTTP 200 + เปิดเป็น JPEG ได้ครบทุกรูป) — เน้นรูปตัวโรงแรม, ที่เหลือเป็นแลนด์มาร์กใกล้เคียง (สยาม/ป่าตอง/ถนนถลาง/หอนาฬิกา/เจ้าพระยา/ทุ่งนาแม่ริม)
- ซื่อสัตย์กับผู้ใช้: footer มี disclaimer "ราคา/คะแนนอ้างอิงโดยประมาณ + รูปจาก Wikimedia" • แก้ข้อความบอท 590→1,400 / 5,900→21,500 ทั้ง `app.js` และ `GEM_SYS` (deploy ai-chat ใหม่แล้ว)
- ไฟล์ RAG `TripThai-hotels-RAG.txt` (Desktop) regen ใหม่แล้ว 7,758 ตัวอักษร — นำเข้าใหม่ทับของเดิมได้เลย (ลบ source เก่าก่อนกันซ้ำ)

## รูปโรงแรม 12 รูปเข้า tourism + คำบรรยายติด embedding (27 ก.ย.) [กลุ่ม tourism ถูกลบแล้ว 28/9/68 — บันทึกไว้เป็นประวัติ]

- ปัญหา: URL ใน text ธรรมดาไม่เข้า `images[]` (UI/LINE อ่านจาก metadata เท่านั้น) → ingest รูปทั้ง 12 เป็น source ชนิด image ในกลุ่ม tourism (title=ชื่อโรงแรม, image_url=https) พร้อมคำบรรยายไทย
- แก้ flow รองรับ: `Shape Local OCR` + `Set OCR Text` เอาคำบรรยาย (caption) ต่อหน้าผล OCR — รูปวิวไม่มีตัวหนังสือก็ embed ได้ • `ocrapi` เลิก 422 เมื่อ OCR ว่าง (คืนข้อความว่างให้ caption ทำงาน) — rebuild + restart แล้ว
- ทดสอบ: 12/12 สำเร็จ (5 รอบแรก + 7 รอบหลังแก้) • ถาม "แนะนำโรงแรมหรูริมน้ำ" ได้ images[] 2 รูป (เจ้าพระยา+เคมปินสกี้) → ขึ้นทั้งแชทเว็บและ LINE • `difftest.py` ALL PASS

## Memory บทสนทนาฝั่ง server (27 ก.ย.)

- ปัญหา: สาขา qwen (`llm.qa=qwen3:4b` ที่ใช้อยู่) ไร้ memory — gemini มี agent memory อยู่แล้ว • TripThai มี history ฝั่ง browser, LINE มี session แต่ใช้ไม่ได้เมื่อเป็น qwen
- ทำ: สาขา qwen อ่าน/เขียนตาราง `n8n_chat_histories` เดียวกับ agent (format เดียวกัน สลับ engine ไม่เสียบริบท) — โหนด `Build Mem Read`→`Read Mem History` (SELECT ประวัติ 10 แถวล่าสุด, aggregate กันเคส session ใหม่ 0 แถว) → `Build Ollama RAG` แนบ "ประวัติการสนทนาก่อนหน้า" → ตอบ → `Build Mem Save`+`Save Mem Turn` (INSERT 2 แถว human/ai + ตัดเหลือ 60 แถว/session กันบวม, CTE 1 statement) → `Pass Answer` ส่งคำตอบต่อให้ `Guard Empty`
- กับดักที่เจอ: PG คืน 0 แถว = โหนดถัดไปไม่รัน เงียบ ๆ (execution success แต่ Respond ไม่ทำงาน) — memread ใช้ `COALESCE(json_agg...)` คืน 1 แถวเสมอ, memsave ใช้ `SELECT COUNT` คืน 1 แถวเสมอ
- จอทดสอบ (`ask.php`) ส่ง session คงที่ต่อ browser (`web-+session_id`) แทนสุ่มใหม่ทุกครั้ง — LINE ได้อัตโนมัติผ่าน session `channel:userId`
- ทดสอบ: 2 เทิร์น (ถามแมนดาริน→"แล้วราคาเท่าไหร่") เทิร์น 2 อ้างโรงแรมเดิมถูก = จำบริบทได้ • แถว compact (คำถาม+คำตอบ ไม่ยัด context ซ้ำแบบ agent) • ลบ session ทดสอบแล้ว • `difftest.py` ALL PASS

## แชท TripThai พิมพ์ข้อความโชว์รูปได้ (27 ก.ย.)

- ปัญหา: แชทพิมพ์ใช้ "สมองเดิม" ใน browser (engine ใช้เฉพาะสั่งเสียง) — สมองเดิมมี URL รูปแต่ไม่เคยแปะ → ขอภาพแล้วได้แต่ข้อความ
- แก้ `tripthai/app.js` 2 จุด: ผลค้นหาที่พักแนบรูป top-3 + หน้าถามรายโรงแรม (`askHotel`) แปะรูป (สไตล์เดียวกับ `voiceAttachMedia`)
- ทดสอบ: `node --check` ผ่าน • จำลองเคสผู้ใช้ ("พัทยา" → Hilton top) ได้ `<img>` 2 รูป https ครบ • ไม่แตะเส้น engine

## ShopDee E-Commerce (27 ก.ย.)

- เว็บใหม่ `local/www/shopdee/` (ธีมส้มล้อ Shopee): หน้าแรก + หมวด 10 หมวด + ค้นหา/เรียง + หน้ารายละเอียด + ตะกร้า (localStorage) + ชำระเงิน + เช็คพัสดุด้วยเบอร์ + แชทบอท (ข้อความ/เสียง) — `http://127.0.0.1:8081/shopdee/`
- DB `shopdee` (Postgres postgres-rag): `shop_products` 100 รายการ (10 หมวด) + `shop_orders`/`shop_order_items` • migration `08_shopdee.sql` + seed script • ตะกร้า: ส่งฟรีครบ 299 (ต่ำกว่าค่าส่ง 35) + คูปอง SHOPDEE50 (-50 เมื่อครบ 500) • ราคาอ่านจาก DB ใหม่ทุกครั้ง + ตัดสต็อกใน transaction
- API: `products.php` (list/search/get/cats) • `order.php` (create/get/byphone) • `chat.php` (→ n8n ai-chat **group 5 Shop** + persona นักขาย) • เสียง reuse `tripthai/stt.php+tts.php` ตรง (userId แบบ WEB_ เดียวกัน)
- ช่องทาง: `channel_map` เพิ่ม `shopweb` (ShopDee Web → group 5) • แชท forward เข้า inbox ช่อง shopweb • `webthread.php`+api-06 รับ `?channel=` (web|shopweb, default web) + PG nodes `alwaysOutputData` (แขกใหม่ได้ JSON ปกติ ไม่ใช่ 200 ว่าง — flag อยู่ระดับ node ไม่ใช่ parameters)
- RAG กลุ่ม Shop: แคตตาล็อกข้อความ 43 chunks + รูปสินค้าขายดี 20 รูป (caption ชื่อ+ราคา) — แชทบอทตอบพร้อมรูปได้
- ทดสอบ: สั่งซื้อ+คูปอง (ยอดตรง สต็อกตัด) • แชทถามหูฟังตอบจาก RAG พร้อมรูป • forward/webthread shopweb • `difftest.py` ALL PASS • PHP lint + `node --check` ผ่าน

## ShopDee Text-to-SQL Both mode (28 ก.ย.)

- ปัญหา: บอทตอบราคาตลาดมั่ว (เช่น จอ 27" ตอบ 12,000-35,000 ทั้งที่ DB ขาย 2,819) และ RAG ผสมสินค้าผิดตัว (SD-0010 ราคา 12,209 ปนกับ SD-0012) เพราะค้นเจอหลายตัวแล้ว LLM เบลนด์เอง
- กฎสถาปัตย์: **การค้นข้อมูล (Vector + Structured) ทำใน n8n ที่เป็น API เท่านั้น ห้าม query DB จากโค้ดฝั่งเว็บตรง** — `shopdee/api/chat.php` เป็น proxy เรียก `api-ai-chat` + `api-shop-sql` แล้วรวมคำตอบ
- ทำ workflow ใหม่ **`ChatDesk API-12 Shop SQL`** (`local/n8n/api-12-shopsql.json`, webhook `api-shop-sql`): Prep → Route SQL (กฎ intent) → IF → Build Template SQL (รหัสออเดอร์/เบอร์โทร/ค้นสินค้า+งบ+คำพ้อง) → Validate (SELECT อย่างเดียว, allowlist 3 ตาราง, ออเดอร์ต้องมี code/phone, สินค้าต้องมี is_active, LIMIT≤50, whole-word) → IF → Run Shop SQL (credential `ai_reader` read-only + statement_timeout 10s) → Shape (mask เบอร์/ที่อยู่, ตอบ lookup แบบ deterministic กันเบลนด์) → Save SQL Audit → Respond (โหนด PG เปิด `alwaysOutputData` เสมอ กัน 0 แถวแล้ว downstream อด)
- `chat.php` รวมคำตอบ: lookup → ตอบ deterministic จาก SQL อย่างเดียว (ตัด RAG prose กันปน), both → เสริมบล็อกข้อมูลสดให้ LLM + ต่อท้ายเส้น rag, rag-only → เดิม
- บทเรียน n8n: (1) PATCH อัปเดตแค่ draft — publish ด้วย `POST /rest/workflows/:id/activate {versionId}` แล้วเช็ค `activeVersion` (2) Code node syntax ผิด = 500 "No Respond to Webhook" (3) PG INSERT ไม่มี RETURNING = 0 items ทำ Respond อด (4) ห้ามฝังข้อความไทยในพารามิเตอร์โหนด (5) validator ตรวจ whole-word กัน `created_at` โดนจับเป็น CREATE (6) `trim()` ห้ามใส่ multibyte ใน mask
- ทดสอบ: จอ 27" ตอบ 2,819 ตรง DB ไม่ปน • สต็อก 306 • สถานะออเดอร์ pending • แนะนำตามงบ • injection/DUMP ปลอดภัย (ตารางครบ 100) • audit ลง `ai_sql_audit` • `difftest.py` ALL PASS

## แชทพิมพ์ TripThai ใช้ engine เส้นเดียวกับเสียง (27 ก.ย.)

- ปัญหา: แชทพิมพ์เรียกแต่สมองเดิม (ไม่แตะ RAG/memory) ส่วนเสียงใช้ engine — คำตอบคนละชั้น
- แก้ `tripthai/app.js`: `sendChat` → `textTurn` → `voiceTurn(t, noContinue=true)` เส้นเดียวกับเสียง (RAG+รูป+ที่มา+memory) • `voiceTurn` รับ flag ไม่เปิดไมค์ต่อทั้งเคสสำเร็จและ fallback • engine ล่ม fallback สมองเดิมอัตโนมัติ (ของเดิมใน voiceTurn) • ปุ่มลัดยังตอบทันทีแบบเดิม
- หมายเหตุ: ปุ่มลำโพง (spkOn) คุมเสียงตอบ — เปิดอยู่พิมพ์ถามก็มีเสียงอ่าน, ปิดก็เงียบ
- ทดสอบ: `node --check` ผ่าน • ไฟล์เสิร์ฟมีครบ (`textTurn`, route ใหม่, `noContinue` 2 จุด)
