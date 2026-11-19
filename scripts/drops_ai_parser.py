"""
EMORPHOSIS — Automação de Drops com Claude (Anthropic API) -> Google Calendar (.ics)
Lê legendas/anúncios de posts do Instagram de marcas do diretório Emorphosis,
extrai automaticamente data, horário (BRT), nome do drop e gera um arquivo .ics
pronto para importar na agenda "Próximos drops" do Google Calendar.

Como usar:
1. Adicione ANTHROPIC_API_KEY=... no seu arquivo .env
2. Rode:
   python scripts/drops_ai_parser.py "Drop Bussfly dia 25/11 às 20h no site oficial @bussfly"
"""

from __future__ import annotations

import datetime as dt
import json
import sys
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
OUT_ICS = ROOT / "database" / "proximos_drops_gerados.ics"


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def extract_drop_with_claude(api_key: str, post_text: str) -> dict:
    today = dt.date.today().isoformat()
    system_prompt = (
        "Você é o extrator oficial de drops da plataforma brasileira Emorphosis. "
        f"A data de referência atual é {today} (fuso America/Sao_Paulo). "
        "Dado o texto de um post do Instagram de uma marca brasileira, retorne APENAS um JSON válido "
        "com as chaves: brand_name (str), drop_title (str), date_ymd (YYYYMMDD), "
        "time_hm (HHMM ou vazio se dia inteiro), instagram_handle (str), notes (str)."
    )

    body = json.dumps(
        {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 400,
            "system": system_prompt,
            "messages": [{"role": "user", "content": post_text}],
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    raw_txt = data["content"][0]["text"].strip()
    if raw_txt.startswith("```"):
        raw_txt = raw_txt.strip("`").removeprefix("json").strip()
    return json.loads(raw_txt)


def append_ics_event(ev: dict) -> Path:
    uid = f"{uuid.uuid4()}@emorphosis.com.br"
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ymd = ev.get("date_ymd", dt.date.today().strftime("%Y%m%d"))
    hm = (ev.get("time_hm") or "").strip()

    if len(hm) == 4 and hm.isdigit():
        dtstart = f"DTSTART;TZID=America/Sao_Paulo:{ymd}T{hm}00"
        end_hour = min(23, int(hm[:2]) + 1)
        dtend = f"DTEND;TZID=America/Sao_Paulo:{ymd}T{end_hour:02d}{hm[2:]}00"
    else:
        dtstart = f"DTSTART;VALUE=DATE:{ymd}"
        dtend = f"DTEND;VALUE=DATE:{ymd}"

    summary = f"{ev.get('drop_title') or 'Drop'} — {ev.get('brand_name') or ''}".strip(" —")
    desc = f"@{ev.get('instagram_handle', '')} | {ev.get('notes', '')}".strip(" |")

    vevent = "\n".join(
        [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{stamp}",
            dtstart,
            dtend,
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{desc}",
            "END:VEVENT",
        ]
    )

    if OUT_ICS.exists():
        existing = OUT_ICS.read_text(encoding="utf-8").replace("END:VCALENDAR", "").rstrip()
        content = f"{existing}\n{vevent}\nEND:VCALENDAR\n"
    else:
        content = f"BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Emorphosis//Drops Radar//PT\n{vevent}\nEND:VCALENDAR\n"

    OUT_ICS.write_text(content, encoding="utf-8")
    return OUT_ICS


def main() -> int:
    if len(sys.argv) < 2:
        print('Uso: python scripts/drops_ai_parser.py "<legenda do post do drop>"')
        return 1

    env = load_env(ENV_PATH)
    api_key = env.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("[AVISO] Adicione ANTHROPIC_API_KEY=... no arquivo .env para ativar a extração automática com Claude.")
        return 1

    caption = " ".join(sys.argv[1:])
    extracted = extract_drop_with_claude(api_key, caption)
    ics_path = append_ics_event(extracted)
    print(f"[OK] Drop extraído: {extracted}")
    print(f"[OK] Evento salvo em: {ics_path} (pronto para importar no Google Calendar 'Próximos drops')")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
