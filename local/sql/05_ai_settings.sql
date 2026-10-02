-- ChatDesk LOCAL — per-activity AI settings (05).
-- llm.qa: answering brain (gemini | qwen3:4b) — RAG agent, ai-chat, LINE agent
-- tts.engine: auto | neural | piper
-- voice.llm_model: legacy alias (kept, llm.qa wins)
INSERT INTO app_settings (key, value)
SELECT 'llm.qa', COALESCE((SELECT value FROM app_settings WHERE key = 'voice.llm_model'), 'gemini')
WHERE NOT EXISTS (SELECT 1 FROM app_settings WHERE key = 'llm.qa');
INSERT INTO app_settings (key, value) VALUES ('tts.engine', 'auto')
ON CONFLICT (key) DO NOTHING;
