# DEVLOG — Emorphosis (`emorphosis.com.br`)

Registro cronológico de alterações, decisões técnicas e contexto de negócio do projeto.
Mantido separado do [GEMINI.md](./GEMINI.md) para respeitar o limite de `24.000` bytes dos arquivos de regra do Antigravity sem perder a memória histórica da equipe.

> **Como registrar novas entradas:** adicione sempre **no topo** (logo abaixo desta seção), mantendo a ordem cronológica inversa. Inclua **Data**, **Responsável**, **O que mudou** e **Contexto / Porquê** (sem nunca registrar senhas, tokens, e-mails pessoais ou dados de `.env`).

---

## [2026-11-19] — Reestruturação Multi-Página do Notion (`EMORPHOSIS` -> `Desenvolvimento`) & Remoção de AI Slop
**Responsável:** Filipe (+ Antigravity)
**Arquivos principais:** `docs/notion_assets/notion-cover.png`, `scripts/notion_hub.py`, `scripts/test_notion_hub.py`, `.env.example`, `docs/NOTION_HUB_SETUP.md`, `.agents/skills/emorphosis-notion-hub/SKILL.md`

### O que mudou
- Reestruturado o Notion de página única para **hub multi-página de todo o time Emorphosis** (construindo por enquanto a área de **Desenvolvimento**):
  - **Raiz (`EMORPHOSIS`)**: portal enxuto com links da plataforma (`H0M3`, `M4RCAS`, `C4L3NDAR10`, `S0BR3`, `SONHOS`, `GITHUB`) e subpágina `Desenvolvimento` (`NOTION_DEV_PAGE_ID`).
  - **Subpágina `Desenvolvimento`**: moveu `Dev Task Tracker` e `Idea & Media Vault` para páginas dedicadas e independentes (`is_inline: false`), com ícones nativos verdes da Notion API e capa oficial, eliminando o empilhamento inline.
- Removido todo **AI slop** da interface gerada, da capa e dos seeds:
  - Removido `DEV HUB //` da capa `docs/notion_assets/notion-cover.png` mantendo `EMR PHS` + `EMERGENT METAMORPHOSIS`.
  - Removidos todos os emojis, blocos redundantes (`TERMINAL_NAV`, `ATALHOS_CLI`, `TERMINAL CHEATSHEET`), textos entre parênteses e explicações após travessão em cabeçalhos, views (`Kanban`, `Prioridades Ativas`, `Concluídas`, `Moodboard`, `Inbox`, `Pipeline`) e tarefas iniciais.
  - Adicionados métodos `list_views`, `get_view` e `update_view` em `NotionClient` para migrar e renomear views já existentes sem perda de dados ao rodar `notion_hub.py theme`.
- Adicionado `NOTION_DEV_PAGE_ID` em `.env.example` e validada toda a suíte offline em `scripts/test_notion_hub.py` (`15` testes passando).

### Contexto / Porquê
- Preparar o workspace do Notion para crescer com outras áreas do coletivo Emorphosis sem poluição visual e sem concentrar todos os bancos concatenados em uma página só.

---

## [2026-11-19] — Identidade Visual Emorphosis no Notion (`notion_hub.py theme` + Assets Oficiais)
**Responsável:** Filipe (+ Antigravity)
**Arquivos principais:** `docs/notion_assets/notion-cover.png`, `docs/notion_assets/notion-icon.png`, `scripts/notion_hub.py`, `scripts/test_notion_hub.py`, `docs/NOTION_HUB_SETUP.md`, `.agents/skills/emorphosis-notion-hub/SKILL.md`

### O que mudou
- Criados os assets visuais oficiais do hub em `docs/notion_assets/` (excluídos do deploy FTP da Hostinger via `EXCLUDE_NAMES`):
  - `notion-cover.png` (`1500×540`): banner cyber preto/verde neon `#19f028` com silhueta radar do Brasil e tipografia terminal `EMR PHS // DEV HUB`.
  - `notion-icon.png` (`512×512`): ícone pasta+losango em verde neon sobre `#020502`.
