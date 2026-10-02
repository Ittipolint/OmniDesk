<?php
// ChatDesk LOCAL — API กลุ่ม RAG (ADMIN เท่านั้น; thin forwarder -> n8n api-ragmeta)
require_once dirname(__DIR__, 2) . '/inc/bootstrap.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    cd_json(array('ok' => false, 'error' => 'ต้องเรียกด้วย POST เท่านั้น'), 405);
}
cd_require_admin();
$input = cd_input();
if (!cd_csrf_check(isset($input['csrf']) ? $input['csrf'] : '')) {
    cd_json(array('ok' => false, 'error' => 'หมดเวลาใช้งาน กรุณารีเฟรชหน้าแล้วลองใหม่'), 403);
}

function fwd_ragmeta($op, $extra = array())
{
    $res = cd_n8n_post('api-ragmeta', array_merge(array('op' => $op), $extra), 30);
    if ($res['error'] !== null) {
        cd_json(array('ok' => false, 'error' => $res['error']), 502);
    }
    return $res['data'];
}

$op = isset($input['op']) ? (string) $input['op'] : 'list';

if ($op === 'add') {
    $name = trim((string) (isset($input['name']) ? $input['name'] : ''));
    if ($name === '' || !preg_match('/^[A-Za-z0-9_ก-ฮ-]{2,64}$/u', $name)) {
        cd_json(array('ok' => false, 'error' => 'ชื่อกลุ่ม A-Z a-z 0-9 _ - ก-ฮ ยาว 2–64'), 422);
    }
    $r = fwd_ragmeta('add', array(
        'name' => $name,
        'description' => mb_substr(trim((string) (isset($input['description']) ? $input['description'] : '')), 0, 255),
    ));
    if (empty($r['ok'])) {
        $msg = isset($r['error']) ? (string) $r['error'] : 'เพิ่มไม่สำเร็จ';
        if (stripos($msg, 'duplicate') !== false || stripos($msg, 'unique') !== false || stripos($msg, 'already') !== false) {
            $msg = 'มีกลุ่มนี้แล้ว';
        }
        cd_json(array('ok' => false, 'error' => $msg), 422);
    }
    cd_json(array('ok' => true));
}

if ($op === 'delete') {
    $id = (int) (isset($input['id']) ? $input['id'] : 0);
    $list = fwd_ragmeta('list');
    $found = false;
    if (is_array($list) && isset($list['groups']) && is_array($list['groups'])) {
        foreach ($list['groups'] as $g) {
            if ((int) $g['id'] === $id) {
                $found = true;
                break;
            }
        }
    }
    if (!$found) {
        cd_json(array('ok' => false, 'error' => 'ไม่พบกลุ่ม'), 404);
    }
    $r = fwd_ragmeta('delete', array('id' => $id));
    if (empty($r['ok'])) {
        cd_json(array('ok' => false, 'error' => isset($r['error']) ? (string) $r['error'] : 'ลบไม่สำเร็จ'), 502);
    }
    cd_json(array('ok' => true));
}

// list + จำนวน chunks ต่อกลุ่ม
$r = fwd_ragmeta('list');
if (empty($r['ok'])) {
    cd_json(array('ok' => false, 'error' => isset($r['error']) ? (string) $r['error'] : 'engine ผิดพลาด'), 502);
}
$groups = array();
if (isset($r['groups']) && is_array($r['groups'])) {
    foreach ($r['groups'] as $g) {
        $groups[] = array(
            'id' => (int) $g['id'],
            'name' => (string) $g['name'],
            'description' => (string) (isset($g['description']) ? $g['description'] : ''),
            'persona' => (string) (isset($g['persona_system']) ? $g['persona_system'] : (isset($g['persona']) ? $g['persona'] : '')),
            'chunks' => (int) $g['chunks'],
        );
    }
}
cd_json(array('ok' => true, 'groups' => $groups));
