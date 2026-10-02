<?php
/**
 * ChatDesk — API: อัปโหลดไฟล์มีเดีย (ภาพ/วิดีโอ)
 *
 * ใช้ได้ 2 แบบ:
 *   1) multipart/form-data  — field ชื่อ "file"   (จากหน้าเว็บ)
 *   2) POST ตัว body เป็น binary ตรง ๆ พร้อม header "X-ChatDesk-Filename"  (จาก n8n)
 *
 * คืน JSON: { ok, url, type, size }
 */

require_once dirname(__DIR__) . '/inc/bootstrap.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    cd_json(array('ok' => false, 'error' => 'ต้องเรียกด้วย POST เท่านั้น'), 405);
}

/* อนุญาตเฉพาะแอดมิน (จากหน้าเว็บ) หรือ n8n (มี secret หรือ — เมื่อยังไม่ได้ตั้ง secret — มี header X-ChatDesk-Filename)
 * เงื่อนไขสอดคล้องกับ api/incoming.php: ตรวจ secret เฉพาะเมื่อตั้งค่าไว้ */
$secret = (string) $CFG['n8n']['secret'];
$isN8n  = false;
if ($secret !== '') {
    $given = isset($_SERVER['HTTP_X_CHATDESK_SECRET']) ? (string) $_SERVER['HTTP_X_CHATDESK_SECRET'] : '';
    if (hash_equals($secret, $given)) {
        $isN8n = true;
    }
} elseif (isset($_SERVER['HTTP_X_CHATDESK_FILENAME'])) {
    /* ยังไม่ได้ตั้ง secret → ถือว่า request ที่ส่ง header X-ChatDesk-Filename เป็น n8n */
    $isN8n = true;
}
if (!$isN8n) {
    cd_require_login();
}

$uploadDir = CD_ROOT . '/uploads/';
if (!is_dir($uploadDir)) {
    @mkdir($uploadDir, 0755, true);
}
if (!is_writable($uploadDir)) {
    cd_json(array('ok' => false, 'error' => 'โฟลเดอร์ uploads/ เขียนไม่ได้ กรุณาตั้งสิทธิ์ให้ถูกต้อง'), 500);
}

$extAllowed = array(
    'jpg' => 'image', 'jpeg' => 'image', 'png' => 'image', 'gif' => 'image',
    'webp' => 'image', 'mp4' => 'video', 'mov' => 'video', 'm4v' => 'video',
);
$maxBytes = 50 * 1024 * 1024;   // 50 MB กันเกิน limit ของ LINE (วิดีโอสูงสุด ~200MB)

/* ------------------------- รับไฟล์จาก $_FILES (webchat) ------------------------ */
$tmpName = '';
$origName = '';
if (!empty($_FILES['file']['tmp_name']) && is_uploaded_file($_FILES['file']['tmp_name'])) {
    $tmpName  = $_FILES['file']['tmp_name'];
    $origName = $_FILES['file']['name'];
    if ($_FILES['file']['error'] !== UPLOAD_ERR_OK) {
        cd_json(array('ok' => false, 'error' => 'อัปโหลดไฟล์ไม่สำเร็จ (error ' . $_FILES['file']['error'] . ')'), 422);
    }
} else {
    /* ------------------------- รับ raw body (n8n) ------------------------- */
    $raw = file_get_contents('php://input');
    if ($raw === false || $raw === '') {
        cd_json(array('ok' => false, 'error' => 'ไม่พบไฟล์ — ต้องส่ง multipart field "file" หรือ body binary'), 422);
    }
    $tmpName  = tempnam(sys_get_temp_dir(), 'cd_');
    file_put_contents($tmpName, $raw);
    $origName = isset($_SERVER['HTTP_X_CHATDESK_FILENAME']) ? $_SERVER['HTTP_X_CHATDESK_FILENAME'] : 'upload.bin';
}

