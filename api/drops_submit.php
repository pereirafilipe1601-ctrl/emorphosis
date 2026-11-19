<?php
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
date_default_timezone_set('America/Sao_Paulo');

require_once __DIR__ . '/config_loader.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'Method not allowed']);
    exit;
}

$raw = file_get_contents('php://input') ?: '';
$payload = json_decode($raw, true);
if (!is_array($payload)) {
    $payload = $_POST;
}

$email = trim((string)($payload['email'] ?? ''));
$marca = trim((string)($payload['marca'] ?? ''));
$dropDate = trim((string)($payload['drop_date'] ?? ''));
$dropTime = trim((string)($payload['drop_time'] ?? '19:00'));
$linkPost = trim((string)($payload['link_post'] ?? ''));

if ($email === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Invalid email']);
    exit;
}

$marca = mb_substr($marca, 0, 120);
$linkPost = mb_substr($linkPost, 0, 300);

if ($dropDate === '' || !preg_match('/^\d{4}-\d{2}-\d{2}$/', $dropDate)) {
    $dropDate = date('Y-m-d', strtotime('+1 day'));
}
if ($dropTime === '' || !preg_match('/^\d{2}:\d{2}$/', $dropTime)) {
    $dropTime = '19:00';
}

$dropTimestamp = strtotime($dropDate . ' ' . $dropTime . ':00');
if ($dropTimestamp === false || $dropTimestamp <= 0) {
    $dropTimestamp = time() + 86400;
}

// Cruza o nome/@instagram da marca com o catálogo (assets/data/marcas.json)
$marcasFile = dirname(__DIR__) . '/assets/data/marcas.json';
$brands = [];
if (is_file($marcasFile)) {
    $decoded = json_decode((string)file_get_contents($marcasFile), true);
    if (is_array($decoded)) {
        $brands = $decoded;
    }
}

$matchedBrand = null;
$cleanQuery = mb_strtolower(ltrim($marca, '@'), 'UTF-8');
foreach ($brands as $b) {
    $bName = mb_strtolower((string)($b['name'] ?? ''), 'UTF-8');
    $bSlug = mb_strtolower((string)($b['slug'] ?? ''), 'UTF-8');
    $bHandle = mb_strtolower((string)($b['handle'] ?? ''), 'UTF-8');
    if ($cleanQuery !== '' && ($cleanQuery === $bName || $cleanQuery === $bSlug || $cleanQuery === $bHandle || strpos($bName, $cleanQuery) !== false || strpos($cleanQuery, $bName) !== false)) {
        $matchedBrand = $b;
        break;
    }
}

$brandTitleName = $matchedBrand ? (string)$matchedBrand['name'] : ($marca !== '' ? $marca : 'Marca Independente');
$brandSlug = $matchedBrand ? (string)$matchedBrand['slug'] : null;
$brandImg = $matchedBrand ? (string)$matchedBrand['img'] : 'assets/img/favicon.png';
$brandIgUrl = $matchedBrand ? (string)$matchedBrand['url'] : '';
$eventTitle = (stripos($brandTitleName, 'drop') === 0) ? $brandTitleName : ('Drop ' . $brandTitleName);

$storageDir = __DIR__ . '/storage';
if (!is_dir($storageDir)) {
    @mkdir($storageDir, 0755, true);
}

// 1. Adiciona AUTOMATICAMENTE ao calendário de drops (api/storage/scheduled_drops.json)
$scheduledFile = $storageDir . '/scheduled_drops.json';
$scheduledDrops = [];
if (is_file($scheduledFile)) {
    $existing = json_decode((string)file_get_contents($scheduledFile), true);
    if (is_array($existing)) {
        $scheduledDrops = $existing;
    }
}

$newDropEvent = [
    'id' => 'drop_' . time() . '_' . substr(md5($email . $brandTitleName . $dropTimestamp), 0, 8),
    'title' => $eventTitle,
    'marca' => $brandTitleName,
    'slug' => $brandSlug,
    'img' => $brandImg,
    'ig_url' => $brandIgUrl,
    'link_post' => $linkPost,
    'submitted_by' => $email,
    'drop_date' => $dropDate,
    'drop_time' => $dropTime,
    'has_time' => true,
    'drop_iso' => date('c', $dropTimestamp),
    'timestamp' => $dropTimestamp,
    'created_at' => gmdate('c'),
];

