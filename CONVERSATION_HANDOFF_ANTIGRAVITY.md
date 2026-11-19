# EMORPHOSIS (`emorphosis.com.br`) — Pacote de Contexto & Histórico da Conversa (Antigravity Handoff)

Este documento consolida todo o histórico de desenvolvimento, arquitetura e decisões técnicas do projeto **EMORPHOSIS** (`https://emorphosis.com.br`) para continuidade imediata no Google Antigravity em outro computador.

---

## 1. Como abrir este projeto no Antigravity

1. Abra a pasta do projeto como Workspace/Projeto no **Antigravity** (nesta máquina: `C:\Users\trsha\.gemini\antigravity\scratch\emorphosis` — já vinculada ao projeto `emorphosis`).
2. Na primeira mensagem de um novo chat dentro do projeto, envie:
   > *"Leia o arquivo `CONVERSATION_HANDOFF_ANTIGRAVITY.md` e os arquivos em `_conversa_emorphosis/` para carregar todo o histórico e contexto do projeto Emorphosis."*

### Conteúdo transferido da conversa original (`_conversa_emorphosis/`)
Toda a documentação, mídias, scripts auxiliares e histórico da conversa **Projeto Emorphosis** foram consolidados na pasta local `_conversa_emorphosis/` (automaticamente ignorada no deploy FTP via `EXCLUDE_NAMES` em `scripts/deploy_ftp.py`):
- `_conversa_emorphosis/levantamento_precos_marcas.md` — Auditoria de preços das 131 marcas (`103` com preço verificado, `28` drops fechados/sob consulta).
- `_conversa_emorphosis/levantamento_localizacao_marcas.md` — Mapeamento de Cidade/UF das 131 marcas em 10 estados (`SP`, `SC`, `PR`, `RS`, `RJ`, `MG`, `ES`, `GO`, `RN`, `DF`).
- `_conversa_emorphosis/scratch_auxiliar/` — Scripts Python e JSONs auxiliares usados na auditoria de preços, localização e coordenadas do mapa (já atualizados para usar caminhos relativos ao projeto).
- `_conversa_emorphosis/midias_usuario/` e `_conversa_emorphosis/midias_etapas/` — Imagens e mídias trocadas/geradas durante a conversa.
- `_conversa_emorphosis/transcript_projeto_emorphosis.jsonl` — Log completo em JSONL da conversa original.

---

## 2. Visão Geral da Arquitetura do Site

- **Domínio em produção:** `https://emorphosis.com.br` (Hospedado na Hostinger em `/domains/emorphosis.com.br/public_html`).
- **Deploy automatizado via FTPS:** `python scripts/deploy_ftp.py` (lê credenciais de `.env` na raiz do projeto sem expor senhas no terminal).
- **Gerador do Catálogo de 131 Marcas:** `python scripts/build_marcas.py` (lê `database/marcas.txt`, `database/brand_prices.json`, `database/brand_locations.json`, cruza imagens em `assets/img/marcas/` e gera `m4rcas.html` e `assets/data/marcas.json`; versão atual de cache de assets: `20261118g`).

---

## 3. Funcionalidades Implementadas

### 3.1. `H0M3` (`index.html`, `assets/js/main.js`, `api/presence.php`, `assets/data/brazil_map_bounds.json`)
- **Fundo Oficial 2560x1440:** `assets/img/home-bg.png` + botão central `?` (`m4rcas.html`).
- **Mapa Interativo de Marcas por Estado + Radar em Tempo Real:**
  - Pede permissão de localização exata ao navegador (`navigator.geolocation.getCurrentPosition`) com botão rápido `📍 GPS` no HUD e fallback por IP em `api/presence.php`.
  - O arquivo `assets/data/brazil_map_bounds.json` (gerado por `scripts/extract_brazil_border.ps1`) contém os píxeis verdes exatos da borda exterior da figura do Brasil em `home-bg.png` (`minX=496, maxX=1333, minY=325, maxY=1110`, além de `rows[y] = [leftX, rightX]` e `cols[x] = [topY, bottomY]`).
  - Todos os pontos de usuários ativos são parametrizados e confinados estritamente dentro dos píxeis verdes da borda da figura do Brasil (`clampInsideBrazilGreenBorder`).
  - Exibe os 10 estados com marcas (`assets/data/brazil_states_shapes.json`), abrindo uma janela estilo aplicativo de computador com as marcas da UF selecionada; no celular (`<= 820px`), os botões dos estados ficam em fileira horizontal centralizada abaixo do mapa e o botão `10 ESTADOS` fica centralizado acima da barra `RADAR ATIVO`.
