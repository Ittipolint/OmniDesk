<?php
// ChatDesk LOCAL — API ตารางช่องทาง routing (ADMIN เท่านั้น; thin forwarder -> n8n api-channels)
// POST JSON: { op: list|get|set|add|delete, channel?, line_bot_id?, label?, rag_group_id?, line_channel_token?, is_active?, csrf }
// หมายเหตุ: ส่ง line_channel_token = '' คือล้าง token; ไม่ส่งคีย์ = ไม่เปลี่ยน
require_once dirname(__DIR__, 2) . '/inc/bootstrap.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    cd_json(array('ok' => false, 'error' => 'ต้องเรียกด้วย POST เท่านั้น'), 405);
}
cd_require_admin();
$input = cd_input();
if (!cd_csrf_check(isset($input['csrf']) ? $input['csrf'] : '')) {
    cd_json(array('ok' => false, 'error' => 'หมดเวลาใช้งาน กรุณารีเฟรชหน้าแล้วลองใหม่'), 403);
}

$op = isset($input['op']) ? (string) $input['op'] : 'list';
if ($op !== 'list' && $op !== 'get' && $op !== 'set' && $op !== 'add' && $op !== 'delete') {
    cd_json(array('ok' => false, 'error' => 'ไม่รู้จักคำสั่งนี้'), 422);
}
if (($op === 'add' || $op === 'delete') && !preg_match('/^[a-z0-9_]{2,32}$/', (string) (isset($input['channel']) ? $input['channel'] : ''))) {
    cd_json(array('ok' => false, 'error' => 'รหัสช่องทาง a-z 0-9 _ ยาว 2–32'), 422);
}
$payload = array('op' => $op);
foreach (array('channel', 'line_bot_id', 'label', 'rag_group_id', 'group_ids', 'persona_system', 'line_channel_token', 'is_active') as $k) {
    if (array_key_exists($k, $input)) {
        $payload[$k] = $input[$k];
    }
}
if (array_key_exists('group_ids', $payload) && is_array($payload['group_ids'])) {
    $gids = array();
    foreach ($payload['group_ids'] as $g) {
        $g = (int) $g;
        if ($g > 0) {
            $gids[] = $g;
        }
    }
    $payload['group_ids'] = array_values(array_unique($gids));
}
if (array_key_exists('persona_system', $payload)) {
    $payload['persona_system'] = mb_substr(trim((string) $payload['persona_system']), 0, 4000);
}
if ($op === 'set') {
    if (isset($payload['channel']) && !preg_match('/^[a-z0-9_]{2,32}$/', (string) $payload['channel'])) {
        cd_json(array('ok' => false, 'error' => 'รหัสช่องทาง a-z 0-9 _ ยาว 2–32'), 422);
    }
    // auto-resolve line_bot_id จาก token (GET bot/info) เมื่อไม่ได้กรอกมา
    $resolved = '';
    if (!empty($payload['line_channel_token']) && empty($payload['line_bot_id'])) {
        $info = cd_line_bot_info((string) $payload['line_channel_token']);
        if ($info !== null && isset($info['userId'])) {
            $payload['line_bot_id'] = (string) $info['userId'];
            $resolved = (string) $info['userId'];
        }
    }
}

$res = cd_n8n_post('api-channels', $payload, 30);
if ($res['error'] !== null) {
    cd_json(array('ok' => false, 'error' => $res['error']), 502);
}
$data = $res['data'];
if (!is_array($data) || empty($data['ok'])) {
    cd_json(array('ok' => false, 'error' => isset($data['error']) ? (string) $data['error'] : 'engine ผิดพลาด'), 502);
}
// ไม่ส่ง token กลับไปหน้าเว็บ (ส่งแค่ has_token)
$scrub = function ($c) {
    unset($c['line_channel_token']);
    return $c;
};
if (isset($data['channels']) && is_array($data['channels'])) {
    $data['channels'] = array_map($scrub, $data['channels']);
}
if (isset($data['channel']) && is_array($data['channel'])) {
    $data['channel'] = $scrub($data['channel']);
}
if (isset($resolved) && $resolved !== '') {
    $data['resolved_bot'] = $resolved;
}
cd_json($data);

/**
 * ถาม LINE ว่า token นี้เป็นของบอทตัวไหน (GET /v2/bot/info)
 * คืน array (userId/basicId/displayName) หรือ null ถ้า token ใช้ไม่ได้/ต่อไม่ได้
 * หมายเหตุ: เป็น lookup ประกอบ UX ฝั่ง PHP เท่านั้น งาน RAG/DB ทั้งหมดยังผ่าน n8n
 */
function cd_line_bot_info($token)
{
    if (!function_exists('curl_init') || $token === '') {
        return null;
    }
    $ch = curl_init('https://api.line.me/v2/bot/info');
    curl_setopt_array($ch, array(
        CURLOPT_HTTPGET => true,
        CURLOPT_HTTPHEADER => array('Authorization: Bearer ' . $token),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 15,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_FOLLOWLOCATION => false,
    ));
    $raw = curl_exec($ch);
    $errno = curl_errno($ch);
    $http = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    if ($errno || $http < 200 || $http >= 300) {
        return null;
    }
    $data = json_decode((string) $raw, true);
    if (!is_array($data) || empty($data['userId'])) {
        return null;
    }
    return $data;
}
