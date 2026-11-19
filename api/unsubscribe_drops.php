<?php
declare(strict_types=1);

header('Content-Type: text/html; charset=utf-8');

require_once __DIR__ . '/config_loader.php';

$email = strtolower(trim((string)($_GET['email'] ?? '')));
$token = trim((string)($_GET['token'] ?? ''));
$secret = emorphosis_runtime_secret('DROP_RADAR_SECRET');
$expected = hash_hmac('sha256', $email, $secret);

$removed = false;
if ($email !== '' && $token !== '' && hash_equals($expected, $token)) {
    $subFile = __DIR__ . '/storage/drop_subscriptions.json';
    if (is_file($subFile)) {
        $subs = json_decode((string)file_get_contents($subFile), true);
        if (is_array($subs) && isset($subs[$email])) {
            unset($subs[$email]);
            @file_put_contents(
                $subFile,
                json_encode($subs, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
                LOCK_EX
            );
            $removed = true;
        }
    }
}
?>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Alertas de Drops — emorphosis.com.br</title>
  <style>
    body {
      margin: 0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #000000;
      color: #39ff48;
      font-family: Consolas, Monaco, monospace;
      padding: 20px;
    }
    .box {
      max-width: 480px;
      background: #020803;
      border: 2px solid #19f028;
      border-radius: 12px;
      padding: 28px;
      text-align: center;
      box-shadow: 0 0 24px rgba(25, 240, 40, 0.3);
    }
    a {
      display: inline-block;
      margin-top: 16px;
      color: #39ff48;
      border: 1.5px solid #39ff48;
      padding: 9px 18px;
      border-radius: 8px;
      text-decoration: none;
      font-weight: bold;
    }
  </style>
</head>
<body>
  <div class="box">
    <h2><?php echo $removed ? 'Inscrição Cancelada' : 'Link de Cancelamento'; ?></h2>
    <p>
      <?php
      echo $removed
          ? 'Seu e-mail foi removido dos alertas de drops da Emorphosis.'
          : 'Este e-mail já não estava ativo na lista ou o link expirou.';
      ?>
    </p>
    <a href="https://emorphosis.com.br/m4rcas.html">← VOLTAR PARA EMORPHOSIS</a>
  </div>
</body>
</html>
