<?php
// ChatDesk LOCAL — API จัดการผู้ใช้ (thin forwarders -> n8n api-users)
// ไฟล์นี้รวม list/save/delete/group: ตรวจ ADMIN+CSRF ที่นี่ ส่ง op ต่อไปยัง engine
require_once dirname(__DIR__, 2) . '/inc/bootstrap.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    cd_json(array('ok' => false, 'error' => 'ต้องเรียกด้วย POST เท่านั้น'), 405);
}
cd_require_admin();
$input = cd_input();
if (!cd_csrf_check(isset($input['csrf']) ? $input['csrf'] : '')) {
    cd_json(array('ok' => false, 'error' => 'หมดเวลาใช้งาน กรุณารีเฟรชหน้าแล้วลองใหม่'), 403);
}

$script = isset($_SERVER['SCRIPT_NAME']) ? $_SERVER['SCRIPT_NAME'] : '';
$isGroup = strpos($script, 'group.php') !== false;

function fwd_users($op, $extra = array())
{
    $res = cd_n8n_post('api-users', array_merge(array('op' => $op), $extra), 30);
    if ($res['error'] !== null) {
        cd_json(array('ok' => false, 'error' => $res['error']), 502);
    }
    return $res['data'];
}

if ($isGroup) {
    // group.php — { op: add|delete, ... }
    $op = isset($input['op']) ? (string) $input['op'] : '';
    if ($op === 'add') {
        $name = strtoupper(trim((string) (isset($input['name']) ? $input['name'] : '')));
        if ($name === '' || !preg_match('/^[A-Z0-9_]{2,32}$/', $name)) {
            cd_json(array('ok' => false, 'error' => 'ชื่อกลุ่ม A-Z 0-9 _ ยาว 2–32'), 422);
        }
        cd_json(fwd_users('group_add', array(
            'name' => $name,
            'description' => mb_substr(trim((string) (isset($input['description']) ? $input['description'] : '')), 0, 255),
        )));
    }
    if ($op === 'delete') {
        $id = (int) (isset($input['id']) ? $input['id'] : 0);
        if ($id <= 0) {
            cd_json(array('ok' => false, 'error' => 'ต้องระบุ id'), 422);
        }
        cd_json(fwd_users('group_del', array('id' => $id)));
    }
    cd_json(array('ok' => false, 'error' => 'ไม่รู้จักคำสั่งนี้'), 422);
}

// save.php / delete.php / list.php แยกตามชื่อไฟล์
if (strpos($script, 'list.php') !== false) {
    cd_json(fwd_users('list'));
}

if (strpos($script, 'delete.php') !== false) {
    $id = (int) (isset($input['id']) ? $input['id'] : 0);
    if ($id === (int) $_SESSION['user_id']) {
        cd_json(array('ok' => false, 'error' => 'ลบตัวเองไม่ได้'), 422);
    }
    cd_json(fwd_users('delete', array('id' => $id)));
}

// save.php — สร้าง/แก้ไข (รหัสผ่าน hash ฝั่ง PHP ส่ง pass_hash ไป engine)
$id = isset($input['id']) ? (int) $input['id'] : 0;
if ($id > 0) {
    if (isset($input['password']) && trim((string) $input['password']) !== '') {
        if (mb_strlen(trim((string) $input['password'])) < 4) {
            cd_json(array('ok' => false, 'error' => 'รหัสผ่านอย่างน้อย 4 ตัว'), 422);
        }
        $r = fwd_users('setpass', array('id' => $id, 'pass_hash' => password_hash(trim((string) $input['password']), PASSWORD_DEFAULT)));
        if (empty($r['ok'])) {
            cd_json($r);
        }
    }
    if (isset($input['is_active'])) {
        if ((int) $input['is_active'] !== 1 && $id === (int) $_SESSION['user_id']) {
            cd_json(array('ok' => false, 'error' => 'ปิดตัวเองไม่ได้'), 422);
        }
        $r = fwd_users('active', array('id' => $id, 'is_active' => ((int) $input['is_active'] === 1) ? 1 : 0));
        if (empty($r['ok'])) {
            cd_json($r);
        }
    }
    if (isset($input['display_name'])) {
        $r = fwd_users('display', array('id' => $id, 'display_name' => mb_substr(trim((string) $input['display_name']), 0, 150)));
        if (empty($r['ok'])) {
            cd_json($r);
        }
    }
    if (isset($input['groups']) && is_array($input['groups'])) {
        $gids = array();
        foreach ($input['groups'] as $gid) {
            $gid = (int) $gid;
            if ($gid > 0) {
                $gids[] = $gid;
            }
        }
        $r = fwd_users('groups', array('id' => $id, 'groups' => array_values(array_unique($gids))));
        if (empty($r['ok'])) {
            cd_json($r);
        }
    }
    cd_json(array('ok' => true, 'id' => $id));
}

$username = trim((string) (isset($input['username']) ? $input['username'] : ''));
$password = (string) (isset($input['password']) ? $input['password'] : '');
if ($username === '' || !preg_match('/^[A-Za-z0-9_.@-]{3,64}$/', $username)) {
    cd_json(array('ok' => false, 'error' => 'ชื่อผู้ใช้ 3–64 ตัว (a-z 0-9 _ . @ -)'), 422);
}
if (mb_strlen($password) < 4) {
    cd_json(array('ok' => false, 'error' => 'รหัสผ่านอย่างน้อย 4 ตัว'), 422);
}
$gids = array();
if (isset($input['groups']) && is_array($input['groups'])) {
    foreach ($input['groups'] as $gid) {
        $gid = (int) $gid;
        if ($gid > 0) {
            $gids[] = $gid;
        }
    }
    $gids = array_values(array_unique($gids));
}
$r = fwd_users('create', array(
    'username' => $username,
    'pass_hash' => password_hash($password, PASSWORD_DEFAULT),
    'display_name' => mb_substr(trim((string) (isset($input['display_name']) ? $input['display_name'] : '')), 0, 150),
    'groups' => $gids,
));
if (empty($r['ok']) || empty($r['id'])) {
    cd_json(is_array($r) ? $r : array('ok' => false, 'error' => 'สร้างไม่สำเร็จ'));
}
cd_json(array('ok' => true, 'id' => (int) $r['id']));