- Implementado o comando idempotente `python scripts/notion_hub.py theme` (`--page-id`, `--cover`, `--icon`, `--skip-layout`) e integrado o mesmo tema ao `bootstrap`:
  - Sobe capa e ícone para a página raiz via Notion File Upload API e aplica ícones verdes nos dois bancos (`Idea & Media Vault` e `Dev Task Tracker`).
  - Organiza o layout HUD terminal (`EMORPHOSIS // DEV HUB`, colunas `00 // TERMINAL_NAV` com links do site + `00 // ATALHOS_CLI`, headings verdes `01 //`, `02 //` e toggle `03 // TERMINAL CHEATSHEET & VISUAL`) preservando os bancos de dados e quaisquer notas/dividers customizados da página.
  - Vincula automaticamente `assets/img/fitlab/aevus-jaqueta.png` ao card semente do Fit Lab caso esteja sem capa no Moodboard.
- Ampliados os testes offline em `scripts/test_notion_hub.py` (`15` testes cobrindo idempotência do `theme`, fallback sem colunas, `--skip-layout` e preservação de blocos customizados).

### Contexto / Porquê
- Aproximar a experiência visual do Notion Dev Hub da estética `#020502` / `#19f028` do site `emorphosis.com.br` sem depender de CSS customizado (não suportado nativamente pelo Notion) e sem risco de perda de dados em hubs já provisionados.

---

## [2026-11-19] — Emorphosis Notion Dev Hub (Tarefas + Cofre de Ideias Multimídia + Antigravity)
**Responsável:** Filipe (+ Antigravity)
**Arquivos principais:** `scripts/notion_hub.py`, `scripts/test_notion_hub.py`, `docs/NOTION_HUB_SETUP.md`, `.agents/skills/emorphosis-notion-hub/SKILL.md`, `.env.example`, `scripts/deploy_ftp.py`, `README.md`, `GEMINI.md`

### O que mudou
- Criado `scripts/notion_hub.py` em Python stdlib (zero dependências) compatível com **Notion API `2026-03-11`** (`data_sources`, `Views API` e `File Upload API` com `single_part` até 20 MiB e `multi_part` em streaming de 10 MiB para áudios/vídeos pesados de até 5 GiB no Notion Plus/Business).
- Implementados comandos `doctor`, `bootstrap` (provisionamento automático dos bancos `📋 Dev Task Tracker` e `💡 Idea & Media Vault`, relação bidirecional `Ideia Origem` ⇄ `Tarefas Geradas`, 6 views e seed do backlog do `GEMINI.md`), `tasks` (`list`/`add`/`update`), `ideas` (`list`/`add`/`attach`/`promote`) e `devlog sync` (prévia/escrita no `DEVLOG.md`).
- Adicionados testes unitários offline em `scripts/test_notion_hub.py`, guia completo do zero em `docs/NOTION_HUB_SETUP.md` (incluindo conexão do Notion MCP oficial `https://mcp.notion.com/mcp` no Antigravity) e skill compartilhada `.agents/skills/emorphosis-notion-hub/SKILL.md`.
- Adicionadas variáveis `NOTION_*` em `.env.example` e incluída a pasta `docs` em `EXCLUDE_NAMES` de `scripts/deploy_ftp.py` para manter documentação interna fora da Hostinger.

### Contexto / Porquê
- Centralizar o controle de tarefas dos desenvolvedores e o repositório multimídia de ideias (áudios, vídeos, fotos e links) no Notion integrado ao Google Antigravity, eliminando setup manual propenso a erro e mantendo sincronia direta com o `DEVLOG.md`.

---

## [2026-11-19] — Automação Total de Sync Git & Suporte a Edição Paralela
**Responsável:** Arquivobrasileiro / Filipe (+ Antigravity)
**Arquivos principais:** `.agents/hooks.json`, `.agents/hooks/git_sync_hook.py`, `.gitattributes`, `.agents/rules/emorphosis-conventions.md`, `README.md`, `GEMINI.md`, `scripts/deploy_ftp.py`

### O que mudou
- Configurados lifecycle hooks do Antigravity em `.agents/hooks.json` executando `.agents/hooks/git_sync_hook.py`:
  - `SessionStart` e `PreInvocation` (no início do turno, throttle de 45s): executam `git fetch` + `git pull --rebase --autostash origin main` automaticamente.
  - `Stop`: exige registro atualizado no `DEVLOG.md` quando há código alterado, verifica proteção contra arquivos sensíveis, faz `git commit`, `git pull --rebase --autostash` e `git push origin main`.
