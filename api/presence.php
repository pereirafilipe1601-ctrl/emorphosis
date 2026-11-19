<?php
/**
 * EMORPHOSIS — Radar de Presença Seguro (Cidade/UF + Célula de Pixel no Mapa)
 * - NENHUMA coordenada GPS exata (rua/bairro) ou endereço IP é armazenada em disco ou exposta na API.
 * - Armazena e retorna apenas a Cidade/UF (ex: "Curitiba", "PR") e o pixel quantizado (mx, my) no mapa 2560x1440.
 */
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: SAMEORIGIN');
header('Referrer-Policy: no-referrer');

$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origin === 'https://emorphosis.com.br' || $origin === 'https://www.emorphosis.com.br') {
    header('Access-Control-Allow-Origin: ' . $origin);
} else {
    header('Access-Control-Allow-Origin: https://emorphosis.com.br');
}
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

date_default_timezone_set('America/Sao_Paulo');

require_once __DIR__ . '/config_loader.php';

$storageDir = __DIR__ . '/storage';
if (!is_dir($storageDir)) {
    @mkdir($storageDir, 0755, true);
}

$activeFile = $storageDir . '/active_nodes_anon.json';
$uniqueFile = $storageDir . '/unique_visitors.json';
$ACTIVE_TTL = 120;

$MIN_X = 504;
$MAX_X = 1325;
$MIN_Y = 333;
$MAX_Y = 1102;

function get_visitor_ip(): string {
    $keys = [
        'HTTP_CF_CONNECTING_IP',
        'HTTP_X_REAL_IP',
        'HTTP_X_FORWARDED_FOR',
        'HTTP_CLIENT_IP',
        'REMOTE_ADDR'
    ];
    foreach ($keys as $k) {
        if (!empty($_SERVER[$k])) {
            $raw = trim((string)$_SERVER[$k]);
            $parts = explode(',', $raw);
            $ip = trim($parts[0]);
            if (filter_var($ip, FILTER_VALIDATE_IP)) {
                return $ip;
            }
        }
    }
    return '127.0.0.1';
}

function latlon_to_coarse_pixel(float $lat, float $lon): array {
    $lat = max(-33.75, min(5.27, $lat));
    $lon = max(-73.98, min(-34.79, $lon));

    $normX = ($lon - (-73.9828)) / (-34.7931 - (-73.9828));
    $normY = (5.2718 - $lat) / (5.2718 - (-33.7512));

    $rawX = 496.0 + $normX * (1333.0 - 496.0) - $normY * 14.0;
    $rawY = 325.0 + $normY * (1110.0 - 325.0) + ($normX - 0.35) * 18.0;

    $mx = (int)(round($rawX / 6.0) * 6);
    $my = (int)(round($rawY / 6.0) * 6);

    return [
        'mx' => max(504, min(1325, $mx)),
        'my' => max(333, min(1102, $my))
    ];
}

function resolve_city_and_pixel_from_ip(string $ip): array {
    if ($ip === '127.0.0.1' || $ip === '::1' || strpos($ip, '192.168.') === 0 || strpos($ip, '10.') === 0) {
        return ['city' => 'Curitiba', 'region' => 'PR', 'mx' => 1001, 'my' => 928];
    }

    if (function_exists('curl_init')) {
        $ch = curl_init('https://ipwho.is/' . rawurlencode($ip));
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_CONNECTTIMEOUT => 2,
            CURLOPT_TIMEOUT        => 2,
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_USERAGENT      => 'EmorphosisAnonRadar/2.1'
        ]);
        $raw = curl_exec($ch);
        $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        if ($raw && $code >= 200 && $code < 300) {
            $d = json_decode((string)$raw, true);
            if (is_array($d) && !empty($d['success']) && strtoupper((string)($d['country_code'] ?? '')) === 'BR') {
                $city = trim(strip_tags((string)($d['city'] ?? 'Brasil')));
                $reg = strtoupper(trim(strip_tags((string)($d['region_code'] ?? 'BR'))));
                $lat = (float)($d['latitude'] ?? -25.4284);
                $lon = (float)($d['longitude'] ?? -49.2733);
                if ($reg === 'PR' && $lat >= -26.15 && $lat <= -25.05 && $lon >= -49.85 && $lon <= -48.85) {
                    return ['city' => $city !== '' ? $city : 'Curitiba', 'region' => 'PR', 'mx' => 1001, 'my' => 928];
                }
                $px = latlon_to_coarse_pixel($lat, $lon);
                return [
                    'city' => $city !== '' ? $city : 'Brasil',
                    'region' => $reg !== '' ? $reg : 'BR',
                    'mx' => $px['mx'],
                    'my' => $px['my']
                ];
            }
        }
    }

    return ['city' => 'Curitiba', 'region' => 'PR', 'mx' => 1001, 'my' => 928];
}

