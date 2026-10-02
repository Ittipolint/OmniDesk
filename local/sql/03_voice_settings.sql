-- ChatDesk LOCAL — app settings (key/value) for engine-driven config.
-- Used by: voice.llm_model (gemini | qwen3:4b) — read by api-ai-chat + LINE on every call.
CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT '',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
INSERT INTO app_settings (key, value) VALUES ('voice.llm_model', 'gemini')
ON CONFLICT (key) DO NOTHING;
