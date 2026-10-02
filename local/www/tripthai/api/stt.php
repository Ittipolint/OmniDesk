<?php
/**
 * TripThai Voice — STT proxy: รับไฟล์เสียงจากวิดเจ็ต แล้วส่งต่อให้ Whisper server
 *
 * POST multipart: audio=<file>, userId=WEB_xxx
 * ตอบกลับ JSON: { ok:true, text:"..." } หรือ { ok:false, error:"..." }
 *
 * หมายเหตุด้านความปลอดภัย (ระดับเดโมส่งอาจารย์):
 *  - ตรวจ userId (WEB_*), ขนาดไฟล์ <= 5MB, ชนิดไฟล์เสียงเท่านั้น
 *  - Whisper อยู่หลัง Cloudflare Tunnel URL ที่เดายาก + รับเฉพาะ request จาก proxy นี้
 *    (production จริงควรเพิ่ม token / Cloudflare Access ที่ฝั่ง Whisper อีกชั้น)
 */

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
@set_time_limit(100);

// ---------- ตั้งค่า (ผ่าน n8n API Engine กลางเท่านั้น — ไม่มี fallback ตรง) ----------
define('STT_MAX_BYTES', 5 * 1024 * 1024);   // 5MB ~ เสียง 60 วิ
define('STT_TIMEOUT', 90);                   // วินาที

function stt_fail($msg, $code = 200)
{
    http_response_code($code);
    echo json_encode(array('ok' => false, 'error' => $msg), JSON_UNESCAPED_UNICODE);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    stt_fail('ต้องเรียกด้วย POST เท่านั้น', 405);
}

$userId = isset($_POST['userId']) ? trim((string) $_POST['userId']) : '';
if (!preg_match('/^WEB_[A-Za-z0-9_-]{1,64}$/', $userId)) {
    stt_fail('userId ไม่ถูกต้อง', 422);
}

if (!isset($_FILES['audio']) || !is_array($_FILES['audio'])) {
    stt_fail('ไม่พบไฟล์เสียง (คีย์ "audio")', 422);
}
$f = $_FILES['audio'];
if ($f['error'] !== UPLOAD_ERR_OK) {
    stt_fail('อัปโหลดไฟล์ไม่สำเร็จ (รหัส ' . (int) $f['error'] . ')', 422);
}
if ($f['size'] <= 0 || $f['size'] > STT_MAX_BYTES) {
    stt_fail('ไฟล์เสียงต้องมีขนาด 1 ไบต์ – 5MB', 413);
}
if (!is_uploaded_file($f['tmp_name'])) {
    stt_fail('ไฟล์ไม่ถูกต้อง', 422);
}

// ตรวจชนิดไฟล์แบบหลวม ๆ (MediaRecorder ส่ง audio/webm; บาง browser เป็น application/octet-stream)
$mime = '';
if (function_exists('finfo_open')) {
    $fi = finfo_open(FILEINFO_MIME_TYPE);
    if ($fi) {
        $mime = (string) finfo_file($fi, $f['tmp_name']);
        finfo_close($fi);
    }
}
$mimeOk = ($mime === '')
    || (strpos($mime, 'audio/') === 0)
    || (strpos($mime, 'video/') === 0)
    || ($mime === 'application/octet-stream');
if (!$mimeOk) {
    stt_fail('ชนิดไฟล์ไม่ใช่เสียง (' . $mime . ')', 415);
}

if (!function_exists('curl_init')) {
    stt_fail('PHP cURL ไม่พร้อม', 500);
}

// 0) ผ่าน n8n API Engine กลางก่อน (api-stt) — ไม่ได้ค่อยยิงตรง Whisper
define('N8N_STT_URL', 'http://host.docker.internal:5678/webhook/api-stt');
$ch = curl_init(N8N_STT_URL);
curl_setopt_array($ch, array(
    CURLOPT_POST           => true,
    CURLOPT_POSTFIELDS     => array(
        'audio'  => new CURLFile($f['tmp_name'], $mime !== '' ? $mime : 'audio/webm', 'voice.webm'),
        'userId' => $userId,
    ),
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT        => STT_TIMEOUT,
    CURLOPT_CONNECTTIMEOUT => 10,
    CURLOPT_FOLLOWLOCATION => false,
));
$raw   = curl_exec($ch);
$errno = curl_errno($ch);
$http  = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);
if (!$errno && $http >= 200 && $http < 300) {
    $data = json_decode((string) $raw, true);
    if (is_array($data) && isset($data['ok'])) {
        if (!empty($data['ok']) && trim((string) (isset($data['text']) ? $data['text'] : '')) !== '') {
            echo json_encode(array('ok' => true, 'text' => mb_substr(trim((string) $data['text']), 0, 2000)), JSON_UNESCAPED_UNICODE);
            exit;
        }
        if (isset($data['error'])) {
            // engine ตอบมีเหตุผล (เช่น ฟังไม่ออก) — ส่งต่อข้อความนั้นเลย
            echo json_encode(array('ok' => false, 'error' => (string) $data['error']), JSON_UNESCAPED_UNICODE);
            exit;
        }
    }
}
stt_fail('API Engine (n8n api-stt) ไม่ตอบสนอง', 502);
