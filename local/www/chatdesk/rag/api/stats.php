<?php
// ChatDesk LOCAL — API สถิติ RAG (ADMIN เท่านั้น; thin forwarder -> n8n api-ragmeta)
require_once dirname(__DIR__, 2) . '/inc/bootstrap.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    cd_json(array('ok' => false, 'error' => 'ต้องเรียกด้วย POST เท่านั้น'), 405);
}
cd_require_admin();
$input = cd_input();
if (!cd_csrf_check(isset($input['csrf']) ? $input['csrf'] : '')) {
    cd_json(array('ok' => false, 'error' => 'หมดเวลาใช้งาน กรุณารีเฟรชหน้าแล้วลองใหม่'), 403);
}

$res = cd_n8n_post('api-ragmeta', array('op' => 'stats'), 30);
if ($res['error'] !== null) {
    cd_json(array('ok' => false, 'error' => $res['error']), 502);
}
$data = $res['data'];
if (!is_array($data) || empty($data['ok'])) {
    cd_json(array('ok' => false, 'error' => isset($data['error']) ? (string) $data['error'] : 'engine ผิดพลาด'), 502);
}
$groups = array();
if (isset($data['groups']) && is_array($data['groups'])) {
    foreach ($data['groups'] as $g) {
        $groups[] = array('name' => (string) $g['name'], 'chunks' => (int) $g['chunks']);
    }
}
cd_json(array(
    'ok' => true,
    'sources' => (int) $data['sources'],
    'chunks' => (int) $data['chunks'],
    'images' => (int) $data['images'],
    'groups' => $groups,
));
