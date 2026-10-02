<?php
// ChatDesk LOCAL — API ตั้งค่า AI รายกิจกรรม (ADMIN เท่านั้น; thin forwarder -> n8n api-voice)
// POST JSON: { op: get|set, key?: llm.qa|tts.engine, value?, model? (legacy=llm.qa), csrf }
require_once dirname(__DIR__, 2) . '/inc/bootstrap.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    cd_json(array('ok' => false, 'error' => 'ต้องเรียกด้วย POST เท่านั้น'), 405);
}
cd_require_admin();
$input = cd_input();
if (!cd_csrf_check(isset($input['csrf']) ? $input['csrf'] : '')) {
    cd_json(array('ok' => false, 'error' => 'หมดเวลาใช้งาน กรุณารีเฟรชหน้าแล้วลองใหม่'), 403);
}

$op = isset($input['op']) ? (string) $input['op'] : 'get';
if ($op !== 'get' && $op !== 'set') {
    cd_json(array('ok' => false, 'error' => 'ไม่รู้จักคำสั่งนี้'), 422);
}
$payload = array('op' => $op);
if ($op === 'set') {
    if (isset($input['model']) && !isset($input['key'])) {
        // legacy: {model} -> llm.qa
        $input['key'] = 'llm.qa';
        $input['value'] = $input['model'];
    }
    $key = isset($input['key']) ? (string) $input['key'] : '';
    $value = isset($input['value']) ? (string) $input['value'] : '';
    $allow = array(
        'llm.qa' => array('gemini', 'qwen3:4b'),
        'tts.engine' => array('auto', 'neural', 'piper'),
        'ocr.engine' => array('gemini', 'easyocr'),
    );
    if ($key === 'n8n.api_key') {
        cd_json(array('ok' => false, 'error' => 'ไม่อนุญาต'), 403);
    }
    if ($key === 'gemini.api_key') {
        // free-form แต่ล็อก charset กัน SQLi/พัง JSON (n8n ตรวจซ้ำอีกชั้น)
        if (!preg_match('/^[A-Za-z0-9._-]{20,500}$/', $value)) {
            cd_json(array('ok' => false, 'error' => 'รูปแบบ API key ไม่ถูกต้อง (20-500 ตัวอักษร: A-Z a-z 0-9 . _ -)'), 422);
        }
    } elseif (!isset($allow[$key]) || !in_array($value, $allow[$key], true)) {
        cd_json(array('ok' => false, 'error' => 'คีย์หรือค่าไม่ถูกต้อง'), 422);
    }
    $payload['key'] = $key;
    $payload['value'] = $value;
}

$res = cd_n8n_post('api-voice', $payload, 30);
if ($res['error'] !== null) {
    cd_json(array('ok' => false, 'error' => $res['error']), 502);
}
$data = $res['data'];
if (!is_array($data) || empty($data['ok'])) {
    cd_json(array('ok' => false, 'error' => isset($data['error']) ? (string) $data['error'] : 'engine ผิดพลาด'), 502);
}
cd_json($data);