- Criado `.gitattributes` com `DEVLOG.md merge=union` para mesclar automaticamente entradas simultâneas no diário sem conflito manual.
- Em conflitos reais nas mesmas linhas de um arquivo de código, o hook aborta/pausa com segurança e instrui o próprio Antigravity (`decision: continue`) a mesclar preservando as alterações dos dois desenvolvedores.

### Contexto / Porquê
- Eliminar a dependência de rodar `git pull`/`git commit`/`git push` manualmente entre os dois computadores da equipe e permitir colaboração paralela fluida sem conflitos no `DEVLOG.md`.

---

## [2026-11-19] — Consolidação do Projeto, Segurança, Git/GitHub & Deploy
**Responsável:** Arquivobrasileiro / Filipe (+ Antigravity)
**Arquivos principais:** `GEMINI.md`, `README.md`, `DEVLOG.md`, `.env.example`, `.gitignore`, `.htaccess`, `.agents/**`, `api/config_loader.php`, `api/config.example.php`, `api/*.php`, `c4l3ndar10.html`, `marca.html`, `scripts/deploy_ftp.py`

### O que mudou
- Estruturado o workspace para desenvolvimento em dupla no Antigravity com `GEMINI.md` (< 20 KB), `README.md` de onboarding, `.env.example`, `.gitignore` ampliado e pasta `.agents/` compartilhável (regras em `emorphosis-conventions.md` + skills `emorphosis-catalog-build` e `emorphosis-ftp-deploy`).
- Criado `api/config_loader.php` e `api/config.example.php`, removendo segredos/tokens/e-mails hardcoded de `api/delete_calendar_drop.php`, `api/subscribe_drops.php`, `api/unsubscribe_drops.php`, `api/cron_dispatch_drops.php`, `api/presence.php`, `api/drops_submit.php` e `c4l3ndar10.html`.
- Atualizado `scripts/deploy_ftp.py` para gerar `api/config.php` a partir do `.env` durante o deploy e excluir documentação interna (`GEMINI.md`, `README.md`, `DEVLOG.md`, `.agents`, `config.example.php`) e todos os arquivos runtime de `api/storage/`.
- Sincronizado cache-busting de `marca.html` (`?v=20261118g`) e corrigidas referências textuais antigas de "133 marcas" para `131 marcas`.
- Repositório Git inicializado na branch `main`, configurado com SSH para `github.com/pereirafilipe1601-ctrl/emorphosis` e publicado em produção na Hostinger via FTPS (`29` arquivos enviados e validados no ar).

### Contexto / Porquê
- Ao migrar o projeto para um segundo desenvolvedor usando repositório Git no GitHub, uma auditoria detectou tokens/salts hardcoded no PHP, exposição do e-mail admin no HTML/JS e arquivos sensíveis (`.env`, `_conversa_emorphosis/transcript_projeto_emorphosis.jsonl`, `api/storage/*.json`) fora do `.gitignore`. A refatoração garante que nenhum segredo vá para o Git mantendo compatibilidade automática com o deploy na Hostinger.

---

## [2026-11-19] — Migração de Contexto para Workspace de Projeto
**Responsável:** Filipe (+ Antigravity — conversa `Migração De Contexto Da Conversa`)
**Arquivos principais:** `CONVERSATION_HANDOFF_ANTIGRAVITY.md`, `_conversa_emorphosis/`

### O que mudou
- Transferido o histórico da conversa original (que havia começado fora de um projeto vinculado no Antigravity) para a pasta `_conversa_emorphosis/` e documentado o handoff em `CONVERSATION_HANDOFF_ANTIGRAVITY.md`.
- Verificada a integridade dos 68 arquivos de mídia, scripts auxiliares de auditoria (`scratch_auxiliar/`), levantamentos de preços/localização e log JSONL completo (`1.839` linhas).

### Contexto / Porquê
- O desenvolvimento inicial nasceu em uma conversa solta; vincular formalmente ao workspace `emorphosis` foi necessário para organizar o trabalho contínuo e preparar o compartilhamento com outro desenvolvedor.

---

