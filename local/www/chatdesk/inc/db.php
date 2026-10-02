<?php
/**
 * ChatDesk LOCAL — การเชื่อมต่อฐานข้อมูล Postgres (PDO)
 */

function cd_db($quiet = false)
{
    static $pdo = null;
    if ($pdo !== null) {
        return $pdo;
    }

    global $CFG;
    $db = $CFG['db'];
    $driver = isset($db['driver']) ? $db['driver'] : 'pgsql';

    if ($driver === 'pgsql') {
        $dsn = sprintf(
            'pgsql:host=%s;port=%d;dbname=%s',
            $db['host'], (int) $db['port'], $db['name']
        );
    } else {
        $dsn = sprintf(
            'mysql:host=%s;port=%d;dbname=%s;charset=%s',
            $db['host'], (int) $db['port'], $db['name'], $db['charset']
        );
    }

    try {
        $pdo = new PDO($dsn, $db['user'], $db['pass'], array(
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES   => false,
        ));
    } catch (PDOException $e) {
        $pdo = null;
        if ($quiet) {
            return null;
        }
        cd_db_fail('เชื่อมต่อฐานข้อมูลไม่สำเร็จ', $e->getMessage());
    }

    // ให้ timezone ตรงกับ PHP
    try {
        if ($driver === 'pgsql') {
            $pdo->exec("SET TIME ZONE 'Asia/Bangkok'");
        } else {
            $offset = (new DateTime('now', new DateTimeZone(date_default_timezone_get())))->format('P');
            $pdo->exec("SET time_zone = '" . $offset . "'");
        }
    } catch (Exception $e) {
    }

    return $pdo;
}

/** ตารางที่ต้องใช้ถูกสร้างแล้วหรือยัง */
function cd_db_ready()
{
    static $ready = null;
    if ($ready !== null) {
        return $ready;
    }
    $pdo = cd_db(true);
    if ($pdo === null) {
        return false;
    }
    try {
        $pdo->query('SELECT 1 FROM cd_conversations LIMIT 1');
        $pdo->query('SELECT 1 FROM cd_messages LIMIT 1');
        $ready = true;
    } catch (PDOException $e) {
        $ready = false;
    }
    return $ready;
}

/** แสดงหน้า error แบบอ่านง่าย แล้วหยุดการทำงาน */
function cd_db_fail($title, $detail)
{
    global $CFG;
    $isApi = strpos($_SERVER['REQUEST_URI'], '/api/') !== false;
    $msg   = !empty($CFG['debug']) ? $detail : 'กรุณาตรวจสอบค่าในไฟล์ config.php';

    if ($isApi) {
        http_response_code(500);
        header('Content-Type: application/json; charset=utf-8');
        echo json_encode(array('ok' => false, 'error' => $title, 'detail' => $msg), JSON_UNESCAPED_UNICODE);
        exit;
    }

    http_response_code(500);
    header('Content-Type: text/html; charset=utf-8');
    echo '<!doctype html><meta charset="utf-8"><title>ตั้งค่าไม่ถูกต้อง</title>'
        . '<style>body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;background:#f6f7fb;margin:0;'
        . 'display:flex;min-height:100vh;align-items:center;justify-content:center;padding:24px}'
        . '.b{background:#fff;max-width:560px;padding:32px;border-radius:16px;box-shadow:0 10px 40px rgba(15,23,42,.08)}'
        . 'h1{margin:0 0 12px;font-size:20px;color:#0f172a}p{color:#475569;line-height:1.7;margin:0 0 8px}'
        . 'code{background:#f1f5f9;padding:2px 6px;border-radius:6px;font-size:13px}</style>'
        . '<div class="b"><h1>⚠️ ' . htmlspecialchars($title, ENT_QUOTES, 'UTF-8') . '</h1>'
        . '<p>' . htmlspecialchars($msg, ENT_QUOTES, 'UTF-8') . '</p>'
        . '<p>ขั้นตอนแก้ไข: รันไฟล์ <code>local/sql/01_chatdesk_pg.sql</code> กับ Postgres แล้วตรวจค่า <code>db</code> ในไฟล์ <code>config.php</code></p></div>';
    exit;
}
