-- ShopDee Text-to-SQL (Both mode RAG+SQL) — 28 ก.ย.
-- หมายเหตุ: audit log อยู่ DB chatdesk (n8n เขียนผ่าน credential ChatDesk Postgres)
-- ส่วน role ai_reader (read-only สำหรับ shop_* + statement_timeout) สร้างครั้งเดียวด้วย superuser:
--   CREATE ROLE ai_reader WITH LOGIN PASSWORD '<strong-password>';
--   ALTER ROLE ai_reader SET statement_timeout = '10s';
--   GRANT CONNECT ON DATABASE shopdee TO ai_reader;
--   (ใน shopdee) GRANT USAGE ON SCHEMA public TO ai_reader;
--   (ใน shopdee) GRANT SELECT ON shop_products, shop_orders, shop_order_items TO ai_reader;
CREATE TABLE IF NOT EXISTS ai_sql_audit (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    channel TEXT NOT NULL DEFAULT 'shop',
    user_ref TEXT NOT NULL DEFAULT '',
    question TEXT NOT NULL DEFAULT '',
    route TEXT NOT NULL DEFAULT '',
    sql TEXT NOT NULL DEFAULT '',
    rows INT NOT NULL DEFAULT 0,
    ms INT NOT NULL DEFAULT 0,
    ok BOOLEAN NOT NULL DEFAULT FALSE,
    err TEXT NOT NULL DEFAULT ''
);
-- รันไฟล์นี้กับ DB chatdesk (n8n api-shop-sql เขียน audit ผ่าน credential ChatDesk Postgres)
