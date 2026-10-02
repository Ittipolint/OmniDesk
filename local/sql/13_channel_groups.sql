-- ChatDesk LOCAL — 1 channel : N RAG groups + persona ผูกกับ channel
-- เฟส A (additive, ปลอดภัย): เพิ่มของใหม่ + backfill, ยังไม่ลบของเก่า
-- เฟส B อยู่ท้ายไฟล์ (รันหลัง import workflow ใหม่ครบแล้วเท่านั้น)
CREATE TABLE IF NOT EXISTS channel_rag_groups (
    channel_code TEXT NOT NULL REFERENCES channel_map (channel_code) ON DELETE CASCADE,
    group_id INTEGER NOT NULL REFERENCES rag_groups (id) ON DELETE CASCADE,
    PRIMARY KEY (channel_code, group_id)
);
-- ย้าย mapping เดิมมา (กันซ้ำถ้ารันซ้ำ)
INSERT INTO channel_rag_groups (channel_code, group_id)
SELECT channel_code, rag_group_id FROM channel_map WHERE rag_group_id IS NOT NULL
ON CONFLICT DO NOTHING;

ALTER TABLE channel_map ADD COLUMN IF NOT EXISTS persona_system TEXT NOT NULL DEFAULT '';
-- backfill น้ำเสียงจากกลุ่มเดิม (พฤติกรรมไม่เปลี่ยน)
UPDATE channel_map m SET persona_system = g.persona_system
  FROM rag_groups g WHERE g.id = m.rag_group_id AND COALESCE(g.persona_system, '') <> ''
  AND COALESCE(m.persona_system, '') = '';

-- ================= เฟส B (รันหลัง import workflow ใหม่ครบ) =================
ALTER TABLE channel_map DROP COLUMN IF EXISTS rag_group_id;
ALTER TABLE rag_groups DROP COLUMN IF EXISTS persona_system;
