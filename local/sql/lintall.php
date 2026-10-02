<?php
// Lint all local ChatDesk PHP files. Run: docker exec chatdesk-web php /tmp/lintall.php
$files = new RecursiveIteratorIterator(new RecursiveDirectoryIterator('/var/www/html'));
$fail = 0;
foreach ($files as $f) {
    if (substr($f, -4) !== '.php') {
        continue;
    }
    exec('php -l ' . escapeshellarg($f) . ' 2>&1', $o, $c);
    if ($c) {
        $fail++;
        echo 'FAIL: ' . $f . PHP_EOL . implode(PHP_EOL, $o) . PHP_EOL;
    }
}
echo $fail ? ("FAILURES: $fail" . PHP_EOL) : "ALL LINT OK" . PHP_EOL;
