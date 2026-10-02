<?php
/**
 * ChatDesk LOCAL — API: พนักงานพิมพ์ตอบลูกค้า (thin forwarder -> n8n API Engine)
 * POST JSON: { conversationId, text?, type?, mediaUrl?, mediaPreviewUrl?, stickerPackage?, stickerId?, csrf }
 * type = text | image | video | sticker (ไม่ระบุ = text)
 *
 * PHP ทำแค่: auth + CSRF + ตรวจข้อมูล → ส่งต่อให้ n8n workflow `chatdesk-send`
 * ซึ่งทำหน้าที่: ปิดบอทอัตโนมัติ + บันทึกข้อความ agent + พุชออก LINE (ถ้าเป็นห้อง line)
 */

require_once dirname(__DIR__) . '/inc/bootstrap.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    cd_json(array('ok' => false, 'error' => 'ต้องเรียกด้วย POST เท่านั้น'), 405);
}

cd_require_login();

$input = cd_input();
if (!cd_csrf_check(isset($input['csrf']) ? $input['csrf'] : '')) {
    cd_json(array('ok' => false, 'error' => 'หมดเวลาใช้งาน กรุณารีเฟรชหน้าแล้วลองใหม่'), 403);
}

$convId = isset($input['conversationId']) ? (int) $input['conversationId'] : 0;
$text   = isset($input['text']) ? trim((string) $input['text']) : '';
$type   = isset($input['type']) ? preg_replace('/[^a-z]/', '', strtolower($input['type'])) : 'text';
if ($type === '') {
    $type = 'text';
}
if (!in_array($type, array('text', 'image', 'video', 'sticker'), true)) {
    cd_json(array('ok' => false, 'error' => 'ไม่รู้จักประเภทข้อความนี้'), 422);
}
if ($type === 'text' && $text === '') {
    cd_json(array('ok' => false, 'error' => 'กรุณาพิมพ์ข้อความ'), 422);
}
$max = (int) $CFG['app']['max_length'];
if (mb_strlen($text) > $max) {
    $text = mb_substr($text, 0, $max);
}

/* ตรวจ payload ของมีเดีย (เร็ว ลดรอบ n8n ฟรี) */
$media = array('mediaUrl' => '', 'mediaPreviewUrl' => '', 'stickerPackage' => '', 'stickerId' => '');
if ($type === 'image' || $type === 'video') {
    $media['mediaUrl']        = isset($input['mediaUrl']) ? trim((string) $input['mediaUrl']) : '';
    $media['mediaPreviewUrl'] = isset($input['mediaPreviewUrl']) ? trim((string) $input['mediaPreviewUrl']) : '';
    if (!preg_match('~^https?://~i', $media['mediaUrl']) || $media['mediaUrl'] === '') {
        cd_json(array('ok' => false, 'error' => 'ไม่พบ URL ของไฟล์'), 422);
    }
    if ($media['mediaPreviewUrl'] !== '' && !preg_match('~^https?://~i', $media['mediaPreviewUrl'])) {
        cd_json(array('ok' => false, 'error' => 'URL ตัวอย่างไฟล์ไม่ถูกต้อง'), 422);
    }
} elseif ($type === 'sticker') {
    $media['stickerPackage'] = isset($input['stickerPackage']) ? trim((string) $input['stickerPackage']) : '';
    $media['stickerId']      = isset($input['stickerId']) ? trim((string) $input['stickerId']) : '';
    if ($media['stickerPackage'] === '' || $media['stickerId'] === '') {
        cd_json(array('ok' => false, 'error' => 'ข้อมูลสติกเกอร์ไม่ครบ'), 422);
    }
}

if (!function_exists('curl_init')) {
    cd_json(array('ok' => false, 'error' => 'PHP cURL ไม่พร้อม'), 500);
}

$ch = curl_init('http://host.docker.internal:5678/webhook/chatdesk-send');
curl_setopt_array($ch, array(
    CURLOPT_POST           => true,
    CURLOPT_POSTFIELDS     => json_encode(array(
        'conversationId' => $convId,
        'text'           => $text,
        'type'           => $type,
        'mediaUrl'       => $media['mediaUrl'],
        'mediaPreviewUrl' => $media['mediaPreviewUrl'],
        'stickerPackage' => $media['stickerPackage'],
        'stickerId'      => $media['stickerId'],
    ), JSON_UNESCAPED_UNICODE),
    CURLOPT_HTTPHEADER     => array('Content-Type: application/json; charset=utf-8'),
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT        => 90,
    CURLOPT_CONNECTTIMEOUT => 10,
    CURLOPT_FOLLOWLOCATION => false,
));
$raw   = curl_exec($ch);
$errno = curl_errno($ch);
$http  = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($errno) {
    cd_json(array('ok' => false, 'error' => 'เชื่อมต่อ API Engine (n8n) ไม่ได้'), 502);
}
$data = json_decode((string) $raw, true);
if ($http < 200 || $http >= 300 || !is_array($data) || empty($data['ok'])) {
    $detail = (is_array($data) && isset($data['error'])) ? (string) $data['error'] : ('HTTP ' . $http);
    cd_json(array('ok' => false, 'error' => 'ส่งไม่สำเร็จ: ' . $detail), 502);
}

cd_json(array(
    'ok'        => true,
    'messageId' => isset($data['messageId']) ? (int) $data['messageId'] : 0,
    'botMuted'  => !empty($data['botMuted']),
    'time'      => date('H:i'),
));
