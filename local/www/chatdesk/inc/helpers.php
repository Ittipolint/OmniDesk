<?php
/**
 * ChatDesk — ฟังก์ชันช่วยเหลือ
 */

/** escape สำหรับแสดงผลใน HTML */
function e($s)
{
    return htmlspecialchars((string) $s, ENT_QUOTES, 'UTF-8');
}

/** เลขกัน cache ของไฟล์ css/js — ใช้เวลาแก้ไขไฟล์ จะได้ไม่ต้องสั่งใครกด Ctrl+F5 */
function cd_asset_ver($relPath)
{
    $time = @filemtime(CD_ROOT . '/' . ltrim($relPath, '/'));
    return $time ? $time : CD_VERSION;
}

/** ตอบกลับเป็น JSON แล้วจบการทำงาน */
function cd_json($data, $status = 200)
{
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    header('X-Content-Type-Options: nosniff');
    header('Cache-Control: no-store');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_HEX_TAG | JSON_HEX_AMP);
    exit;
}

/** อ่าน body ที่เป็น JSON (ถ้าไม่ใช่ JSON ให้ใช้ $_POST) */
function cd_input()
{
    $in = json_decode(file_get_contents('php://input'), true);
    return is_array($in) ? $in : $_POST;
}

/* --------------------- n8n API Engine กลาง --------------------- */

/** base URL ของ n8n local (เรียกภายในเครื่อง ไม่ผ่านเน็ต) */
function cd_n8n_base()
{
    $v = getenv('N8N_LOCAL');
    if ($v === false || $v === '') {
        $v = 'http://host.docker.internal:5678';
    }
    return rtrim($v, '/');
}

/**
 * เรียก n8n webhook ภายใน (PHP ทำแค่ auth/validate แล้วส่งต่อ)
 * คืน array(http, data|null, error|null)
 */
function cd_n8n_post($path, $payload, $timeout = 60)
{
    if (!function_exists('curl_init')) {
        return array('http' => 0, 'data' => null, 'error' => 'PHP cURL ไม่พร้อม');
    }
    $ch = curl_init(cd_n8n_base() . '/webhook/' . ltrim($path, '/'));
    curl_setopt_array($ch, array(
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => json_encode($payload, JSON_UNESCAPED_UNICODE),
        CURLOPT_HTTPHEADER     => array('Content-Type: application/json; charset=utf-8'),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => (int) $timeout,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_FOLLOWLOCATION => false,
    ));
    $raw   = curl_exec($ch);
    $errno = curl_errno($ch);
    $err   = curl_error($ch);
    $http  = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    if ($errno) {
        return array('http' => 0, 'data' => null, 'error' => 'เชื่อมต่อ API Engine (n8n) ไม่ได้: ' . $err);
    }
    $data = json_decode((string) $raw, true);
    if ($http < 200 || $http >= 300 || !is_array($data)) {
        return array('http' => $http, 'data' => null, 'error' => 'API Engine ตอบกลับ HTTP ' . $http);
    }
    return array('http' => $http, 'data' => $data, 'error' => null);
}

/* ------------------------------- CSRF / สิทธิ์ ------------------------------ */

function cd_csrf_token()
{
    if (empty($_SESSION['csrf'])) {
        $_SESSION['csrf'] = bin2hex(random_bytes(16));
    }
    return $_SESSION['csrf'];
}

function cd_csrf_check($token)
{
    return !empty($_SESSION['csrf']) && is_string($token) && hash_equals($_SESSION['csrf'], $token);
}

function cd_is_admin()
{
    $groups = cd_user_groups();
    return in_array('ADMIN', $groups, true);
}

/** ใช้ในไฟล์ api ที่เฉพาะผู้ดูแลเรียกได้ */
function cd_require_admin()
{
    if (!cd_is_admin()) {
        cd_json(array('ok' => false, 'error' => 'เฉพาะกลุ่ม ADMIN'), 403);
    }
}

