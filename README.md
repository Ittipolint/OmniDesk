# OmniDesk — ระบบรวมแชทหลายช่องทาง + AI (RAG + Text-to-SQL)

OmniDesk คือระบบ **Omnichannel Inbox + AI Chatbot** ที่รันบนเครื่อง local (Docker)
รวมข้อความจาก **LINE OA, Facebook Messenger, เว็บไซต์ร้าน/บริษัท** ไว้ในกล่องเดียว
พนักงานตอบได้จากที่เดียว บอท AI ตอบอัตโนมัติจากฐานความรู้ (RAG) และข้อมูลร้านแบบ
structured (Text-to-SQL) พร้อมรูปภาพประกอบ

```
LINE OA ──┐
FB Page ──┼──▶ Cloudflare Tunnel ─▶ n8n (:5678, API Engine) ─┬─ RAG (Postgres + pgvector)
ShopDee ──┤                                                   ├─ Shop SQL (Text-to-SQL)
IntelTech ┘                                                   ├─ Gemini / Ollama (LLM)
                                                              └─ LINE/FB Push API
พนักงาน ◀── OmniDesk Inbox (:8081/chatdesk/) ◀── n8n (api-read/api-receive/api-send)
```

> รายละเอียดเชิงเทคนิคทั้งหมดดูที่ [`Technical-Spec.md`](Technical-Spec.md)
> บันทึกการพัฒนารายวัน (dev journal) ดูที่ [`local/README.md`](local/README.md)

## ส่วนประกอบ

| ส่วน | ที่อยู่ | หน้าที่ |
|---|---|---|
| ShopDee (เว็บร้าน) | `local/www/shopdee/` → `:8081/shopdee/` | หน้าร้าน 100 สินค้า, ตะกร้า, สั่งซื้อ, แชทบอทขายของ |
| IntelTech (เว็บบริษัท) | `local/www/inteltech/` → `:8081/inteltech/` | เว็บองค์กร + แชทบอท (RAG-only) |
| OmniDesk (inbox พนักงาน) | `local/www/chatdesk/` → `:8081/chatdesk/` | กล่องรวมแชท, จัดการ RAG/ผู้ใช้/ช่องทาง (ต้อง login) |
| TripThai (เว็บเดิม) | `local/www/tripthai/` | เว็บท่องเที่ยว + เสียง (คงไว้เพื่อ reuse STT/TTS) |
| n8n workflows | `local/n8n/*.json` (21 ไฟล์) | API Engine กลาง: สมอง AI, รับ/ส่งทุกช่องทาง |
| SQL migrations | `local/sql/*.sql` | schema + seed (รันตามเลข 01→14) |
| Odoo connector | `local/odoo/` | CRM bridge (รับ Lead/Order, ส่งข้อความจาก Lead) — **พักงานชั่วคราว** |
| PHP runtime | `local/php/Dockerfile` | php:8.3-apache + pdo_pgsql |
| Tunnels | `local/docker-compose.yml` + `regen-tunnels.ps1` | Cloudflare quick tunnel (n8n + web) |

### ช่องทาง (channels) และกลุ่มความรู้ (RAG groups)

| channel | ใช้ที่ไหน | RAG groups |
|---|---|---|
| `line` | LINE OA (ChatDesk) | itil-concept |
| `shopweb` | ShopDee Web | ShopDee-Profile (+ Shop SQL) |
| `intelweb` | IntelTech Web | IntelTech-Profile / inteltech-data (RAG-only) |
| `fbchat` | FacebookChat (เพจ OmniDesk) | itil-concept + ShopDee-Profile |

1 channel ผูกได้ N groups (`channel_rag_groups`) + น้ำเสียงบอทรายช่อง (`persona_system`)
ดู/แก้ได้ในจอ RAG → tab ช่องทาง (ADMIN)

## เริ่มใช้งาน (Quickstart)

