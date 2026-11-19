<?php
declare(strict_types=1);

/* ==========================================================================
   EMORPHOSIS — Disparador Automático de Alertas de Drop (1 Hora Antes)
   - Sincroniza com o Google Calendar oficial da Emorphosis (.ics) e com
     api/storage/scheduled_drops.json.
   - Identifica quais marcas do catálogo (assets/data/marcas.json) participarão do drop.
   - Quando falta ~1 hora (janela entre 15 e 75 minutos antes do início),
     envia um e-mail para cada usuário inscrito naquela marca informando:
       1. Qual marca realizará o drop
       2. O horário exato do drop (Horário de Brasília)
       3. O link oficial do Instagram da marca
   ========================================================================== */

header('Content-Type: application/json; charset=utf-8');
date_default_timezone_set('America/Sao_Paulo');

require_once __DIR__ . '/config_loader.php';

$storageDir = __DIR__ . '/storage';
if (!is_dir($storageDir)) {
    @mkdir($storageDir, 0755, true);
}

$mode = (string)($_GET['mode'] ?? $_POST['mode'] ?? 'cron');

// Se chamado via web-ping automático dos visitantes, limita a 1 verificação a cada 3 minutos
$lastRunFile = $storageDir . '/last_cron_run.txt';
if ($mode === 'ping' && is_file($lastRunFile)) {
    $lastTs = (int)trim((string)file_get_contents($lastRunFile));
    if (time() - $lastTs < 180) {
        echo json_encode(['ok' => true, 'status' => 'throttled', 'last_run_ago_sec' => time() - $lastTs]);
        exit;
    }
}
@file_put_contents($lastRunFile, (string)time());

// 1. Carrega catálogo de marcas (assets/data/marcas.json)
$marcasFile = dirname(__DIR__) . '/assets/data/marcas.json';
$brands = [];
if (is_file($marcasFile)) {
    $decoded = json_decode((string)file_get_contents($marcasFile), true);
    if (is_array($decoded)) {
        $brands = $decoded;
    }
}

function normalize_str(string $s): string {
    $s = mb_strtolower($s, 'UTF-8');
    $map = [
        'á'=>'a','à'=>'a','ã'=>'a','â'=>'a','ä'=>'a',
        'é'=>'e','è'=>'e','ê'=>'e','ë'=>'e',
        'í'=>'i','ì'=>'i','î'=>'i','ï'=>'i',
        'ó'=>'o','ò'=>'o','õ'=>'o','ô'=>'o','ö'=>'o',
        'ú'=>'u','ù'=>'u','û'=>'u','ü'=>'u',
        'ç'=>'c','ñ'=>'n'
    ];
    $s = strtr($s, $map);
    return preg_replace('/[^a-z0-9]+/', ' ', $s) ?? $s;
}

function match_brands_from_summary(string $summary, array $brands): array {
    $normSummary = ' ' . trim(normalize_str($summary)) . ' ';
    // Remove palavras genéricas como "drop", "sale", "restock", "re drop", "pre venda"
    $cleaned = preg_replace('/\b(drop|re|restock|sale|pre|venda|presencial|em|sp|merch|pt|1|2|3)\b/', ' ', $normSummary) ?? $normSummary;
    $cleaned = ' ' . trim(preg_replace('/\s+/', ' ', $cleaned) ?? '') . ' ';

    $matched = [];
    foreach ($brands as $b) {
        $slug = (string)($b['slug'] ?? '');
        $name = (string)($b['name'] ?? '');
        $handle = (string)($b['handle'] ?? '');
        if ($slug === '') continue;

        $normName = trim(normalize_str($name));
        $normSlug = trim(normalize_str($slug));
        $normHandle = trim(normalize_str($handle));

        // 1. Nome completo ou slug exato como palavra no summary
        if ($normName !== '' && mb_strlen($normName) >= 3 && strpos($normSummary, ' ' . $normName . ' ') !== false) {
            $matched[$slug] = $b;
            continue;
        }
        if ($normSlug !== '' && mb_strlen($normSlug) >= 3 && strpos($normSummary, ' ' . $normSlug . ' ') !== false) {
            $matched[$slug] = $b;
            continue;
        }
        if ($normHandle !== '' && mb_strlen($normHandle) >= 4 && strpos($normSummary, ' ' . $normHandle . ' ') !== false) {
            $matched[$slug] = $b;
            continue;
        }

        // 2. Primeira palavra distintiva da marca (ex: "Ablaze", "Kardigan", "Vilela", "Gaiji")
        $firstWord = explode(' ', $normName)[0] ?? '';
        if (mb_strlen($firstWord) >= 4 && strpos($cleaned, ' ' . $firstWord . ' ') !== false) {
            $matched[$slug] = $b;
        }
    }
    return array_values($matched);
}