/** ใช้ในไฟล์ที่ต้อง login ทุกกลุ่ม (พนักงานตอบแชทได้) */
function cd_require_login()
{
    if (!cd_current_user()) {
        cd_json(array('ok' => false, 'error' => 'กรุณาเข้าสู่ระบบใหม่'), 401);
    }
}

/* ------------------------------ ผู้ใช้/กลุ่ม ------------------------------ */

/** user ที่ login อยู่ (array) หรือ null */
function cd_current_user()
{
    if (empty($_SESSION['user_id'])) {
        return null;
    }
    try {
        $st = cd_db()->prepare('SELECT id, username, display_name, is_active FROM cd_users WHERE id = ? LIMIT 1');
        $st->execute(array((int) $_SESSION['user_id']));
        $u = $st->fetch();
        if (!$u || (int) $u['is_active'] !== 1) {
            unset($_SESSION['user_id']);
            return null;
        }
        return $u;
    } catch (Exception $e) {
        return null;
    }
}

/** ชื่อกลุ่มทั้งหมดของ user ที่ login อยู่ */
function cd_user_groups()
{
    if (empty($_SESSION['user_id'])) {
        return array();
    }
    if (isset($_SESSION['user_groups']) && is_array($_SESSION['user_groups'])) {
        return $_SESSION['user_groups'];
    }
    try {
        $st = cd_db()->prepare(
            'SELECT g.name FROM cd_groups g
             INNER JOIN cd_user_groups ug ON ug.group_id = g.id
             WHERE ug.user_id = ?'
        );
        $st->execute(array((int) $_SESSION['user_id']));
        $groups = array();
        foreach ($st->fetchAll() as $r) {
            $groups[] = $r['name'];
        }
        $_SESSION['user_groups'] = $groups;
        return $groups;
    } catch (Exception $e) {
        return array();
    }
}

/** login ด้วย username/password — สำเร็จคืน user array */
function cd_login($username, $password)
{
    try {
        $st = cd_db()->prepare('SELECT * FROM cd_users WHERE username = ? LIMIT 1');
        $st->execute(array(trim((string) $username)));
        $u = $st->fetch();
    } catch (Exception $e) {
        return null;
    }
    if (!$u || (int) $u['is_active'] !== 1) {
        return null;
    }
    if (!password_verify((string) $password, (string) $u['pass_hash'])) {
        return null;
    }
    if (session_status() === PHP_SESSION_ACTIVE) {
        session_regenerate_id(true);
    }
    $_SESSION['user_id'] = (int) $u['id'];
    unset($_SESSION['user_groups']);
    unset($_SESSION['admin_ok']); // เลิกใช้ flag เดิม
    return $u;
}

function cd_logout()
{
    unset($_SESSION['user_id'], $_SESSION['user_groups'], $_SESSION['admin_ok'], $_SESSION['csrf']);
}

function cd_check_password($plain)
{
    global $CFG;
    $cp = (string) $CFG['admin']['pass'];
    if (strpos($cp, '$2y$') === 0 || strpos($cp, '$argon2') === 0) {
        return password_verify($plain, $cp);
    }
    return hash_equals($cp, (string) $plain);
}

/* ------------------------------ ห้องแชท/ข้อความ ---------------------------- */

/** หาห้องแชทจาก LINE userId ถ้ายังไม่มีให้สร้างใหม่ */
function cd_find_or_create_conversation($userId, $displayName = null, $pictureUrl = null, $channel = 'line')
{
    $pdo = cd_db();

    $st = $pdo->prepare('SELECT * FROM cd_conversations WHERE channel = ? AND external_user_id = ? LIMIT 1');
    $st->execute(array($channel, $userId));
    $row = $st->fetch();

    if ($row) {
        // อัปเดตชื่อ/รูปถ้าเพิ่งได้มา หรือเปลี่ยนไป
        if ($displayName !== null && $displayName !== '' && $displayName !== $row['display_name']) {
            $pdo->prepare('UPDATE cd_conversations SET display_name = ?, picture_url = ? WHERE id = ?')
                ->execute(array($displayName, $pictureUrl, $row['id']));
            $row['display_name'] = $displayName;
        }
        return $row;
    }

    $ins = $pdo->prepare(
        'INSERT INTO cd_conversations (channel, external_user_id, display_name, picture_url, created_at)
         VALUES (?, ?, ?, ?, NOW())'
    );
    $ins->execute(array($channel, $userId, $displayName, $pictureUrl));

    $st->execute(array($channel, $userId));
    return $st->fetch();
}

