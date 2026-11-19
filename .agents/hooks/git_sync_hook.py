"""
EMORPHOSIS — Hook Automático de Sincronização Git + DEVLOG para Antigravity
Eventos suportados (.agents/hooks.json):
  - session_start  : puxa commits do colega ao iniciar o chat
  - pre_invocation : verifica (no início do turno, throttle de 45s) se há commits novos no GitHub
  - stop           : garante registro no DEVLOG.md, faz commit, pull --rebase --autostash e push
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GIT_DIR = REPO_ROOT / ".git"
STAMP_FILE = GIT_DIR / "agy_last_fetch_ts"
FETCH_THROTTLE_SEC = 45
PROTECTED_PREFIXES = (
    ".env",
    "api/config.php",
    "api/db.php",
    "api/storage/",
    "_conversa_emorphosis/",
)


def run_git(args: list[str], timeout: int = 15, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env.setdefault("GCM_INTERACTIVE", "never")
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["git", *args],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def has_origin_main() -> bool:
    if not GIT_DIR.exists():
        return False
    res = run_git(["remote", "get-url", "origin"], timeout=5)
    return res.returncode == 0 and bool(res.stdout.strip())


def is_rebase_in_progress() -> bool:
    return (GIT_DIR / "rebase-merge").exists() or (GIT_DIR / "rebase-apply").exists()


def get_status_lines() -> list[str]:
    res = run_git(["status", "--porcelain"], timeout=8)
    if res.returncode != 0:
        return []
    return [line for line in res.stdout.splitlines() if line.strip()]


def extract_paths(status_lines: list[str]) -> list[str]:
    paths: list[str] = []
    for line in status_lines:
        raw = line[3:].strip() if len(line) > 3 else ""
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1].strip()
        raw = raw.strip('"')
        if raw:
            paths.append(raw)
    return paths


def get_ahead_behind() -> tuple[int, int]:
    res = run_git(["rev-list", "--left-right", "--count", "HEAD...origin/main"], timeout=5)
    if res.returncode != 0:
        return (0, 0)
    parts = res.stdout.strip().split()
    if len(parts) != 2:
        return (0, 0)
    try:
        return (int(parts[0]), int(parts[1]))
    except ValueError:
        return (0, 0)


def get_unmerged_files() -> list[str]:
    res = run_git(["diff", "--name-only", "--diff-filter=U"], timeout=5)
    if res.returncode != 0:
        return []
    return [line.strip() for line in res.stdout.splitlines() if line.strip()]


def pull_latest(force_fetch: bool = True) -> tuple[str, list[str]]:
    """
    Faz fetch + pull --rebase --autostash se origin/main estiver à frente.
    Retorna (status, detalhes):
      status in {'up_to_date', 'throttled', 'pulled', 'conflict', 'rebase_active', 'offline'}
    """
    if not has_origin_main():
        return ("offline", [])

    if is_rebase_in_progress():
        return ("rebase_active", get_unmerged_files())

    now = time.time()
    if not force_fetch and STAMP_FILE.exists():
        try:
            last_ts = float(STAMP_FILE.read_text(encoding="utf-8").strip())
            if now - last_ts < FETCH_THROTTLE_SEC:
                return ("throttled", [])
        except Exception:
            pass

    fetch = run_git(["fetch", "origin", "main"], timeout=12)
    if fetch.returncode != 0:
        return ("offline", [])

    try:
        STAMP_FILE.write_text(str(now), encoding="utf-8")
    except Exception:
        pass

    _, behind = get_ahead_behind()
    if behind <= 0:
        return ("up_to_date", [])

    log_res = run_git(["log", "--oneline", "HEAD..origin/main"], timeout=5)
    incoming = [l.strip() for l in log_res.stdout.splitlines() if l.strip()]

    pull = run_git(["pull", "--rebase", "--autostash", "origin", "main"], timeout=15)
    if pull.returncode == 0:
        return ("pulled", incoming)

    conflicts = get_unmerged_files()
    run_git(["rebase", "--abort"], timeout=8)
    return ("conflict", conflicts or incoming)


def build_commit_message(changed_paths: list[str]) -> str:
    author_res = run_git(["config", "user.name"], timeout=5)
    author = re.sub(r"[^a-zA-Z0-9_-]+", "", (author_res.stdout or "dev").strip().lower()) or "dev"

    devlog_path = REPO_ROOT / "DEVLOG.md"
    if "DEVLOG.md" in changed_paths and devlog_path.exists():
        for line in devlog_path.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"^##\s+\[\d{4}-\d{2}-\d{2}\]\s+[—-]\s+(.+)$", line.strip())
            if m:
                title = re.sub(r"\s+", " ", m.group(1)).strip()[:64]
                return f"sync({author}): {title}"

    short_files = ", ".join(Path(p).name for p in changed_paths[:3])
    if len(changed_paths) > 3:
        short_files += f" (+{len(changed_paths) - 3})"
    return f"sync({author}): update {short_files}"


def handle_session_or_pre(force_fetch: bool, payload: dict) -> dict:
    if not force_fetch and payload.get("invocationNum", 1) != 1:
        return {}

    status, details = pull_latest(force_fetch=force_fetch)
    if status == "pulled" and details:
        msg = (
            "[Git Auto-Sync] Alterações do colega baixadas de origin/main:\n- "
            + "\n- ".join(details[:8])
            + "\nConsidere reler os arquivos modificados ou DEVLOG.md antes de editar."
        )
        return {"injectSteps": [{"systemMessage": {"systemMessage": msg}}]}

    if status == "conflict":
        msg = (
            "[Git Auto-Sync] Há alterações remotas em origin/main que conflitam com edições locais "
            f"({', '.join(details[:6])}). O rebase foi abortado para preservar suas edições locais; "
            "revise e mescle com cuidado antes do próximo push."
        )
        return {"injectSteps": [{"systemMessage": {"systemMessage": msg}}]}

    if status == "rebase_active" and details:
        msg = (
            "[Git Auto-Sync] Rebase em andamento com conflitos em: "
            + ", ".join(details[:6])
            + ". Resolva-os preservando as alterações de ambos os devs."
        )
        return {"injectSteps": [{"systemMessage": {"systemMessage": msg}}]}

    return {}


def handle_stop(payload: dict) -> dict:
    if payload.get("terminationReason") not in (None, "", "NO_TOOL_CALL"):
        return {}

    if not has_origin_main():
        return {}

    if is_rebase_in_progress():
        conflicts = get_unmerged_files()
        if conflicts:
            if payload.get("continuationActive"):
                return {}
            return {
                "decision": "continue",
                "reason": (
                    "[Git Auto-Sync] Conflito ainda pendente em: "
                    + ", ".join(conflicts)
                    + ". Remova os marcadores de conflito mantendo as alterações dos dois devs e rode `git add`."
                ),
            }
        run_git(["rebase", "--continue"], timeout=12, extra_env={"GIT_EDITOR": "true"})

    status_lines = get_status_lines()
    changed_paths = extract_paths(status_lines)

    for p in changed_paths:
        norm = p.replace("\\", "/")
        if any(norm == pref or norm.startswith(pref) for pref in PROTECTED_PREFIXES):
            if norm not in (".env.example", "api/storage/.htaccess", "api/storage/index.php"):
                return {
                    "decision": "continue",
                    "reason": f"[Git Auto-Sync] Arquivo sensível detectado fora do .gitignore ({norm}). Remova ou ignore antes de sincronizar.",
                }

    continuation_active = bool(payload.get("continuationActive"))
    code_changed = any(
        not p.endswith(".md") and not p.startswith(".agents/") and p != ".gitattributes"
        for p in changed_paths
    )
    if code_changed and "DEVLOG.md" not in changed_paths and not continuation_active:
        return {
            "decision": "continue",
            "reason": (
                "Atualize o topo do DEVLOG.md com Data, Responsável, o que foi alterado e o Contexto/Porquê "
                "desta entrega antes de finalizar (o hook fará o commit e push automático logo em seguida)."
            ),
        }

    if changed_paths:
        add_res = run_git(["add", "-A"], timeout=10)
        if add_res.returncode == 0:
            commit_msg = build_commit_message(changed_paths)
            run_git(["commit", "-m", commit_msg], timeout=12)

    pull_fetch = run_git(["fetch", "origin", "main"], timeout=12)
    if pull_fetch.returncode != 0:
        return {}

    _, behind = get_ahead_behind()
    if behind > 0:
        rebase = run_git(["pull", "--rebase", "--autostash", "origin", "main"], timeout=18)
        if rebase.returncode != 0:
            conflicts = get_unmerged_files()
            if conflicts:
                return {
                    "decision": "continue",
                    "reason": (
                        "[Git Auto-Sync] Conflito simultâneo detectado em: "
                        + ", ".join(conflicts)
                        + ". Resolva os marcadores de conflito preservando as alterações de ambos os devs, "
                        "remova os marcadores (<<<<<<< / ======= / >>>>>>>) e execute `git add`."
                    ),
                }
            run_git(["rebase", "--abort"], timeout=8)
            return {}

    ahead, _ = get_ahead_behind()
    if ahead > 0:
        run_git(["push", "origin", "main"], timeout=20)

    return {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True, choices=["session_start", "pre_invocation", "stop"])
    args = parser.parse_args()

    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}

    if args.event == "session_start":
        out = handle_session_or_pre(force_fetch=True, payload=payload)
    elif args.event == "pre_invocation":
        out = handle_session_or_pre(force_fetch=False, payload=payload)
    else:
        out = handle_stop(payload)

    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