function send_drop_alert_email(string $toEmail, string $token, array $brand, string $eventTitle, int $dropTimestamp): bool {
    $brandName = (string)($brand['name'] ?? 'Marca Emorphosis');
    $brandHandle = (string)($brand['handle'] ?? '');
    $brandUrl = (string)($brand['url'] ?? 'https://emorphosis.com.br/m4rcas.html');
    $horarioFormatado = date('d/m/Y \à\s H:i', $dropTimestamp) . ' (Horário de Brasília)';

    $unsubUrl = 'https://emorphosis.com.br/api/unsubscribe_drops.php?email=' . urlencode($toEmail) . '&token=' . urlencode($token);

    $subjectRaw = "⚡ FALTA 1 HORA: Drop {$brandName} hoje às " . date('H:i', $dropTimestamp) . "!";
    $subject = '=?UTF-8?B?' . base64_encode($subjectRaw) . '?=';

    $htmlBody = '<!DOCTYPE html>
<html lang="pt-BR">
<body style="margin:0;padding:24px;background-color:#000000;color:#19f028;font-family:Consolas,Monaco,monospace;">
  <div style="max-width:580px;margin:0 auto;background-color:#020803;border:2px solid #39ff48;border-radius:14px;padding:28px;box-shadow:0 0 24px rgba(25,240,40,0.3);">
    <div style="font-size:11px;letter-spacing:2px;color:#52ff5e;margin-bottom:8px;">EMORPHOSIS // ALERTA DE DROP (FALTA 1 HORA)</div>
    <h1 style="margin:0 0 14px;font-size:24px;color:#39ff48;">Falta 1 Hora para o Drop!</h1>
    <p style="font-size:14px;line-height:1.6;color:#d6ffda;margin:0 0 18px;">
      Prepare-se: uma das marcas em que você se inscreveu na <strong>EMORPHOSIS</strong> realizará um lançamento em aproximadamente <strong>1 hora</strong>.
    </p>
    <div style="background:#000000;border:1.5px solid #19f028;border-radius:10px;padding:18px;margin-bottom:22px;">
      <p style="margin:0 0 10px;font-size:15px;color:#d6ffda;">
        <strong style="color:#39ff48;">MARCA:</strong> ' . htmlspecialchars($brandName, ENT_QUOTES, 'UTF-8') . ($brandHandle !== '' ? ' (@' . htmlspecialchars($brandHandle, ENT_QUOTES, 'UTF-8') . ')' : '') . '
      </p>
      <p style="margin:0 0 10px;font-size:15px;color:#d6ffda;">
        <strong style="color:#39ff48;">EVENTO:</strong> ' . htmlspecialchars($eventTitle, ENT_QUOTES, 'UTF-8') . '
      </p>
      <p style="margin:0 0 10px;font-size:15px;color:#d6ffda;">
        <strong style="color:#39ff48;">HORÁRIO DO DROP:</strong> ' . htmlspecialchars($horarioFormatado, ENT_QUOTES, 'UTF-8') . '
      </p>
      <p style="margin:0;font-size:14px;color:#d6ffda;">
        <strong style="color:#39ff48;">INSTAGRAM DA MARCA:</strong>
        <a href="' . htmlspecialchars($brandUrl, ENT_QUOTES, 'UTF-8') . '" style="color:#52ff5e;text-decoration:underline;">' . htmlspecialchars($brandUrl, ENT_QUOTES, 'UTF-8') . '</a>
      </p>
    </div>
    <p style="margin:0 0 22px;text-align:center;">
      <a href="' . htmlspecialchars($brandUrl, ENT_QUOTES, 'UTF-8') . '" style="display:inline-block;background:#041707;color:#39ff48;border:2px solid #39ff48;padding:13px 24px;border-radius:10px;text-decoration:none;font-weight:bold;font-size:14px;letter-spacing:1px;">ABRIR INSTAGRAM DA MARCA ↗</a>
    </p>
    <hr style="border:none;border-top:1px solid #0e3b13;margin:20px 0;" />
    <p style="font-size:11px;color:#68a86e;margin:0;text-align:center;">
      Você recebeu este e-mail porque ativou os alertas de drops em <a href="https://emorphosis.com.br/m4rcas.html" style="color:#52ff5e;">emorphosis.com.br</a>.<br/>
      <a href="' . htmlspecialchars($unsubUrl, ENT_QUOTES, 'UTF-8') . '" style="color:#52ff5e;">Cancelar inscrição</a>
    </p>
  </div>
</body>
</html>';

    $headers = [
        'MIME-Version: 1.0',
        'Content-Type: text/html; charset=UTF-8',
        'From: Emorphosis Drops <noreply@emorphosis.com.br>',
        'Reply-To: noreply@emorphosis.com.br',
        'X-Mailer: EmorphosisDropRadar/1.0'
    ];

    return @mail($toEmail, $subject, $htmlBody, implode("\r\n", $headers));
}