/**
 * บันทึกข้อความ 1 บรรทัด
 * คืน id ของข้อความ หรือ 0 ถ้าเป็นข้อความซ้ำ (LINE ส่งซ้ำ)
 */
function cd_save_message($conversationId, $sender, $content, $extra = array())
{
    $pdo = cd_db();

    $externalId = isset($extra['external_id']) && $extra['external_id'] !== '' ? $extra['external_id'] : null;
    if ($externalId !== null) {
        $chk = $pdo->prepare('SELECT id FROM cd_messages WHERE external_message_id = ? LIMIT 1');
        $chk->execute(array($externalId));
        if ($chk->fetch()) {
            return 0;   // เคยบันทึกไปแล้ว
        }
    }

    $st = $pdo->prepare(
        'INSERT INTO cd_messages
           (conversation_id, sender, content, message_type, media_url, media_preview_url,
            sticker_package, sticker_id, external_message_id, status, error_message, raw,
            delivered_at, created_at)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())
          RETURNING id'
    );
    $st->execute(array(
        $conversationId,
        $sender,
        $content,
        isset($extra['type']) ? $extra['type'] : 'text',
        isset($extra['media_url']) ? mb_substr($extra['media_url'], 0, 500) : null,
        isset($extra['media_preview_url']) ? mb_substr($extra['media_preview_url'], 0, 500) : null,
        isset($extra['sticker_package']) ? mb_substr($extra['sticker_package'], 0, 50) : null,
        isset($extra['sticker_id']) ? mb_substr($extra['sticker_id'], 0, 50) : null,
        $externalId,
        isset($extra['status']) ? $extra['status'] : 'ok',
        isset($extra['error']) ? mb_substr($extra['error'], 0, 500) : null,
        isset($extra['raw']) ? mb_substr($extra['raw'], 0, 60000) : null,
    ));
    $id = (int) $st->fetchColumn();

    // อัปเดตสรุปของห้อง
    $type     = isset($extra['type']) ? $extra['type'] : 'text';
    $preview  = mb_substr(preg_replace('/\s+/u', ' ', $content), 0, 200);
    if ($type !== 'text') {
        $preview = array(
            'image'   => '[ภาพ]',
            'video'   => '[วิดีโอ]',
            'sticker' => '[สติกเกอร์]',
            'audio'   => '[เสียง]',
            'file'    => '[ไฟล์]',
        );
        $preview = isset($preview[$type]) ? $preview[$type] : ('[' . $type . ']');
    }
    if ($sender === 'customer') {
        $pdo->prepare(
            'UPDATE cd_conversations
                SET last_message_at = NOW(), last_message_text = ?, unread_count = unread_count + 1,
                    status = \'open\'
              WHERE id = ?'
        )->execute(array($preview, $conversationId));
    } else {
        $pdo->prepare('UPDATE cd_conversations SET last_message_at = NOW(), last_message_text = ? WHERE id = ?')
            ->execute(array($preview, $conversationId));
    }

    return $id;
}

