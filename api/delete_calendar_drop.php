<?php
/**
 * EMORPHOSIS — Exclusão Rápida de Drops Agendados (Exclusivo Admin)
 * - Verifica chave/token de administrador via ADMIN_DROP_TOKEN (config_loader.php / .env)
 * - Remove o drop de api/storage/scheduled_drops.json
 * - Adiciona o UID / chave de deduplicação em api/storage/deleted_drops.json
 *   para ocultar imediatamente também eventos vindos do feed .ics e cancelar disparo de alerta
 */
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
date_default_timezone_set('America/Sao_Paulo');

require_once __DIR__ . '/config_loader.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'Method not allowed']);
    exit;
}

$configuredAdminToken = emorphosis_config('ADMIN_DROP_TOKEN');
if ($configuredAdminToken === '') {
    http_response_code(503);
    echo json_encode(['ok' => false, 'error' => 'Credencial de administrador não configurada no servidor (ADMIN_DROP_TOKEN).']);
    exit;
}

$raw = file_get_contents('php://input');
$data = json_decode((string)$raw, true);
if (!is_array($data)) {
    $data = $_POST;
}

$providedToken = trim((string)($data['admin_token'] ?? ''));
$sessionHash = hash_hmac('sha256', 'emorphosis_admin_session_v1', $configuredAdminToken);

$isAuthorized = $providedToken !== '' && (
    hash_equals($configuredAdminToken, $providedToken) ||
    hash_equals($sessionHash, $providedToken)
);

if (!$isAuthorized) {
    http_response_code(403);
    echo json_encode(['ok' => false, 'error' => 'Acesso negado. Credencial de administrador inválida.']);
    exit;
}

// Se for apenas validação de login admin
if (!empty($data['action']) && $data['action'] === 'verify') {
    echo json_encode([
        'ok' => true,
        'token_hash' => $sessionHash
    ]);
    exit;
}

$uid = trim((string)($data['uid'] ?? ''));
$dedupKey = trim((string)($data['dedup_key'] ?? ''));
$title = trim((string)($data['title'] ?? ''));
$timestamp = isset($data['timestamp']) ? (int)$data['timestamp'] : 0;

if ($uid === '' && $dedupKey === '') {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Identificador do drop ausente.']);
    exit;
}

$storageDir = __DIR__ . '/storage';
if (!is_dir($storageDir)) {
    @mkdir($storageDir, 0755, true);
}

// 1. Registra na lista de drops deletados/ocultados (deleted_drops.json)
$deletedFile = $storageDir . '/deleted_drops.json';
$deleted = [
    'uids' => [],
    'dedup_keys' => []
];
if (is_file($deletedFile)) {
    $parsedDel = json_decode((string)file_get_contents($deletedFile), true);
    if (is_array($parsedDel)) {
        $deleted['uids'] = isset($parsedDel['uids']) && is_array($parsedDel['uids']) ? $parsedDel['uids'] : [];
        $deleted['dedup_keys'] = isset($parsedDel['dedup_keys']) && is_array($parsedDel['dedup_keys']) ? $parsedDel['dedup_keys'] : [];
    }
}

if ($uid !== '' && !in_array($uid, $deleted['uids'], true)) {
    $deleted['uids'][] = $uid;
}
if ($dedupKey !== '' && !in_array($dedupKey, $deleted['dedup_keys'], true)) {
    $deleted['dedup_keys'][] = $dedupKey;
}
@file_put_contents($deletedFile, json_encode($deleted, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE), LOCK_EX);

// 2. Remove de scheduled_drops.json caso tenha sido adicionado pelo formulário
$customDropsFile = $storageDir . '/scheduled_drops.json';
$removedFromCustom = 0;
if (is_file($customDropsFile)) {
    $customDrops = json_decode((string)file_get_contents($customDropsFile), true);
    if (is_array($customDrops)) {
        $remaining = [];
        foreach ($customDrops as $cd) {
            $cdId = (string)($cd['id'] ?? '');
            $cdTs = isset($cd['timestamp']) ? (int)$cd['timestamp'] : 0;
            $cdTitle = (string)($cd['title'] ?? '');
            if (
                ($uid !== '' && $cdId === $uid) ||
                ($timestamp > 0 && $cdTs === $timestamp && ($title === '' || strcasecmp($cdTitle, $title) === 0))
            ) {
                $removedFromCustom++;
                continue;
            }
            $remaining[] = $cd;
        }
        if ($removedFromCustom > 0) {
            @file_put_contents($customDropsFile, json_encode($remaining, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), LOCK_EX);
        }
    }
}

echo json_encode([
    'ok' => true,
    'removed_uid' => $uid,
    'removed_dedup_key' => $dedupKey,
    'removed_from_scheduled' => $removedFromCustom
], JSON_UNESCAPED_UNICODE);
