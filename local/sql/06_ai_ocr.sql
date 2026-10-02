-- ChatDesk LOCAL — OCR engine setting (06).
-- ocr.engine: gemini | easyocr (default gemini = current behavior)
INSERT INTO app_settings (key, value) VALUES ('ocr.engine', 'gemini')
ON CONFLICT (key) DO NOTHING;