### 1. สิ่งที่ต้องมี
- Docker Desktop + Postgres (service ชื่อ `postgres-rag`, มี extension `vector` + `pg_trgm`)
- n8n local ที่ `http://127.0.0.1:5678` (import workflows จาก `local/n8n/*.json`)
- โปรเจกต์นี้วางที่เครื่องแล้วสั่งจากโฟลเดอร์ `local\`

### 2. รันเว็บ + tunnel
```powershell
& 'C:\Users\pol\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe' compose -f .\docker-compose.yml up -d
```
- เว็บ: http://127.0.0.1:8081/{shopdee,inteltech,chatdesk,tripthai}/
- ถ้า tunnel หมดอายุ (~20 ชม.) รัน `local\regen-tunnels.ps1` แล้วอัปเดต Webhook URL
  ใน LINE Developers / Meta App Dashboard ตาม (ดู `local/README.md` หัวข้อ Tunnel)

### 3. ฐานข้อมูล (รันตามลำดับ)
```bash
psql -h localhost -U raguser -d chatdesk -f 01_chatdesk_pg.sql
# ... 02_msg_function, 03_voice_settings, 04_channels, 05_ai_settings,
#     06_ai_ocr, 07_gemini_key, 10_shop_sql_audit, 12_channel_admin,
#     13_channel_groups, 14_channel_save
psql -h localhost -U raguser -d shopdee -f 08_shopdee.sql
psql -h localhost -U raguser -d shopdee -f seed_products.sql
psql -h localhost -U raguser -d shopdee -f 11_product_images.sql
php seed_admin.php   # สร้าง admin (ดูรหัสใน local/README.md)
```

### 4. ใส่ secrets (ไม่มีค่า default ใน repo — ไฟล์จริงถูก gitignore)
| Secret | ใส่ที่ไหน |
|---|---|
| LINE Channel access token (ราย OA) | จอ RAG → tab ช่องทาง (หรือ credential `lineMessagingApi` ใน n8n) |
| FB Page access token | Meta → Messenger settings → Generate Token → ใส่ใน n8n credential `ChatDesk FB Page Token`; ถ้าใช้ poller ให้แทน `__FB_PAGE_TOKEN__` ใน `chatdesk-fb-poller.json` ก่อน import |
| Gemini API key | OmniDesk → ⚙️ AI Setting → แถว Gemini API Key |
| Odoo shared token | env `CHATDESK_ODOO_TOKEN` (ต้องตรงกับที่ n8n `api-13/14` ส่ง; ในไฟล์ export เป็น `__ODOO_SHARED_TOKEN__`) |
| Odoo/Postgres passwords | `local/odoo/config/odoo.conf` (copy จาก `odoo.conf.example`) |

Login เริ่มต้นหลัง seed: `admin` / ดูรหัสใน `local/README.md` (มี STAFF ตัวอย่าง `staff1`)
**เปลี่ยนรหัสทุกตัวเมื่อขึ้นใช้งานจริง**

## สถานะและข้อจำกัดที่รู้แล้ว (tin/2026-10-02)

1. **FB webhook ไม่ส่ง event มา** (Meta ต่อ callback ติด, verify ผ่าน, `messages` subscribed
   แล้ว แต่ไม่มี event เข้าเลย) — ใช้ **`ChatDesk FB Poller`** ดึง inbox เพจทุก 1 นาทีแทน
   (ดีเลย์ ~1 นาที, ตอบจริงครบ) ถ้าวันไหน webhook ฟื้น ต้องระวังตอบซ้ำ (mid ซ้ำ)
2. **Tunnel ชั่วคราว** เปลี่ยน URL ทุก ~20 ชม. → อัปเดต `PUBLIC_WEB_BASE` ทุกครั้ง
   (`python3 local/n8n/update_public_base.py <url-web-ใหม่>`) ไม่งั้นรูปใน LINE หลุด
3. **LINE รับเฉพาะรูป `https://`** — รูป local ต้อง rewrite ผ่าน public web tunnel
4. **Odoo พักงานชั่วคราว** ตามคำสั่ง (โค้ดครบ แต่ไม่พัฒนาต่อจนกว่าจะสั่ง)
5. Token ในไฟล์ export ถูกแทนด้วย `__FB_PAGE_TOKEN__` / `__ODOO_SHARED_TOKEN__` แล้ว —
   import แล้วต้องกรอกค่าจริงเอง

## โครง repo

```
OmniDesk/
├── README.md                  # ไฟล์นี้
├── Technical-Spec.md          # สเปกเทคนิค
├── omnidesk-logo.svg / omnidesk-icon.svg
├── LINElogo.jpg / LINELOGO.png
└── local/
    ├── docker-compose.yml     # web + 2 tunnels
    ├── regen-tunnels.ps1
    ├── README.md              # dev journal (26 ก.ย.–2 ต.ค. 2026)
    ├── php/Dockerfile
    ├── sql/                   # 01–14 migrations + seeds
    ├── www/{chatdesk,shopdee,inteltech,tripthai}/
    ├── n8n/                   # 21 workflow exports + import/patch scripts
    └── odoo/                  # connector + compose (data/ ถูก ignore)
```
