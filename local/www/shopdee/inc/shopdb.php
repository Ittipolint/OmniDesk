<?php
// ShopDee LOCAL — PDO helper (Postgres postgres-rag, DB shopdee)
function shopdb()
{
    static $pdo = null;
    if ($pdo !== null) {
        return $pdo;
    }
    $dsn = sprintf('pgsql:host=%s;port=%d;dbname=%s', 'host.docker.internal', 5432, 'shopdee');
    $pdo = new PDO($dsn, 'raguser', 'ragpass123', array(
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false,
    ));
    return $pdo;
}

function shop_json($data, $code = 200)
{
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
}

function shop_input()
{
    $in = json_decode(file_get_contents('php://input'), true);
    return is_array($in) ? $in : $_POST;
}
