<?php
/**
 * EMORPHOSIS — Armazenamento e Consulta dos Sonhos Registrados no Prompt Inicial
 * - POST: Registra o sonho enviado pelo usuário em api/storage/dream_submissions.json
 *         e também espelha em /sonhos/respostas.json e /sonhos/respostas.txt
 * - GET:  Retorna a lista completa de sonhos registrados (JSON ou TXT)
 */
declare(strict_types=1);

date_default_timezone_set('America/Sao_Paulo');
header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');

$storageDir = __DIR__ . '/storage';
if (!is_dir($storageDir)) {
    @mkdir($storageDir, 0755, true);
}

$sonhosDir = dirname(__DIR__) . '/sonhos';
if (!is_dir($sonhosDir)) {
    @mkdir($sonhosDir, 0755, true);
}

$jsonFile = $storageDir . '/dream_submissions.json';
$publicJsonFile = $sonhosDir . '/respostas.json';
$publicTxtFile = $sonhosDir . '/respostas.txt';

function loadDreams(string $file): array {
    if (!is_file($file)) {
        return [];
    }
    $raw = @file_get_contents($file);
    if (!$raw) {
        return [];
    }
    $decoded = json_decode($raw, true);
    return is_array($decoded) ? $decoded : [];
}

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $format = strtolower(trim((string)($_GET['format'] ?? 'json')));
    $dreams = loadDreams($jsonFile);

    if ($format === 'txt') {
        header('Content-Type: text/plain; charset=utf-8');
        if (empty($dreams)) {
            echo "=== EMORPHOSIS // ARQUIVO DE SONHOS REGISTRADOS ===\n(Nenhuma resposta registrada ainda.)\n";
            exit;
        }
        $lines = ["=== EMORPHOSIS // ARQUIVO DE SONHOS REGISTRADOS (" . count($dreams) . ") ===\n"];
        foreach ($dreams as $idx => $item) {
            $num = str_pad((string)($idx + 1), 3, '0', STR_PAD_LEFT);
            $dt = (string)($item['date_br'] ?? $item['created_at'] ?? '');
            $loc = trim((string)($item['location'] ?? ''));
            $locTag = $loc !== '' ? " [{$loc}]" : '';
            $dreamTxt = (string)($item['dream'] ?? '');
            $lines[] = "[#{$num}] {$dt}{$locTag} -> {$dreamTxt}";
        }
        echo implode("\n", $lines) . "\n";
        exit;
    }

    header('Content-Type: application/json; charset=utf-8');
    echo json_encode([
        'ok' => true,
        'total' => count($dreams),
        'dreams' => $dreams
    ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Content-Type: application/json; charset=utf-8');
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'Method not allowed']);
    exit;
}

header('Content-Type: application/json; charset=utf-8');

$raw = file_get_contents('php://input') ?: '';
$payload = json_decode($raw, true);
if (!is_array($payload)) {
    $payload = $_POST;
}

$dream = trim((string)($payload['dream'] ?? ''));
$dream = preg_replace('/\s+/u', ' ', $dream) ?: '';
$dream = mb_substr($dream, 0, 300, 'UTF-8');

if ($dream === '') {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Empty dream']);
    exit;
}

$city = trim((string)($payload['city'] ?? ''));
$region = trim((string)($payload['region'] ?? ''));
$location = '';
if ($city !== '' && $region !== '') {
    $location = $city . ' - ' . $region;
} elseif ($city !== '') {
    $location = $city;
}

$dreams = loadDreams($jsonFile);

$entry = [
    'id' => 'drm_' . date('Ymd_His') . '_' . substr(md5($dream . microtime()), 0, 6),
    'dream' => $dream,
    'location' => $location !== '' ? $location : 'Brasil',
    'date_br' => date('d/m/Y H:i:s'),
    'created_at' => date('c'),
];

array_unshift($dreams, $entry);

// Limite de segurança de 5.000 registros
if (count($dreams) > 5000) {
    $dreams = array_slice($dreams, 0, 5000);
}

$encodedJson = json_encode($dreams, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
@file_put_contents($jsonFile, $encodedJson, LOCK_EX);
@file_put_contents($publicJsonFile, $encodedJson, LOCK_EX);

// Atualiza também o arquivo texto legível em /sonhos/respostas.txt
$txtLines = ["=== EMORPHOSIS // ARQUIVO DE SONHOS REGISTRADOS (" . count($dreams) . ") ===\n"];
foreach ($dreams as $idx => $item) {
    $num = str_pad((string)($idx + 1), 3, '0', STR_PAD_LEFT);
    $dt = (string)($item['date_br'] ?? '');
    $loc = (string)($item['location'] ?? 'Brasil');
    $dTxt = (string)($item['dream'] ?? '');
    $txtLines[] = "[#{$num}] {$dt} [{$loc}] -> {$dTxt}";
}
@file_put_contents($publicTxtFile, implode("\n", $txtLines) . "\n", LOCK_EX);

echo json_encode([
    'ok' => true,
    'total' => count($dreams),
    'entry' => $entry
], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
