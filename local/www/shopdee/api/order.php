<?php
// ShopDee LOCAL — API คำสั่งซื้อ
// POST { op: create, items: [{id, qty}], name, phone, address?, note?, payment?: cod|transfer }
// POST { op: get, code } / { op: byphone, phone }
require_once __DIR__ . '/../inc/shopdb.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    shop_json(array('ok' => false, 'error' => 'ต้องเรียกด้วย POST เท่านั้น'), 405);
}
$in = shop_input();
$op = isset($in['op']) ? (string) $in['op'] : 'create';
try {
    $db = shopdb();
    if ($op === 'get') {
        $code = trim((string) (isset($in['code']) ? $in['code'] : ''));
        $st = $db->prepare('SELECT * FROM shop_orders WHERE code = ?');
        $st->execute(array($code));
        $o = $st->fetch();
        if (!$o) {
            shop_json(array('ok' => false, 'error' => 'ไม่พบคำสั่งซื้อ'), 404);
        }
        $st = $db->prepare('SELECT product_id, name, price, qty FROM shop_order_items WHERE order_id = ? ORDER BY id');
        $st->execute(array($o['id']));
        $o['items'] = $st->fetchAll();
        shop_json(array('ok' => true, 'order' => $o));
    }
    if ($op === 'byphone') {
        $phone = preg_replace('/[^0-9+]/', '', (string) (isset($in['phone']) ? $in['phone'] : ''));
        if (strlen($phone) < 9) {
            shop_json(array('ok' => false, 'error' => 'เบอร์โทรไม่ถูกต้อง'), 422);
        }
        $st = $db->prepare('SELECT code, total, status, created_at, (SELECT COUNT(*) FROM shop_order_items i WHERE i.order_id = o.id) AS lines FROM shop_orders o WHERE cust_phone = ? ORDER BY id DESC LIMIT 20');
        $st->execute(array($phone));
        shop_json(array('ok' => true, 'orders' => $st->fetchAll()));
    }
    // create
    $items = isset($in['items']) && is_array($in['items']) ? $in['items'] : array();
    if (!$items) {
        shop_json(array('ok' => false, 'error' => 'ตะกร้าว่าง'), 422);
    }
    $name = mb_substr(trim((string) (isset($in['name']) ? $in['name'] : '')), 0, 120);
    $phone = preg_replace('/[^0-9+]/', '', (string) (isset($in['phone']) ? $in['phone'] : ''));
    if ($name === '' || strlen($phone) < 9) {
        shop_json(array('ok' => false, 'error' => 'ชื่อ/เบอร์โทรไม่ถูกต้อง'), 422);
    }
    $address = mb_substr(trim((string) (isset($in['address']) ? $in['address'] : '')), 0, 500);
    $note = mb_substr(trim((string) (isset($in['note']) ? $in['note'] : '')), 0, 500);
    $payment = isset($in['payment']) && $in['payment'] === 'transfer' ? 'transfer' : 'cod';
    // อ่านราคาจริงจาก DB ทุกครั้ง (ไม่เชื่อราคาจาก client)
    $lines = array();
    $subtotal = 0;
    foreach ($items as $it) {
        $pid = (int) (isset($it['id']) ? $it['id'] : 0);
        $qty = min(99, max(1, (int) (isset($it['qty']) ? $it['qty'] : 1)));
        if ($pid <= 0) {
            continue;
        }
        $st = $db->prepare('SELECT id, sku, name, price, stock FROM shop_products WHERE id = ? AND is_active');
        $st->execute(array($pid));
        $p = $st->fetch();
        if (!$p) {
            shop_json(array('ok' => false, 'error' => 'มีสินค้าที่ไม่มีขายแล้ว (id ' . $pid . ')'), 422);
        }
        if ($p['stock'] < $qty) {
            shop_json(array('ok' => false, 'error' => 'สต็อกไม่พอ: ' . $p['name'] . ' (เหลือ ' . (int) $p['stock'] . ')'), 422);
        }
        $lines[] = array('id' => (int) $p['id'], 'sku' => isset($p['sku']) ? (string) $p['sku'] : '', 'name' => $p['name'], 'price' => (int) $p['price'], 'qty' => $qty);
        $subtotal += (int) $p['price'] * $qty;
    }
    if (!$lines) {
        shop_json(array('ok' => false, 'error' => 'ตะกร้าว่าง'), 422);
    }
    $shipping = $subtotal >= 299 ? 0 : 35;
    $discount = 0;
    $coupon = strtoupper(trim((string) (isset($in['coupon']) ? $in['coupon'] : '')));
    if ($coupon === 'SHOPDEE50' && $subtotal >= 500) {
        $discount = min(50, $subtotal);
    }
    $total = $subtotal - $discount + $shipping;
    $code = 'SD' . date('ymdHis') . strtoupper(substr(md5(uniqid((string) mt_rand(), true)), 0, 4));
    $db->beginTransaction();
    $st = $db->prepare('INSERT INTO shop_orders (code, cust_name, cust_phone, address, note, subtotal, discount, shipping, total, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)');
    $st->execute(array($code, $name, $phone, $address, $note . ($payment === 'transfer' ? ' [โอน]' : ' [COD]') . ($discount ? ' [คูปอง SHOPDEE50]' : ''), $subtotal, $discount, $shipping, $total, $payment === 'transfer' ? 'await_payment' : 'pending'));
    $oid = (int) $db->lastInsertId();
    $stItem = $db->prepare('INSERT INTO shop_order_items (order_id, product_id, name, price, qty) VALUES (?, ?, ?, ?, ?)');
    $stStock = $db->prepare('UPDATE shop_products SET stock = stock - ?, sold = sold + ? WHERE id = ?');
    foreach ($lines as $ln) {
        $stItem->execute(array($oid, $ln['id'], $ln['name'], $ln['price'], $ln['qty']));
        $stStock->execute(array($ln['qty'], $ln['qty'], $ln['id']));
    }
    $db->commit();
    // ส่งลูกค้าเข้า Odoo (best-effort: ห้ามทำให้ checkout พัง)
    // op=order -> upsert Contact ตามเบอร์ + สร้าง Sale Order (confirm) + draft invoice + ปิด Lead ที่เปิดอยู่
    $refUid = isset($in['userId']) ? trim((string) $in['userId']) : '';
    shop_odoo_lead(array('op' => 'order', 'name' => $name, 'phone' => $phone, 'address' => $address,
        'note' => $note, 'payment' => $payment, 'code' => $code, 'total' => $total,
        'items' => $lines, 'channel' => 'shopweb',
        'external_user_id' => preg_match('/^WEB_[A-Za-z0-9_-]{1,64}$/', $refUid) ? $refUid : ''));
    shop_json(array('ok' => true, 'code' => $code, 'total' => $total, 'shipping' => $shipping, 'lines' => count($lines)));
} catch (Exception $e) {
    if (isset($db) && $db->inTransaction()) {
        $db->rollBack();
    }
    $msg = $e->getMessage();
    if (strpos($msg, 'สต็อกไม่พอ') === 0 || strpos($msg, 'มีสินค้า') === 0) {
        shop_json(array('ok' => false, 'error' => $msg), 422);
    }
    shop_json(array('ok' => false, 'error' => 'สั่งซื้อไม่สำเร็จ'), 500);
}

// ส่งข้อมูลลูกค้า/ออเดอร์เข้า Odoo CRM ผ่าน n8n (best-effort 5 วิ, ห้าม throw)
function shop_odoo_lead($order)
{
    if (!function_exists('curl_init')) {
        return;
    }
    $ch = curl_init('http://host.docker.internal:5678/webhook/api-odoo-lead');
    curl_setopt_array($ch, array(
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode($order, JSON_UNESCAPED_UNICODE),
        CURLOPT_HTTPHEADER => array('Content-Type: application/json; charset=utf-8'),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 5,
        CURLOPT_CONNECTTIMEOUT => 3,
        CURLOPT_FOLLOWLOCATION => false,
    ));
    @curl_exec($ch);
    curl_close($ch);
}