$input = [];
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $rawBody = file_get_contents('php://input');
    if ($rawBody) {
        $decoded = json_decode($rawBody, true);
        if (is_array($decoded)) {
            $input = $decoded;
        }
    }
}

$ip = get_visitor_ip();
$rawUid = isset($input['uid']) ? preg_replace('/[^a-zA-Z0-9_-]/', '', (string)$input['uid']) : '';
if ($rawUid === '' || strlen($rawUid) < 6) {
    $rawUid = 'u_' . substr(hash('sha256', $ip . '_' . ($_SERVER['HTTP_USER_AGENT'] ?? 'ua')), 0, 16);
}

$sid = substr(hash_hmac('sha256', $rawUid, emorphosis_runtime_secret('PRESENCE_SID_SALT')), 0, 16);
$ipHash = substr(hash_hmac('sha256', $ip, emorphosis_runtime_secret('PRESENCE_IP_SALT')), 0, 24);

$clientMx = isset($input['mx']) && is_numeric($input['mx']) ? (int)$input['mx'] : null;
$clientMy = isset($input['my']) && is_numeric($input['my']) ? (int)$input['my'] : null;
$clientCity = isset($input['city']) ? mb_substr(trim(strip_tags((string)$input['city'])), 0, 42) : '';
$clientRegion = isset($input['region']) ? strtoupper(mb_substr( preg_replace('/[^a-zA-Z]/', '', (string)$input['region']), 0, 3)) : '';

$now = time();

$fp = @fopen($activeFile, 'c+');
$activeNodes = [];
if ($fp) {
    @flock($fp, LOCK_EX);
    $contents = stream_get_contents($fp);
    if ($contents) {
        $parsed = json_decode($contents, true);
        if (is_array($parsed)) {
            $activeNodes = $parsed;
        }
    }
}

foreach ($activeNodes as $k => $node) {
    $lastSeen = isset($node['last_seen']) ? (int)$node['last_seen'] : 0;
    if (($now - $lastSeen) > $ACTIVE_TTL) {
        unset($activeNodes[$k]);
    }
}

$existing = $activeNodes[$sid] ?? null;

if ($clientMx !== null && $clientMy !== null && $clientMx >= $MIN_X && $clientMx <= $MAX_X && $clientMy >= $MIN_Y && $clientMy <= $MAX_Y) {
    $mx = (int)(round($clientMx / 6.0) * 6);
    $my = (int)(round($clientMy / 6.0) * 6);
    $mx = max($MIN_X, min($MAX_X, $mx));
    $my = max($MIN_Y, min($MAX_Y, $my));
    if ($clientCity !== '') {
        $city = $clientCity;
        $region = $clientRegion !== '' ? $clientRegion : 'BR';
    } elseif (!empty($existing['city']) && $existing['city'] !== 'Brasil') {
        $city = (string)$existing['city'];
        $region = (string)($existing['region'] ?? 'BR');
    } else {
        $pt = resolve_city_and_pixel_from_ip($ip);
        $city = $pt['city'];
        $region = $pt['region'];
    }
} elseif (is_array($existing) && isset($existing['mx'], $existing['my']) && !empty($existing['city']) && $existing['city'] !== 'Brasil') {
    $mx = (int)$existing['mx'];
    $my = (int)$existing['my'];
    $city = (string)$existing['city'];
    $region = (string)($existing['region'] ?? 'BR');
} else {
    $pt = resolve_city_and_pixel_from_ip($ip);
    $mx = $pt['mx'];
    $my = $pt['my'];
    $city = $pt['city'];
    $region = $pt['region'];
}