/** ข้อความในห้อง (เรียงเก่า -> ใหม่) */
function cd_thread($conversationId, $limit = 200, $sinceId = 0)
{
    $where = 'WHERE conversation_id = ? AND deleted_at IS NULL';
    $args  = array($conversationId);
    if ($sinceId > 0) {
        $where .= ' AND id > ?';
        $args[] = (int) $sinceId;
    }
    $st = cd_db()->prepare(
        'SELECT id, sender, content, message_type, media_url, media_preview_url,
                sticker_package, sticker_id, status, error_message, created_at,
                delivered_at, read_at, deleted_at
           FROM cd_messages ' . $where . ' ORDER BY id DESC LIMIT ' . (int) $limit
    );
    $st->execute($args);
    return array_reverse($st->fetchAll());
}

/** จัดรูปข้อความให้พร้อมส่งไปหน้าเว็บ */
function cd_format_message($row)
{
    return array(
        'id'                => (int) $row['id'],
        'sender'            => $row['sender'],
        'type'              => $row['message_type'],
        'content'           => $row['content'],
        'html'              => cd_text_html($row['content']),
        'mediaUrl'          => $row['media_url'],
        'mediaPreviewUrl'   => $row['media_preview_url'],
        'stickerPackage'    => $row['sticker_package'],
        'stickerId'         => $row['sticker_id'],
        'status'            => $row['status'],
        'error'             => $row['error_message'],
        'delivered'         => !empty($row['delivered_at']),
        'read'              => !empty($row['read_at']),
        'deleted'           => !empty($row['deleted_at']),
        'deliveredAt'       => $row['delivered_at'] ? date('H:i', strtotime($row['delivered_at'])) : null,
        'readAt'            => $row['read_at'] ? date('H:i', strtotime($row['read_at'])) : null,
        'time'              => date('H:i', strtotime($row['created_at'])),
        'date'              => date('d/m/Y', strtotime($row['created_at'])),
    );
}

/** แปลงข้อความเป็น HTML ปลอดภัย (ขึ้นบรรทัดใหม่ + ลิงก์) */
function cd_text_html($text)
{
    $html = e($text);
    $html = preg_replace(
        '~(https?://[^\s<]+)~u',
        '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>',
        $html
    );
    return nl2br($html, false);
}

/**
 * ลบข้อความ (soft delete) — ใช้ได้กับข้อความของบอทและเจ้าหน้าที่
 * คืน true เมื่อสำเร็จ, false เมื่อหาไม่เจอหรือไม่มีสิทธิ์ลบ
 */
function cd_delete_message($messageId)
{
    $pdo = cd_db();
    $st = $pdo->prepare('SELECT * FROM cd_messages WHERE id = ? LIMIT 1');
    $st->execute(array((int) $messageId));
    $row = $st->fetch();
    if (!$row || $row['deleted_at'] !== null) {
        return false;
    }
    // ลบได้เฉพาะข้อความที่ "เราส่งออกไป" (บอท / เจ้าหน้าที่) เท่านั้น
    if (!in_array($row['sender'], array('bot', 'agent'), true)) {
        return false;
    }

    $pdo->prepare('UPDATE cd_messages SET deleted_at = NOW() WHERE id = ?')->execute(array((int) $messageId));

    // ถ้าข้อความที่ลบคือข้อความล่าสุด ให้ย้อนกลับไปใช้ข้อความสุดท้ายที่ยังเหลืออยู่
    $last = $pdo->prepare(
        'SELECT content, message_type, created_at FROM cd_messages
          WHERE conversation_id = ? AND deleted_at IS NULL
          ORDER BY id DESC LIMIT 1'
    );
    $last->execute(array((int) $row['conversation_id']));
    $lr = $last->fetch();
    if ($lr) {
        $preview = mb_substr(preg_replace('/\s+/u', ' ', $lr['content']), 0, 200);
        $pdo->prepare('UPDATE cd_conversations SET last_message_at = ?, last_message_text = ? WHERE id = ?')
            ->execute(array($lr['created_at'], $preview, (int) $row['conversation_id']));
    } else {
        $pdo->prepare('UPDATE cd_conversations SET last_message_at = NULL, last_message_text = NULL WHERE id = ?')
            ->execute(array((int) $row['conversation_id']));
    }

    return true;
}