## Histórico Consolidado da Origem (`Projeto Emorphosis`, 2026-11-05 a 2026-11-18)

### [2026-11-18] — Auditoria Geográfica (10 UFs), Janelas de Estado & Diretório de Sonhos (`/sonhos/`)
- **O que mudou:**
  - Levantamento de Cidade/UF das **131 marcas** salvo em `database/brand_locations.json` (`110` alta confiança via bio/CNPJ/Registro.br/Shopify, `12` média via origem de frete/DDD, `9` estimada) distribuídas em **10 estados**: `SP` (88), `SC` (14), `PR` (9), `RS` (5), `RJ` (5), `MG` (4), `ES` (3), `GO` (1), `RN` (1), `DF` (1).
  - Evolução do mapa na `H0M3` (`assets/js/main.js`, `assets/data/brazil_states_shapes.json`): substituídos os pinos individuais no mapa por **botões clicáveis por UF** que abrem uma janela estilo aplicativo desktop com descrição em prompt animado sobre cada marca, além de botões `10 ESTADOS` e `GPS` reposicionados à esquerda (e layout horizontal centralizado no mobile `<= 820px`).
  - Criado o modal inicial de pergunta ("qual seu sonho?") com tela de transição preta glitch `#emorphosis` (fontes `Rubik Glitch` e `Silkscreen`), API `api/save_dream.php` e diretório público espelhado em `/sonhos/index.html` (`.json` + `.txt`).
- **Contexto / Porquê:**
  - A primeira versão com 131 ícones direto no mapa e contornos verdes sobre as UFs ficou visualmente carregada e desalinhada com a arte de `home-bg.png`; o modelo de janela por estado preservou a estética limpa do mapa e deu legibilidade às marcas regionais.

### [2026-11-14 a 2026-11-15] — Curadoria de Mídias, Catálogo de 131 Marcas & Auditoria de Preços
- **O que mudou:**
  - Atualização de fotos das marcas, remoção de `bolvor` (movida para `database/imagens_sem_link/`), atualização de `@ewcruel` (mantida na ordem alfabética do `C`) e `@fashiondwsign` (Maison RefTaylor movida para o `M`), consolidando **131 marcas** no diretório.
  - Auditoria meticulosa de catálogo completo (navegando páginas internas de lojas como Shopify/Nuvemshop/WooCommerce) em `database/brand_prices.json`: **103 marcas** com preço mínimo/máximo mapeado e **28 marcas** em drop fechado/sob consulta.
  - Implementada barra lateral minimizável/maximizável em `M4RCAS` (`assets/js/marcas-app.js`, `assets/css/style.css`) com slider de valor máximo, faixas de **média de preço** (`(mín + máx) / 2`), ordenação e responsividade mobile.
- **Contexto / Porquê:**
  - A primeira varredura capturava apenas produtos da vitrine inicial de algumas lojas; a reanálise profunda evitou médias distorcidas e a barra lateral substituindo a lista inline manteve o foco visual no grid de marcas.

### [2026-11-11] — Borda Exata do Mapa, Privacidade Zero-Leak, Contador Único & `S0BR3`
- **O que mudou:**
  - Criado `scripts/extract_brazil_border.ps1` para extrair pixel a pixel os limites verdes da figura do Brasil em `assets/img/home-bg.png` (`2560x1440`), gerando `assets/data/brazil_map_bounds.json` (`rows`/`cols`) usado por `clampInsideBrazilGreenBorder()` em `main.js`.
  - Endurecimento de privacidade em `api/presence.php` e `main.js`: remoção de chaves antigas de geolocalização exata, conversão local para âncoras/células quantizadas de 6px e uso exclusivo de hashes HMAC-SHA256 e Cidade/UF.
  - Criado contador permanente de visitantes únicos por IP (`unique_visitors.json` + `unique_visitors_max.txt` garantindo contagem monotônica que nunca diminui).
  - Filtro de apenas **drops futuros** em `api/get_calendar_drops.php` + botão admin `✕` de exclusão rápida (`api/delete_calendar_drop.php`).
  - Atualizados cards da equipe na `S0BR3` (`shadow`, `kimurauptown`, `vitomaneiro`, `pedroispunk`, `marloon`, `lipesanst`, `C6ut6`) com links do Instagram e criada a página easter-egg `sair.html` a partir do link discreto `"Sair da sala..."`.
