# EMORPHOSIS // DEV HUB — Guia de Configuração do Notion + Antigravity (Do Zero)

Este guia configura do zero o **EMORPHOSIS // DEV HUB** no Notion (controle de tarefas dos desenvolvedores + cofre multimídia de ideias com áudio, vídeo, fotos e links) integrado ao **Google Antigravity** em modo **híbrido**:

1. **Notion MCP Oficial (`https://mcp.notion.com/mcp`)** — para conversar direto com o Notion em linguagem natural dentro do Antigravity (ler tarefas, registrar ideias, atualizar cards).
2. **CLI Python do Repositório ([`scripts/notion_hub.py`](../scripts/notion_hub.py))** — para **criar automaticamente toda a estrutura com 1 comando (`bootstrap`)**, fazer **upload direto de áudios/vídeos pesados (até 5 GB no Notion Plus/Business)** via File Upload API e **sincronizar entregas concluídas com o [`DEVLOG.md`](../DEVLOG.md)**.

---

## Parte 1 — Criar o Workspace e a Página Raiz no Notion (~3 min)

1. Acesse [notion.so](https://www.notion.so) e crie/abra o workspace do projeto (ex: **EMORPHOSIS**).
2. Em **Settings → Upgrade / Plan**, ative o plano **Plus** (ou Business) para liberar **uploads diretos de até 5 GB por arquivo** (vídeos, áudios longos, fotos em alta resolução) e **blocos ilimitados para múltiplos membros**.
3. Convide o segundo desenvolvedor da equipe em **Settings → People → Add members** (com permissão *Full access*).
4. Na barra lateral, crie uma página em branco na raiz do Teamspace com o título:
   ```text
   EMORPHOSIS // DEV HUB
   ```
   *(Opcional: adicione ícone ⚡ e capa escura/verde seguindo a identidade do site.)*
5. **Copie o link dessa página** (botão **Share → Copy link** ou URL do navegador). Você vai usá-lo na Parte 3.

---

## Parte 2 — Criar a Internal Integration (Token da Notion API) (~2 min)

1. Acesse o portal de integrações do Notion: [notion.so/profile/integrations](https://www.notion.so/profile/integrations).
2. Clique em **+ New integration**:
   - **Name:** `Emorphosis Dev Hub Agent`
   - **Associated workspace:** selecione o workspace **EMORPHOSIS**
   - **Type:** `Internal`
3. Na aba **Configuration**:
   - Marque em **Capabilities**:
     - ✅ Read content
     - ✅ Update content
     - ✅ Insert content
     - ✅ Read comments / Insert comments *(opcional, útil para discussões)*
   - Clique em **Save** e copie o **Internal Integration Secret** (`ntn_...`).
4. **Passo obrigatório (que quase todo mundo esquece!):**
   - Volte à página **`EMORPHOSIS // DEV HUB`** no Notion.
   - Clique no menu **`•••`** (canto superior direito) → **Connections** → selecione **`Emorphosis Dev Hub Agent`** → **Confirm**.
   *(Compartilhar a página raiz concede acesso automático a todos os bancos de dados que o script vai criar dentro dela.)*

---

## Parte 3 — Configurar `.env` e Provisionar Tudo com 1 Comando (~1 min)

1. Se ainda não tiver o arquivo `.env` na raiz do repositório, copie o modelo:
   ```bash
   # Windows PowerShell
   Copy-Item .env.example .env

   # Linux / macOS
   cp .env.example .env
   ```
2. Abra o `.env` local (nunca commitado no Git) e cole o token na seção 5:
   ```env
   NOTION_API_KEY=ntn_cole_seu_token_aqui
   ```
3. Valide a conexão:
   ```bash
   python scripts/notion_hub.py doctor
   ```
4. **Provisione toda a estrutura automaticamente** passando a URL da página `EMORPHOSIS // DEV HUB`:
   ```bash
   python scripts/notion_hub.py bootstrap --page-id "https://www.notion.so/SEU-LINK-AQUI"
   ```

O que o comando `bootstrap` cria sozinho em ~10 segundos:
- Banner superior no `EMORPHOSIS // DEV HUB`.
- Banco **`💡 Idea & Media Vault`** com propriedades (`Ideia`, `Status`, `Formatos`, `Pilar`, `Autor`, `Link Principal`, `Mídia / Drive`, `Anexos / Capa`, `Criado em`).
- Banco **`📋 Dev Task Tracker`** com propriedades (`Tarefa`, `Status` [Backlog → A Fazer → Em Andamento → Em Revisão → Concluído], `Prioridade`, `Responsável`, `Área`, `Tipo`, `Prazo`, `Branch / PR`, `Registrado no DEVLOG`).
- **Relação bidirecional** automática: **`Ideia Origem` ⇄ `Tarefas Geradas`**.
- **6 Views prontas**:
  - No *Task Tracker*: `📋 Kanban (Status)`, `🔥 Prioridades Ativas`, `✅ Concluídas (DEVLOG)`.
  - No *Idea Vault*: `🎨 Moodboard (Galeria com capa)`, `📥 Inbox de Captura`, `🚀 Pipeline de Ideias`.
- **Backlog inicial** já populado com as 3 pendências reais do [`GEMINI.md`](../GEMINI.md) + 1 ideia vinculada ao Fit Lab.
- **Gravação automática** dos IDs (`NOTION_ROOT_PAGE_ID`, `NOTION_TASKS_DB_ID`, `NOTION_TASKS_DS_ID`, `NOTION_IDEAS_DB_ID`, `NOTION_IDEAS_DS_ID`) no seu `.env`.

5. Rode o diagnóstico novamente para confirmar tudo verde:
   ```bash
   python scripts/notion_hub.py doctor
   ```

---

## Parte 4 — Conectar o Notion MCP Oficial no Google Antigravity (~2 min)

Para que o Antigravity leia e escreva no seu Notion **direto no chat (sem rodar CLI manualmente para consultas/anotações rápidas)**:

### Via interface do Antigravity
1. No menu lateral do Antigravity, abra **Customizations → MCP Servers** (ou no painel do agente: `•••` → **MCP Servers → Manage MCP Servers → View raw config**).
2. Se o **Notion** aparecer na loja nativa (*MCP Store*), clique em **Install / Connect** e autorize via OAuth no navegador.
3. Caso adicione manualmente no `mcp_config.json`, use exatamente a chave **`serverUrl`** (padrão do Antigravity para Streamable HTTP):
   ```json
   {
     "mcpServers": {
       "notion": {
         "serverUrl": "https://mcp.notion.com/mcp"
       }
     }
   }
   ```
4. Salve, clique em **Refresh** na lista de MCP Servers e complete o login OAuth do Notion no navegador escolhendo a página **`EMORPHOSIS // DEV HUB`** (ou o workspace inteiro).

> **Dica de uso em conversas remotas vs. locais:**
> - **Conversa no app/IDE local:** funciona tanto o **Notion MCP** quanto o CLI `scripts/notion_hub.py` (incluindo upload de arquivos locais pesados!).
> - **Conversa remota na nuvem:** o **Notion MCP** conectado na sua conta/projeto funciona direto; se quiser rodar o CLI na VM remota, adicione `api.notion.com` nos domínios permitidos (`allowed_hosts`) ou rode o CLI no terminal local.

---

## Parte 5 — Onboarding do 2º Desenvolvedor

Como os IDs do Notion e o token ficam no `.env` (ignorado no Git por segurança):
1. O segundo dev puxa o repositório (`git pull`) — ele já recebe `scripts/notion_hub.py`, esta documentação e a skill `.agents/skills/emorphosis-notion-hub/`.
2. Compartilhe com ele (por canal privado, nunca no Git) o bloco `# --- 5. Notion Dev Hub ---` do `.env` já preenchido pelo `bootstrap`.
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
```
