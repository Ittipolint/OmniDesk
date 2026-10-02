<?php
// ChatDesk LOCAL — API เอกสาร RAG รายชิ้น (ADMIN เท่านั้น; thin forwarder -> n8n api-ragmeta)
// POST JSON: { op: listsources|deletesource, group_id, id?, csrf }
// deletesource: ลบ rag_sources (CASCADE ลบ chunks) + เก็บไฟล์รูป local ที่อ้างอิง (uploads/rag_* เท่านั้น)
require_once dirname(__DIR__, 2) . '/inc/bootstrap.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    cd_json(array('ok' => false, 'error' => 'ต้องเรียกด้วย POST เท่านั้น'), 405);
}
cd_require_admin();
$input = cd_input();
if (!cd_csrf_check(isset($input['csrf']) ? $input['csrf'] : '')) {
    cd_json(array('ok' => false, 'error' => 'หมดเวลาใช้งาน กรุณารีเฟรชหน้าแล้วลองใหม่'), 403);
}

function fwd_ragmeta_src($op, $extra = array())
{
    $res = cd_n8n_post('api-ragmeta', array_merge(array('op' => $op), $extra), 30);
    if ($res['error'] !== null) {
        cd_json(array('ok' => false, 'error' => $res['error']), 502);
    }
    return $res['data'];
}

$op = isset($input['op']) ? (string) $input['op'] : 'listsources';
$groupId = (int) (isset($input['group_id']) ? $input['group_id'] : 0);
if ($groupId <= 0) {
    cd_json(array('ok' => false, 'error' => 'ต้องระบุกลุ่ม'), 422);
}

if ($op === 'listsources') {
    $r = fwd_ragmeta_src('listsources', array('group_id' => $groupId));
    if (empty($r['ok'])) {
        cd_json(array('ok' => false, 'error' => isset($r['error']) ? (string) $r['error'] : 'engine ผิดพลาด'), 502);
    }
    $out = array();
    if (isset($r['sources']) && is_array($r['sources'])) {
        foreach ($r['sources'] as $s) {
            $out[] = array(
                'id' => (int) $s['id'],
                'source_type' => (string) $s['source_type'],
                'title' => (string) $s['title'],
                'source_ref' => (string) $s['source_ref'],
                'image_url' => (string) $s['image_url'],
                'created_at' => (string) $s['created_at'],
                'chunks' => (int) $s['chunks'],
            );
        }
    }
    cd_json(array('ok' => true, 'sources' => $out));
}

if ($op === 'deletesource') {
    $id = (int) (isset($input['id']) ? $input['id'] : 0);
    if ($id <= 0) {
        cd_json(array('ok' => false, 'error' => 'ต้องระบุ id เอกสาร'), 422);
    }
    $r = fwd_ragmeta_src('deletesource', array('id' => $id, 'group_id' => $groupId));
    if (empty($r['ok'])) {
        cd_json(array('ok' => false, 'error' => isset($r['error']) ? (string) $r['error'] : 'ลบไม่สำเร็จ'), 502);
    }
    if (empty($r['deleted'])) {
        cd_json(array('ok' => false, 'error' => 'ไม่พบเอกสารในกลุ่มนี้'), 404);
    }
    // เก็บไฟล์รูป local ที่เอกสารนี้อ้างอิง (เฉพาะไฟล์ที่ระบบสร้าง: uploads/rag_*)
    $cleaned = false;
    $imgUrl = isset($r['image_url']) ? (string) $r['image_url'] : '';
    if ($imgUrl !== '') {
        $path = parse_url($imgUrl, PHP_URL_PATH);
        $base = $path !== null ? basename($path) : '';
        if (preg_match('/^rag_\d{8}_\d{6}_[0-9a-f]{8}\.(jpg|jpeg|png|gif|webp)$/', $base)) {
            $full = dirname(__DIR__, 2) . '/uploads/' . $base;
            if (is_file($full)) {
                $cleaned = @unlink($full);
            } else {
                $cleaned = true; // ไฟล์ไม่อยู่แล้ว ถือว่าสะอาด
            }
        }
    }
    cd_json(array('ok' => true, 'deleted' => true, 'file_cleaned' => $cleaned));
}

cd_json(array('ok' => false, 'error' => 'ไม่รู้จักคำสั่งนี้'), 422);
