<?php
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
date_default_timezone_set('America/Sao_Paulo');

$storageDir = __DIR__ . '/storage';
if (!is_dir($storageDir)) {
    @mkdir($storageDir, 0755, true);
}

$marcasFile = dirname(__DIR__) . '/assets/data/marcas.json';
$brands = [];
if (is_file($marcasFile)) {
    $decoded = json_decode((string)file_get_contents($marcasFile), true);
    if (is_array($decoded)) {
        $brands = $decoded;
    }
}

function norm_cal_str(string $s): string {
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

function find_brand_for_text(string $text, array $brands): ?array {
    $norm = ' ' . trim(norm_cal_str($text)) . ' ';
    $cleaned = preg_replace('/\b(drop|re|restock|sale|pre|venda|presencial|em|sp|merch|pt|1|2|3)\b/', ' ', $norm) ?? $norm;
    $cleaned = ' ' . trim(preg_replace('/\s+/', ' ', $cleaned) ?? '') . ' ';

    foreach ($brands as $b) {
        $slug = (string)($b['slug'] ?? '');
        $name = (string)($b['name'] ?? '');
        $handle = (string)($b['handle'] ?? '');
        if ($slug === '') continue;

        $nName = trim(norm_cal_str($name));
        $nSlug = trim(norm_cal_str($slug));
        $nHandle = trim(norm_cal_str($handle));

        if ($nName !== '' && mb_strlen($nName) >= 3 && strpos($norm, ' ' . $nName . ' ') !== false) {
            return $b;
        }
        if ($nSlug !== '' && mb_strlen($nSlug) >= 3 && strpos($norm, ' ' . $nSlug . ' ') !== false) {
            return $b;
        }
        if ($nHandle !== '' && mb_strlen($nHandle) >= 4 && strpos($norm, ' ' . $nHandle . ' ') !== false) {
            return $b;
        }
        $firstWord = explode(' ', $nName)[0] ?? '';
        if (mb_strlen($firstWord) >= 4 && strpos($cleaned, ' ' . $firstWord . ' ') !== false) {
            return $b;
        }
    }
    return null;
}

// Carrega lista de drops deletados manualmente pelo administrador
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

$now = time();
$events = [];
$dedupMap = [];

// 1. Eventos sugeridos/agendados automaticamente via formulário (api/storage/scheduled_drops.json)
$customDropsFile = $storageDir . '/scheduled_drops.json';
if (is_file($customDropsFile)) {
    $customDrops = json_decode((string)file_get_contents($customDropsFile), true);
    if (is_array($customDrops)) {
        foreach ($customDrops as $cd) {
            $ts = isset($cd['timestamp']) ? (int)$cd['timestamp'] : strtotime((string)($cd['drop_iso'] ?? ''));
            // Filtra apenas drops futuros
            if ($ts <= 0 || $ts < $now) {
                continue;
            }

            $evUid = (string)($cd['id'] ?? md5(($cd['title'] ?? '') . $ts));
            if (isset($deletedUids[$evUid])) {
                continue;
            }

            $brandObj = null;
            if (!empty($cd['slug'])) {
                foreach ($brands as $b) {
                    if (($b['slug'] ?? '') === $cd['slug']) {
                        $brandObj = $b;
                        break;
                    }
                }
            }
            if (!$brandObj && !empty($cd['marca'])) {
                $brandObj = find_brand_for_text((string)$cd['marca'], $brands);
            }

            $marcaName = $brandObj ? (string)$brandObj['name'] : (string)($cd['marca'] ?? '');
            $slugVal = $brandObj ? (string)$brandObj['slug'] : (string)($cd['slug'] ?? norm_cal_str($marcaName));
            $dedupKey = trim($slugVal) . '_' . date('Y-m-d_H:i', $ts);

            if (isset($deletedDedupKeys[$dedupKey]) || isset($dedupMap[$dedupKey])) {
                continue;
            }
            $dedupMap[$dedupKey] = true;

            $events[] = [
                'uid' => $evUid,
                'dedup_key' => $dedupKey,
                'title' => (string)($cd['title'] ?? ('Drop ' . $marcaName)),
                'marca' => $marcaName,
                'slug' => $brandObj ? $brandObj['slug'] : ($cd['slug'] ?? null),
                'img' => $brandObj ? $brandObj['img'] : 'assets/img/favicon.png',
                'url' => !empty($cd['link_post']) ? (string)$cd['link_post'] : ($brandObj ? $brandObj['url'] : ''),
                'ig_url' => $brandObj ? $brandObj['url'] : '',
                'timestamp' => $ts,
                'date_br' => date('d/m/Y', $ts),
                'time_br' => !empty($cd['has_time']) ? date('H:i', $ts) : '19:00',
                'iso_date' => date('Y-m-d', $ts),
                'source' => 'radar',
            ];
        }
    }
}

// 2. Eventos do Google Calendar Oficial (.ics) — apenas futuros
$icalUrl = 'https://calendar.google.com/calendar/ical/e279d9d10a587ca926785f28efb4fc3cda446fc8b7a4adecec5a111bf316dd01%40group.calendar.google.com/public/basic.ics';
$icalCacheFile = $storageDir . '/ical_cache.ics';
$icalRaw = '';

if (is_file($icalCacheFile) && (time() - filemtime($icalCacheFile) < 120)) {
    $icalRaw = (string)file_get_contents($icalCacheFile);
} else {
    $ctx = stream_context_create([
        'http' => [
            'timeout' => 6,
            'user_agent' => 'EmorphosisDropRadar/1.1'
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

if ($icalRaw !== '') {
    $unfolded = preg_replace("/\r?\n[ \t]/", '', $icalRaw) ?? $icalRaw;
    if (preg_match_all('/BEGIN:VEVENT(.*?)END:VEVENT/s', $unfolded, $matches)) {
        foreach ($matches[1] as $block) {
            $uid = '';
            $summary = '';
            $dtStartTs = null;
            $hasTime = false;

            if (preg_match('/^UID:(.*)$/m', $block, $m)) {
                $uid = trim($m[1]);
            }
            if (preg_match('/^SUMMARY:(.*)$/m', $block, $m)) {
                $summary = trim($m[1]);
            }
            if (preg_match('/^DTSTART(?:;([^:]+))?:(.*)$/m', $block, $m)) {
                $val = trim($m[2]);
                if (preg_match('/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$/', $val, $dm)) {
                    $dtStartTs = gmmktime((int)$dm[4], (int)$dm[5], (int)$dm[6], (int)$dm[2], (int)$dm[3], (int)$dm[1]);
                    $hasTime = true;
                } elseif (preg_match('/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})$/', $val, $dm)) {
                    $dtStartTs = mktime((int)$dm[4], (int)$dm[5], (int)$dm[6], (int)$dm[2], (int)$dm[3], (int)$dm[1]);
                    $hasTime = true;
                } elseif (preg_match('/^(\d{4})(\d{2})(\d{2})$/', $val, $dm)) {
                    // Eventos de dia inteiro valem até o fim do próprio dia (23:59:59)
                    $dtStartTs = mktime(23, 59, 59, (int)$dm[2], (int)$dm[3], (int)$dm[1]);
                    $hasTime = false;
                }
            }

            // Filtra exclusivamente drops futuros ($dtStartTs >= $now) e que não foram deletados pelo admin
            if ($uid !== '' && $summary !== '' && is_int($dtStartTs) && $dtStartTs >= $now) {
                if (isset($deletedUids[$uid])) {
                    continue;
                }

                $brandObj = find_brand_for_text($summary, $brands);
                $marcaName = $brandObj ? (string)$brandObj['name'] : $summary;
                $slugVal = $brandObj ? (string)$brandObj['slug'] : trim(norm_cal_str($marcaName));
                $dedupKey = $slugVal . '_' . date('Y-m-d_H:i', $dtStartTs);

                if (isset($deletedDedupKeys[$dedupKey]) || isset($dedupMap[$dedupKey])) {
                    continue;
                }
                $dedupMap[$dedupKey] = true;

                $events[] = [
                    'uid' => $uid,
                    'dedup_key' => $dedupKey,
                    'title' => $summary,
                    'marca' => $marcaName,
                    'slug' => $brandObj ? $brandObj['slug'] : null,
                    'img' => $brandObj ? $brandObj['img'] : 'assets/img/favicon.png',
                    'url' => $brandObj ? $brandObj['url'] : '',
                    'ig_url' => $brandObj ? $brandObj['url'] : '',
                    'timestamp' => $dtStartTs,
                    'date_br' => date('d/m/Y', $dtStartTs),
                    'time_br' => $hasTime ? date('H:i', $dtStartTs) : 'Dia todo',
                    'iso_date' => date('Y-m-d', $dtStartTs),
                    'source' => 'gcal',
                ];
            }
        }
    }
}

// Ordena em ordem cronológica dos próximos drops futuros (o mais próximo primeiro)
usort($events, static function (array $a, array $b): int {
    return $a['timestamp'] <=> $b['timestamp'];
});

echo json_encode([
    'ok' => true,
    'count' => count($events),
    'events' => $events,
], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
