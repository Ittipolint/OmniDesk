<?php
/**
 * ChatDesk LOCAL — API: ข้อความในห้องแชท (thin forwarder -> n8n api-read)
 * GET ?id=<conversationId>&since=<messageId>
 */

require_once dirname(__DIR__) . '/inc/bootstrap.php';

cd_require_login();

$convId = isset($_GET['id']) ? (int) $_GET['id'] : 0;
$since  = isset($_GET['since']) ? (int) $_GET['since'] : 0;

$res = cd_n8n_post('api-read', array('resource' => 'thread', 'id' => $convId, 'since' => $since), 30);
if ($res['error'] !== null) {
    cd_json(array('ok' => false, 'error' => $res['error']), 502);
}
$data = $res['data'];
if (is_array($data) && empty($data['ok']) && isset($data['error']) && $data['error'] === 'ไม่พบห้องแชทนี้') {
    cd_json($data, 404);
}
cd_json($data);
