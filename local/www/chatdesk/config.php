<?php
/**
 * ChatDesk LOCAL — ไฟล์ตั้งค่าหลัก (รันใน Docker เครื่องนี้)
 * ค่า DB ชี้ Postgres (database `chatdesk`), n8n ชี้ local ผ่าน tunnel/โฮสต์
 */

if (!function_exists('cd_env')) {
    function cd_env($key, $default)
    {
        $v = getenv($key);
        if ($v === false || $v === '') {
            return $default;
        }
        if (is_bool($default)) {
            return in_array(strtolower($v), array('1', 'true', 'yes', 'on'), true);
        }
        if (is_int($default)) {
            return (int) $v;
        }
        return $v;
    }
}

return array(

    /* 1) Postgres (local container postgres-rag, database `chatdesk`) */
    'db' => array(
        'driver'  => cd_env('DB_DRIVER', 'pgsql'),
        'host'    => cd_env('DB_HOST', 'host.docker.internal'),
        'port'    => cd_env('DB_PORT', 5432),
        'name'    => cd_env('DB_NAME', 'chatdesk'),
        'user'    => cd_env('DB_USER', 'raguser'),
        'pass'    => cd_env('DB_PASS', 'ragpass123'),
        'charset' => 'utf8',
    ),

    /* 2) n8n local (เรียกผ่าน tunnel สาธารณะหรือโฮสต์ภายใน) */
    'n8n' => array(
        // URL ของ webhook ที่ใช้ "ส่งข้อความออกไปหาลูกค้าทาง LINE" (workflow ChatDesk Manager - Push)
        // หมายเหตุ: ใช้ tunnel สาธารณะเพื่อให้agent/ข้อความวิ่งได้จากทุกที่; ภายในเครื่องใช้ host.docker.internal ก็ได้
        'push_url' => cd_env('N8N_PUSH_URL', 'https://appeals-arts-deemed-moscow.trycloudflare.com/webhook/chatdesk-push'),
        'timeout'  => cd_env('N8N_TIMEOUT', 30),
        // รหัสลับที่ n8n ต้องส่งมาด้วยตอนยิงเข้า api/incoming.php (เว้นว่าง = ไม่ตรวจ)
        'secret'   => cd_env('N8N_SECRET', ''),
    ),

    /* 2.1) RAG (n8n local workflows: ingest + answer, Gemini embeddings 768) */
    'rag' => array(
        'ingest_url' => cd_env('RAG_INGEST_URL', 'http://host.docker.internal:5678/webhook/rag-ingest'),
        'answer_url' => cd_env('RAG_ANSWER_URL', 'http://host.docker.internal:5678/webhook/rag-answer'),
        'timeout'    => cd_env('RAG_TIMEOUT', 600),
    ),

    /* 2.2) Gemini (ใช้ทั้ง RAG answer และ proxy อื่น ๆ ฝั่ง server) */
    'gemini' => array(
        'key'   => cd_env('GEMINI_KEY', '__GEMINI_API_KEY__'),
        'model' => cd_env('GEMINI_MODEL', 'gemini-2.5-flash'),
    ),

    /* 3) หน้าจัดการ */
    'app' => array(
        'title'        => cd_env('APP_TITLE', 'OmniDesk (Local)'),
        'subtitle'     => cd_env('APP_SUBTITLE', 'กล่องข้อความ LINE + RAG'),
        'timezone'     => cd_env('APP_TIMEZONE', 'Asia/Bangkok'),
        'poll_inbox'   => cd_env('APP_POLL_INBOX', 5),
        'poll_thread'  => cd_env('APP_POLL_THREAD', 3),
        'max_length'   => cd_env('APP_MAX_LENGTH', 2000),
        'auto_mute_bot' => cd_env('APP_AUTO_MUTE_BOT', true),
        // base path ใต้ document root (local: /chatdesk ; cloud: /week7/chatdesk)
        'base_path'    => cd_env('APP_BASE_PATH', '/chatdesk'),
    ),

    /* 4) บัญชีบูตสแตร็ป — ใช้เฉพาะตอนยังไม่มี user ในฐานข้อมูล (seed ครั้งแรก) */
    'admin' => array(
        'user' => cd_env('ADMIN_USER', 'admin'),
        'pass' => cd_env('ADMIN_PASS', '10203040'),
    ),

    'debug' => cd_env('APP_DEBUG', true),
);
