<?php
/**
 * ChatDesk LOCAL — API นำเข้าข้อมูล RAG (ADMIN เท่านั้น)
 * รับ: text / pdf(file) / image(file หรือ image_url) / url + group_id + title
 * ส่งต่อให้ n8n workflow RAG-Ingest ทำ OCR/แบ่ง chunk/embedding ลง pgvector
 */
require_once dirname(__DIR__, 2) . '/inc/bootstrap.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    cd_json(array('ok' => false, 'error' => 'ต้องเรียกด้วย POST เท่านั้น'), 405);
}
cd_require_admin();

$input = cd_input();
if (!cd_csrf_check(isset($input['csrf']) ? (string) $input['csrf'] : (isset($_POST['csrf']) ? (string) $_POST['csrf'] : ''))) {
    cd_json(array('ok' => false, 'error' => 'หมดเวลาใช้งาน กรุณารีเฟรชหน้าแล้วลองใหม่'), 403);
}

$type = isset($input['type']) ? (string) $input['type'] : (isset($_POST['type']) ? (string) $_POST['type'] : '');
if (!in_array($type, array('text', 'pdf', 'image', 'url'), true)) {
    cd_json(array('ok' => false, 'error' => 'ชนิดข้อมูลไม่ถูกต้อง'), 422);
}
$groupId = (int) (isset($input['group_id']) ? $input['group_id'] : (isset($_POST['group_id']) ? $_POST['group_id'] : 0));
$title   = mb_substr(trim((string) (isset($input['title']) ? $input['title'] : (isset($_POST['title']) ? $_POST['title'] : ''))), 0, 255);

if (!cd_db_ready()) {
    cd_json(array('ok' => false, 'error' => 'ฐานข้อมูลไม่พร้อม'), 500);
}
$st = cd_db()->prepare('SELECT id, name FROM rag_groups WHERE id = ?');
$st->execute(array($groupId));
$group = $st->fetch();
if (!$group) {
    cd_json(array('ok' => false, 'error' => 'ไม่พบกลุ่มข้อมูล'), 422);
}

// เตรียม payload ตามชนิด (group_name ส่งให้ n8n ด้วย — อย่าให้ n8n เดาเอง)
$post = array('group_id' => $groupId, 'group_name' => $group['name'], 'title' => $title, 'type' => $type);
$files = array();
if ($type === 'text') {
    $text = trim((string) (isset($input['text']) ? $input['text'] : ''));
    if ($text === '') {
        cd_json(array('ok' => false, 'error' => 'กรุณาวางข้อความ'), 422);
    }
    $post['text'] = mb_substr($text, 0, 60000);
} elseif ($type === 'url') {
    $url = trim((string) (isset($input['text']) ? $input['text'] : ''));
    if (!preg_match('~^https?://~i', $url)) {
        cd_json(array('ok' => false, 'error' => 'URL ต้องขึ้นต้น http:// หรือ https://'), 422);
    }
    $post['url'] = mb_substr($url, 0, 2000);
} else {
    // pdf / image: ไฟล์แนบ หรือ image_url
    if (!empty($_FILES['file']['tmp_name']) && is_uploaded_file($_FILES['file']['tmp_name'])) {
        if ($_FILES['file']['error'] !== UPLOAD_ERR_OK) {
            cd_json(array('ok' => false, 'error' => 'อัปโหลดไฟล์ไม่สำเร็จ'), 422);
        }
        if ($_FILES['file']['size'] > 25 * 1024 * 1024) {
            cd_json(array('ok' => false, 'error' => 'ไฟล์ใหญ่เกิน 25MB'), 413);
        }
        $files['file'] = new CURLFile(
            $_FILES['file']['tmp_name'],
            $_FILES['file']['type'] !== '' ? $_FILES['file']['type'] : 'application/octet-stream',
            $_FILES['file']['name']
        );
    }
    if ($type === 'image') {
        // รูปภาพรับเฉพาะ URL public HTTPS (ไม่มีอัปโหลดไฟล์แล้ว) — n8n ดาวน์โหลดเองแล้ว OCR
        $imgUrl = mb_substr(trim((string) (isset($input['image_url']) ? $input['image_url'] : (isset($_POST['image_url']) ? $_POST['image_url'] : ''))), 0, 2000);
        if (!preg_match('~^https://~i', $imgUrl)) {
            cd_json(array('ok' => false, 'error' => 'URL รูปต้องเป็น public HTTPS'), 422);
        }
        $cap = mb_substr(trim((string) (isset($input['text']) ? $input['text'] : (isset($_POST['text']) ? $_POST['text'] : ''))), 0, 5000);
        $post['image_url'] = $imgUrl;
        $post['text'] = $cap;
    } elseif (empty($files)) {
        cd_json(array('ok' => false, 'error' => 'เลือกไฟล์ PDF ก่อน'), 422);
    }
}

global $CFG;
$url = trim((string) $CFG['rag']['ingest_url']);
if ($url === '') {
    cd_json(array('ok' => false, 'error' => 'ยังไม่ได้ตั้งค่า RAG ingest webhook'), 500);
}
if (!function_exists('curl_init')) {
    cd_json(array('ok' => false, 'error' => 'PHP cURL ไม่พร้อม'), 500);
}

$ch = curl_init($url);
if (!empty($files)) {
    curl_setopt_array($ch, array(
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => array_merge($post, $files),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => (int) $CFG['rag']['timeout'],
        CURLOPT_CONNECTTIMEOUT => 15,
    ));
} else {
    curl_setopt_array($ch, array(
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode($post, JSON_UNESCAPED_UNICODE),
        CURLOPT_HTTPHEADER => array('Content-Type: application/json; charset=utf-8'),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => (int) $CFG['rag']['timeout'],
        CURLOPT_CONNECTTIMEOUT => 15,
    ));
}
$raw   = curl_exec($ch);
$errno = curl_errno($ch);
$err   = curl_error($ch);
$http  = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($errno) {
    cd_json(array('ok' => false, 'error' => 'เชื่อมต่อ RAG engine ไม่ได้: ' . $err . ' (ตรวจว่า n8n workflow RAG-Ingest เปิดอยู่)'), 502);
}
$data = json_decode((string) $raw, true);
if ($http < 200 || $http >= 300 || !is_array($data)) {
    if ($http >= 200 && $http < 300) {
        // n8n responseMode=responseNode: workflow พังก่อนถึง Respond (เช่น โควต้า Gemini 429)
        // จะตอบ 200 ตัวเปล่า/ไม่ใช่ JSON — บอกให้ชัดแทนเลข HTTP เพียวๆ
        cd_json(array('ok' => false, 'error' => 'RAG engine ขัดข้องก่อนตอบกลับ (HTTP ' . $http . ' แต่ข้อมูลไม่สมบูรณ์ — มักเป็นโควต้า Gemini 429, ตรวจ executions ใน n8n workflow RAG-03)'), 502);
    }
    cd_json(array('ok' => false, 'error' => 'RAG engine ตอบกลับ HTTP ' . $http), 502);
}
if (empty($data['ok'])) {
    cd_json(array('ok' => false, 'error' => isset($data['error']) ? (string) $data['error'] : 'นำเข้าไม่สำเร็จ'), 502);
}
cd_json(array('ok' => true, 'message' => isset($data['message']) ? (string) $data['message'] : 'นำเข้า + Embedding สำเร็จ', 'chunks' => isset($data['chunks']) ? (int) $data['chunks'] : 0));
