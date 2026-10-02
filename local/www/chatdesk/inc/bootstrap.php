<?php
/**
 * ChatDesk — bootstrap: โหลด config, เปิด session, ต่อฐานข้อมูล
 */

if (defined('CD_BOOTSTRAPPED')) {
    return;
}
define('CD_BOOTSTRAPPED', true);

define('CD_ROOT', dirname(__DIR__));
define('CD_VERSION', '1.0.0');

$CFG = require CD_ROOT . '/config.php';

if (!empty($CFG['debug'])) {
    ini_set('display_errors', '1');
    error_reporting(E_ALL);
} else {
    ini_set('display_errors', '0');
    error_reporting(E_ALL & ~E_NOTICE & ~E_DEPRECATED);
}

date_default_timezone_set($CFG['app']['timezone']);

if (session_status() !== PHP_SESSION_ACTIVE) {
    $secure = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off')
        || (isset($_SERVER['HTTP_X_FORWARDED_PROTO']) && $_SERVER['HTTP_X_FORWARDED_PROTO'] === 'https');
    session_set_cookie_params(array(
        'lifetime' => 0,
        'path'     => '/',
        'secure'   => $secure,
        'httponly' => true,
        'samesite' => 'Lax',
    ));
    session_name('CHATDESK');
    session_start();
}

require_once CD_ROOT . '/inc/db.php';
require_once CD_ROOT . '/inc/helpers.php';
