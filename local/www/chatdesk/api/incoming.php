<?php
/**
 * ChatDesk LOCAL — API: รับข้อความ (thin forwarder -> n8n API Engine)
 * ตรวจ secret + validate เบื้องต้นที่นี่ งาน DB ทั้งหมดทำใน n8n `api-receive`
 * POST JSON: { userId, text|message|reply|content, sender?, displayName?, pictureUrl?,
 *              messageType?, mediaUrl?, stickerPackage?, stickerId?, messageId?, secret? }
 */

require_once dirname(__DIR__) . '/inc/bootstrap.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    cd_json(array('ok' => false, 'error' => 'ต้องเรียกด้วย POST เท่านั้น'), 405);
}

$input = cd_input();

/* ---- รหัสลับ: ตรวจเฉพาะเมื่อตั้งค่าไว้ ---- */
$secret = (string) $CFG['n8n']['secret'];
if ($secret !== '') {
    $given = isset($input['secret']) ? (string) $input['secret']
           : (isset($_SERVER['HTTP_X_CHATDESK_SECRET']) ? (string) $_SERVER['HTTP_X_CHATDESK_SECRET'] : '');
    if (!hash_equals($secret, $given)) {
        cd_json(array('ok' => false, 'error' => 'รหัสลับไม่ถูกต้อง'), 403);
    }
}

/* ---- ตรวจข้อมูลเบื้องต้น (เร็ว ไม่ต้องรอ engine) ---- */
$userId = isset($input['userId']) ? trim((string) $input['userId']) : '';
if ($userId === '') {
    cd_json(array('ok' => false, 'error' => 'ไม่พบ userId ของลูกค้า'), 422);
}
$text = '';
foreach (array('text', 'message', 'reply', 'content') as $k) {
    if (isset($input[$k]) && is_scalar($input[$k]) && trim((string) $input[$k]) !== '') {
        $text = trim((string) $input[$k]);
        break;
    }
}
if ($text === '' && (!isset($input['messageType']) || strtolower(preg_replace('/[^a-z]/', '', (string) $input['messageType'])) === 'text')) {
    cd_json(array('ok' => false, 'error' => 'ไม่พบข้อความ — ให้ส่งมาในคีย์ "text"'), 422);
}

/* ---- ส่งต่อให้ engine ---- */
$res = cd_n8n_post('api-receive', $input, 30);
if ($res['error'] !== null) {
    cd_json(array('ok' => false, 'error' => $res['error']), 502);
}
$data = $res['data'];
if (!is_array($data) || empty($data['ok'])) {
    cd_json(array('ok' => false, 'error' => isset($data['error']) ? (string) $data['error'] : 'engine ผิดพลาด'), 502);
}
cd_json($data);
