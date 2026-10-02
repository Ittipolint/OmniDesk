<?php
/**
 * ChatDesk LOCAL — lib กลางเรียก RAG engine
 * ใช้ร่วมกันทั้งจอทดสอบ (rag/api/ask.php), TripThai proxy, และ flow ตอบ LINE
 * คืน array(ok, text, images[], sources[], error?)
 */
function rag_answer($question, $groupId = null, $topK = 4, $sessionId = null)
{
    global $CFG;
    $url = trim((string) $CFG['rag']['answer_url']);
    if ($url === '') {
        return array('ok' => false, 'error' => 'ยังไม่ได้ตั้งค่า RAG answer webhook');
    }
    if (!function_exists('curl_init')) {
        return array('ok' => false, 'error' => 'PHP cURL ไม่พร้อม');
    }
    $payload = array('question' => mb_substr($question, 0, 2000), 'top_k' => $topK);
    if ($groupId) {
        $payload['group_id'] = (int) $groupId;
    }
    if ($sessionId !== null && preg_match('/^[A-Za-z0-9:_-]{1,128}$/', (string) $sessionId)) {
        $payload['session_id'] = (string) $sessionId;
    }
    $ch = curl_init($url);
    curl_setopt_array($ch, array(
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode($payload, JSON_UNESCAPED_UNICODE),
        CURLOPT_HTTPHEADER => array('Content-Type: application/json; charset=utf-8'),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => (int) $CFG['rag']['timeout'],
        CURLOPT_CONNECTTIMEOUT => 15,
        CURLOPT_FOLLOWLOCATION => false,
    ));
    $raw   = curl_exec($ch);
    $errno = curl_errno($ch);
    $err   = curl_error($ch);
    $http  = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($errno) {
        return array('ok' => false, 'error' => 'เชื่อมต่อ RAG engine ไม่ได้: ' . $err);
    }
    $data = json_decode((string) $raw, true);
    if ($http < 200 || $http >= 300 || !is_array($data) || empty($data['ok'])) {
        if (($http >= 200 && $http < 300 && !is_array($data)) || (is_array($data) && empty($data))) {
            // n8n responseMode=responseNode: workflow พังก่อนถึง Respond (เช่น โควต้า Gemini 429)
            // จะตอบ 200 ตัวเปล่า/ไม่ใช่ JSON — บอกให้ชัดแทนเลข HTTP เพียวๆ
            return array('ok' => false, 'error' => 'RAG engine ขัดข้องก่อนตอบกลับ (HTTP ' . $http . ' แต่ข้อมูลไม่สมบูรณ์ — มักเป็นโควต้า Gemini 429, ตรวจ executions ใน n8n workflow RAG-04)');
        }
        $detail = (is_array($data) && isset($data['error'])) ? (string) $data['error'] : ('HTTP ' . $http);
        return array('ok' => false, 'error' => 'RAG engine ผิดพลาด: ' . $detail);
    }
    $images = array();
    if (isset($data['images']) && is_array($data['images'])) {
        foreach ($data['images'] as $u) {
            $u = trim((string) $u);
            if (preg_match('~^https?://~i', $u)) {
                $images[] = mb_substr($u, 0, 2000);
            }
            if (count($images) >= 5) {
                break;
            }
        }
    }
    $sources = array();
    if (isset($data['sources']) && is_array($data['sources'])) {
        foreach ($data['sources'] as $s) {
            $sources[] = mb_substr(trim((string) $s), 0, 255);
            if (count($sources) >= 8) {
                break;
            }
        }
    }
    return array(
        'ok'      => true,
        'text'    => isset($data['text']) ? (string) $data['text'] : '',
        'images'  => $images,
        'sources' => $sources,
    );
}
