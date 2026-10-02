<?php
// Seed admin user (run inside chatdesk-web container).
// Usage: docker exec chatdesk-web php /var/www/html/../sql/seed_admin.php
// (Placed in www/ temporarily during setup; safe to delete afterwards.)
$dsn = getenv('CD_DSN') ?: 'pgsql:host=host.docker.internal;port=5432;dbname=chatdesk';
$pdo = new PDO($dsn, 'raguser', 'ragpass123', array(PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION));
$hash = password_hash('10203040', PASSWORD_DEFAULT);
$pdo->prepare("INSERT INTO cd_users (username, pass_hash, display_name) VALUES ('admin', ?, 'Administrator') ON CONFLICT (username) DO UPDATE SET pass_hash = EXCLUDED.pass_hash")
    ->execute(array($hash));
$pdo->exec("INSERT INTO cd_user_groups (user_id, group_id) SELECT u.id, g.id FROM cd_users u, cd_groups g WHERE u.username='admin' AND g.name='ADMIN' ON CONFLICT DO NOTHING");
echo "admin seeded\n";
