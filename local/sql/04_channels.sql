-- ChatDesk LOCAL — per-channel RAG routing (1 channel : N RAG groups, persona ผูกกับ channel).
-- ดู junction + backfill ใน 13_channel_groups.sql, add/set ผ่าน cd_channel_add/set ใน 14_channel_save.sql
CREATE TABLE IF NOT EXISTS channel_map (
    channel_code TEXT PRIMARY KEY,
    label TEXT NOT NULL DEFAULT '',
    line_bot_id TEXT UNIQUE,
    line_channel_token TEXT NOT NULL DEFAULT '',
    is_active SMALLINT NOT NULL DEFAULT 1,
    persona_system TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS channel_rag_groups (
    channel_code TEXT NOT NULL REFERENCES channel_map (channel_code) ON DELETE CASCADE,
    group_id INTEGER NOT NULL REFERENCES rag_groups (id) ON DELETE CASCADE,
    PRIMARY KEY (channel_code, group_id)
);

-- knowledge groups (ว่างก่อน ingest ภายหลัง)
INSERT INTO rag_groups (name, description) VALUES
    ('itil-concept', 'กลุ่มข้อมูลภายในองค์กร'),
    ('ShopDee-Profile', 'กลุ่มข้อมูลสาธารณะ')
ON CONFLICT (name) DO NOTHING;

-- channels (token เติมภายหลัง; fallback code 'line' รับทุก destination ที่ยังไม่ผูก)
INSERT INTO channel_map (channel_code, label, line_bot_id, line_channel_token, is_active) VALUES
    ('line', 'ChatDesk', NULL, '', 1),
    ('shopweb', 'ShopDee Web', NULL, '', 1)
ON CONFLICT (channel_code) DO NOTHING;
INSERT INTO channel_rag_groups (channel_code, group_id)
SELECT 'line', id FROM rag_groups WHERE name = 'itil-concept'
UNION ALL SELECT 'shopweb', id FROM rag_groups WHERE name = 'ShopDee-Profile'
ON CONFLICT DO NOTHING;