/** ใช้กับ LINE — ตั้ง status ราวกับว่าอ่านแล้ว (อ่านเมื่อถึง LINE server หากไม่มี read event) */
function cd_mark_message_read($conversationId, $senderFilter = null)
{
    $sql = 'UPDATE cd_messages SET read_at = COALESCE(read_at, NOW()) WHERE conversation_id = ? AND read_at IS NULL';
    $args = array((int) $conversationId);
    if ($senderFilter !== null) {
        $sql .= ' AND sender = ?';
        $args[] = $senderFilter;
    }
    cd_db()->prepare($sql)->execute($args);
}

/* --------------------------------- ส่ง LINE -------------------------------- */

/**
 * ส่งข้อความออกไปหาลูกค้าทาง LINE โดยยิงผ่าน webhook ของ n8n
 * (channel access token เก็บอยู่ใน credential ของ n8n ไม่ต้องเอามาไว้บน hosting)
 *
 * $type: text | image | video | sticker
 * $media: สำหรับ image/video → { mediaUrl, mediaPreviewUrl }
 *         สำหรับ sticker    → { stickerPackage, stickerId }
 */
function cd_push_line($userId, $text, $type = 'text', $media = array())
{
    global $CFG;
    $url = trim((string) $CFG['n8n']['push_url']);

    $parts = parse_url($url);
    if ($parts === false || empty($parts['scheme']) || empty($parts['host'])
        || !in_array(strtolower($parts['scheme']), array('http', 'https'), true)) {
        return array('ok' => false, 'error' => 'URL สำหรับส่ง LINE ไม่ถูกต้อง (ตรวจค่า n8n.push_url ใน config.php)');
    }
    if (!function_exists('curl_init')) {
        return array('ok' => false, 'error' => 'hosting นี้ไม่ได้เปิดใช้ PHP cURL extension');
    }

    $payload = array(
        'userId' => $userId,
        'text'   => $text,
        'type'   => $type,
        'source' => 'chatdesk-agent',
    );
    if ($type === 'image' || $type === 'video') {
        $payload['mediaUrl']       = isset($media['mediaUrl']) ? $media['mediaUrl'] : '';
        $payload['mediaPreviewUrl'] = isset($media['mediaPreviewUrl']) ? $media['mediaPreviewUrl'] : '';
    } elseif ($type === 'sticker') {
        $payload['stickerPackage'] = isset($media['stickerPackage']) ? $media['stickerPackage'] : '';
        $payload['stickerId']      = isset($media['stickerId']) ? $media['stickerId'] : '';
    }
    if ($CFG['n8n']['secret'] !== '') {
        $payload['secret'] = $CFG['n8n']['secret'];
    }

    $ch = curl_init($url);
    curl_setopt_array($ch, array(
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => json_encode($payload, JSON_UNESCAPED_UNICODE),
        CURLOPT_HTTPHEADER     => array('Content-Type: application/json; charset=utf-8'),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => (int) $CFG['n8n']['timeout'],
        CURLOPT_CONNECTTIMEOUT => 15,
        CURLOPT_FOLLOWLOCATION => false,
    ));
    if (defined('CURLPROTO_HTTP') && defined('CURLPROTO_HTTPS')) {
        @curl_setopt($ch, CURLOPT_PROTOCOLS, CURLPROTO_HTTP | CURLPROTO_HTTPS);
    }

    $raw   = curl_exec($ch);
    $errno = curl_errno($ch);
    $err   = curl_error($ch);
    $http  = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($errno) {
        return array('ok' => false, 'error' => 'เชื่อมต่อ n8n ไม่ได้: ' . $err, 'raw' => '');
    }
    if ($http < 200 || $http >= 300) {
        return array('ok' => false, 'error' => 'n8n ตอบกลับ HTTP ' . $http, 'raw' => (string) $raw);
    }
    return array('ok' => true, 'error' => '', 'raw' => (string) $raw);
}
