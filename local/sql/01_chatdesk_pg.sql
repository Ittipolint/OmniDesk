-- ChatDesk local (Postgres) — converted from MySQL + users/groups + RAG tables
-- Run: psql -h localhost -U raguser -d chatdesk -f 01_chatdesk_pg.sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============ ChatDesk core (converted) ============
CREATE TABLE IF NOT EXISTS cd_conversations (
  id SERIAL PRIMARY KEY,
  channel TEXT NOT NULL DEFAULT 'line',
  external_user_id TEXT NOT NULL,
  display_name TEXT,
  picture_url TEXT,
  status TEXT NOT NULL DEFAULT 'open',
  bot_enabled SMALLINT NOT NULL DEFAULT 1,
  unread_count INTEGER NOT NULL DEFAULT 0,
  last_message_at TIMESTAMPTZ,
  last_message_text TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (channel, external_user_id)
);
CREATE INDEX IF NOT EXISTS idx_conv_status_time ON cd_conversations (status, last_message_at DESC);

CREATE TABLE IF NOT EXISTS cd_messages (
  id SERIAL PRIMARY KEY,
  conversation_id INTEGER NOT NULL REFERENCES cd_conversations(id) ON DELETE CASCADE,
  sender TEXT NOT NULL DEFAULT 'customer',
  content TEXT NOT NULL DEFAULT '',
  message_type TEXT NOT NULL DEFAULT 'text',
  media_url TEXT,
  media_preview_url TEXT,
  sticker_package TEXT,
  sticker_id TEXT,
  external_message_id TEXT UNIQUE,
  status TEXT NOT NULL DEFAULT 'ok',
  error_message TEXT,
  raw TEXT,
  delivered_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  read_at TIMESTAMPTZ,
  deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_msg_conv ON cd_messages (conversation_id, id);
CREATE INDEX IF NOT EXISTS idx_msg_ext ON cd_messages (external_message_id);

-- ============ Users & groups ============
CREATE TABLE IF NOT EXISTS cd_groups (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS cd_users (
  id SERIAL PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  pass_hash TEXT NOT NULL,
  display_name TEXT NOT NULL DEFAULT '',
  is_active SMALLINT NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS cd_user_groups (
  user_id INTEGER NOT NULL REFERENCES cd_users(id) ON DELETE CASCADE,
  group_id INTEGER NOT NULL REFERENCES cd_groups(id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, group_id)
);

-- ============ RAG ============
CREATE TABLE IF NOT EXISTS rag_groups (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS rag_sources (
  id SERIAL PRIMARY KEY,
  group_id INTEGER NOT NULL REFERENCES rag_groups(id) ON DELETE CASCADE,
  source_type TEXT NOT NULL DEFAULT 'text',
  title TEXT NOT NULL DEFAULT '',
  source_ref TEXT NOT NULL DEFAULT '',
  image_url TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_rag_src_group ON rag_sources (group_id);
CREATE TABLE IF NOT EXISTS rag_chunks (
  id SERIAL PRIMARY KEY,
  source_id INTEGER REFERENCES rag_sources(id) ON DELETE CASCADE,
  group_id INTEGER NOT NULL,
  chunk_no INTEGER NOT NULL DEFAULT 0,
  content TEXT NOT NULL,
  embedding vector(768),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_group ON rag_chunks (group_id);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_embedding
  ON rag_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_meta_group
  ON rag_chunks (((metadata->>'group_id')::int));

-- ============ Seeds ============
INSERT INTO cd_groups (name, description) VALUES
  ('ADMIN', 'ผู้ดูแลระบบ — เข้าเมนูจัดการผู้ใช้และ RAG ได้'),
  ('STAFF', 'พนักงานตอบแชท')
ON CONFLICT (name) DO NOTHING;
INSERT INTO rag_groups (name, description) VALUES
  ('itil-concept', 'กลุ่มข้อมูลภายในองค์กร'),
  ('ShopDee-Profile', 'กลุ่มข้อมูลสาธารณะ')
ON CONFLICT (name) DO NOTHING;
-- NOTE: admin user seeded by seed_admin.php (bcrypt via PHP), not here.
