"""
EMORPHOSIS — Script Seguro de Deploy via FTP para Hostinger
Lê as credenciais diretamente do arquivo local .env (sem exibir senhas no terminal)
e envia os arquivos do site para a pasta public_html na Hostinger.
"""

from __future__ import annotations

import ftplib
import os
import ssl
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

EXCLUDE_NAMES = {
    ".env",
    ".env.example",
    ".git",
    ".gitignore",
    ".agents",
    "GEMINI.md",
    "README.md",
    "DEVLOG.md",
    "scripts",
    "database",
    "__pycache__",
    ".DS_Store",
    "Thumbs.db",
    "db.example.php",
    "config.example.php",
    "runtime_secrets.json",
    "drops_submissions.jsonl",
    "active_users.json",
    "active_users_v2.json",
    "active_nodes_anon.json",
    "unique_visitors.json",
    "unique_visitors_max.txt",
    "ip_geo_cache.json",
    "ip_geo_cache_v2.json",
    "drop_subscriptions.json",
    "sent_drop_alerts.json",
    "scheduled_drops.json",
    "deleted_drops.json",
    "notified_drops.json",
    "last_cron_run.txt",
    "ical_cache.ics",
    "gcal_webhook.txt",
    "dream_submissions.json",
    "respostas.json",
    "respostas.txt",
    "CONVERSATION_HANDOFF_ANTIGRAVITY.md",
    "_conversa_emorphosis",
}


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        val = val.strip().strip('"').strip("'")
        env[key.strip()] = val
    return env


class HostingerFTP_TLS(ftplib.FTP_TLS):
    """Compatibilidade de reuso de sessão TLS exigido pelo Pure-FTPd da Hostinger."""

    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(
                conn,
                server_hostname=self.host,
                session=self.sock.session,
            )
        return conn, size


def connect_ftp(host: str, port: int, user: str, password: str) -> ftplib.FTP:
    clean_host = host.replace("ftp://", "").replace("ftps://", "").strip("/")
    # Tenta FTPS explícito primeiro; se o servidor recusar TLS no canal de dados, usa FTP padrão
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ftps = HostingerFTP_TLS(context=ctx, timeout=30)
        ftps.connect(clean_host, port)
        ftps.login(user, password)
        ftps.prot_p()
        ftps.encoding = "utf-8"
        print(f"[OK] Conectado com seguranca (FTPS) em {clean_host}:{port}")
        return ftps
    except Exception:
        ftp = ftplib.FTP(timeout=30)
        ftp.connect(clean_host, port)
        ftp.login(user, password)
        ftp.encoding = "utf-8"
        print(f"[OK] Conectado via FTP em {clean_host}:{port}")
        return ftp


def ensure_remote_dir(ftp: ftplib.FTP, remote_dir: str) -> None:
    parts = [p for p in remote_dir.replace("\\", "/").split("/") if p and p != "."]
    for part in parts:
        try:
            ftp.cwd(part)
        except ftplib.error_perm:
            ftp.mkd(part)
            ftp.cwd(part)


def upload_directory(ftp: ftplib.FTP, local_dir: Path, force: bool = False) -> int:
    count = 0
    remote_sizes: dict[str, int] = {}
    if not force:
        try:
            for name, facts in ftp.mlsd():
                if "size" in facts:
                    remote_sizes[name] = int(facts["size"])
        except Exception:
            pass

    for item in sorted(local_dir.iterdir()):
        if item.name in EXCLUDE_NAMES:
            continue
        if item.is_dir():
            try:
                ftp.mkd(item.name)
            except ftplib.error_perm:
                pass
            ftp.cwd(item.name)
            count += upload_directory(ftp, item, force=force)
            ftp.cwd("..")
        elif item.is_file():
            rel = item.relative_to(PROJECT_ROOT)
            # Evita reenviar mídias binárias inalteradas em deploys subsequentes
            force_marcas = "--force-marcas" in sys.argv and local_dir.name == "marcas"
            if (
                not force
                and not force_marcas
                and item.suffix.lower() in {".mp4", ".webm", ".mov", ".jpg", ".jpeg", ".png", ".webp"}
                and remote_sizes.get(item.name) == item.stat().st_size
            ):
                continue
            with item.open("rb") as fh:
                ftp.storbinary(f"STOR {item.name}", fh)
            print(f"  -> Enviado: {rel}")
            count += 1
    return count


