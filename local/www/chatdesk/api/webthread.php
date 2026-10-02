<?php
/**
 * ChatDesk LOCAL — API สาธารณะสำหรับแขกเว็บ (thin forwarder -> n8n api-read)
 * GET ?userId=WEB_xxxx&since=<messageId>&channel=web|shopweb (เฉพาะห้องของตัวเอง)
 */

require_once dirname(__DIR__) . '/inc/bootstrap.php';

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    cd_json(array('ok' => false, 'error' => 'ต้องเรียกด้วย GET เท่านั้น'), 405);
}

$userId = isset($_GET['userId']) ? trim((string) $_GET['userId']) : '';
if (!preg_match('/^WEB_[A-Za-z0-9_-]{1,64}$/', $userId)) {
    cd_json(array('ok' => false, 'error' => 'userId ไม่ถูกต้อง'), 422);
}
$since = isset($_GET['since']) ? max(0, (int) $_GET['since']) : 0;
$channel = isset($_GET['channel']) ? (string) $_GET['channel'] : 'web';
if ($channel !== 'web' && $channel !== 'shopweb') {
    $channel = 'web';
}

$res = cd_n8n_post('api-read', array('resource' => 'webthread', 'userId' => $userId, 'since' => $since, 'channel' => $channel), 30);
if ($res['error'] !== null) {
    cd_json(array('ok' => false, 'error' => $res['error']), 502);
}
cd_json($res['data']);
