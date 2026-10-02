<?php
/**
 * TripThai Voice — Gemini brain proxy: รับข้อความจากวิดเจ็ต ส่งให้ Gemini 2.5 Flash ตอบ
 *
 * POST JSON: { text: "...", userId: "WEB_xxx", history: [{role:"user"|"model", text:"..."}] }
 * ตอบกลับ JSON: { ok:true, text:"..." }
 *
 * หมายเหตุ: API key เก็บฝั่ง server ไฟล์นี้เท่านั้น ห้ามย้ายไปไว้ใน JS หน้าเว็บ
 */

@set_time_limit(90);

// n8n API Engine กลางเท่านั้น (สมองรวม: RAG-first + Gemini + history) — ไม่มี fallback ตรง
define('N8N_AICHAT_URL', 'http://host.docker.internal:5678/webhook/api-ai-chat');
define('N8N_AICHAT_TIMEOUT', 150);
define('GEMINI_MAX_TURNS', 10);

function gem_fail($msg, $code = 200)
{
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(array('ok' => false, 'error' => $msg), JSON_UNESCAPED_UNICODE);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    gem_fail('ต้องเรียกด้วย POST เท่านั้น', 405);
}

$in = json_decode(file_get_contents('php://input'), true);
if (!is_array($in)) {
    $in = $_POST;
}
$userId = isset($in['userId']) ? trim((string) $in['userId']) : '';
if (!preg_match('/^WEB_[A-Za-z0-9_-]{1,64}$/', $userId)) {
    gem_fail('userId ไม่ถูกต้อง', 422);
}
$text = isset($in['text']) ? trim((string) $in['text']) : '';
if ($text === '' || mb_strlen($text) > 1000) {
    gem_fail('ข้อความต้องมี 1–1000 ตัวอักษร', 422);
}

// ถาม n8n API Engine กลาง (สมองรวม: RAG + Gemini + จำบริบท) — ช่องทางเดียว
$ai = tri_aichat($text, $userId, isset($in['history']) ? $in['history'] : array());
if ($ai === null) {
    gem_fail('API Engine (n8n api-ai-chat) ไม่ตอบสนอง', 502);
}
header('Content-Type: application/json; charset=utf-8');
echo json_encode(array('ok' => true, 'text' => mb_substr($ai['text'], 0, 2000),
                       'images' => $ai['images'], 'sources' => $ai['sources'],
                       'via' => $ai['via']), JSON_UNESCAPED_UNICODE);
exit;

// helper: เรียก n8n api-ai-chat
function tri_aichat($text, $userId, $history)
{
    $hist = array();
    if (is_array($history)) {
        foreach ($history as $h) {
            if (!is_array($h) || !isset($h['text'])) {
                continue;
            }
            $t = trim(mb_substr((string) $h['text'], 0, 1000));
            if ($t === '') {
                continue;
            }
            $hist[] = array(
                'role' => (isset($h['role']) && $h['role'] === 'model') ? 'model' : 'user',
                'text' => $t,
            );
            if (count($hist) >= GEMINI_MAX_TURNS) {
                break;
            }
        }
    }
    $ch = curl_init(N8N_AICHAT_URL);
    curl_setopt_array($ch, array(
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode(array(
            'text' => mb_substr($text, 0, 2000), 'userId' => $userId,
            'history' => $hist, 'session_id' => $userId,
            'group_id' => 1, // TripThai เลิกใช้แล้ว (28/9/68: กลุ่ม tourism ถูกลบ + ตัด channel web)
        ), JSON_UNESCAPED_UNICODE),
        CURLOPT_HTTPHEADER => array('Content-Type: application/json; charset=utf-8'),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => N8N_AICHAT_TIMEOUT,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_FOLLOWLOCATION => false,
    ));
    $raw = curl_exec($ch);
    $errno = curl_errno($ch);
    curl_close($ch);
    if ($errno) {
        return null;
    }
    $data = json_decode((string) $raw, true);
    if (!is_array($data) || empty($data['ok']) || trim((string) (isset($data['text']) ? $data['text'] : '')) === '') {
        return null;
    }
    $images = array();
    if (isset($data['images']) && is_array($data['images'])) {
        foreach ($data['images'] as $u) {
            $u = trim((string) $u);
            if (preg_match('~^https?://~i', $u)) {
                $images[] = mb_substr($u, 0, 2000);
            }
            if (count($images) >= 3) {
                break;
            }
        }
    }
    return array('text' => (string) $data['text'], 'images' => $images,
                 'sources' => (isset($data['sources']) && is_array($data['sources'])) ? $data['sources'] : array(),
                 'via' => isset($data['via']) ? (string) $data['via'] : 'ai-chat');
}
