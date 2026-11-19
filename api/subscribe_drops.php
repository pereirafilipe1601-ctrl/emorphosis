<?php
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');

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

$email = strtolower(trim((string)($payload['email'] ?? '')));
$allBrands = !empty($payload['all_brands']);
$brandsInput = $payload['brands'] ?? [];
if (!is_array($brandsInput)) {
    $brandsInput = [];
}

if ($email === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Invalid email']);
    exit;
}

// Carrega o catálogo oficial de marcas para validar slugs e nomes
$marcasFile = dirname(__DIR__) . '/assets/data/marcas.json';
$marcasCatalog = [];
if (is_file($marcasFile)) {
    $decoded = json_decode((string)file_get_contents($marcasFile), true);
    if (is_array($decoded)) {
        foreach ($decoded as $b) {
            if (!empty($b['slug'])) {
                $marcasCatalog[(string)$b['slug']] = $b;
            }
        }
    }
}

$validSlugs = [];
foreach ($brandsInput as $slug) {
    $s = strtolower(trim((string)$slug));
    if ($s !== '' && (isset($marcasCatalog[$s]) || preg_match('/^[a-z0-9_-]{1,50}$/', $s))) {
        $validSlugs[$s] = true;
    }
}
$selectedSlugs = array_keys($validSlugs);

if (!$allBrands && count($selectedSlugs) === 0) {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Select at least one brand']);
    exit;
}

$storageDir = __DIR__ . '/storage';
if (!is_dir($storageDir)) {
    @mkdir($storageDir, 0755, true);
}

$subFile = $storageDir . '/drop_subscriptions.json';
$subs = [];
if (is_file($subFile)) {
    $existing = json_decode((string)file_get_contents($subFile), true);
    if (is_array($existing)) {
        $subs = $existing;
    }
}

$secret = emorphosis_runtime_secret('DROP_RADAR_SECRET');
$token = hash_hmac('sha256', $email, $secret);

if (isset($subs[$email]) && is_array($subs[$email])) {
    $prevSlugs = is_array($subs[$email]['brands'] ?? null) ? $subs[$email]['brands'] : [];
    $mergedSlugs = array_values(array_unique(array_merge($prevSlugs, $selectedSlugs)));
    $subs[$email] = [
        'email' => $email,
        'all_brands' => $allBrands || !empty($subs[$email]['all_brands']),
        'brands' => $mergedSlugs,
        'token' => $token,
        'updated_at' => gmdate('c'),
        'created_at' => $subs[$email]['created_at'] ?? gmdate('c'),
    ];
} else {
    $subs[$email] = [
        'email' => $email,
        'all_brands' => $allBrands,
        'brands' => $selectedSlugs,
        'token' => $token,
        'updated_at' => gmdate('c'),
        'created_at' => gmdate('c'),
    ];
}