array_unshift($scheduledDrops, $newDropEvent);
@file_put_contents(
    $scheduledFile,
    json_encode($scheduledDrops, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
    LOCK_EX
);

// Se o mesmo drop havia sido excluído antes, libera a chave em deleted_drops.json
$deletedFile = $storageDir . '/deleted_drops.json';
if (is_file($deletedFile)) {
    $parsedDel = json_decode((string)file_get_contents($deletedFile), true);
    if (is_array($parsedDel) && !empty($parsedDel['dedup_keys']) && is_array($parsedDel['dedup_keys'])) {
        $slugVal = $brandSlug ?: strtolower(preg_replace('/[^a-zA-Z0-9]+/', ' ', $brandTitleName));
        $newDedupKey = trim((string)$slugVal) . '_' . date('Y-m-d_H:i', $dropTimestamp);
        $parsedDel['dedup_keys'] = array_values(array_filter(
            $parsedDel['dedup_keys'],
            static fn($k) => $k !== $newDedupKey
        ));
        @file_put_contents($deletedFile, json_encode($parsedDel, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE), LOCK_EX);
    }
}

// 2. Grava histórico em drops_submissions.jsonl
@file_put_contents(
    $storageDir . '/drops_submissions.jsonl',
    json_encode($newDropEvent, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . PHP_EOL,
    FILE_APPEND | LOCK_EX
);

// 3. Se houver Webhook do Google Apps Script configurado (api/storage/gcal_webhook.txt),
//    insere automaticamente também direto na conta do Google Calendar (e279d9...group.calendar.google.com)
$gcalWebhookFile = $storageDir . '/gcal_webhook.txt';
$gcalSynced = false;
if (is_file($gcalWebhookFile)) {
    $webhookUrl = trim((string)file_get_contents($gcalWebhookFile));
    if ($webhookUrl !== '' && strpos($webhookUrl, 'https://script.google.com/') === 0) {
        $ctx = stream_context_create([
            'http' => [
                'method' => 'POST',
                'header' => "Content-Type: application/json\r\n",
                'content' => json_encode([
                    'calendarId' => 'e279d9d10a587ca926785f28efb4fc3cda446fc8b7a4adecec5a111bf316dd01@group.calendar.google.com',
                    'title' => $eventTitle,
                    'startIso' => date('c', $dropTimestamp),
                    'endIso' => date('c', $dropTimestamp + 3600),
                    'description' => trim("Marca: {$brandTitleName}\nPost/Link: {$linkPost}\nSugerido por: {$email}"),
                ]),
                'timeout' => 8,
            ]
        ]);
        $resp = @file_get_contents($webhookUrl, false, $ctx);
        if ($resp !== false) {
            $gcalSynced = true;
            // Limpa o cache do .ics para refletir na hora
            if (is_file($storageDir . '/ical_cache.ics')) {
                @unlink($storageDir . '/ical_cache.ics');
            }
        }
    }
}

// 4. Envia e-mail estilizado para o e-mail admin configurado (ADMIN_NOTIFY_EMAIL)
$toProjectEmail = emorphosis_config('ADMIN_NOTIFY_EMAIL');
$marcaDisplay = $brandTitleName;
$dataDropFormatada = date('d/m/Y \à\s H:i', $dropTimestamp) . ' (Horário de Brasília)';
$dataHoraEnvio = date('d/m/Y \à\s H:i:s');

$utcStart = gmdate('Ymd\THis\Z', $dropTimestamp);
$utcEnd = gmdate('Ymd\THis\Z', $dropTimestamp + 3600);
$gcalAddUrl = 'https://calendar.google.com/calendar/render?action=TEMPLATE'
    . '&text=' . urlencode($eventTitle)
    . '&dates=' . $utcStart . '/' . $utcEnd
    . '&details=' . urlencode("Drop sugerido no Radar Emorphosis\nMarca: {$brandTitleName}\nPost: {$linkPost}")
    . '&src=e279d9d10a587ca926785f28efb4fc3cda446fc8b7a4adecec5a111bf316dd01%40group.calendar.google.com';

$subjectRaw = 'EMORPHOSIS // Drop Adicionado ao Calendário: ' . $eventTitle . ' (' . date('d/m H:i', $dropTimestamp) . ')';
$subject = '=?UTF-8?B?' . base64_encode($subjectRaw) . '?=';

$linkHtml = $linkPost !== ''
    ? '<a href="' . htmlspecialchars($linkPost, ENT_QUOTES, 'UTF-8') . '" style="color:#52ff5e;text-decoration:underline;">' . htmlspecialchars($linkPost, ENT_QUOTES, 'UTF-8') . '</a>'
    : '<span style="color:#68a86e;">(Não informado)</span>';

$htmlBody = '<!DOCTYPE html>
<html lang="pt-BR">
<body style="margin:0;padding:24px;background-color:#000000;color:#19f028;font-family:Consolas,Monaco,monospace;">
  <div style="max-width:580px;margin:0 auto;background-color:#020803;border:2px solid #39ff48;border-radius:14px;padding:28px;box-shadow:0 0 24px rgba(25,240,40,0.3);">
    <div style="font-size:11px;letter-spacing:2px;color:#52ff5e;margin-bottom:8px;">EMORPHOSIS // AUTOMAÇÃO DO CALENDÁRIO DE DROPS</div>
    <h1 style="margin:0 0 14px;font-size:22px;color:#39ff48;">Novo Drop Adicionado Automaticamente!</h1>
    <p style="font-size:14px;line-height:1.6;color:#d6ffda;margin:0 0 18px;">
      Um novo drop foi enviado na aba <strong>C4L3NDAR10</strong> e já foi adicionado automaticamente ao calendário do site e à fila de disparo de e-mails (1h antes):
    </p>
    <div style="background:#000000;border:1.5px solid #19f028;border-radius:10px;padding:18px;margin-bottom:20px;">
      <p style="margin:0 0 10px;font-size:14px;color:#d6ffda;">
        <strong style="color:#39ff48;">EVENTO NO CALENDÁRIO:</strong> ' . htmlspecialchars($eventTitle, ENT_QUOTES, 'UTF-8') . '
      </p>
      <p style="margin:0 0 10px;font-size:14px;color:#d6ffda;">
        <strong style="color:#39ff48;">DATA E HORÁRIO DO DROP:</strong> ' . htmlspecialchars($dataDropFormatada, ENT_QUOTES, 'UTF-8') . '
      </p>
      <p style="margin:0 0 10px;font-size:14px;color:#d6ffda;">
        <strong style="color:#39ff48;">E-MAIL DO USUÁRIO:</strong> ' . htmlspecialchars($email, ENT_QUOTES, 'UTF-8') . '
      </p>
      <p style="margin:0;font-size:14px;color:#d6ffda;">
        <strong style="color:#39ff48;">LINK DO POST / ANÚNCIO:</strong> ' . $linkHtml . '
      </p>
    </div>
    <p style="margin:0 0 12px;text-align:center;">
      <a href="' . htmlspecialchars($gcalAddUrl, ENT_QUOTES, 'UTF-8') . '" style="display:inline-block;background:#041707;color:#39ff48;border:2px solid #39ff48;padding:11px 22px;border-radius:10px;text-decoration:none;font-weight:bold;font-size:13px;">+ ESPELHAR NO GOOGLE CALENDAR ↗</a>
    </p>
  </div>
</body>
</html>';

$headers = [
    'MIME-Version: 1.0',
    'Content-Type: text/html; charset=UTF-8',
    'From: Emorphosis Drops <noreply@emorphosis.com.br>',
    'Reply-To: ' . $email,
    'X-Mailer: EmorphosisDropRadar/1.0'
];

$mailSent = false;
if ($toProjectEmail !== '' && filter_var($toProjectEmail, FILTER_VALIDATE_EMAIL)) {
    $mailSent = @mail($toProjectEmail, $subject, $htmlBody, implode("\r\n", $headers));
}

echo json_encode([
    'ok' => true,
    'mail_sent' => $mailSent,
    'gcal_synced' => $gcalSynced,
    'event' => $newDropEvent,
], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
