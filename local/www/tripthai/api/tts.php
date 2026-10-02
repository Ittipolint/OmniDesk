<?php
/**
 * TripThai Voice — TTS proxy: รับข้อความ แล้วส่งต่อให้ Piper Thai (VITS) บน Docker
 *
 * POST JSON: { text: "...", userId: "WEB_xxx" }
 * ตอบกลับ: audio/wav (หรือ JSON {ok:false} เมื่อผิดพลาด)
 */

@set_time_limit(90);

// ผ่าน n8n API Engine กลางเท่านั้น (api-tts คืน base64) — ไม่มี fallback ตรง
define('TTS_TIMEOUT', 60);
define('TTS_MAX_CHARS', 600);

function tts_fail($msg, $code = 200)
{
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(array('ok' => false, 'error' => $msg), JSON_UNESCAPED_UNICODE);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    tts_fail('ต้องเรียกด้วย POST เท่านั้น', 405);
}

$in = json_decode(file_get_contents('php://input'), true);
if (!is_array($in)) {
    $in = $_POST;
}
$userId = isset($in['userId']) ? trim((string) $in['userId']) : '';
if (!preg_match('/^WEB_[A-Za-z0-9_-]{1,64}$/', $userId)) {
    tts_fail('userId ไม่ถูกต้อง', 422);
}
$text = isset($in['text']) ? trim((string) $in['text']) : '';
if ($text === '' || mb_strlen($text) > TTS_MAX_CHARS) {
    tts_fail('ข้อความต้องมี 1–600 ตัวอักษร', 422);
}

if (!function_exists('curl_init')) {
    tts_fail('PHP cURL ไม่พร้อม', 500);
}

// 0) ผ่าน n8n API Engine กลางก่อน (api-tts คืน base64) — ไม่ได้ค่อยยิงตรง Piper
define('N8N_TTS_URL', 'http://host.docker.internal:5678/webhook/api-tts');
$ch = curl_init(N8N_TTS_URL);
curl_setopt_array($ch, array(
    CURLOPT_POST           => true,
    CURLOPT_POSTFIELDS     => json_encode(array('text' => $text, 'userId' => $userId), JSON_UNESCAPED_UNICODE),
    CURLOPT_HTTPHEADER     => array('Content-Type: application/json; charset=utf-8'),
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT        => TTS_TIMEOUT,
    CURLOPT_CONNECTTIMEOUT => 10,
    CURLOPT_FOLLOWLOCATION => false,
));
$raw   = curl_exec($ch);
$errno = curl_errno($ch);
curl_close($ch);
if (!$errno) {
    $data = json_decode((string) $raw, true);
    if (is_array($data) && !empty($data['ok']) && isset($data['audio'])) {
        $bin = base64_decode((string) $data['audio'], true);
        if ($bin !== false && strlen($bin) > 1000) {
            header('Content-Type: audio/wav');
            header('Cache-Control: no-store');
            header('Content-Length: ' . strlen($bin));
            echo $bin;
            exit;
        }
    }
    if (is_array($data) && isset($data['error'])) {
        tts_fail((string) $data['error'], 502);
    }
}
tts_fail('API Engine (n8n api-tts) ไม่ตอบสนอง', 502);
