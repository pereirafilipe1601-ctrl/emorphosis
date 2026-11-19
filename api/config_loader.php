<?php
/**
 * EMORPHOSIS — Carregador Central de Configuração e Segredos
 * Ordem de resolução:
 *  1. api/config.php (gerado no deploy ou criado localmente)
 *  2. Variáveis de ambiente (getenv / $_ENV / $_SERVER)
 *  3. .env na raiz do projeto (conveniência para desenvolvimento local)
 * Para segredos HMAC de runtime (salts/unsubscribe), gera e persiste
 * uma chave aleatória em api/storage/runtime_secrets.json se não houver config explícita.
 */
declare(strict_types=1);

function emorphosis_load_dotenv_once(): array
{
    static $parsed = null;
    if ($parsed !== null) {
        return $parsed;
    }
    $parsed = [];
    $envPath = dirname(__DIR__) . '/.env';
    if (!is_file($envPath)) {
        return $parsed;
    }
    $lines = @file($envPath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    if (!is_array($lines)) {
        return $parsed;
    }
    foreach ($lines as $rawLine) {
        $line = trim((string)$rawLine);
        if ($line === '' || $line[0] === '#' || strpos($line, '=') === false) {
            continue;
        }
        [$k, $v] = explode('=', $line, 2);
        $k = trim($k);
        $v = trim($v);
        if (strlen($v) >= 2 && (($v[0] === '"' && $v[strlen($v) - 1] === '"') || ($v[0] === "'" && $v[strlen($v) - 1] === "'"))) {
            $v = substr($v, 1, -1);
        }
        if ($k !== '') {
            $parsed[$k] = $v;
        }
    }
    return $parsed;
}

function emorphosis_load_config_array(): array
{
    static $cfg = null;
    if ($cfg !== null) {
        return $cfg;
    }
    $cfg = [];
    $configFile = __DIR__ . '/config.php';
    if (is_file($configFile)) {
        $loaded = require $configFile;
        if (is_array($loaded)) {
            $cfg = $loaded;
        }
    }
    return $cfg;
}

function emorphosis_config(string $key, string $default = ''): string
{
    $cfg = emorphosis_load_config_array();
    if (isset($cfg[$key]) && is_string($cfg[$key]) && trim($cfg[$key]) !== '') {
        return trim($cfg[$key]);
    }

    $envVal = getenv($key);
    if (is_string($envVal) && trim($envVal) !== '') {
        return trim($envVal);
    }

    if (isset($_ENV[$key]) && is_string($_ENV[$key]) && trim($_ENV[$key]) !== '') {
        return trim($_ENV[$key]);
    }

    if (isset($_SERVER[$key]) && is_string($_SERVER[$key]) && trim($_SERVER[$key]) !== '') {
        return trim($_SERVER[$key]);
    }

    $dotenv = emorphosis_load_dotenv_once();
    if (isset($dotenv[$key]) && trim($dotenv[$key]) !== '') {
        return trim($dotenv[$key]);
    }

    return $default;
}

function emorphosis_runtime_secret(string $key): string
{
    $configured = emorphosis_config($key);
    if ($configured !== '') {
        return $configured;
    }

    $storageDir = __DIR__ . '/storage';
    if (!is_dir($storageDir)) {
        @mkdir($storageDir, 0755, true);
    }
    $secretsFile = $storageDir . '/runtime_secrets.json';
    $fp = @fopen($secretsFile, 'c+');
    if ($fp && @flock($fp, LOCK_EX)) {
        $raw = stream_get_contents($fp);
        $data = is_string($raw) && $raw !== '' ? json_decode($raw, true) : [];
        if (!is_array($data)) {
            $data = [];
        }
        if (empty($data[$key]) || !is_string($data[$key])) {
            $data[$key] = bin2hex(random_bytes(32));
            ftruncate($fp, 0);
            rewind($fp);
            fwrite($fp, (string)json_encode($data, JSON_PRETTY_PRINT));
            fflush($fp);
        }
        @flock($fp, LOCK_UN);
        fclose($fp);
        return (string)$data[$key];
    }
    if ($fp) {
        fclose($fp);
    }

    return hash('sha256', __FILE__ . '|' . $key);
}
