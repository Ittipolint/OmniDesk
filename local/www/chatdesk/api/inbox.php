<?php
/**
 * ChatDesk LOCAL — API: รายการห้องแชท (thin forwarder -> n8n api-read)
 * GET ?filter=all|unread|mine|closed&q=คำค้น
 */

require_once dirname(__DIR__) . '/inc/bootstrap.php';

cd_require_login();

$filter = isset($_GET['filter']) ? (string) $_GET['filter'] : 'all';
$q      = isset($_GET['q']) ? trim((string) $_GET['q']) : '';

$res = cd_n8n_post('api-read', array('resource' => 'inbox', 'filter' => $filter, 'q' => $q), 30);
if ($res['error'] !== null) {
    cd_json(array('ok' => false, 'error' => $res['error']), 502);
}
cd_json($res['data']);