- **Contador de Visitantes Únicos & Caixa de Sonhos (`/sonhos/`):**
  - Contador único por IP e modal de pergunta/sonho (`api/save_dream.php`), espelhado em `/sonhos/` (`sonhos/index.html`) e com efeito de tela preta `#emorphosis` (fonte `Rubik Glitch` + frases em `Silkscreen` preto/verde/branco).

### 3.2. `M4RCAS` (`m4rcas.html`, `assets/js/marcas-app.js`, `scripts/build_marcas.py`)
- **Barra de Busca Grande + Menu "Três Riscos" (`☰`):**
  - Acima do grid de 131 marcas ficam apenas a barra de busca centralizada e o botão `☰` (`#marcas-hamburger-btn`).
  - Ao clicar no botão `☰`, abre-se a gaveta (`#marcas-drawer-panel`) com:
    1. Seção da Página (`CATÁL0G0 (131)`, `QU1Z GRINGA → BR`, `C0L3ÇÕ3S & F1T LAB`)
    2. Divisória verde neon (`.subtabs-divider`)
    3. Filtros de categoria (`TODAS`, `ROUPAS`, `HANDMADE`, `ACESSÓRIOS`, `CALÇADOS`, `SOB MEDIDA / ALFAIATARIA`, `UPCYCLING`, `DIVERSOS`).
- **F1T LAB (Manequim Virtual + Estúdio de Recorte de Peças Pessoais):**
  - Peças reais recortadas da Atelier Aevus (jaqueta + calça) e Drestudio (boné).
  - Sistema de upload de peças próprias (`#fitlab-custom-studio`): o usuário envia uma foto da roupa, o algoritmo em canvas remove o fundo e vãos internos automaticamente, recorta a peça e salva na coleção privada do navegador do usuário (`IndexedDB` `emorphosis_personal_wardrobe_db`).
- **Sistema de Inscrição e Alertas de Drops por E-mail (1h Antes):**
  - Formulário no final do catálogo (`#drop-subscribe-box`) -> `api/subscribe_drops.php` (`api/storage/drop_subscriptions.json`).
  - E-mails HTML estilizados em preto e verde neon (`From: Emorphosis Drops <noreply@emorphosis.com.br>`).
  - Disparador automático `api/cron_dispatch_drops.php` que avisa os inscritos quando falta 1 hora para o drop.

### 3.3. `C4L3NDAR10` (`c4l3ndar10.html`, `api/drops_submit.php`, `api/get_calendar_drops.php`, `api/delete_calendar_drop.php`)
- **Google Calendar Oficial Embedado:** `e279d9d10a587ca926785f28efb4fc3cda446fc8b7a4adecec5a111bf316dd01@group.calendar.google.com`.
- **Automação de Sugestão de Drops:**
  - Qualquer drop enviado pelo formulário `#drops-radar-form` é adicionado automaticamente a `api/storage/scheduled_drops.json`, aparece na seção **Drops Agendados no Calendário** (que exibe apenas drops futuros em ordem cronológica), entra na fila de alertas de 1h antes e envia notificação para o e-mail configurado em `ADMIN_NOTIFY_EMAIL` (`.env` / `api/config.php`).
- **Botão `✕` de Exclusão Rápida (Exclusivo Admin):**
  - Ativado pelo ícone `🔒` informando a chave configurada em `ADMIN_DROP_TOKEN` (`.env` / `api/config.php`).
  - Permite excluir instantaneamente qualquer drop duplicado ou indesejado via `api/delete_calendar_drop.php`.
