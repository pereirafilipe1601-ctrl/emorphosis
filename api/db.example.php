<?php
/**
 * EMORPHOSIS — Configuração PDO MySQL (Hostinger)
 * Copie este arquivo para api/db.php no servidor (ou via deploy SSH)
 * com os dados criados em hPanel -> Bancos de Dados -> Gerenciamento.
 */

declare(strict_types=1);

$DB_HOST = getenv('DB_HOST') ?: 'localhost';
$DB_NAME = getenv('DB_NAME') ?: 'u000000000_emorphosis';
$DB_USER = getenv('DB_USER') ?: 'u000000000_admin';
$DB_PASS = getenv('DB_PASS') ?: 'SUA_SENHA_AQUI';

try {
    $pdo = new PDO(
        "mysql:host={$DB_HOST};dbname={$DB_NAME};charset=utf8mb4",
        $DB_USER,
        $DB_PASS,
        [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ]
    );
} catch (PDOException $e) {
    http_response_code(500);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['ok' => false, 'error' => 'Database connection failed']);
    exit;
}
