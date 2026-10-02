<?php
/**
 * ShopDee — Chatbot brain proxy: รับข้อความจากเว็บ ส่งให้ n8n api-ai-chat (RAG กลุ่ม Shop)
 *
 * POST JSON: { text: "...", userId: "WEB_xxx", history: [{role:"user"|"model", text:"..."}] }
 * ตอบกลับ JSON: { ok:true, text, images[], sources[], via }
 *
 * หมายเหตุ: ใช้ userId แบบเดียวกับ TripThai (WEB_*) เพื่อ reuse เส้นเสียง STT/TTS เดิม
 * แยกห้อง/ช่องทางด้วย channel='shopweb' + RAG group 5 ตอน forward เข้า ChatDesk/n8n
 */
@set_time_limit(240);

define('N8N_AICHAT_URL', 'http://host.docker.internal:5678/webhook/api-ai-chat');
define('N8N_AICHAT_TIMEOUT', 150);
define('N8N_SHOPSQL_URL', 'http://host.docker.internal:5678/webhook/api-shop-sql');
define('N8N_SHOPSQL_TIMEOUT', 60);
define('SHOP_MAX_TURNS', 10);

function shop_fail($msg, $code = 200)
{
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(array('ok' => false, 'error' => $msg), JSON_UNESCAPED_UNICODE);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    shop_fail('ต้องเรียกด้วย POST เท่านั้น', 405);
}

$in = json_decode(file_get_contents('php://input'), true);
if (!is_array($in)) {
    $in = $_POST;
}
$userId = isset($in['userId']) ? trim((string) $in['userId']) : '';
if (!preg_match('/^WEB_[A-Za-z0-9_-]{1,64}$/', $userId)) {
    shop_fail('userId ไม่ถูกต้อง', 422);
}
$text = isset($in['text']) ? trim((string) $in['text']) : '';
if ($text === '' || mb_strlen($text) > 1000) {
    shop_fail('ข้อความต้องมี 1–1000 ตัวอักษร', 422);
}

// หลักการ: PHP เป็น proxy เท่านั้น — การค้นข้อมูลทั้งหมด (Vector + Structured)
// ทำใน n8n (api-ai-chat + api-shop-sql) ห้าม query DB จากฝั่งเว็บตรง
$ai = null;
$sql = shop_sql_lookup($text, isset($in['history']) ? $in['history'] : array(), $userId);
$qtext = $text . (($sql && $sql['block'] !== '') ? "\n\n[ข้อมูลสดจากฐานข้อมูลร้าน — ข้อเท็จจริงจาก DB ต้องยึดตัวเลขราคา/สต็อก/ชื่อร้านตามนี้เท่านั้น ห้ามดึงตัวเลขจากแถวอื่นหรือแต่ง spec เพิ่ม]\n" . $sql['block'] : '');
$ai = shop_aichat($qtext, $userId, isset($in['history']) ? $in['history'] : array());
if ($ai === null) {
    // n8n หลักล่ม แต่มีคำตอบ deterministic จาก SQL → ตอบแค่นั้น
    if ($sql && $sql['answer'] !== '') {
        header('Content-Type: application/json; charset=utf-8');
        echo json_encode(array('ok' => true, 'text' => $sql['answer'],
            'images' => isset($sql['images']) ? $sql['images'] : array(), 'sources' => $sql['sources'], 'via' => 'sql'), JSON_UNESCAPED_UNICODE);
        exit;
    }
    shop_fail('API Engine (n8n api-ai-chat) ไม่ตอบสนอง', 502);
}
$adviceQ = preg_match('/(แนะนำ|เปรียบเทียบ|เปรียบ|คุ้ม|ดีไหม|เลือก|ตัวไหน|รุ่นไหน|ดีกว่า)/u', $text);
if ($sql && $sql['answer'] !== '' && ($sql['kind'] === 'lookup' || ($sql['rows'] > 0 && !$adviceQ))) {
    // สินค้าพึ่ง SQL อย่างเดียว: SQL เจอแถว + ไม่ใช่คำถามเชิงแนะนำ/เปรียบเทียบ
    // → ตอบ deterministic จาก DB ตรง กัน AI ผสมข้อมูลข้ามแถว
    // (เช่น เอาราคา SD-0010 ขาตั้งมือถือ มาตอบเป็นจอ SD-0012)
    $finalText = $sql['answer'];
    // รวมรูปจาก SQL + รูปจาก RAG
    $sqlImages = isset($sql['images']) ? $sql['images'] : array();
    $ragImages = isset($ai['images']) ? $ai['images'] : array();
    $allImages = array_values(array_slice(array_merge($sqlImages, $ragImages), 0, 4));
    $sources = array_merge($sql['sources'], $ragImages ? array('รูปประกอบจาก RAG') : array(), $ai['sources']);
    $via = 'sql';
} else {
    $sources = array_merge($ai['sources'], ($sql && $sql['block'] !== '') ? $sql['sources'] : array());
    // เส้น rag (Shape RAG) ไม่ผ่าน LLM — ต้องต่อบล็อกข้อมูลสดท้ายคำตอบเอง;
    // เส้น LLM (qwen/gemini) เห็นบล็อกในคำถามแล้ว ไม่ต้องต่อซ้ำ
    $finalText = $ai['text'];
    if ($sql && $sql['block'] !== '' && ($ai['via'] === 'rag' || $sql['rows'] > 0)) {
        $finalText .= "\n\n" . $sql['block'];
    }
    $via = $ai['via'] . (($sql && ($sql['block'] !== '' || $sql['answer'] !== '')) ? '+sql' : '');
    // รวมรูปจาก SQL + รูปจาก RAG
    $sqlImages = ($sql && isset($sql['images'])) ? $sql['images'] : array();
    $ragImages = isset($ai['images']) ? $ai['images'] : array();
    $allImages = array_values(array_slice(array_merge($sqlImages, $ragImages), 0, 4));
}
$sources = array_values(array_slice($sources, 0, 8));
header('Content-Type: application/json; charset=utf-8');
echo json_encode(array('ok' => true, 'text' => mb_substr($finalText, 0, 2000),
                           'images' => $allImages, 'sources' => $sources,
                           'via' => $via), JSON_UNESCAPED_UNICODE);
