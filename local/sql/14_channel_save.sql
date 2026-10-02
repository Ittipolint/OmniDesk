-- ChatDesk LOCAL — channel add/set via SELECT wrapper (functions return rows; n8n pg node friendly)
DROP FUNCTION IF EXISTS cd_channel_add(TEXT, TEXT, INTEGER, TEXT, TEXT, SMALLINT);
DROP FUNCTION IF EXISTS cd_channel_add(TEXT, TEXT, INTEGER, TEXT, TEXT, INTEGER);
CREATE FUNCTION cd_channel_add(
    p_code TEXT,
    p_label TEXT DEFAULT '',
    p_groups INT[] DEFAULT '{}',
    p_bot TEXT DEFAULT NULL,
    p_token TEXT DEFAULT '',
    p_active INTEGER DEFAULT 1,
    p_persona TEXT DEFAULT ''
) RETURNS TABLE (added TEXT, err TEXT) AS $$
BEGIN
    IF p_code IS NULL OR p_code !~ '^[a-z0-9_]{2,32}$' THEN
        RETURN QUERY SELECT NULL::TEXT, 'bad code'::TEXT;
        RETURN;
    END IF;
    BEGIN
        INSERT INTO channel_map (channel_code, label, line_bot_id, line_channel_token, is_active, persona_system)
        VALUES (p_code, COALESCE(p_label, ''), NULLIF(p_bot, ''), COALESCE(p_token, ''), COALESCE(p_active, 1), COALESCE(p_persona, ''))
        RETURNING channel_map.channel_code INTO added;
        INSERT INTO channel_rag_groups (channel_code, group_id)
        SELECT added, unnest(COALESCE(p_groups, '{}')) ON CONFLICT DO NOTHING;
        err := NULL;
        RETURN NEXT;
    EXCEPTION
        WHEN unique_violation THEN
            RETURN QUERY SELECT NULL::TEXT, 'code หรือ LINE bot ซ้ำกับช่องทางอื่น'::TEXT;
        WHEN foreign_key_violation THEN
            RETURN QUERY SELECT NULL::TEXT, 'RAG group ไม่ถูกต้อง'::TEXT;
    END;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION cd_channel_set(
    p_code TEXT,
    p_label TEXT DEFAULT NULL,
    p_groups INT[] DEFAULT NULL,
    p_bot TEXT DEFAULT NULL,
    p_token TEXT DEFAULT NULL,
    p_active INTEGER DEFAULT NULL,
    p_persona TEXT DEFAULT NULL
) RETURNS TABLE (updated INTEGER) AS $$
DECLARE
    n INTEGER := 0;
BEGIN
    UPDATE channel_map SET
        label = COALESCE(p_label, label),
        line_bot_id = CASE WHEN p_bot IS NULL THEN line_bot_id WHEN p_bot = '' THEN NULL ELSE p_bot END,
        line_channel_token = COALESCE(p_token, line_channel_token),
        is_active = COALESCE(p_active, is_active),
        persona_system = COALESCE(p_persona, persona_system)
    WHERE channel_code = p_code;
    GET DIAGNOSTICS n = ROW_COUNT;
    IF n > 0 AND p_groups IS NOT NULL THEN
        DELETE FROM channel_rag_groups WHERE channel_code = p_code;
        INSERT INTO channel_rag_groups (channel_code, group_id)
        SELECT p_code, unnest(p_groups)
        ON CONFLICT DO NOTHING;
    END IF;
    RETURN QUERY SELECT n;
END;
$$ LANGUAGE plpgsql;
