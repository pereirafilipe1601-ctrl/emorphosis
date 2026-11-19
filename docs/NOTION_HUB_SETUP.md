# EMORPHOSIS — Guia de Configuração do Notion + Antigravity

Este guia configura do zero o workspace **EMORPHOSIS** no Notion (começando pela área de **Desenvolvimento**, com cofre multimídia e integração com o **Google Antigravity** em modo híbrido):

1. **Notion MCP Oficial (`https://mcp.notion.com/mcp`)** — para ler e editar páginas/tarefas diretamente no chat do Antigravity.
2. **CLI Python do Repositório ([`scripts/notion_hub.py`](../scripts/notion_hub.py))** — para provisionar a hierarquia completa com 1 comando (`bootstrap`), atualizar estrutura/identidade visual (`theme`), subir mídias pesadas até 5 GB e sincronizar entregas com o [`DEVLOG.md`](../DEVLOG.md).

---

## Parte 1 — Criar o Workspace e a Página Raiz no Notion (~3 min)

1. Acesse [notion.so](https://www.notion.so) e crie/abra o workspace **EMORPHOSIS**.
2. Em **Settings → Upgrade / Plan**, ative o plano **Plus** (ou Business) para liberar uploads diretos de até 5 GB por arquivo e blocos ilimitados.
3. Convide os membros da equipe em **Settings → People → Add members**.
4. Na barra lateral, crie uma página em branco na raiz do Teamspace com o título:
   ```text
   EMORPHOSIS
   ```
5. **Copie o link dessa página** (**Share → Copy link**). Você vai usá-lo na Parte 3.

---

## Parte 2 — Criar a Internal Integration (Token da Notion API) (~2 min)

1. Acesse [notion.so/profile/integrations](https://www.notion.so/profile/integrations).
2. Clique em **+ New integration**:
   - **Name:** `Emorphosis Agent` (ou `Emorphosis Dev Hub Agent`)
   - **Associated workspace:** **EMORPHOSIS**
   - **Type:** `Internal`
3. Em **Configuration → Capabilities**, marque:
   - Read content
   - Update content
   - Insert content
   - Read comments / Insert comments
4. Clique em **Save** e copie o **Internal Integration Secret** (`ntn_...`).
5. **Passo obrigatório:** volte à página **`EMORPHOSIS`** no Notion, clique em **`•••` → Connections** → selecione sua integração → **Confirm**.

---

## Parte 3 — Configurar `.env` e Provisionar Tudo com 1 Comando (~1 min)

1. Se ainda não tiver `.env` na raiz do repositório, copie o modelo:
   ```bash
   # Windows PowerShell / cmd
   copy .env.example .env

   # Linux / macOS
   cp .env.example .env
   ```
2. Abra o `.env` local e cole o token na seção 5:
   ```env
   NOTION_API_KEY=ntn_cole_seu_token_aqui
   ```
3. Valide a conexão:
   ```bash
   python scripts/notion_hub.py doctor
   ```
4. **Provisione toda a estrutura** passando a URL da página `EMORPHOSIS`:
   ```bash
   python scripts/notion_hub.py bootstrap --page-id "https://www.notion.so/SEU-LINK-AQUI"
   ```

O que o comando `bootstrap` cria automaticamente:
- Página raiz **`EMORPHOSIS`** com capa oficial do calendário (`assets/img/calendar-bg.png`, aplicada também em todas as subáreas), ícone (`docs/notion_assets/notion-icon.png`) e links rápidos da plataforma (`H0M3`, `M4RCAS`, `C4L3NDAR10`, `S0BR3`, `SONHOS`, `GITHUB`).
- Subpágina **`Desenvolvimento`** (primeira área ativa do time) contendo os dois bancos separados em páginas dedicadas (`is_inline: false`), sem nada empilhado inline:
  - **`Dev Task Tracker`** — views **`Kanban`**, **`Prioridades Ativas`** e **`Concluídas`**.
  - **`Idea & Media Vault`** — views **`Moodboard`**, **`Inbox`** e **`Pipeline`**.
- **Relação bidirecional** automática: **`Ideia Origem` ⇄ `Tarefas Geradas`**.
- Backlog inicial com pendências do [`GEMINI.md`](../GEMINI.md) e preview visual no Fit Lab (`aevus-jaqueta.png`).
- Gravação automática dos IDs (`NOTION_ROOT_PAGE_ID`, `NOTION_DEV_PAGE_ID`, `NOTION_TASKS_DB_ID`, `NOTION_TASKS_DS_ID`, `NOTION_IDEAS_DB_ID`, `NOTION_IDEAS_DS_ID`) no `.env`.

5. Para migrar ou reaplicar a estrutura multi-página, capa, ícones e views limpas em um workspace já criado (sem apagar dados):
   ```bash
   python scripts/notion_hub.py theme
   ```
   *(No Notion, ative o **Dark Mode** com `Ctrl + Shift + L` / `Cmd + Shift + L` e ligue **`••• → Full width`**.)*

6. Rode o diagnóstico novamente:
   ```bash
   python scripts/notion_hub.py doctor
   ```

---

## Parte 4 — Conectar o Notion MCP Oficial no Google Antigravity (~2 min)

1. No Antigravity, abra **Customizations → MCP Servers** (ou `•••` → **MCP Servers → Manage MCP Servers → View raw config**).
2. Instale o **Notion** pela loja nativa ou adicione em `mcp_config.json`:
   ```json
   {
     "mcpServers": {
       "notion": {
         "serverUrl": "https://mcp.notion.com/mcp"
       }
     }
   }
   ```
3. Salve, clique em **Refresh** e conclua o login OAuth no navegador autorizando a página **`EMORPHOSIS`** (ou o workspace inteiro).

---

## Parte 5 — Onboarding do 2º Desenvolvedor

1. O colega puxa o repositório (`git pull`).
2. Compartilhe por canal privado o bloco `# --- 5. Notion Hub ---` do `.env` preenchido.
3. Ele também conecta o **Notion MCP** no Antigravity dele com a própria conta Notion.

---

## Parte 6 — Guia Rápido do Dia a Dia

### No chat do Antigravity (via MCP ou Skill)
- *"Quais tarefas de prioridade Alta estão abertas no Notion para mim?"*
- *"Salva essa referência de vídeo e nossas anotações no Idea Vault com pilar Fit Lab."*
- *"Transforma a ideia X em tarefa no Dev Task Tracker e prepara a branch."*
- *"Marque a tarefa Y como Concluído com o link do commit e sincronize o DEVLOG.md."*

### No terminal via `scripts/notion_hub.py` (ideal para uploads pesados de áudio/vídeo/fotos!)

```bash
# Listar tarefas abertas de um dev
python scripts/notion_hub.py tasks list --owner Filipe

# Criar nova tarefa
python scripts/notion_hub.py tasks add \
  --title "Criar recortes PNG de 5 marcas para o Fit Lab" \
  --priority Alta --owner Filipe --area "Fit Lab" --type Feature

# Atualizar status e anexar link de PR/commit
python scripts/notion_hub.py tasks update <TASK_ID_OU_URL> \
  --status "Concluído" --pr "https://github.com/pereirafilipe1601-ctrl/emorphosis/commit/..."

# Salvar ideia multimídia (sobe áudio + vídeo + foto direto no Notion com capa automática!)
python scripts/notion_hub.py ideas add \
  --title "Efeito sonoro glitch + transição no mapa H0M3" \
  --pillar "Visual / Glitch" --pillar "H0M3 / Mapa" --author Filipe \
  --link "https://www.instagram.com/reel/..." \
  --file ~/Downloads/audio_ideia.m4a \
  --file ~/Downloads/referencia_video.mp4 \
  --file ~/Downloads/print_moodboard.png \
  --notes "Testar volume sutil com botão mute.\n- [ ] Prototipar em H0M3"

# Anexar novos áudios/vídeos/links a uma ideia já existente
python scripts/notion_hub.py ideas attach <IDEA_ID_OU_URL> \
  --file ~/Downloads/gravacao_nova.ogg \
  --embed "https://youtu.be/..."

# Promover uma ideia aprovada direto para tarefa vinculada
python scripts/notion_hub.py ideas promote <IDEA_ID_OU_URL> \
  --owner Arquivobrasileiro --priority Alta

# Gerar prévia e depois aplicar no DEVLOG.md as tarefas concluídas
python scripts/notion_hub.py devlog sync
python scripts/notion_hub.py devlog sync --apply --author "Filipe (+ Antigravity)"

# Aplicar/atualizar identidade visual (capa, ícone neon, HUD verde e preview Fit Lab)
python scripts/notion_hub.py theme
```