- **Contexto / Porquê:**
  - Coordenadas geográficas cruas extrapolavam a silhueta estilizada do Brasil na arte de fundo e podiam expor localização precisa de usuários; o confinamento por píxeis verdes + quantização resolveu precisão visual e privacidade simultaneamente.

### [2026-11-10] — Menu `☰`, Radar de Drops por E-mail (1h Antes), Upload no Fit Lab & Mapa Inicial
- **O que mudou:**
  - Simplificado o topo da página `M4RCAS`: mantida apenas a barra de busca grande + botão `☰` (`#marcas-hamburger-btn`) abrindo o menu com `Catálogo / Quiz Gringa → BR / Coleções & Fit Lab` e filtros de categoria separados por divisor neon.
  - Criado sistema de alertas de drops por e-mail 1h antes (`api/subscribe_drops.php`, `api/unsubscribe_drops.php`, `api/cron_dispatch_drops.php`) cruzando o feed `.ics` público do Google Calendar com `assets/data/marcas.json` e enviando e-mails HTML em preto/verde neon.
  - Automatizado o formulário de sugestão em `C4L3NDAR10` (`api/drops_submit.php` -> `scheduled_drops.json` + e-mail de notificação + suporte opcional a webhook do Google Apps Script).
  - Implementado no **Fit Lab** (`marcas-app.js`) o estúdio client-side de upload e remoção automática de fundo via Canvas HTML5 + persistência privada no navegador (`IndexedDB` `emorphosis_personal_wardrobe_db`).
  - Lançada a primeira versão do radar de usuários ativos no mapa do Brasil (`presence.php` + fallback `ipwho.is`).
- **Contexto / Porquê:**
  - Dar utilidade recorrente ao diretório além da vitrine estática: avisar fãs 1h antes de lançamentos e permitir experimentar peças pessoais sobre recortes das marcas sem necessidade de backend pesado ou upload de fotos privadas para servidor.

### [2026-11-08 a 2026-11-09] — Catálogo Automatizado, Estética Matrix/Glitch & Primeiros Recortes PNG
- **O que mudou:**
  - Estruturado `scripts/build_marcas.py` lendo `database/marcas.txt`, mapeando imagens de `assets/img/marcas/` e gerando `m4rcas.html` e `marcas.json` em grid 3×N com `mix-blend-mode` no fundo em vídeo (`assets/video/home-bg.mp4`).
  - Definida a estética oficial em `H0M3` (`home-bg.png` 2560×1440 + botão misterioso `?` levando a `M4RCAS`), fundos dedicados em `C4L3NDAR10` (`calendar-bg.png`) e `S0BR3` (`sobre-bg.png`), header translúcida e efeito `.glitch-text`.
  - Inseridos os 3 primeiros recortes PNG reais no Manequim Virtual (`aevus-jaqueta.png`, `aevus-calca.png`, `drestudio-bone.png`).
  - Documentadas ideias de longo prazo e divisão inicial de papéis do coletivo (implementação técnica, direção criativa/visual, vídeo/marketing, arte final/vetorização).
- **Contexto / Porquê:**
  - Gerar `m4rcas.html` via script Python a partir de `database/marcas.txt` evitou manter manualmente mais de 130 cards HTML e garantiu ordenação/consistência entre catálogo visual e JSON da API.

### [2026-11-05] — Recuperação, Decisão de Stack & Automação de Deploy Hostinger
- **O que mudou:**
  - Após expiração do plano anterior na Hostinger (`emorfoses.com.br`) e ausência de backup local recuperável, decidiu-se reconstruir a plataforma do zero em arquivos estáticos + PHP puro hospedados na Hostinger (`emorphosis.com.br`).
  - Criados o script incremental de deploy `scripts/deploy_ftp.py` (FTPS com reuso de sessão TLS compatível com Pure-FTPd da Hostinger, lendo `.env`), `database/schema.sql` e `api/db.example.php`.
- **Contexto / Porquê:**
  - Stack enxuta sem `Node.js`/bundler permite rodar direto em hospedagem compartilhada Apache/PHP da Hostinger com custo mínimo e deploy automatizado por um único comando Python.
