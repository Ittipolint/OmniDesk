-- ChatDesk LOCAL — channel admin entry points (add/delete via SELECT wrapper).
-- เหตุผล: n8n postgres node คืน 0 แถวให้ INSERT/DELETE/CTE ที่มี mutation
-- ใช้ SELECT * FROM function(...) แทน (pattern เดียวกับ cd_msg_in ใน 02_msg_function.sql)
DROP FUNCTION IF EXISTS cd_channel_add(TEXT, TEXT, INTEGER, TEXT, TEXT, SMALLINT);
DROP FUNCTION IF EXISTS cd_channel_add(TEXT, TEXT, INTEGER, TEXT, TEXT, INTEGER);
CREATE FUNCTION cd_channel_add(
    p_code TEXT,
    p_label TEXT DEFAULT '',
    p_group INTEGER DEFAULT NULL,
    p_bot TEXT DEFAULT NULL,
    p_token TEXT DEFAULT '',
    p_active INTEGER DEFAULT 1
) RETURNS TABLE (added TEXT, err TEXT) AS $$
BEGIN
    IF p_code IS NULL OR p_code !~ '^[a-z0-9_]{2,32}$' THEN
        RETURN QUERY SELECT NULL::TEXT, 'bad code'::TEXT;
        RETURN;
    END IF;
    BEGIN
        INSERT INTO channel_map (channel_code, label, rag_group_id, line_bot_id, line_channel_token, is_active)
        VALUES (p_code, COALESCE(p_label, ''), p_group, NULLIF(p_bot, ''), COALESCE(p_token, ''), COALESCE(p_active, 1))
        RETURNING channel_map.channel_code INTO added;
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

CREATE OR REPLACE FUNCTION cd_channel_del(p_code TEXT)
RETURNS TABLE (deleted INTEGER) AS $$
DECLARE
    n INTEGER;
BEGIN
    DELETE FROM channel_map WHERE channel_code = p_code;
    GET DIAGNOSTICS n = ROW_COUNT;
    RETURN QUERY SELECT n;
END;
$$ LANGUAGE plpgsql;
