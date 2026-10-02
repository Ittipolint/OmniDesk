-- ChatDesk LOCAL — stored function: single entry point for ALL incoming messages (n8n api-receive).
-- Mirrors PHP cd_find_or_create_conversation + cd_save_message exactly.
CREATE OR REPLACE FUNCTION cd_msg_in(
    p_channel TEXT,
    p_userid TEXT,
    p_text TEXT,
    p_sender TEXT DEFAULT 'customer',
    p_display TEXT DEFAULT NULL,
    p_picture TEXT DEFAULT NULL,
    p_msgtype TEXT DEFAULT 'text',
    p_media_url TEXT DEFAULT NULL,
    p_media_preview TEXT DEFAULT NULL,
    p_sticker_pkg TEXT DEFAULT NULL,
    p_sticker_id TEXT DEFAULT NULL,
    p_external_id TEXT DEFAULT NULL
) RETURNS TABLE (
    conversation_id INTEGER,
    message_id INTEGER,
    duplicate BOOLEAN,
    bot_enabled BOOLEAN,
    display_name TEXT
) AS $$
#variable_conflict use_column
DECLARE
    v_conv_id INTEGER;
    v_bot SMALLINT;
    v_name TEXT;
    v_mid INTEGER;
    v_preview TEXT;
BEGIN
    IF p_userid IS NULL OR p_userid = '' THEN
        RAISE EXCEPTION 'missing userId';
    END IF;
    IF p_text IS NULL OR p_text = '' THEN
        RAISE EXCEPTION 'missing text';
    END IF;
    IF p_sender IS NULL OR p_sender NOT IN ('customer', 'bot', 'agent', 'system') THEN
        p_sender := 'customer';
    END IF;

    -- find or create conversation
    SELECT c.id INTO v_conv_id FROM cd_conversations c
     WHERE c.channel = p_channel AND c.external_user_id = p_userid LIMIT 1;
    IF NOT FOUND THEN
        INSERT INTO cd_conversations (channel, external_user_id, display_name, picture_url)
        VALUES (p_channel, p_userid, NULLIF(p_display, ''), NULLIF(p_picture, ''))
        RETURNING id INTO v_conv_id;
    ELSIF p_display IS NOT NULL AND p_display <> '' THEN
        UPDATE cd_conversations SET display_name = p_display, picture_url = p_picture
         WHERE id = v_conv_id AND (display_name IS NULL OR display_name <> p_display);
    END IF;

    -- dedupe by external id
    IF p_external_id IS NOT NULL AND p_external_id <> '' THEN
        PERFORM 1 FROM cd_messages WHERE external_message_id = p_external_id LIMIT 1;
        IF FOUND THEN
            SELECT c.bot_enabled, COALESCE(NULLIF(c.display_name, ''), 'ลูกค้า #' || c.id)
              INTO v_bot, v_name FROM cd_conversations c WHERE c.id = v_conv_id;
            RETURN QUERY SELECT v_conv_id, 0, TRUE, (v_bot = 1), v_name;
            RETURN;
        END IF;
    END IF;

    -- preview text (mirror PHP)
    IF p_msgtype = 'text' THEN
        v_preview := SUBSTRING(REGEXP_REPLACE(p_text, '\s+', ' ', 'g'), 1, 200);
    ELSE
        v_preview := CASE p_msgtype
            WHEN 'image' THEN '[ภาพ]' WHEN 'video' THEN '[วิดีโอ]'
            WHEN 'sticker' THEN '[สติกเกอร์]' WHEN 'audio' THEN '[เสียง]'
            WHEN 'file' THEN '[ไฟล์]' ELSE '[' || p_msgtype || ']' END;
    END IF;

    INSERT INTO cd_messages
        (conversation_id, sender, content, message_type, media_url, media_preview_url,
         sticker_package, sticker_id, external_message_id, status, delivered_at, created_at)
    VALUES (v_conv_id, p_sender, SUBSTRING(p_text, 1, 8000), p_msgtype,
            NULLIF(SUBSTRING(p_media_url, 1, 500), ''), NULLIF(SUBSTRING(p_media_preview, 1, 500), ''),
            NULLIF(SUBSTRING(p_sticker_pkg, 1, 50), ''), NULLIF(SUBSTRING(p_sticker_id, 1, 50), ''),
            NULLIF(p_external_id, ''), 'ok', NOW(), NOW())
    RETURNING id INTO v_mid;

    IF p_sender = 'customer' THEN
        UPDATE cd_conversations
           SET last_message_at = NOW(), last_message_text = v_preview,
               unread_count = unread_count + 1, status = 'open'
         WHERE id = v_conv_id;
    ELSE
        UPDATE cd_conversations
           SET last_message_at = NOW(), last_message_text = v_preview
         WHERE id = v_conv_id;
    END IF;

    SELECT c.bot_enabled, COALESCE(NULLIF(c.display_name, ''), 'ลูกค้า #' || c.id)
      INTO v_bot, v_name FROM cd_conversations c WHERE c.id = v_conv_id;
    RETURN QUERY SELECT v_conv_id, v_mid, FALSE, (v_bot = 1), v_name;
END;
$$ LANGUAGE plpgsql;