@file_put_contents(
    $subFile,
    json_encode($subs, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
    LOCK_EX
);

// Também registra em banco MySQL caso api/db.php esteja configurado
$dbFile = __DIR__ . '/db.php';
if (is_file($dbFile)) {
    try {
        require $dbFile;
        if (isset($pdo) && $pdo instanceof PDO) {
            $stmt = $pdo->prepare(
                'INSERT IGNORE INTO inscritos_drops (email, marca_slug) VALUES (:email, :marca)'
            );
            if ($allBrands) {
                $stmt->execute([':email' => $email, ':marca' => '*']);
            } else {
                foreach ($selectedSlugs as $slug) {
                    $stmt->execute([':email' => $email, ':marca' => $slug]);
                }
            }
        }
    } catch (Throwable $e) {
        // Mantém funcionamento via JSON protegido
    }
}

// Monta lista legível das marcas inscritas para o e-mail de confirmação
$brandNames = [];
if ($subs[$email]['all_brands']) {
    $brandNames[] = 'Todas as ' . count($marcasCatalog) . ' marcas do catálogo Emorphosis';
} else {
    foreach ($subs[$email]['brands'] as $s) {
        if (isset($marcasCatalog[$s])) {
            $b = $marcasCatalog[$s];
            $brandNames[] = $b['name'] . ' (@' . $b['handle'] . ')';
        } else {
            $brandNames[] = strtoupper($s);
        }
    }
}

$brandsHtmlList = '';
foreach (array_slice($brandNames, 0, 35) as $bn) {
    $brandsHtmlList .= '<li style="margin-bottom:4px;color:#52ff5e;">' . htmlspecialchars($bn, ENT_QUOTES, 'UTF-8') . '</li>';
}
if (count($brandNames) > 35) {
    $more = count($brandNames) - 35;
    $brandsHtmlList .= '<li style="color:#9effa6;">+ ' . $more . ' outra(s) marca(s)</li>';
}

$unsubUrl = 'https://emorphosis.com.br/api/unsubscribe_drops.php?email=' . urlencode($email) . '&token=' . urlencode($token);

$subject = '=?UTF-8?B?' . base64_encode('EMORPHOSIS // Inscrição Confirmada no Radar de Drops (Aviso 1h Antes)') . '?=';
$htmlBody = '<!DOCTYPE html>
<html lang="pt-BR">
<body style="margin:0;padding:24px;background-color:#000000;color:#19f028;font-family:Consolas,Monaco,monospace;">
  <div style="max-width:580px;margin:0 auto;background-color:#020803;border:2px solid #19f028;border-radius:12px;padding:28px;">
    <div style="font-size:11px;letter-spacing:2px;color:#52ff5e;margin-bottom:8px;">EMORPHOSIS // RADAR DE DROPS</div>
    <h1 style="margin:0 0 14px;font-size:22px;color:#39ff48;">Inscrição Ativada com Sucesso</h1>
    <p style="font-size:14px;line-height:1.6;color:#d6ffda;margin:0 0 16px;">
      Seu e-mail foi cadastrado no sistema de alertas da <strong>EMORPHOSIS</strong>. Quando faltar <strong>1 hora</strong> para o drop de uma das suas marcas começar, você receberá um alerta contendo:
    </p>
    <ul style="font-size:13px;line-height:1.6;color:#9effa6;margin:0 0 18px;padding-left:20px;">
      <li>Qual marca realizará o drop</li>
      <li>O horário exato do lançamento</li>
      <li>O link direto para o Instagram oficial da marca</li>
    </ul>
    <div style="background:#000000;border:1px solid #19f028;border-radius:8px;padding:14px 16px;margin-bottom:20px;">
      <div style="font-size:12px;font-weight:bold;color:#39ff48;margin-bottom:8px;">MARCAS MONITORADAS POR VOCÊ:</div>
      <ul style="margin:0;padding-left:18px;font-size:13px;">' . $brandsHtmlList . '</ul>
    </div>
    <p style="margin:0 0 20px;">
      <a href="https://emorphosis.com.br/c4l3ndar10.html" style="display:inline-block;background:#041707;color:#39ff48;border:1.5px solid #39ff48;padding:10px 18px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:13px;">VER CALENDÁRIO DE DROPS ↗</a>
    </p>
    <hr style="border:none;border-top:1px solid #0e3b13;margin:20px 0;" />
    <p style="font-size:11px;color:#68a86e;margin:0;">
      Para cancelar seus alertas a qualquer momento, <a href="' . htmlspecialchars($unsubUrl, ENT_QUOTES, 'UTF-8') . '" style="color:#52ff5e;">clique aqui</a>.
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

@mail($email, $subject, $htmlBody, implode("\r\n", $headers));

echo json_encode([
    'ok' => true,
    'email' => $email,
    'all_brands' => $subs[$email]['all_brands'],
    'brands_count' => $subs[$email]['all_brands'] ? count($marcasCatalog) : count($subs[$email]['brands']),
]);