def maybe_generate_db_php(env: dict[str, str]) -> Path | None:
    db_name = env.get("DB_NAME", "")
    db_user = env.get("DB_USER", "")
    db_pass = env.get("DB_PASS", "")
    db_host = env.get("DB_HOST", "localhost") or "localhost"
    if not (db_name and db_user and db_pass):
        return None

    api_dir = PROJECT_ROOT / "api"
    api_dir.mkdir(exist_ok=True)
    db_php = api_dir / "db.php"
    content = f"""<?php
declare(strict_types=1);

$DB_HOST = {db_host!r};
$DB_NAME = {db_name!r};
$DB_USER = {db_user!r};
$DB_PASS = {db_pass!r};

try {{
    $pdo = new PDO(
        "mysql:host={{$DB_HOST}};dbname={{$DB_NAME}};charset=utf8mb4",
        $DB_USER,
        $DB_PASS,
        [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ]
    );
}} catch (PDOException $e) {{
    http_response_code(500);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['ok' => false, 'error' => 'Database connection failed']);
    exit;
}}
"""
    db_php.write_text(content, encoding="utf-8")
    return db_php


def maybe_generate_config_php(env: dict[str, str]) -> Path | None:
    keys = (
        "ADMIN_DROP_TOKEN",
        "ADMIN_NOTIFY_EMAIL",
        "DROP_RADAR_SECRET",
        "PRESENCE_SID_SALT",
        "PRESENCE_IP_SALT",
    )
    values = {k: env.get(k, "") for k in keys if env.get(k, "")}
    if not values:
        return None

    api_dir = PROJECT_ROOT / "api"
    api_dir.mkdir(exist_ok=True)
    config_php = api_dir / "config.php"
    lines = [
        "<?php",
        "declare(strict_types=1);",
        "",
        "return [",
    ]
    for k in keys:
        lines.append(f"    {k!r} => {env.get(k, '')!r},")
    lines.append("];")
    lines.append("")
    config_php.write_text("\n".join(lines), encoding="utf-8")
    return config_php


def main() -> int:
    env = load_env(ENV_PATH)
    host = env.get("FTP_HOST", "")
    port = int(env.get("FTP_PORT", "21") or "21")
    user = env.get("FTP_USER", "")
    password = env.get("FTP_PASS", "")
    remote_dir = env.get("FTP_REMOTE_DIR", "public_html").strip()

    missing = [k for k, v in [("FTP_HOST", host), ("FTP_USER", user), ("FTP_PASS", password)] if not v]
    if missing:
        print(f"[ERRO] Preencha os campos obrigatorios no arquivo .env: {', '.join(missing)}")
        return 1

    maybe_generate_db_php(env)
    maybe_generate_config_php(env)

    ftp = connect_ftp(host, port, user, password)
    try:
        items = []
        try:
            items = ftp.nlst()
        except Exception:
            pass

        # Detecta automaticamente a estrutura domains/<dominio>/public_html da Hostinger
        if remote_dir and remote_dir in items:
            ftp.cwd(remote_dir)
            print(f"[OK] Diretorio remoto selecionado: /{remote_dir}")
        elif "domains" in items:
            ftp.cwd("domains")
            doms = [d for d in ftp.nlst() if d not in (".", "..")]
            target_dom = "emorphosis.com.br" if "emorphosis.com.br" in doms else (doms[0] if doms else "")
            if not target_dom:
                print("[ERRO] Nenhum dominio encontrado dentro de /domains")
                return 1
            ftp.cwd(f"{target_dom}/public_html")
            print(f"[OK] Diretorio remoto selecionado: /domains/{target_dom}/public_html")
        elif remote_dir and remote_dir != "public_html":
            ensure_remote_dir(ftp, remote_dir)
            print(f"[OK] Diretorio remoto selecionado: /{remote_dir}")
        else:
            print(f"[OK] Diretorio remoto atual: {ftp.pwd()}")

        # Remove a pagina padrao default.php da Hostinger, se existir
        try:
            current_files = ftp.nlst()
            if "default.php" in current_files:
                ftp.delete("default.php")
                print("  -> Removido placeholder padrao da Hostinger: default.php")
        except Exception:
            pass

        total = upload_directory(ftp, PROJECT_ROOT)
        print(f"\n[CONCLUIDO] {total} arquivo(s) enviados com sucesso para a Hostinger!")
    finally:
        try:
            ftp.quit()
        except Exception:
            ftp.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
