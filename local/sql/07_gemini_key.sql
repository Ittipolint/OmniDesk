-- ChatDesk LOCAL — Gemini API key rotation (07).
-- gemini.api_key: single source of truth for all Gemini HTTP calls (OCR/embed/query/ai-chat direct).
--   Seed = key เดิมที่ฝังใน generator (valid — probe ตรง Google ได้ 429 ไม่ใช่ 400).
-- n8n.api_key: Personal API key (scopes credential:update+read, label chatdesk-key-rotation)
--   ให้ workflow api-10 ใช้ PATCH credential Google Gemini ผ่าน n8n Public API.
--   คีย์นี้ห้ามโชว์ใน UI เด็ดขาด (api-10 op=get ไม่ดึงออกมา).
INSERT INTO app_settings (key, value) VALUES ('gemini.api_key', '__GEMINI_API_KEY__')
ON CONFLICT (key) DO NOTHING;
INSERT INTO app_settings (key, value) VALUES ('n8n.api_key', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0Y2U5NTNmZC03NmFhLTQxMzktYmM5Ny01MDA3NGQ2Y2MzZmMiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiNDY5M2NlZWEtYTVmZS00MmRlLTkwYzktODg0Yjc4MmJkYTY3IiwiaWF0IjoxNzkwNDc0ODU1LCJleHAiOjQxMDI0NDQ4MDAwMDB9.lFhQrJPT0VXXkRzfZnWWRoeKWoQgghFEYHzaaNwlJRQ')
ON CONFLICT (key) DO NOTHING;