// Modo de teste imediato: ?mode=test&email=usuario@exemplo.com&slug=aevus
if ($mode === 'test') {
    $testEmail = strtolower(trim((string)($_GET['email'] ?? $_POST['email'] ?? '')));
    $testSlug = strtolower(trim((string)($_GET['slug'] ?? $_POST['slug'] ?? 'aevus')));
    if ($testEmail === '' || !filter_var($testEmail, FILTER_VALIDATE_EMAIL)) {
        http_response_code(400);
        echo json_encode(['ok' => false, 'error' => 'Valid email required for test']);
        exit;
    }
    $targetBrand = null;
    foreach ($brands as $b) {
        if (($b['slug'] ?? '') === $testSlug) {
            $targetBrand = $b;
            break;
        }
    }
    if (!$targetBrand && count($brands) > 0) {
        $targetBrand = $brands[0];
    }
    $secret = emorphosis_runtime_secret('DROP_RADAR_SECRET');
    $token = hash_hmac('sha256', $testEmail, $secret);
    $sent = send_drop_alert_email(
        $testEmail,
        $token,
        $targetBrand,
        'Drop ' . ($targetBrand['name'] ?? 'Emorphosis'),
        time() + 3600
    );
    echo json_encode(['ok' => true, 'mode' => 'test', 'sent' => $sent, 'brand' => $targetBrand['name'] ?? '']);
    exit;
}

// 2. Carrega inscritos
$subFile = $storageDir . '/drop_subscriptions.json';
$subs = [];
if (is_file($subFile)) {
    $decoded = json_decode((string)file_get_contents($subFile), true);
    if (is_array($decoded)) {
        $subs = $decoded;
    }
}

if (count($subs) === 0) {
    echo json_encode(['ok' => true, 'status' => 'no_subscribers', 'sent_count' => 0]);
    exit;
}

// 3. Busca e faz parse do feed iCal oficial do Google Calendar da Emorphosis
$icalUrl = 'https://calendar.google.com/calendar/ical/e279d9d10a587ca926785f28efb4fc3cda446fc8b7a4adecec5a111bf316dd01%40group.calendar.google.com/public/basic.ics';
$icalCacheFile = $storageDir . '/ical_cache.ics';
$icalRaw = '';

if (is_file($icalCacheFile) && (time() - filemtime($icalCacheFile) < 300)) {
    $icalRaw = (string)file_get_contents($icalCacheFile);
} else {
    $ctx = stream_context_create([
        'http' => [
            'timeout' => 8,
            'user_agent' => 'EmorphosisDropRadar/1.0'
        ]
    ]);
    $fetched = @file_get_contents($icalUrl, false, $ctx);
    if (is_string($fetched) && strpos($fetched, 'BEGIN:VCALENDAR') !== false) {
        $icalRaw = $fetched;
        @file_put_contents($icalCacheFile, $icalRaw);
    } elseif (is_file($icalCacheFile)) {
        $icalRaw = (string)file_get_contents($icalCacheFile);
    }
}

$events = [];

if ($icalRaw !== '') {
    // Desdobra linhas continuadas do padrão RFC 5545 (CRLF + espaço)
    $unfolded = preg_replace("/\r?\n[ \t]/", '', $icalRaw) ?? $icalRaw;
    if (preg_match_all('/BEGIN:VEVENT(.*?)END:VEVENT/s', $unfolded, $matches)) {
        foreach ($matches[1] as $block) {
            $uid = '';
            $summary = '';
            $dtStartTs = null;

            if (preg_match('/^UID:(.*)$/m', $block, $m)) {
                $uid = trim($m[1]);
            }
            if (preg_match('/^SUMMARY:(.*)$/m', $block, $m)) {
                $summary = trim($m[1]);
            }
            if (preg_match('/^DTSTART(?:;([^:]+))?:(.*)$/m', $block, $m)) {
                $params = strtoupper(trim($m[1] ?? ''));
                $val = trim($m[2]);

                if (preg_match('/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$/', $val, $dm)) {
                    // Horário em UTC -> converte para timestamp Unix
                    $dtStartTs = gmmktime((int)$dm[4], (int)$dm[5], (int)$dm[6], (int)$dm[2], (int)$dm[3], (int)$dm[1]);
                } elseif (preg_match('/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})$/', $val, $dm)) {
                    // Horário local America/Sao_Paulo
                    $dtStartTs = mktime((int)$dm[4], (int)$dm[5], (int)$dm[6], (int)$dm[2], (int)$dm[3], (int)$dm[1]);
                } elseif (preg_match('/^(\d{4})(\d{2})(\d{2})$/', $val, $dm)) {
                    // Evento de dia inteiro: assume 12:00 (meio-dia BRT) como horário padrão do drop
                    $dtStartTs = mktime(12, 0, 0, (int)$dm[2], (int)$dm[3], (int)$dm[1]);
                }
            }

            if ($uid !== '' && $summary !== '' && is_int($dtStartTs)) {
                $events[] = [
                    'uid' => $uid,
                    'summary' => $summary,
                    'timestamp' => $dtStartTs,
                    'explicit_slug' => null,
                ];
            }
        }
    }
}

