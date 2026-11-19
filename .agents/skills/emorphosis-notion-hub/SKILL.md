---
name: emorphosis-notion-hub
description: >-
  Use this skill when managing developer tasks, capturing multimedia project
  ideas (audio, video, photos, links), bootstrapping the Emorphosis Notion Dev
  Hub, promoting ideas to tasks, or syncing completed Notion tasks with DEVLOG.md.
---

# Emorphosis Notion Dev Hub Runbook

Fluxo operacional para o **EMORPHOSIS // DEV HUB** no Notion, combinando **Notion MCP** (leitura/escrita conversacional) e **`scripts/notion_hub.py`** (bootstrap automático, upload direto de áudios/vídeos/fotos via Notion File Upload API `2026-03-11` e sync com `DEVLOG.md`).

## Quando usar cada via

1. **Notion MCP conectado no Antigravity (`https://mcp.notion.com/mcp`)**:
   - Preferir para consultar tarefas, resumir ideias, editar texto de páginas, mover status rapidamente ou responder perguntas sobre o backlog durante o chat.
2. **CLI local (`scripts/notion_hub.py`)**:
   - Preferir para:
     - Provisionar/reconstruir a estrutura (`bootstrap`), aplicar/reaplicar a identidade visual Emorphosis (`theme`) e diagnosticar IDs (`doctor`).
     - Fazer **upload de arquivos locais** (áudio `.ogg`/`.m4a`/`.mp3`, vídeo `.mp4`/`.mov` inclusive > 20 MB via `multi_part`, fotos/prints `.png`/`.jpg`/`.webp` com definição automática de capa na Galeria).
     - Promover ideias para tarefas vinculadas (`ideas promote`) mantendo a relação bidirecional `Ideia Origem` ⇄ `Tarefas Geradas`.
     - Gerar/aplicar entradas no topo do `DEVLOG.md` a partir de tarefas concluídas (`devlog sync --apply`).

## Esquema Padrão do Hub

- **Página raiz:** `EMORPHOSIS // DEV HUB` (`NOTION_ROOT_PAGE_ID`) — estilizada com `docs/notion_assets/notion-cover.png`, `docs/notion_assets/notion-icon.png` e blocos HUD verdes (`Ctrl+Shift+L` + `Full width` no Notion).
- **Banco 1 — `📋 Dev Task Tracker`** (`NOTION_TASKS_DB_ID` / `NOTION_TASKS_DS_ID`):
  - `Tarefa` (title), `Status` (status: `Backlog`, `A Fazer`, `Em Andamento`, `Em Revisão`, `Concluído`), `Prioridade` (`Crítica`, `Alta`, `Média`, `Baixa`), `Responsável` (`Filipe`, `Arquivobrasileiro`, `Ambos`), `Área` (`H0M3 / Mapa`, `M4RCAS / Catálogo`, `Fit Lab`, `C4L3NDAR10`, `Backend PHP / MySQL`, `Design / UI`, `Infra / Deploy`), `Tipo`, `Prazo`, `Branch / PR`, `Ideia Origem` (relation), `Registrado no DEVLOG` (checkbox).
- **Banco 2 — `💡 Idea & Media Vault`** (`NOTION_IDEAS_DB_ID` / `NOTION_IDEAS_DS_ID`):
  - `Ideia` (title), `Status` (`Captura Bruta`, `Em Análise`, `Aprovada`, `Virou Tarefa`, `Arquivada`), `Formatos` (`Áudio`, `Vídeo`, `Foto / Print`, `Link / Ref`, `Texto / Briefing`, `PDF / Doc`), `Pilar`, `Autor`, `Link Principal`, `Mídia / Drive`, `Anexos / Capa` (files), `Tarefas Geradas` (relation).

## Comandos Essenciais

```bash
# Diagnóstico de token e bancos
python scripts/notion_hub.py doctor

# Setup inicial a partir da página raiz vazia (cria bancos, relação, views, tema e seed)
python scripts/notion_hub.py bootstrap --page-id "<URL_OU_ID>"

# Aplicar/atualizar identidade visual Emorphosis (capa, ícone neon, HUD verde e preview Fit Lab)
python scripts/notion_hub.py theme [--skip-layout]

# Tarefas
python scripts/notion_hub.py tasks list [--status "Em Andamento"] [--owner Filipe] [--json]
python scripts/notion_hub.py tasks add --title "..." --priority Alta --owner Filipe --area "Fit Lab"
python scripts/notion_hub.py tasks update <PAGE_ID> --status "Concluído" --pr "<URL>"

# Ideias & Mídias (single-part <= 20 MiB e multi-part > 20 MiB automático)
python scripts/notion_hub.py ideas list [--status "Aprovada"] [--json]
python scripts/notion_hub.py ideas add --title "..." --pillar "Visual / Glitch" --file audio.m4a --file foto.png --link "https://..."
python scripts/notion_hub.py ideas attach <PAGE_ID> --file video.mp4 --embed "https://youtu.be/..."
python scripts/notion_hub.py ideas promote <IDEA_ID> --owner Filipe --priority Alta

# Sincronia com DEVLOG.md
python scripts/notion_hub.py devlog sync
python scripts/notion_hub.py devlog sync --apply --author "Filipe (+ Antigravity)"
```

## Segurança & Regras

- Nunca imprimir `NOTION_API_KEY` ou conteúdo bruto de `.env` em logs ou respostas.
- Sempre consultar `docs/NOTION_HUB_SETUP.md` ao orientar um novo dev no onboarding do Notion + MCP.
- Antes de encerrar alterações no código do `notion_hub.py`, validar com `python -m unittest scripts/test_notion_hub.py -v`.