$size = filesize($tmpName);
if ($size === false || $size <= 0) {
    @unlink($tmpName);
    cd_json(array('ok' => false, 'error' => 'ไฟล์ว่างเปล่า'), 422);
}
if ($size > $maxBytes) {
    @unlink($tmpName);
    cd_json(array('ok' => false, 'error' => 'ไฟล์ใหญ่เกินไป (จำกัด ' . round($maxBytes / 1048576) . ' MB)'), 413);
}

$ext = strtolower(pathinfo($origName, PATHINFO_EXTENSION));

/* ถ้าไม่มี/ไม่อนุญาต extension ให้เดาจาก MIME (เผื่อ n8n ส่งชื่อไฟล์แบบ .bin หรือไม่มี ext) */
$mimeToExt = array(
    'image/jpeg' => 'jpg', 'image/png' => 'png', 'image/gif' => 'gif', 'image/webp' => 'webp',
    'video/mp4' => 'mp4', 'video/quicktime' => 'mov',
);
if (!isset($extAllowed[$ext])) {
    $detectMime = '';
    if (function_exists('finfo_open')) {
        $f = finfo_open(FILEINFO_MIME_TYPE);
        if ($f) { $detectMime = (string) finfo_file($f, $tmpName); finfo_close($f); }
    }
    if (isset($mimeToExt[$detectMime])) {
        $ext = $mimeToExt[$detectMime];
    }
}

if (!isset($extAllowed[$ext])) {
    @unlink($tmpName);
    cd_json(array('ok' => false, 'error' => 'ไม่อนุญาตนามสกุลไฟล์ .' . e($ext) . ' (อนุญาต: jpg png gif webp mp4 mov m4v)'), 415);
}

/* ตรวจ MIME กันของปลอม */
$finfo = function_exists('finfo_open') ? finfo_open(FILEINFO_MIME_TYPE) : false;
$mime  = $finfo ? (string) finfo_file($finfo, $tmpName) : '';
if ($finfo) { finfo_close($finfo); }

$mimeOk = false;
foreach (array('image/jpeg','image/png','image/gif','image/webp','video/mp4','video/quicktime') as $allow) {
    if (strpos($mime, $allow) === 0) { $mimeOk = true; break; }
}
if ($extAllowed[$ext] === 'image' && strpos($mime, 'image/') !== 0) { $mimeOk = false; }
if ($extAllowed[$ext] === 'video' && strpos($mime, 'video/') !== 0) { $mimeOk = false; }

if (!$mimeOk) {
    @unlink($tmpName);
    cd_json(array('ok' => false, 'error' => 'ประเภทไฟล์ไม่ถูกต้อง (ตรวจพบ MIME: ' . ($mime !== '' ? e($mime) : 'ไม่รู้จัก') . ')'), 415);
}

/* สร้างชื่อไฟล์สุ่ม + ย้ายเข้าที่ */
$newname = date('Ymd_His') . '_' . bin2hex(random_bytes(6)) . '.' . $ext;
$dest    = $uploadDir . $newname;

if (!@rename($tmpName, $dest)) {
    if (!@copy($tmpName, $dest)) {
        @unlink($tmpName);
        cd_json(array('ok' => false, 'error' => 'บันทึกไฟล์ไม่สำเร็จ'), 500);
    }
    @unlink($tmpName);
}
@chmod($dest, 0644);

$scheme = 'http';
if ((isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off')
    || (isset($_SERVER['HTTP_X_FORWARDED_PROTO']) && strpos($_SERVER['HTTP_X_FORWARDED_PROTO'], 'https') === 0)) {
    $scheme = 'https';
}
$baseUrl = $scheme . '://' . $_SERVER['HTTP_HOST'] . rtrim(dirname(dirname($_SERVER['SCRIPT_NAME'])), '/') . '/uploads/' . $newname;

cd_json(array(
    'ok'   => true,
    'url'  => $baseUrl,
    'type' => $extAllowed[$ext],
    'ext'  => $ext,
    'size' => (int) $size,
));