// Também carrega drops agendados manualmente em api/storage/scheduled_drops.json (opcional)
$customDropsFile = $storageDir . '/scheduled_drops.json';
if (is_file($customDropsFile)) {
    $customDrops = json_decode((string)file_get_contents($customDropsFile), true);
    if (is_array($customDrops)) {
        foreach ($customDrops as $cd) {
            $ts = isset($cd['timestamp']) ? (int)$cd['timestamp'] : strtotime((string)($cd['drop_iso'] ?? ''));
            if ($ts > 0) {
                $events[] = [
                    'uid' => (string)($cd['id'] ?? md5(($cd['slug'] ?? '') . $ts)),
                    'summary' => (string)($cd['title'] ?? ('Drop ' . ($cd['slug'] ?? ''))),
                    'timestamp' => $ts,
                    'explicit_slug' => $cd['slug'] ?? null,
                ];
            }
        }
    }
}

// 4. Verifica quais drops começam em ~1 hora (janela entre 15 e 75 minutos no futuro)
$now = time();
$sentFile = $storageDir . '/sent_drop_alerts.json';
$sentLog = [];
if (is_file($sentFile)) {
    $decodedSent = json_decode((string)file_get_contents($sentFile), true);
    if (is_array($decodedSent)) {
        $sentLog = $decodedSent;
    }
}

$deletedFile = $storageDir . '/deleted_drops.json';
$deletedUids = [];
$deletedDedupKeys = [];
if (is_file($deletedFile)) {
    $parsedDel = json_decode((string)file_get_contents($deletedFile), true);
    if (is_array($parsedDel)) {
        if (!empty($parsedDel['uids']) && is_array($parsedDel['uids'])) {
            $deletedUids = array_flip($parsedDel['uids']);
        }
        if (!empty($parsedDel['dedup_keys']) && is_array($parsedDel['dedup_keys'])) {
            $deletedDedupKeys = array_flip($parsedDel['dedup_keys']);
        }
    }
}

$sentCount = 0;
$secret = emorphosis_runtime_secret('DROP_RADAR_SECRET');

foreach ($events as $ev) {
    if (isset($deletedUids[$ev['uid']])) {
        continue;
    }
    $diff = $ev['timestamp'] - $now;
    // Janela de 1 hora antes do drop (entre 15 min e 75 min antes do horário do drop)
    if ($diff < 900 || $diff > 4500) {
        continue;
    }

    $matchedBrands = [];
    if (!empty($ev['explicit_slug'])) {
        foreach ($brands as $b) {
            if (($b['slug'] ?? '') === $ev['explicit_slug']) {
                $matchedBrands[] = $b;
                break;
            }
        }
    } else {
        $matchedBrands = match_brands_from_summary($ev['summary'], $brands);
    }

    if (count($matchedBrands) === 0) {
        continue;
    }

    foreach ($matchedBrands as $brand) {
        $slug = (string)$brand['slug'];
        $dedupKey = $slug . '_' . date('Y-m-d_H:i', $ev['timestamp']);
        if (isset($deletedDedupKeys[$dedupKey])) {
            continue;
        }
        foreach ($subs as $email => $subData) {
            $wantsAll = !empty($subData['all_brands']);
            $userBrands = is_array($subData['brands'] ?? null) ? $subData['brands'] : [];
            if (!$wantsAll && !in_array($slug, $userBrands, true)) {
                continue;
            }

            $logKey = $dedupKey . '|' . $email;
            $legacyKey = $ev['uid'] . '|' . $slug . '|' . $email;
            if (isset($sentLog[$logKey]) || isset($sentLog[$legacyKey])) {
                continue;
            }

            $token = (string)($subData['token'] ?? hash_hmac('sha256', (string)$email, $secret));
            $ok = send_drop_alert_email((string)$email, $token, $brand, $ev['summary'], $ev['timestamp']);
            if ($ok) {
                $sentLog[$logKey] = gmdate('c');
                $sentCount++;
            }
        }
    }
}

if ($sentCount > 0) {
    @file_put_contents(
        $sentFile,
        json_encode($sentLog, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
        LOCK_EX
    );
}

echo json_encode([
    'ok' => true,
    'checked_events' => count($events),
    'subscribers' => count($subs),
    'sent_count' => $sentCount,
    'server_time_brt' => date('Y-m-d H:i:s'),
]);
