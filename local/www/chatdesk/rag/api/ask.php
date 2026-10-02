<?php
/**
 * ChatDesk LOCAL — API ถามตอบ RAG (ADMIN เท่านั้นในจอทดสอบ;
 * ส่วน TripThai/LINE เรียกผ่าน rag_answer() ภายในหรือ webhook ตรง)
 * รับ: { question, group_id?, top_k? } → ส่งต่อ n8n RAG-Answer → { text, images[], sources[] }
 */
require_once dirname(__DIR__, 2) . '/inc/bootstrap.php';
require_once dirname(__DIR__, 2) . '/inc/rag.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    cd_json(array('ok' => false, 'error' => 'ต้องเรียกด้วย POST เท่านั้น'), 405);
}
cd_require_admin();
$input = cd_input();
if (!cd_csrf_check(isset($input['csrf']) ? $input['csrf'] : '')) {
    cd_json(array('ok' => false, 'error' => 'หมดเวลาใช้งาน กรุณารีเฟรชหน้าแล้วลองใหม่'), 403);
}

$question = trim((string) (isset($input['question']) ? $input['question'] : ''));
if ($question === '' || mb_strlen($question) > 2000) {
    cd_json(array('ok' => false, 'error' => 'กรุณาพิมพ์คำถาม (ไม่เกิน 2000 ตัวอักษร)'), 422);
}
$groupId = (int) (isset($input['group_id']) ? $input['group_id'] : 0);
$topK = isset($input['top_k']) ? max(1, min(10, (int) $input['top_k'])) : 4;

$res = rag_answer($question, $groupId > 0 ? $groupId : null, $topK, 'web-' . session_id());
if (!$res['ok']) {
    cd_json(array('ok' => false, 'error' => $res['error']), 502);
}
cd_json(array('ok' => true, 'text' => $res['text'], 'images' => $res['images'], 'sources' => $res['sources']));
