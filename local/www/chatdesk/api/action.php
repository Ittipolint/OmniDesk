<?php
/**
 * ChatDesk — API: คำสั่งจัดการห้องแชท (thin forwarder -> n8n api-actions)
 * POST JSON: { conversationId, action, messageId?, csrf }
 *   action = bot_on | bot_off | close | reopen | mark_read | delete_message | delete
 * PHP ทำแค่: auth + CSRF + ตรวจข้อมูล → engine ทำ DB ทั้งหมด
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
$action = isset($input['action']) ? (string) $input['action'] : '';
$valid = array('bot_on', 'bot_off', 'close', 'reopen', 'mark_read', 'delete_message', 'delete');
if ($convId <= 0 || !in_array($action, $valid, true)) {
    cd_json(array('ok' => false, 'error' => 'ไม่รู้จักคำสั่งนี้'), 422);
}
if ($action === 'delete' && !cd_is_admin()) {
    cd_json(array('ok' => false, 'error' => 'เฉพาะกลุ่ม ADMIN'), 403);
}

$payload = array('action' => $action, 'conversationId' => $convId);
if ($action === 'delete_message') {
    $msgId = isset($input['messageId']) ? (int) $input['messageId'] : 0;
    if ($msgId <= 0) {
        cd_json(array('ok' => false, 'error' => 'ต้องระบุ messageId'), 422);
    }
    $payload['messageId'] = $msgId;
}

$res = cd_n8n_post('api-actions', $payload, 30);
if ($res['error'] !== null) {
    cd_json(array('ok' => false, 'error' => $res['error']), 502);
}
$data = $res['data'];
if (!is_array($data) || empty($data['ok'])) {
    $msg = (is_array($data) && isset($data['error'])) ? (string) $data['error'] : 'engine ผิดพลาด';
    $code = ($msg === 'ไม่พบห้องแชทนี้') ? 404 : 422;
    cd_json(array('ok' => false, 'error' => $msg), $code);
}
cd_json($data);
