<?php
// ShopDee LOCAL — API สินค้า (อ่านอย่างเดียว)
// GET ?op=list&category=&q=&sort=pop|new|price_asc|price_desc|rating&page=&per_page=
// GET ?op=get&id= | ?op=cats
require_once __DIR__ . '/../inc/shopdb.php';

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    shop_json(array('ok' => false, 'error' => 'GET เท่านั้น'), 405);
}
$op = isset($_GET['op']) ? (string) $_GET['op'] : 'list';
try {
    $db = shopdb();
    if ($op === 'cats') {
        $st = $db->query("SELECT category, COUNT(*) AS n FROM shop_products WHERE is_active GROUP BY category ORDER BY category");
        shop_json(array('ok' => true, 'cats' => $st->fetchAll()));
    }
    if ($op === 'get') {
        $id = (int) (isset($_GET['id']) ? $_GET['id'] : 0);
        $st = $db->prepare('SELECT * FROM shop_products WHERE id = ? AND is_active');
        $st->execute(array($id));
        $row = $st->fetch();
        if (!$row) {
            shop_json(array('ok' => false, 'error' => 'ไม่พบสินค้า'), 404);
        }
        shop_json(array('ok' => true, 'item' => $row));
    }
    // list
    $where = array('is_active');
    $args = array();
    $cat = trim((string) (isset($_GET['category']) ? $_GET['category'] : ''));
    if ($cat !== '') {
        $where[] = 'category = ?';
        $args[] = $cat;
    }
    $q = trim((string) (isset($_GET['q']) ? $_GET['q'] : ''));
    if ($q !== '') {
        $where[] = '(name ILIKE ? OR description ILIKE ? OR shop_name ILIKE ?)';
        $args[] = '%' . $q . '%';
        $args[] = '%' . $q . '%';
        $args[] = '%' . $q . '%';
    }
    $sort = isset($_GET['sort']) ? (string) $_GET['sort'] : 'pop';
    $order = 'sold DESC, rating DESC';
    if ($sort === 'new') {
        $order = 'id DESC';
    } elseif ($sort === 'price_asc') {
        $order = 'price ASC';
    } elseif ($sort === 'price_desc') {
        $order = 'price DESC';
    } elseif ($sort === 'rating') {
        $order = 'rating DESC, reviews DESC';
    }
    $page = max(1, (int) (isset($_GET['page']) ? $_GET['page'] : 1));
    $per = min(48, max(1, (int) (isset($_GET['per_page']) ? $_GET['per_page'] : 24)));
    $ws = implode(' AND ', $where);
    $st = $db->prepare("SELECT COUNT(*) FROM shop_products WHERE $ws");
    $st->execute($args);
    $total = (int) $st->fetchColumn();
    $st = $db->prepare("SELECT * FROM shop_products WHERE $ws ORDER BY $order LIMIT $per OFFSET " . (($page - 1) * $per));
    $st->execute($args);
    shop_json(array('ok' => true, 'total' => $total, 'page' => $page,
                    'per_page' => $per, 'items' => $st->fetchAll()));
} catch (Exception $e) {
    shop_json(array('ok' => false, 'error' => 'DB ผิดพลาด'), 500);
}