$activeNodes[$sid] = [
    'city' => $city,
    'region' => $region,
    'mx' => $mx,
    'my' => $my,
    'last_seen' => $now
];

if ($fp) {
    ftruncate($fp, 0);
    rewind($fp);
    fwrite($fp, json_encode($activeNodes, JSON_UNESCAPED_UNICODE));
    fflush($fp);
    @flock($fp, LOCK_UN);
    fclose($fp);
}

// Contador PERMANENTE de pessoas únicas por IP — cada IP soma 1 vez e o total nunca diminui
$ufp = @fopen($uniqueFile, 'c+');
$uniqueData = [
    'count' => 0,
    'ips' => []
];
$uniqueMaxFile = $storageDir . '/unique_visitors_max.txt';
$savedMax = is_file($uniqueMaxFile) ? (int)@file_get_contents($uniqueMaxFile) : 0;

if ($ufp && @flock($ufp, LOCK_EX)) {
    $uContents = stream_get_contents($ufp);
    $readOk = true;
    if ($uContents !== false && $uContents !== '') {
        $uParsed = json_decode($uContents, true);
        if (is_array($uParsed)) {
            $uniqueData['count'] = isset($uParsed['count']) ? (int)$uParsed['count'] : 0;
            $uniqueData['ips'] = isset($uParsed['ips']) && is_array($uParsed['ips']) ? $uParsed['ips'] : [];
        } else {
            // Arquivo ilegível: não sobrescreve para não perder o histórico
            $readOk = false;
        }
    }

    if ($readOk) {
        $previousTotal = max((int)$uniqueData['count'], $savedMax);

        // Cada IP (guardado só como hash HMAC irreversível) soma 1 única vez, para sempre
        if (!isset($uniqueData['ips'][$ipHash])) {
            $uniqueData['ips'][$ipHash] = gmdate('Y-m-d');
            $uniqueData['count'] = $previousTotal + 1;
        } else {
            $uniqueData['count'] = $previousTotal;
        }

        ftruncate($ufp, 0);
        rewind($ufp);
        fwrite($ufp, json_encode($uniqueData, JSON_UNESCAPED_UNICODE));
        fflush($ufp);

        if ($uniqueData['count'] > $savedMax) {
            @file_put_contents($uniqueMaxFile, (string)$uniqueData['count'], LOCK_EX);
        }
    } else {
        $uniqueData['count'] = $savedMax;
    }
    @flock($ufp, LOCK_UN);
}
if ($ufp) {
    fclose($ufp);
}

$totalUniqueVisitors = max(1, (int)$uniqueData['count'], $savedMax);

$publicNodes = [];
foreach ($activeNodes as $k => $n) {
    $publicNodes[] = [
        'is_self' => ($k === $sid),
        'city' => $n['city'] ?? 'Brasil',
        'region' => $n['region'] ?? 'BR',
        'mx' => (int)$n['mx'],
        'my' => (int)$n['my']
    ];
}

echo json_encode([
    'ok' => true,
    'online_count' => count($publicNodes),
    'unique_visitors' => $totalUniqueVisitors,
    'ttl' => $ACTIVE_TTL,
    'users' => $publicNodes
], JSON_UNESCAPED_UNICODE);