// แจ้ง Odoo แบบไม่รอผล (ห้องแชท -> Lead, กันซ้ำที่ปลายทาง)
if (function_exists('fastcgi_finish_request')) {
    fastcgi_finish_request();
}
shop_odoo_chat($userId, $text, 'shopweb');
exit;

function shop_odoo_chat($userId, $text, $channel)
{
    if (!function_exists('curl_init')) {
        return;
    }
    $ch = curl_init('http://host.docker.internal:5678/webhook/api-odoo-lead');
    curl_setopt_array($ch, array(
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode(array(
            'op' => 'chat', 'channel' => $channel,
            'external_user_id' => $userId, 'text' => mb_substr($text, 0, 500),
        ), JSON_UNESCAPED_UNICODE),
        CURLOPT_HTTPHEADER => array('Content-Type: application/json; charset=utf-8'),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 8,
        CURLOPT_CONNECTTIMEOUT => 3,
        CURLOPT_FOLLOWLOCATION => false,
    ));
    @curl_exec($ch);
    curl_close($ch);
}

function shop_aichat($text, $userId, $history)
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
            if (count($hist) >= SHOP_MAX_TURNS) {
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
            'channel' => 'shopweb', // api-ai-chat resolve กลุ่ม RAG + persona จาก channel เอง
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

// ---------- Text-to-SQL (Both mode: RAG + live DB) ----------
// Router กฎก่อน: เฉพาะคำถามข้อมูลสด (ราคา/สต็อก/ออเดอร์/รหัส/SKU/เบอร์โทร) เท่านั้น
// เรียก n8n api-shop-sql (structured lookup) — PHP ไม่แตะ DB เอง
// คืน null (ไม่ต้องใช้ SQL) หรือ array(kind, block, answer, sources)
function shop_sql_lookup($text, $history, $userId)
{
    $ch = curl_init(N8N_SHOPSQL_URL);
    curl_setopt_array($ch, array(
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode(array(
            'text' => mb_substr($text, 0, 2000), 'userId' => $userId,
            'history' => is_array($history) ? array_slice($history, -4) : array(),
        ), JSON_UNESCAPED_UNICODE),
        CURLOPT_HTTPHEADER => array('Content-Type: application/json; charset=utf-8'),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => N8N_SHOPSQL_TIMEOUT,
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
    if (!is_array($data) || empty($data['ok'])) {
        return null;
    }
    $imgs = array();
    if (isset($data['images']) && is_array($data['images'])) {
        foreach ($data['images'] as $u) {
            $u = trim((string) $u);
            if (preg_match('~^https?://~i', $u)) {
                $imgs[] = mb_substr($u, 0, 2000);
            }
            if (count($imgs) >= 4) { break; }
        }
    }
    $valid_imgs = array_values($imgs);

    return array(
        'kind' => isset($data['kind']) ? (string) $data['kind'] : 'both',
        'block' => isset($data['block']) ? (string) $data['block'] : '',
        'answer' => isset($data['answer']) ? (string) $data['answer'] : '',
        'sources' => (isset($data['sources']) && is_array($data['sources'])) ? $data['sources'] : array(),
        'images' => $valid_imgs,
        'rows' => isset($data['rows']) ? (int) $data['rows'] : 0,
    );
}
