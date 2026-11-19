"""
EMORPHOSIS — Notion Dev Hub CLI (Tarefas de Devs + Cofre de Ideias Multimídia)

Integração zero-dependências (Python 3.10+ stdlib) com a Notion API (versão 2026-03-11),
suportando o modelo de data_sources, Views API e File Upload API (single-part até 20 MiB
e multi-part em streaming de 10 MiB para áudios/vídeos pesados de até 5 GiB no Notion Plus+).

Comandos principais:
  python scripts/notion_hub.py doctor
  python scripts/notion_hub.py bootstrap --page-id "<URL_OU_ID_DA_PAGINA_RAIZ>"
  python scripts/notion_hub.py tasks list [--status ...] [--owner ...] [--area ...]
  python scripts/notion_hub.py tasks add --title "..." [--priority Alta] [--owner Filipe]
  python scripts/notion_hub.py tasks update <PAGE_ID> --status "Em Andamento"
  python scripts/notion_hub.py ideas list [--status ...] [--format ...]
  python scripts/notion_hub.py ideas add --title "..." --file audio.m4a --file ref.png --link https://...
  python scripts/notion_hub.py ideas attach <PAGE_ID> --file video.mp4 --embed https://youtu.be/...
  python scripts/notion_hub.py ideas promote <IDEA_PAGE_ID> --owner Filipe --priority Alta
  python scripts/notion_hub.py devlog sync [--dry-run | --apply]
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import math
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
DEVLOG_PATH = ROOT / "DEVLOG.md"

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2026-03-11"

SINGLE_PART_MAX_BYTES = 20 * 1024 * 1024  # 20 MiB
MULTI_PART_CHUNK_BYTES = 10 * 1024 * 1024  # 10 MiB (recomendado pela Notion API: 5..20 MiB)

# Taxonomia oficial do Emorphosis Dev Hub
TASK_STATUSES = [
    {"name": "Backlog", "color": "gray", "group": "To-do"},
    {"name": "A Fazer", "color": "default", "group": "To-do"},
    {"name": "Em Andamento", "color": "blue", "group": "In progress"},
    {"name": "Em Revisão", "color": "yellow", "group": "In progress"},
    {"name": "Concluído", "color": "green", "group": "Complete"},
]

TASK_PRIORITIES = [
    {"name": "Crítica", "color": "red"},
    {"name": "Alta", "color": "orange"},
    {"name": "Média", "color": "yellow"},
    {"name": "Baixa", "color": "gray"},
]

TEAM_MEMBERS = [
    {"name": "Filipe", "color": "green"},
    {"name": "Arquivobrasileiro", "color": "purple"},
    {"name": "Ambos", "color": "blue"},
]

PROJECT_AREAS = [
    {"name": "H0M3 / Mapa", "color": "green"},
    {"name": "M4RCAS / Catálogo", "color": "blue"},
    {"name": "Fit Lab", "color": "purple"},
    {"name": "C4L3NDAR10", "color": "orange"},
    {"name": "Backend PHP / MySQL", "color": "red"},
    {"name": "Design / UI", "color": "pink"},
    {"name": "Infra / Deploy", "color": "gray"},
]

TASK_TYPES = [
    {"name": "Feature", "color": "blue"},
    {"name": "Bug", "color": "red"},
    {"name": "Melhoria", "color": "green"},
    {"name": "Conteúdo / Marca", "color": "purple"},
    {"name": "Pesquisa", "color": "yellow"},
]

IDEA_STATUSES = [
    {"name": "Captura Bruta", "color": "gray"},
    {"name": "Em Análise", "color": "yellow"},
    {"name": "Aprovada", "color": "green"},
    {"name": "Virou Tarefa", "color": "blue"},
    {"name": "Arquivada", "color": "brown"},
]

IDEA_FORMATS = [
    {"name": "Áudio", "color": "purple"},
    {"name": "Vídeo", "color": "red"},
    {"name": "Foto / Print", "color": "green"},
    {"name": "Link / Ref", "color": "blue"},
    {"name": "Texto / Briefing", "color": "gray"},
    {"name": "PDF / Doc", "color": "orange"},
]

IDEA_PILLARS = [
    {"name": "Fit Lab", "color": "purple"},
    {"name": "Visual / Glitch", "color": "green"},
    {"name": "H0M3 / Mapa", "color": "blue"},
    {"name": "Catálogo / Marcas", "color": "orange"},
    {"name": "Drops / Calendário", "color": "yellow"},
    {"name": "Social / Editorial", "color": "pink"},
    {"name": "Negócio", "color": "red"},
]

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".heic", ".bmp", ".tif", ".tiff"}
VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv", ".m4v", ".avi", ".mpeg", ".mpg", ".ogv"}
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".opus", ".ogg", ".oga", ".wma"}
PDF_EXTS = {".pdf"}

EXTRA_MIME_TYPES = {
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".oga": "audio/ogg",
    ".opus": "audio/opus",
    ".flac": "audio/flac",
    ".webp": "image/webp",
    ".heic": "image/heic",
    ".mkv": "video/x-matroska",
    ".mov": "video/quicktime",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
}

UUID_HEX_RE = re.compile(r"([0-9a-fA-F]{32})")
UUID_DASH_RE = re.compile(
    r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
)


class NotionAPIError(RuntimeError):
    """Erro estruturado retornado pela Notion API."""

    def __init__(self, status: int, code: str, message: str, raw: Any = None):
        super().__init__(f"Notion API HTTP {status} ({code}): {message}")
        self.status = status
        self.code = code
        self.message = message
        self.raw = raw


# ==========================================================================
# Utilitários de .env e IDs
# ==========================================================================


def load_env(path: Path = ENV_PATH) -> dict[str, str]:
    """Lê variáveis do arquivo .env mescladas com os.environ (sem imprimir valores)."""
    env: dict[str, str] = {}
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            env[key.strip()] = val.strip().strip('"').strip("'")
    # Variáveis exportadas no ambiente têm precedência se preenchidas
    for k, v in os.environ.items():
        if k.startswith("NOTION_") and v:
            env[k] = v
    return env


def upsert_env_values(updates: dict[str, str], path: Path = ENV_PATH) -> None:
    """Atualiza ou adiciona chaves no .env preservando comentários e demais segredos."""
    lines: list[str] = []
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()

    remaining = dict(updates)
    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in remaining:
                new_lines.append(f"{key}={remaining.pop(key)}")
                continue
        new_lines.append(line)

    if remaining:
        if new_lines and new_lines[-1].strip() != "":
            new_lines.append("")
        has_header = any("Notion Dev Hub" in l for l in new_lines)
        if not has_header:
            new_lines.append("# --- 5. Notion Dev Hub (scripts/notion_hub.py) ---")
        for key, val in remaining.items():
            new_lines.append(f"{key}={val}")

    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def extract_notion_id(raw: str) -> str:
    """Aceita UUID com hífens, 32 hex ou URL completa do Notion e normaliza para UUID."""
    text = (raw or "").strip()
    if not text:
        raise ValueError("ID ou URL do Notion vazio.")

    # Remove query string e fragmento de URLs (evita capturar ?v=VIEW_ID por engano)
    cleaned = text.split("?", 1)[0].split("#", 1)[0]

    m_dash = UUID_DASH_RE.search(cleaned)
    if m_dash:
        return m_dash.group(1).lower()

    matches = UUID_HEX_RE.findall(cleaned)
    if matches:
        h = matches[-1].lower()
        return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"

    raise ValueError(f"Não foi possível extrair um ID válido do Notion a partir de: {raw!r}")


def guess_mime_type(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    if ext in EXTRA_MIME_TYPES:
        return EXTRA_MIME_TYPES[ext]
    mime, _ = mimetypes.guess_type(file_path.name)
    return mime or "application/octet-stream"


def classify_media_block(file_path: Path) -> tuple[str, str]:
    """Retorna (notion_block_type, idea_format_label) para um arquivo local."""
    ext = file_path.suffix.lower()
    if ext in IMAGE_EXTS:
        return ("image", "Foto / Print")
    if ext in VIDEO_EXTS:
        return ("video", "Vídeo")
    if ext in AUDIO_EXTS:
        return ("audio", "Áudio")
    if ext in PDF_EXTS:
        return ("pdf", "PDF / Doc")
    return ("file", "PDF / Doc")


def split_rich_text(text: str, chunk_size: int = 1900) -> list[dict[str, Any]]:
    """Quebra strings longas em chunks <= 2000 chars (limite da Notion API)."""
    if not text:
        return []
    parts: list[dict[str, Any]] = []
    for i in range(0, len(text), chunk_size):
        parts.append({"type": "text", "text": {"content": text[i : i + chunk_size]}})
    return parts


def build_multipart_body(
    fields: list[tuple[str, str]],
    file_field: tuple[str, str, str, bytes],
) -> tuple[bytes, str]:
    """
    Constrói corpo multipart/form-data (RFC 2388) usando apenas stdlib.
    file_field = (field_name, filename, content_type, data_bytes)
    """
    boundary = f"----EmorphosisNotion{uuid.uuid4().hex}"
    buf = io.BytesIO()
    crlf = b"\r\n"

    for name, value in fields:
        buf.write(f"--{boundary}\r\n".encode("ascii"))
        buf.write(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        buf.write(value.encode("utf-8"))
        buf.write(crlf)

    f_name, filename, content_type, data = file_field
    safe_filename = filename.replace('"', "'")
    buf.write(f"--{boundary}\r\n".encode("ascii"))
    buf.write(
        f'Content-Disposition: form-data; name="{f_name}"; filename="{safe_filename}"\r\n'.encode(
            "utf-8"
        )
    )
    buf.write(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
    buf.write(data)
    buf.write(crlf)
    buf.write(f"--{boundary}--\r\n".encode("ascii"))

    return buf.getvalue(), f"multipart/form-data; boundary={boundary}"


# ==========================================================================
# Cliente Notion API (2026-03-11)
# ==========================================================================


class NotionClient:
    """Cliente minimalista e resiliente para a Notion REST API (2026-03-11)."""

    def __init__(self, token: str, version: str = NOTION_VERSION, timeout: int = 60):
        if not token:
            raise ValueError(
                "NOTION_API_KEY não configurada. Adicione NOTION_API_KEY=ntn_... no arquivo .env."
            )
        self.token = token
        self.version = version
        self.timeout = timeout

    def _raw_request(
        self,
        method: str,
        path: str,
        body: bytes | None = None,
        content_type: str | None = None,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        url = path if path.startswith("http") else f"{NOTION_API_BASE}{path}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": self.version,
        }
        if content_type:
            headers["Content-Type"] = content_type

        for attempt in range(max_retries + 1):
            req = urllib.request.Request(url, data=body, headers=headers, method=method.upper())
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read().decode("utf-8")
                    return json.loads(raw) if raw.strip() else {}
            except urllib.error.HTTPError as exc:
                err_body = exc.read().decode("utf-8", errors="replace")
                try:
                    err_json = json.loads(err_body)
                except Exception:
                    err_json = {"code": "http_error", "message": err_body}

                # Respeita rate limit (429) e indisponibilidade transitória (502/503/529)
                if exc.code in (429, 502, 503, 529) and attempt < max_retries:
                    retry_after = exc.headers.get("Retry-After") if exc.headers else None
                    delay = float(retry_after) if retry_after and retry_after.isdigit() else (1.5 * (attempt + 1))
                    time.sleep(min(delay, 10.0))
                    continue

                raise NotionAPIError(
                    status=exc.code,
                    code=str(err_json.get("code", "http_error")),
                    message=str(err_json.get("message", err_body)),
                    raw=err_json,
                ) from exc
            except urllib.error.URLError as exc:
                if attempt < max_retries:
                    time.sleep(1.0 * (attempt + 1))
                    continue
                raise RuntimeError(f"Falha de rede ao conectar na Notion API ({url}): {exc.reason}") from exc

        raise RuntimeError("Limite de tentativas excedido na Notion API.")

    def request_json(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
        content_type = "application/json" if payload is not None else None
        return self._raw_request(method, path, body=body, content_type=content_type)

    # --- Endpoints essenciais ---

    def get_me(self) -> dict[str, Any]:
        return self.request_json("GET", "/users/me")

    def get_page(self, page_id: str) -> dict[str, Any]:
        return self.request_json("GET", f"/pages/{page_id}")

    def create_page(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request_json("POST", "/pages", payload)

    def update_page(self, page_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request_json("PATCH", f"/pages/{page_id}", payload)

    def append_block_children(self, block_id: str, children: list[dict[str, Any]]) -> dict[str, Any]:
        return self.request_json("PATCH", f"/blocks/{block_id}/children", {"children": children})

    def create_database(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request_json("POST", "/databases", payload)

    def get_database(self, database_id: str) -> dict[str, Any]:
        return self.request_json("GET", f"/databases/{database_id}")

    def get_data_source(self, data_source_id: str) -> dict[str, Any]:
        return self.request_json("GET", f"/data_sources/{data_source_id}")

    def update_data_source(self, data_source_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request_json("PATCH", f"/data_sources/{data_source_id}", payload)

    def query_data_source(
        self,
        data_source_id: str,
        filter_obj: dict[str, Any] | None = None,
        sorts: list[dict[str, Any]] | None = None,
        page_size: int = 50,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            body: dict[str, Any] = {"page_size": min(page_size, 100)}
            if filter_obj:
                body["filter"] = filter_obj
            if sorts:
                body["sorts"] = sorts
            if cursor:
                body["start_cursor"] = cursor
            resp = self.request_json("POST", f"/data_sources/{data_source_id}/query", body)
            results.extend(resp.get("results", []))
            if not resp.get("has_more") or not resp.get("next_cursor") or len(results) >= page_size:
                break
            cursor = resp["next_cursor"]
        return results[:page_size]

    def create_view(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request_json("POST", "/views", payload)

    # --- File Upload API (single-part <= 20 MiB e multi-part > 20 MiB até 5 GiB) ---

    def upload_file(self, file_path: Path) -> dict[str, Any]:
        """
        Envia um arquivo local (áudio, vídeo, imagem, PDF, etc.) diretamente para o Notion
        via File Upload API. Retorna dict com id, filename, mime_type, block_type, format_label.
        """
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        size = file_path.stat().st_size
        if size == 0:
            raise ValueError(f"Arquivo vazio não pode ser enviado: {file_path}")

        filename = file_path.name
        mime_type = guess_mime_type(file_path)
        block_type, format_label = classify_media_block(file_path)

        if size <= SINGLE_PART_MAX_BYTES:
            created = self.request_json(
                "POST",
                "/file_uploads",
                {
                    "mode": "single_part",
                    "filename": filename,
                    "content_type": mime_type,
                },
            )
            upload_id = created["id"]
            data = file_path.read_bytes()
            body, ctype = build_multipart_body(
                fields=[],
                file_field=("file", filename, mime_type, data),
            )
            self._raw_request("POST", f"/file_uploads/{upload_id}/send", body=body, content_type=ctype)
        else:
            num_parts = math.ceil(size / MULTI_PART_CHUNK_BYTES)
            created = self.request_json(
                "POST",
                "/file_uploads",
                {
                    "mode": "multi_part",
                    "filename": filename,
                    "content_type": mime_type,
                    "number_of_parts": num_parts,
                },
            )
            upload_id = created["id"]
            with file_path.open("rb") as fh:
                for part_num in range(1, num_parts + 1):
                    chunk = fh.read(MULTI_PART_CHUNK_BYTES)
                    body, ctype = build_multipart_body(
                        fields=[("part_number", str(part_num))],
                        file_field=("file", filename, mime_type, chunk),
                    )
                    self._raw_request(
                        "POST",
                        f"/file_uploads/{upload_id}/send",
                        body=body,
                        content_type=ctype,
                    )
            self.request_json("POST", f"/file_uploads/{upload_id}/complete", {})

        return {
            "id": upload_id,
            "filename": filename,
            "size": size,
            "mime_type": mime_type,
            "block_type": block_type,
            "format_label": format_label,
        }


# ==========================================================================
# Extratores de propriedades (leitura amigável de respostas Notion)
# ==========================================================================


def prop_plain_text(props: dict[str, Any], name: str) -> str:
    p = props.get(name) or {}
    ptype = p.get("type")
    if ptype == "title":
        return "".join(t.get("plain_text", "") for t in p.get("title", []))
    if ptype == "rich_text":
        return "".join(t.get("plain_text", "") for t in p.get("rich_text", []))
    if ptype == "status":
        return (p.get("status") or {}).get("name", "")
    if ptype == "select":
        return (p.get("select") or {}).get("name", "")
    if ptype == "multi_select":
        return ", ".join(opt.get("name", "") for opt in p.get("multi_select", []))
    if ptype == "url":
        return p.get("url") or ""
    if ptype == "date":
        return (p.get("date") or {}).get("start", "")
    if ptype == "checkbox":
        return "sim" if p.get("checkbox") else "não"
    if ptype == "files":
        return ", ".join(f.get("name", "arquivo") for f in p.get("files", []))
    if ptype == "relation":
        return str(len(p.get("relation", [])))
    return ""


def prop_multi_list(props: dict[str, Any], name: str) -> list[str]:
    p = props.get(name) or {}
    if p.get("type") == "multi_select":
        return [opt.get("name", "") for opt in p.get("multi_select", []) if opt.get("name")]
    return []


def build_media_block(upload_info: dict[str, Any]) -> dict[str, Any]:
    btype = upload_info["block_type"]
    payload: dict[str, Any] = {
        "type": "file_upload",
        "file_upload": {"id": upload_info["id"]},
    }
    if btype == "file":
        payload["name"] = upload_info["filename"]
    return {
        "object": "block",
        "type": btype,
        btype: payload,
    }


def build_link_block(url: str) -> dict[str, Any]:
    """Usa embed para plataformas de mídia/design e bookmark para links gerais."""
    lower = url.lower()
    embed_domains = (
        "youtube.com",
        "youtu.be",
        "vimeo.com",
        "loom.com",
        "spotify.com",
        "soundcloud.com",
        "figma.com",
        "codepen.io",
        "instagram.com",
        "tiktok.com",
        "drive.google.com",
    )
    if any(dom in lower for dom in embed_domains):
        return {"object": "block", "type": "embed", "embed": {"url": url}}
    return {"object": "block", "type": "bookmark", "bookmark": {"url": url}}


def build_notes_blocks(notes: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for raw_line in notes.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("- [ ] "):
            blocks.append(
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {"rich_text": split_rich_text(line[6:]), "checked": False},
                }
            )
        elif line.startswith("- "):
            blocks.append(
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": split_rich_text(line[2:])},
                }
            )
        else:
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": split_rich_text(line)},
                }
            )
    return blocks


# ==========================================================================
# Schema Builders & Bootstrap
# ==========================================================================


def ideas_initial_properties() -> dict[str, Any]:
    return {
        "Ideia": {"title": {}},
        "Status": {"select": {"options": IDEA_STATUSES}},
        "Formatos": {"multi_select": {"options": IDEA_FORMATS}},
        "Pilar": {"multi_select": {"options": IDEA_PILLARS}},
        "Autor": {"select": {"options": TEAM_MEMBERS}},
        "Link Principal": {"url": {}},
        "Mídia / Drive": {"url": {}},
        "Anexos / Capa": {"files": {}},
        "Criado em": {"created_time": {}},
    }


def tasks_initial_properties(ideas_ds_id: str, include_status_options: bool = True) -> dict[str, Any]:
    status_schema: dict[str, Any] = (
        {"status": {"options": TASK_STATUSES}} if include_status_options else {"status": {}}
    )
    return {
        "Tarefa": {"title": {}},
        "Status": status_schema,
        "Prioridade": {"select": {"options": TASK_PRIORITIES}},
        "Responsável": {"select": {"options": TEAM_MEMBERS}},
        "Área": {"multi_select": {"options": PROJECT_AREAS}},
        "Tipo": {"select": {"options": TASK_TYPES}},
        "Prazo": {"date": {}},
        "Branch / PR": {"url": {}},
        "Ideia Origem": {
            "relation": {
                "data_source_id": ideas_ds_id,
                "type": "dual_property",
                "dual_property": {},
            }
        },
        "Registrado no DEVLOG": {"checkbox": {}},
    }


def _safe_create_view(client: NotionClient, payload: dict[str, Any], label: str) -> bool:
    try:
        client.create_view(payload)
        print(f"  [OK] View criada: {label}")
        return True
    except NotionAPIError as exc:
        print(f"  [AVISO] Não foi possível criar a view '{label}' automaticamente: {exc.message}")
        return False


def cmd_doctor(client: NotionClient, env: dict[str, str]) -> int:
    print("=== EMORPHOSIS // NOTION DEV HUB — DIAGNÓSTICO ===")
    me = client.get_me()
    bot_name = me.get("name") or me.get("id", "desconhecido")
    print(f"[OK] Conectado na Notion API ({client.version}) como: {bot_name}")

    checks = [
        ("NOTION_ROOT_PAGE_ID", "page"),
        ("NOTION_TASKS_DS_ID", "data_source"),
        ("NOTION_IDEAS_DS_ID", "data_source"),
    ]
    missing = False
    for key, kind in checks:
        val = env.get(key, "").strip()
        if not val:
            print(f"[PENDENTE] {key} ainda não configurado no .env")
            missing = True
            continue
        try:
            norm = extract_notion_id(val)
            if kind == "page":
                client.get_page(norm)
            else:
                client.get_data_source(norm)
            print(f"[OK] {key} acessível ({norm})")
        except Exception as exc:
            print(f"[ERRO] {key} ({val}): {exc}")
            missing = True

    if missing:
        print("\nDica: rode `python scripts/notion_hub.py bootstrap --page-id <URL_DA_PAGINA_RAIZ>`")
        return 1

    print("\n[OK] Tudo pronto! Seu Emorphosis Dev Hub está 100% operacional.")
    return 0


def cmd_bootstrap(
    client: NotionClient,
    page_id_raw: str,
    seed: bool = True,
    save_env: bool = True,
    env_path: Path = ENV_PATH,
) -> dict[str, str]:
    root_page_id = extract_notion_id(page_id_raw)
    print(f"1/5 Verificando acesso à página raiz ({root_page_id})...")
    client.get_page(root_page_id)

    # Cabeçalho visual no topo do Hub
    client.append_block_children(
        root_page_id,
        [
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "icon": {"type": "emoji", "emoji": "⚡"},
                    "color": "green_background",
                    "rich_text": split_rich_text(
                        "EMORPHOSIS // DEV HUB — Central de tarefas da equipe e cofre multimídia "
                        "(áudios, vídeos, fotos e links). Integrado ao Google Antigravity via Notion MCP "
                        "e scripts/notion_hub.py."
                    ),
                },
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": split_rich_text("💡 Idea & Media Vault (Moodboard & Referências)")},
            },
        ],
    )

    print("2/5 Criando banco '💡 Idea & Media Vault'...")
    ideas_db = client.create_database(
        {
            "parent": {"type": "page_id", "page_id": root_page_id},
            "icon": {"type": "emoji", "emoji": "💡"},
            "title": split_rich_text("Idea & Media Vault"),
            "is_inline": True,
            "initial_data_source": {"properties": ideas_initial_properties()},
        }
    )
    ideas_db_id = ideas_db["id"]
    ideas_ds_id = ideas_db["data_sources"][0]["id"]
    print(f"  [OK] Idea Vault DB={ideas_db_id} | DS={ideas_ds_id}")

    client.append_block_children(
        root_page_id,
        [
            {"object": "block", "type": "divider", "divider": {}},
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": split_rich_text("📋 Dev Task Tracker (Controle de Tarefas)")},
            },
        ],
    )

    print("3/5 Criando banco '📋 Dev Task Tracker' com relação bidirecional...")
    try:
        tasks_db = client.create_database(
            {
                "parent": {"type": "page_id", "page_id": root_page_id},
                "icon": {"type": "emoji", "emoji": "📋"},
                "title": split_rich_text("Dev Task Tracker"),
                "is_inline": True,
                "initial_data_source": {
                    "properties": tasks_initial_properties(ideas_ds_id, include_status_options=True)
                },
            }
        )
    except NotionAPIError:
        # Fallback: cria com status padrão e aplica opções customizadas via PATCH data_source
        tasks_db = client.create_database(
            {
                "parent": {"type": "page_id", "page_id": root_page_id},
                "icon": {"type": "emoji", "emoji": "📋"},
                "title": split_rich_text("Dev Task Tracker"),
                "is_inline": True,
                "initial_data_source": {
                    "properties": tasks_initial_properties(ideas_ds_id, include_status_options=False)
                },
            }
        )
        tasks_ds_tmp = tasks_db["data_sources"][0]["id"]
        try:
            client.update_data_source(
                tasks_ds_tmp,
                {"properties": {"Status": {"status": {"options": TASK_STATUSES}}}},
            )
        except NotionAPIError as exc:
            print(f"  [AVISO] Status criado com opções padrão do Notion ({exc.message})")

    tasks_db_id = tasks_db["id"]
    tasks_ds_id = tasks_db["data_sources"][0]["id"]
    print(f"  [OK] Task Tracker DB={tasks_db_id} | DS={tasks_ds_id}")

    # Renomeia a propriedade de volta (back-relation) no Idea Vault para "Tarefas Geradas"
    tasks_ds_schema = client.get_data_source(tasks_ds_id)
    ideas_ds_schema = client.get_data_source(ideas_ds_id)

    rel_prop = (tasks_ds_schema.get("properties") or {}).get("Ideia Origem", {})
    synced_id = ((rel_prop.get("relation") or {}).get("dual_property") or {}).get("synced_property_id")
    if synced_id:
        try:
            client.update_data_source(
                ideas_ds_id,
                {"properties": {synced_id: {"name": "Tarefas Geradas"}}},
            )
            print("  [OK] Relação bidirecional nomeada: 'Ideia Origem' ⇄ 'Tarefas Geradas'")
        except NotionAPIError as exc:
            print(f"  [AVISO] Não foi possível renomear back-relation automaticamente: {exc.message}")

    # Views programáticas via Notion Views API (2026-03-11)
    print("4/5 Configurando Views (Kanban, Moodboard Galeria, Inbox e Prioridades)...")
    task_props = tasks_ds_schema.get("properties") or {}
    idea_props = ideas_ds_schema.get("properties") or {}

    task_status_id = (task_props.get("Status") or {}).get("id")
    idea_status_id = (idea_props.get("Status") or {}).get("id")
    idea_files_id = (idea_props.get("Anexos / Capa") or {}).get("id")

    if task_status_id:
        _safe_create_view(
            client,
            {
                "database_id": tasks_db_id,
                "data_source_id": tasks_ds_id,
                "name": "📋 Kanban (Status)",
                "type": "board",
                "position": {"type": "start"},
                "configuration": {
                    "type": "board",
                    "group_by": {
                        "type": "status",
                        "property_id": task_status_id,
                        "group_by": "option",
                        "sort": {"type": "manual"},
                    },
                    "card_layout": "compact",
                    "properties": [
                        {"property_id": "Prioridade", "visible": True},
                        {"property_id": "Responsável", "visible": True},
                        {"property_id": "Área", "visible": True},
                        {"property_id": "Prazo", "visible": True},
                    ],
                },
            },
            "📋 Kanban (Status)",
        )

    _safe_create_view(
        client,
        {
            "database_id": tasks_db_id,
            "data_source_id": tasks_ds_id,
            "name": "🔥 Prioridades Ativas",
            "type": "table",
            "filter": {"property": "Status", "status": {"does_not_equal": "Concluído"}},
        },
        "🔥 Prioridades Ativas",
    )

    _safe_create_view(
        client,
        {
            "database_id": tasks_db_id,
            "data_source_id": tasks_ds_id,
            "name": "✅ Concluídas (DEVLOG)",
            "type": "table",
            "filter": {"property": "Status", "status": {"equals": "Concluído"}},
        },
        "✅ Concluídas (DEVLOG)",
    )

    gallery_config: dict[str, Any] = {
        "type": "gallery",
        "cover_size": "medium",
        "cover_aspect": "cover",
        "card_layout": "list",
        "properties": [
            {"property_id": "Formatos", "visible": True},
            {"property_id": "Pilar", "visible": True},
            {"property_id": "Status", "visible": True},
            {"property_id": "Autor", "visible": True},
        ],
    }
    if idea_files_id:
        gallery_config["cover"] = {"type": "property", "property_id": idea_files_id}
    else:
        gallery_config["cover"] = {"type": "page_cover"}

    _safe_create_view(
        client,
        {
            "database_id": ideas_db_id,
            "data_source_id": ideas_ds_id,
            "name": "🎨 Moodboard (Galeria)",
            "type": "gallery",
            "position": {"type": "start"},
            "configuration": gallery_config,
        },
        "🎨 Moodboard (Galeria)",
    )

    _safe_create_view(
        client,
        {
            "database_id": ideas_db_id,
            "data_source_id": ideas_ds_id,
            "name": "📥 Inbox de Captura",
            "type": "table",
            "filter": {"property": "Status", "select": {"equals": "Captura Bruta"}},
        },
        "📥 Inbox de Captura",
    )

    if idea_status_id:
        _safe_create_view(
            client,
            {
                "database_id": ideas_db_id,
                "data_source_id": ideas_ds_id,
                "name": "🚀 Pipeline de Ideias",
                "type": "board",
                "configuration": {
                    "type": "board",
                    "group_by": {
                        "type": "select",
                        "property_id": idea_status_id,
                        "sort": {"type": "manual"},
                    },
                    "card_layout": "compact",
                },
            },
            "🚀 Pipeline de Ideias",
        )

    # Seed inicial com as pendências reais documentadas no GEMINI.md
    if seed:
        print("5/5 Populando backlog inicial do Emorphosis (pendências do GEMINI.md)...")
        fitlab_idea = create_idea(
            client=client,
            ideas_ds_id=ideas_ds_id,
            title="Expandir biblioteca de recortes PNG reais do Fit Lab",
            formats=["Foto / Print", "Texto / Briefing"],
            pillars=["Fit Lab", "Catálogo / Marcas"],
            status="Virou Tarefa",
            author="Ambos",
            notes=(
                "Ideia referência já mapeada no GEMINI.md: hoje temos 3 recortes reais "
                "(Atelier Aevus jaqueta/calça e Drestudio boné). Reunir fotos/vídeos de peças "
                "icônicas de outras marcas do catálogo de 131 marcas para recortar em PNG."
            ),
        )
        seed_tasks = [
            {
                "title": "Ativar persistência MySQL em produção e migrar endpoints PHP",
                "status": "Backlog",
                "priority": "Alta",
                "owner": "Ambos",
                "areas": ["Backend PHP / MySQL", "Infra / Deploy"],
                "task_type": "Feature",
                "notes": "Configurar DB_NAME/DB_USER/DB_PASS no .env, aplicar database/schema.sql e integrar demais endpoints além de subscribe_drops.php.",
            },
            {
                "title": "Expandir recortes PNG reais no Fit Lab (novas marcas)",
                "status": "A Fazer",
                "priority": "Média",
                "owner": "Ambos",
                "areas": ["Fit Lab", "M4RCAS / Catálogo"],
                "task_type": "Conteúdo / Marca",
                "idea_id": fitlab_idea["id"],
                "notes": "Adicionar novos recortes em assets/img/fitlab/ e registrar em assets/js/marcas-app.js.",
            },
            {
                "title": "Criar validação automatizada (PHP lint + check JSON do build_marcas.py)",
                "status": "Backlog",
                "priority": "Média",
                "owner": "Ambos",
                "areas": ["Infra / Deploy", "M4RCAS / Catálogo"],
                "task_type": "Melhoria",
                "notes": "Script único de verificação pré-deploy (sintaxe PHP, integridade de marcas.json e imagens sem link).",
            },
        ]
        for item in seed_tasks:
            create_task(client=client, tasks_ds_id=tasks_ds_id, **item)
        print("  [OK] 1 ideia de referência + 3 tarefas iniciais criadas.")
    else:
        print("5/5 Seed ignorado (--no-seed).")

    ids = {
        "NOTION_ROOT_PAGE_ID": root_page_id,
        "NOTION_TASKS_DB_ID": tasks_db_id,
        "NOTION_TASKS_DS_ID": tasks_ds_id,
        "NOTION_IDEAS_DB_ID": ideas_db_id,
        "NOTION_IDEAS_DS_ID": ideas_ds_id,
    }
    if save_env:
        upsert_env_values(ids, path=env_path)
        print(f"\n[OK] IDs salvos automaticamente em {env_path.name}!")
    return ids


# ==========================================================================
# Operações de Tarefas (Dev Task Tracker)
# ==========================================================================


def create_task(
    client: NotionClient,
    tasks_ds_id: str,
    title: str,
    status: str = "Backlog",
    priority: str = "Média",
    owner: str | None = None,
    areas: list[str] | None = None,
    task_type: str | None = None,
    due: str | None = None,
    pr_url: str | None = None,
    idea_id: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    props: dict[str, Any] = {
        "Tarefa": {"title": split_rich_text(title)},
        "Status": {"status": {"name": status}},
        "Prioridade": {"select": {"name": priority}},
        "Registrado no DEVLOG": {"checkbox": False},
    }
    if owner:
        props["Responsável"] = {"select": {"name": owner}}
    if areas:
        props["Área"] = {"multi_select": [{"name": a} for a in areas]}
    if task_type:
        props["Tipo"] = {"select": {"name": task_type}}
    if due:
        props["Prazo"] = {"date": {"start": due}}
    if pr_url:
        props["Branch / PR"] = {"url": pr_url}
    if idea_id:
        props["Ideia Origem"] = {"relation": [{"id": extract_notion_id(idea_id)}]}

    payload: dict[str, Any] = {
        "parent": {"type": "data_source_id", "data_source_id": tasks_ds_id},
        "properties": props,
    }
    if notes:
        payload["children"] = build_notes_blocks(notes)
    return client.create_page(payload)


def list_tasks(
    client: NotionClient,
    tasks_ds_id: str,
    status: str | None = None,
    owner: str | None = None,
    area: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    conditions: list[dict[str, Any]] = []
    if status:
        conditions.append({"property": "Status", "status": {"equals": status}})
    if owner:
        conditions.append({"property": "Responsável", "select": {"equals": owner}})
    if area:
        conditions.append({"property": "Área", "multi_select": {"contains": area}})

    filter_obj: dict[str, Any] | None = None
    if len(conditions) == 1:
        filter_obj = conditions[0]
    elif len(conditions) > 1:
        filter_obj = {"and": conditions}

    return client.query_data_source(
        tasks_ds_id,
        filter_obj=filter_obj,
        sorts=[{"timestamp": "last_edited_time", "direction": "descending"}],
        page_size=limit,
    )


def update_task(
    client: NotionClient,
    page_id: str,
    status: str | None = None,
    priority: str | None = None,
    owner: str | None = None,
    areas: list[str] | None = None,
    pr_url: str | None = None,
    due: str | None = None,
    devlog_synced: bool | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    norm_id = extract_notion_id(page_id)
    props: dict[str, Any] = {}
    if status:
        props["Status"] = {"status": {"name": status}}
    if priority:
        props["Prioridade"] = {"select": {"name": priority}}
    if owner:
        props["Responsável"] = {"select": {"name": owner}}
    if areas:
        props["Área"] = {"multi_select": [{"name": a} for a in areas]}
    if pr_url:
        props["Branch / PR"] = {"url": pr_url}
    if due:
        props["Prazo"] = {"date": {"start": due}}
    if devlog_synced is not None:
        props["Registrado no DEVLOG"] = {"checkbox": devlog_synced}

    updated = client.update_page(norm_id, {"properties": props}) if props else client.get_page(norm_id)
    if notes:
        client.append_block_children(norm_id, build_notes_blocks(notes))
    return updated


# ==========================================================================
# Operações de Ideias & Mídia (Idea & Media Vault)
# ==========================================================================


def create_idea(
    client: NotionClient,
    ideas_ds_id: str,
    title: str,
    formats: list[str] | None = None,
    pillars: list[str] | None = None,
    status: str = "Captura Bruta",
    author: str | None = None,
    link: str | None = None,
    drive_url: str | None = None,
    notes: str | None = None,
    files: list[Path] | None = None,
    embeds: list[str] | None = None,
) -> dict[str, Any]:
    detected_formats = list(formats or [])
    children: list[dict[str, Any]] = []
    file_prop_entries: list[dict[str, Any]] = []
    first_image_upload_id: str | None = None

    if notes:
        children.extend(build_notes_blocks(notes))
        if not detected_formats:
            detected_formats.append("Texto / Briefing")

    if link:
        if "Link / Ref" not in detected_formats:
            detected_formats.append("Link / Ref")
        children.append(build_link_block(link))

    for embed_url in embeds or []:
        if "Link / Ref" not in detected_formats:
            detected_formats.append("Link / Ref")
        children.append(build_link_block(embed_url))

    for fpath in files or []:
        up = client.upload_file(fpath)
        if up["format_label"] not in detected_formats:
            detected_formats.append(up["format_label"])
        if up["block_type"] == "image" and not first_image_upload_id:
            first_image_upload_id = up["id"]
        file_prop_entries.append(
            {
                "name": up["filename"],
                "type": "file_upload",
                "file_upload": {"id": up["id"]},
            }
        )
        children.append(build_media_block(up))

    props: dict[str, Any] = {
        "Ideia": {"title": split_rich_text(title)},
        "Status": {"select": {"name": status}},
    }
    if detected_formats:
        props["Formatos"] = {"multi_select": [{"name": f} for f in detected_formats]}
    if pillars:
        props["Pilar"] = {"multi_select": [{"name": p} for p in pillars]}
    if author:
        props["Autor"] = {"select": {"name": author}}
    if link:
        props["Link Principal"] = {"url": link}
    if drive_url:
        props["Mídia / Drive"] = {"url": drive_url}
    if file_prop_entries:
        props["Anexos / Capa"] = {"files": file_prop_entries}

    payload: dict[str, Any] = {
        "parent": {"type": "data_source_id", "data_source_id": ideas_ds_id},
        "properties": props,
    }
    if first_image_upload_id:
        payload["cover"] = {"type": "file_upload", "file_upload": {"id": first_image_upload_id}}
    if children:
        payload["children"] = children

    return client.create_page(payload)


def attach_to_idea(
    client: NotionClient,
    page_id: str,
    files: list[Path] | None = None,
    embeds: list[str] | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    norm_id = extract_notion_id(page_id)
    page = client.get_page(norm_id)
    props = page.get("properties") or {}

    existing_formats = prop_multi_list(props, "Formatos")
    existing_files_raw = (props.get("Anexos / Capa") or {}).get("files", [])

    # Preserva anexos já existentes no card (converte external/file para formato aceito ou mantém novos)
    preserved_files: list[dict[str, Any]] = []
    for item in existing_files_raw:
        ftype = item.get("type")
        if ftype == "external":
            preserved_files.append(
                {
                    "name": item.get("name", "link"),
                    "type": "external",
                    "external": {"url": item["external"]["url"]},
                }
            )
        elif ftype == "file" and (item.get("file") or {}).get("url"):
            file_obj: dict[str, Any] = {"url": item["file"]["url"]}
            if item["file"].get("expiry_time"):
                file_obj["expiry_time"] = item["file"]["expiry_time"]
            preserved_files.append(
                {
                    "name": item.get("name", "arquivo"),
                    "type": "file",
                    "file": file_obj,
                }
            )

    new_children: list[dict[str, Any]] = []
    first_image_upload_id: str | None = None

    if notes:
        new_children.extend(build_notes_blocks(notes))

    for embed_url in embeds or []:
        if "Link / Ref" not in existing_formats:
            existing_formats.append("Link / Ref")
        new_children.append(build_link_block(embed_url))

    uploaded_count = 0
    for fpath in files or []:
        up = client.upload_file(fpath)
        uploaded_count += 1
        if up["format_label"] not in existing_formats:
            existing_formats.append(up["format_label"])
        if up["block_type"] == "image" and not first_image_upload_id:
            first_image_upload_id = up["id"]
        preserved_files.append(
            {
                "name": up["filename"],
                "type": "file_upload",
                "file_upload": {"id": up["id"]},
            }
        )
        new_children.append(build_media_block(up))

    update_payload: dict[str, Any] = {"properties": {}}
    if existing_formats:
        update_payload["properties"]["Formatos"] = {
            "multi_select": [{"name": f} for f in existing_formats]
        }
    if uploaded_count > 0:
        update_payload["properties"]["Anexos / Capa"] = {"files": preserved_files}
    if first_image_upload_id and not page.get("cover"):
        update_payload["cover"] = {
            "type": "file_upload",
            "file_upload": {"id": first_image_upload_id},
        }

    if update_payload["properties"] or "cover" in update_payload:
        client.update_page(norm_id, update_payload)
    if new_children:
        client.append_block_children(norm_id, new_children)

    return client.get_page(norm_id)


def list_ideas(
    client: NotionClient,
    ideas_ds_id: str,
    status: str | None = None,
    fmt: str | None = None,
    pillar: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    conditions: list[dict[str, Any]] = []
    if status:
        conditions.append({"property": "Status", "select": {"equals": status}})
    if fmt:
        conditions.append({"property": "Formatos", "multi_select": {"contains": fmt}})
    if pillar:
        conditions.append({"property": "Pilar", "multi_select": {"contains": pillar}})

    filter_obj: dict[str, Any] | None = None
    if len(conditions) == 1:
        filter_obj = conditions[0]
    elif len(conditions) > 1:
        filter_obj = {"and": conditions}

    return client.query_data_source(
        ideas_ds_id,
        filter_obj=filter_obj,
        sorts=[{"timestamp": "created_time", "direction": "descending"}],
        page_size=limit,
    )


def promote_idea_to_task(
    client: NotionClient,
    tasks_ds_id: str,
    idea_page_id: str,
    title: str | None = None,
    priority: str = "Média",
    owner: str | None = None,
    areas: list[str] | None = None,
    task_type: str = "Feature",
    due: str | None = None,
) -> dict[str, Any]:
    norm_idea = extract_notion_id(idea_page_id)
    idea = client.get_page(norm_idea)
    idea_props = idea.get("properties") or {}
    idea_title = title or prop_plain_text(idea_props, "Ideia") or "Nova tarefa a partir de ideia"

    # Mapeia pilares da ideia para áreas do projeto se --area não for informado
    if not areas:
        pillar_to_area = {
            "Fit Lab": "Fit Lab",
            "Visual / Glitch": "Design / UI",
            "H0M3 / Mapa": "H0M3 / Mapa",
            "Catálogo / Marcas": "M4RCAS / Catálogo",
            "Drops / Calendário": "C4L3NDAR10",
        }
        inferred = [pillar_to_area[p] for p in prop_multi_list(idea_props, "Pilar") if p in pillar_to_area]
        areas = inferred or None

    task = create_task(
        client=client,
        tasks_ds_id=tasks_ds_id,
        title=idea_title,
        status="A Fazer",
        priority=priority,
        owner=owner or prop_plain_text(idea_props, "Autor") or None,
        areas=areas,
        task_type=task_type,
        due=due,
        idea_id=norm_idea,
        notes=f"Promovida automaticamente do Idea & Media Vault: {idea.get('url', '')}",
    )
    client.update_page(norm_idea, {"properties": {"Status": {"select": {"name": "Virou Tarefa"}}}})
    return task


# ==========================================================================
# Sincronização Notion -> DEVLOG.md
# ==========================================================================


def render_devlog_entry(tasks: list[dict[str, Any]], author: str, date_str: str | None = None) -> str:
    today = date_str or dt.date.today().isoformat()
    areas_set: list[str] = []
    bullets: list[str] = []
    for t in tasks:
        props = t.get("properties") or {}
        title = prop_plain_text(props, "Tarefa") or "(sem título)"
        areas = prop_multi_list(props, "Área")
        pr = prop_plain_text(props, "Branch / PR")
        for a in areas:
            if a not in areas_set:
                areas_set.append(a)
        suffix = f" ({pr})" if pr else ""
        bullets.append(f"- {title}{suffix}")

    areas_label = ", ".join(areas_set) if areas_set else "Notion Dev Hub"
    lines = [
        f"## [{today}] — Entregas Concluídas (Sync Notion Dev Hub)",
        f"**Responsável:** {author}",
        f"**Áreas:** {areas_label}",
        "",
        "### O que mudou",
        *bullets,
        "",
        "### Contexto / Porquê",
        "- Registro sincronizado a partir de tarefas concluídas no `Dev Task Tracker` (Notion).",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def prepend_devlog_entry(entry: str, devlog_path: Path = DEVLOG_PATH) -> None:
    content = devlog_path.read_text(encoding="utf-8")
    marker = "\n---\n\n"
    idx = content.find(marker)
    if idx != -1:
        insert_pos = idx + len(marker)
        updated = content[:insert_pos] + entry + content[insert_pos:]
    else:
        updated = entry + content
    devlog_path.write_text(updated, encoding="utf-8")


def sync_devlog(
    client: NotionClient,
    tasks_ds_id: str,
    author: str = "Equipe Emorphosis (+ Antigravity)",
    apply: bool = False,
    limit: int = 20,
    devlog_path: Path = DEVLOG_PATH,
) -> tuple[list[dict[str, Any]], str]:
    completed = client.query_data_source(
        tasks_ds_id,
        filter_obj={
            "and": [
                {"property": "Status", "status": {"equals": "Concluído"}},
                {"property": "Registrado no DEVLOG", "checkbox": {"equals": False}},
            ]
        },
        sorts=[{"timestamp": "last_edited_time", "direction": "descending"}],
        page_size=limit,
    )
    if not completed:
        return ([], "")

    entry = render_devlog_entry(completed, author=author)
    if apply:
        prepend_devlog_entry(entry, devlog_path=devlog_path)
        for task in completed:
            client.update_page(
                task["id"],
                {"properties": {"Registrado no DEVLOG": {"checkbox": True}}},
            )
    return (completed, entry)


# ==========================================================================
# CLI Interface
# ==========================================================================


def _require_ds_id(env: dict[str, str], key: str) -> str:
    val = env.get(key, "").strip()
    if not val:
        raise SystemExit(
            f"[ERRO] {key} não configurado no .env. "
            "Execute `python scripts/notion_hub.py bootstrap --page-id <URL_DA_PAGINA_RAIZ>` primeiro."
        )
    return extract_notion_id(val)


def _print_tasks_table(tasks: list[dict[str, Any]], as_json: bool = False) -> None:
    if as_json:
        out = [
            {
                "id": t["id"],
                "title": prop_plain_text(t.get("properties", {}), "Tarefa"),
                "status": prop_plain_text(t.get("properties", {}), "Status"),
                "priority": prop_plain_text(t.get("properties", {}), "Prioridade"),
                "owner": prop_plain_text(t.get("properties", {}), "Responsável"),
                "areas": prop_multi_list(t.get("properties", {}), "Área"),
                "due": prop_plain_text(t.get("properties", {}), "Prazo"),
                "url": t.get("url", ""),
            }
            for t in tasks
        ]
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    if not tasks:
        print("(Nenhuma tarefa encontrada com os filtros informados.)")
        return

    for t in tasks:
        p = t.get("properties", {})
        status = prop_plain_text(p, "Status") or "-"
        prio = prop_plain_text(p, "Prioridade") or "-"
        owner = prop_plain_text(p, "Responsável") or "-"
        areas = prop_plain_text(p, "Área") or "-"
        title = prop_plain_text(p, "Tarefa") or "(sem título)"
        print(f"[{status} | {prio}] {title}")
        print(f"   ID: {t['id']} | Dev: {owner} | Área: {areas}")
        if t.get("url"):
            print(f"   URL: {t['url']}")


def _print_ideas_table(ideas: list[dict[str, Any]], as_json: bool = False) -> None:
    if as_json:
        out = [
            {
                "id": i["id"],
                "title": prop_plain_text(i.get("properties", {}), "Ideia"),
                "status": prop_plain_text(i.get("properties", {}), "Status"),
                "formats": prop_multi_list(i.get("properties", {}), "Formatos"),
                "pillars": prop_multi_list(i.get("properties", {}), "Pilar"),
                "author": prop_plain_text(i.get("properties", {}), "Autor"),
                "link": prop_plain_text(i.get("properties", {}), "Link Principal"),
                "files": prop_plain_text(i.get("properties", {}), "Anexos / Capa"),
                "url": i.get("url", ""),
            }
            for i in ideas
        ]
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    if not ideas:
        print("(Nenhuma ideia encontrada com os filtros informados.)")
        return

    for item in ideas:
        p = item.get("properties", {})
        status = prop_plain_text(p, "Status") or "-"
        fmts = prop_plain_text(p, "Formatos") or "-"
        pillars = prop_plain_text(p, "Pilar") or "-"
        title = prop_plain_text(p, "Ideia") or "(sem título)"
        print(f"[{status}] {title}")
        print(f"   ID: {item['id']} | Formatos: {fmts} | Pilar: {pillars}")
        if item.get("url"):
            print(f"   URL: {item['url']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="notion_hub.py",
        description="EMORPHOSIS // Notion Dev Hub CLI (Tarefas + Cofre de Ideias Multimídia)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # doctor
    sub.add_parser("doctor", help="Testa conexão com a Notion API e verifica IDs do .env")

    # bootstrap
    p_boot = sub.add_parser(
        "bootstrap",
        help="Cria os 2 bancos, relação bidirecional, views e backlog inicial na página raiz",
    )
    p_boot.add_argument("--page-id", required=True, help="URL ou ID da página raiz no Notion")
    p_boot.add_argument("--no-seed", action="store_true", help="Não criar tarefas/ideia iniciais")
    p_boot.add_argument("--no-save-env", action="store_true", help="Não gravar os IDs no .env")

    # tasks
    p_tasks = sub.add_parser("tasks", help="Gerenciar tarefas no Dev Task Tracker")
    t_sub = p_tasks.add_subparsers(dest="action", required=True)

    p_tl = t_sub.add_parser("list", help="Listar tarefas")
    p_tl.add_argument("--status", help="Filtrar por status (ex: 'Em Andamento')")
    p_tl.add_argument("--owner", help="Filtrar por responsável (ex: Filipe)")
    p_tl.add_argument("--area", help="Filtrar por área (ex: 'Fit Lab')")
    p_tl.add_argument("--limit", type=int, default=50)
    p_tl.add_argument("--json", action="store_true", dest="as_json")

    p_ta = t_sub.add_parser("add", help="Criar nova tarefa")
    p_ta.add_argument("--title", required=True)
    p_ta.add_argument("--status", default="Backlog")
    p_ta.add_argument("--priority", default="Média")
    p_ta.add_argument("--owner")
    p_ta.add_argument("--area", action="append", dest="areas", help="Pode repetir --area")
    p_ta.add_argument("--type", dest="task_type")
    p_ta.add_argument("--due", help="YYYY-MM-DD")
    p_ta.add_argument("--pr", dest="pr_url", help="URL de branch/PR/commit no GitHub")
    p_ta.add_argument("--idea-id", help="ID ou URL da ideia de origem")
    p_ta.add_argument("--notes", help="Texto/checklist no corpo da página")

    p_tu = t_sub.add_parser("update", help="Atualizar tarefa existente")
    p_tu.add_argument("page_id", help="ID ou URL da tarefa")
    p_tu.add_argument("--status")
    p_tu.add_argument("--priority")
    p_tu.add_argument("--owner")
    p_tu.add_argument("--area", action="append", dest="areas")
    p_tu.add_argument("--pr", dest="pr_url")
    p_tu.add_argument("--due")
    p_tu.add_argument("--notes", help="Anexar nota ao corpo da tarefa")
    p_tu.add_argument("--devlog-synced", action="store_true", default=None)

    # ideas
    p_ideas = sub.add_parser("ideas", help="Gerenciar ideias e mídias no Idea & Media Vault")
    i_sub = p_ideas.add_subparsers(dest="action", required=True)

    p_il = i_sub.add_parser("list", help="Listar ideias")
    p_il.add_argument("--status")
    p_il.add_argument("--format", dest="fmt")
    p_il.add_argument("--pillar")
    p_il.add_argument("--limit", type=int, default=50)
    p_il.add_argument("--json", action="store_true", dest="as_json")

    p_ia = i_sub.add_parser("add", help="Registrar ideia (com áudio, vídeo, foto, PDF ou links)")
    p_ia.add_argument("--title", required=True)
    p_ia.add_argument("--format", action="append", dest="formats")
    p_ia.add_argument("--pillar", action="append", dest="pillars")
    p_ia.add_argument("--status", default="Captura Bruta")
    p_ia.add_argument("--author")
    p_ia.add_argument("--link", help="Link principal de referência")
    p_ia.add_argument("--drive-url", help="Link opcional de pasta/arquivo no Google Drive")
    p_ia.add_argument("--notes", help="Descrição, briefing ou transcrição de áudio")
    p_ia.add_argument("--file", action="append", dest="files", help="Caminho de arquivo local (repetível)")
    p_ia.add_argument("--embed", action="append", dest="embeds", help="URL extra para embed/bookmark (repetível)")

    p_iat = i_sub.add_parser("attach", help="Anexar novos arquivos ou links a uma ideia existente")
    p_iat.add_argument("page_id", help="ID ou URL da ideia")
    p_iat.add_argument("--file", action="append", dest="files")
    p_iat.add_argument("--embed", action="append", dest="embeds")
    p_iat.add_argument("--notes")

    p_ip = i_sub.add_parser("promote", help="Promover ideia em tarefa vinculada no Dev Task Tracker")
    p_ip.add_argument("idea_page_id", help="ID ou URL da ideia")
    p_ip.add_argument("--title", help="Sobrescrever título da tarefa")
    p_ip.add_argument("--priority", default="Média")
    p_ip.add_argument("--owner")
    p_ip.add_argument("--area", action="append", dest="areas")
    p_ip.add_argument("--type", dest="task_type", default="Feature")
    p_ip.add_argument("--due")

    # devlog
    p_devlog = sub.add_parser("devlog", help="Sincronizar tarefas concluídas com DEVLOG.md")
    d_sub = p_devlog.add_subparsers(dest="action", required=True)
    p_ds = d_sub.add_parser("sync", help="Gera ou aplica entrada no DEVLOG.md")
    p_ds.add_argument("--author", default="Equipe Emorphosis (+ Antigravity)")
    p_ds.add_argument("--limit", type=int, default=20)
    p_ds.add_argument("--apply", action="store_true", help="Escreve no DEVLOG.md e marca no Notion")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    env = load_env(ENV_PATH)

    try:
        client = NotionClient(env.get("NOTION_API_KEY", ""))

        if args.command == "doctor":
            return cmd_doctor(client, env)

        if args.command == "bootstrap":
            ids = cmd_bootstrap(
                client=client,
                page_id_raw=args.page_id,
                seed=not args.no_seed,
                save_env=not args.no_save_env,
            )
            print("\n=== IDs Provisionados ===")
            for k, v in ids.items():
                print(f"{k}={v}")
            return 0

        if args.command == "tasks":
            tasks_ds_id = _require_ds_id(env, "NOTION_TASKS_DS_ID")
            if args.action == "list":
                rows = list_tasks(
                    client,
                    tasks_ds_id,
                    status=args.status,
                    owner=args.owner,
                    area=args.area,
                    limit=args.limit,
                )
                _print_tasks_table(rows, as_json=args.as_json)
                return 0
            if args.action == "add":
                created = create_task(
                    client,
                    tasks_ds_id,
                    title=args.title,
                    status=args.status,
                    priority=args.priority,
                    owner=args.owner,
                    areas=args.areas,
                    task_type=args.task_type,
                    due=args.due,
                    pr_url=args.pr_url,
                    idea_id=args.idea_id,
                    notes=args.notes,
                )
                print(f"[OK] Tarefa criada: {created.get('url', created['id'])}")
                print(f"     ID: {created['id']}")
                return 0
            if args.action == "update":
                updated = update_task(
                    client,
                    page_id=args.page_id,
                    status=args.status,
                    priority=args.priority,
                    owner=args.owner,
                    areas=args.areas,
                    pr_url=args.pr_url,
                    due=args.due,
                    devlog_synced=args.devlog_synced,
                    notes=args.notes,
                )
                print(f"[OK] Tarefa atualizada: {updated.get('url', updated['id'])}")
                return 0

        if args.command == "ideas":
            ideas_ds_id = _require_ds_id(env, "NOTION_IDEAS_DS_ID")
            if args.action == "list":
                rows = list_ideas(
                    client,
                    ideas_ds_id,
                    status=args.status,
                    fmt=args.fmt,
                    pillar=args.pillar,
                    limit=args.limit,
                )
                _print_ideas_table(rows, as_json=args.as_json)
                return 0
            if args.action == "add":
                file_paths = [Path(f).expanduser().resolve() for f in (args.files or [])]
                created = create_idea(
                    client,
                    ideas_ds_id,
                    title=args.title,
                    formats=args.formats,
                    pillars=args.pillars,
                    status=args.status,
                    author=args.author,
                    link=args.link,
                    drive_url=args.drive_url,
                    notes=args.notes,
                    files=file_paths,
                    embeds=args.embeds,
                )
                print(f"[OK] Ideia registrada no cofre: {created.get('url', created['id'])}")
                print(f"     ID: {created['id']}")
                return 0
            if args.action == "attach":
                file_paths = [Path(f).expanduser().resolve() for f in (args.files or [])]
                updated = attach_to_idea(
                    client,
                    page_id=args.page_id,
                    files=file_paths,
                    embeds=args.embeds,
                    notes=args.notes,
                )
                print(f"[OK] Mídias/notas anexadas: {updated.get('url', updated['id'])}")
                return 0
            if args.action == "promote":
                tasks_ds_id = _require_ds_id(env, "NOTION_TASKS_DS_ID")
                task = promote_idea_to_task(
                    client,
                    tasks_ds_id=tasks_ds_id,
                    idea_page_id=args.idea_page_id,
                    title=args.title,
                    priority=args.priority,
                    owner=args.owner,
                    areas=args.areas,
                    task_type=args.task_type,
                    due=args.due,
                )
                print(f"[OK] Ideia promovida para tarefa: {task.get('url', task['id'])}")
                print(f"     Task ID: {task['id']}")
                return 0

        if args.command == "devlog" and args.action == "sync":
            tasks_ds_id = _require_ds_id(env, "NOTION_TASKS_DS_ID")
            done_tasks, entry = sync_devlog(
                client,
                tasks_ds_id=tasks_ds_id,
                author=args.author,
                apply=args.apply,
                limit=args.limit,
            )
            if not done_tasks:
                print("[INFO] Nenhuma tarefa concluída pendente de registro no DEVLOG.md.")
                return 0
            if args.apply:
                print(f"[OK] {len(done_tasks)} tarefa(s) registradas no DEVLOG.md e marcadas no Notion!")
            else:
                print("=== PRÉVIA DA ENTRADA PARA DEVLOG.md (use --apply para gravar) ===\n")
                print(entry)
            return 0

    except (ValueError, FileNotFoundError, NotionAPIError, RuntimeError) as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
