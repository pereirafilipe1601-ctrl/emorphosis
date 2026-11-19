# GEMINI.md — Emorphosis (`emorphosis.com.br`)

Guia central de arquitetura, convenções e operação para agentes e desenvolvedores trabalhando no projeto **EMORPHOSIS**.

---

## 1. Visão Geral do Projeto

**EMORPHOSIS** (`https://emorphosis.com.br`) é uma plataforma web bilíngue (PT/EN) dedicada a catalogar, mapear e conectar marcas independentes de moda brasileira, ateliês autorais e criadores experimentais.

Funcionalidades principais:
- **H0M3 (`index.html`)**: mapa interativo do Brasil por UF (10 estados com marcas), radar em tempo real de visitantes ativos confinado aos limites verdes do mapa, contador de visitantes únicos por IP e modal/mural de sonhos (`/sonhos/`).
- **M4RCAS (`m4rcas.html`)**: diretório de **131 marcas** (103 com preços mapeados e 28 drop/sob consulta), busca instantânea, filtros por categoria e faixa/média de preço, **Quiz Gringa → BR** e **Fit Lab** (manequim virtual em camadas + estúdio client-side de recorte de peças pessoais via Canvas + `IndexedDB`).
- **Ficha da Marca (`marca.html?m=<slug>`)**: página dinâmica com detalhes da marca, ponte para referências internacionais, arquivo de drops, guia de conservação por categoria e marcas do mesmo estado/vibe.
- **C4L3NDAR10 (`c4l3ndar10.html`)**: embed do Google Calendar oficial + feed cronológico unificado de drops futuros (Google `.ics` + submissões do site), formulário de sugestão com disparo automático de alertas 1h antes por e-mail e modo admin de exclusão.
- **S0BR3 (`s0br3.html`) & `sair.html`**: manifesto do ecossistema, equipe do coletivo e página easter-egg.

---

## 2. Stack Tecnológica & Dependências

Não há `package.json`, bundler ou framework JS. O projeto roda com **arquivos estáticos + PHP puro + scripts Python/PowerShell de build/deploy**:

- **Frontend**: HTML5, CSS3 puro (`assets/css/style.css`), JavaScript Vanilla ES6+ (`IIFE`, sem transpilação), Google Fonts (`Chakra Petch`, `Inter`, `Share Tech Mono`, `Rubik Glitch`, `Silkscreen`), `IndexedDB` e `localStorage`.
- **Backend / Produção**: PHP 8+ (`declare(strict_types=1)`, `PDO`, `cURL`, `mbstring`, `mail()`) em Apache/Hostinger (`.htaccess` com rewrite para URLs limpas e HTTPS obrigatório).
- **Persistência**:
  - Primária: arquivos JSON/JSONL em `api/storage/` (bloqueados ao acesso HTTP via `api/storage/.htaccess` e `api/storage/index.php`).
  - Secundária/Opcional: MySQL via `PDO` (`api/db.php`, schema em `database/schema.sql`; atualmente integrado em `api/subscribe_drops.php`).
- **Build & Automação**:
  - Python `3.12+` utilizando **apenas biblioteca padrão** (`scripts/build_marcas.py`, `scripts/deploy_ftp.py`, `scripts/drops_ai_parser.py`).
  - Windows PowerShell + .NET `System.Drawing` (`scripts/extract_brazil_border.ps1`).
- **Integrações Externas**:
  - Google Calendar feed público `.ics` e embed (`@group.calendar.google.com`).
  - Google Apps Script Webhook opcional (`api/storage/gcal_webhook.txt`) para espelhar submissões direto no Google Calendar.
  - `https://ipwho.is/` (geolocalização aproximada por IP no `presence.php` e fallback client-side no `main.js`).
  - Anthropic Messages API (`claude-sonnet-4-20250514`) opcional em `scripts/drops_ai_parser.py`.

---

## 3. Mapa da Estrutura de Pastas

```text
emorphosis/
├── index.html                    # H0M3: mapa do Brasil, radar em tempo real, contador e botão ?
├── m4rcas.html                   # M4RCAS: GERADO por scripts/build_marcas.py (não editar à mão)
├── marca.html                    # Ficha individual da marca (?m=<slug>)
├── c4l3ndar10.html               # C4L3NDAR10: Google Calendar, feed de drops, formulário e modo admin
├── s0br3.html                    # S0BR3: manifesto e equipe
├── sair.html                     # Página oculta/easter-egg (noindex)
├── .htaccess                     # Rewrites Hostinger (HTTPS, URLs sem .html, Cache-Control)
├── .env / .env.example           # Variáveis locais (FTP, MySQL, segredos PHP, Anthropic)
├── DEVLOG.md                     # Diário cronológico de alterações e contexto (sem limite de 24 KB)
├── api/                          # Endpoints PHP (America/Sao_Paulo, JSON)
│   ├── presence.php              # Radar anônimo + contador permanente de visitantes únicos
│   ├── save_dream.php            # POST/GET de sonhos -> api/storage + espelho em /sonhos/
│   ├── subscribe_drops.php       # Inscrição de alertas 1h antes + e-mail de confirmação
│   ├── unsubscribe_drops.php     # Cancelamento via HMAC-SHA256
│   ├── drops_submit.php          # Cadastro automático de drop + e-mail admin + webhook GCal
│   ├── get_calendar_drops.php    # Merge/dedup de scheduled_drops.json + feed .ics (só futuros)
│   ├── delete_calendar_drop.php  # Exclusão admin (scheduled_drops.json + deleted_drops.json)
│   ├── cron_dispatch_drops.php   # Disparo de alertas na janela de 15–75 min antes do drop
│   ├── config_loader.php         # Resolução de segredos (.env / api/config.php / runtime_secrets)
│   ├── config.example.php        # Modelo de configuração privada (deploy gera api/config.php)
│   ├── db.example.php            # Modelo de conexão PDO MySQL (copiar para api/db.php)
│   └── storage/                  # Dados runtime protegidos por .htaccess (não subir ao Git)
├── assets/
│   ├── css/style.css             # Folha de estilos global (tema preto + verde matrix #19f028)
│   ├── js/
│   │   ├── i18n.js               # Dicionário PT/EN e listener emorphosis:langchange
│   │   ├── main.js               # Glitch, radar/mapa Brasil, modal de estados, modal de sonhos
│   │   ├── marcas-app.js         # Catálogo, filtros de preço/categoria, Quiz, Fit Lab + IndexedDB
│   │   └── marca-profile.js      # Renderizador da página marca.html
│   ├── data/
│   │   ├── marcas.json           # Cópia de distribuição do catálogo (gerada por build_marcas.py)
│   │   ├── brazil_map_bounds.json# Borda verde pixel-a-pixel de home-bg.png
│   │   └── brazil_states_shapes.json # Contornos e âncoras das UFs no modal de estados
│   ├── img/                      # Logos, backgrounds, marcas/ (131 JPGs) e fitlab/ (recortes PNG)
│   └── video/home-bg.mp4         # Vídeo de fundo da página M4RCAS
├── database/                     # Fontes de verdade do catálogo e schema SQL
│   ├── marcas.txt                # Lista mestre de @instagram e categorias entre parênteses
│   ├── brand_prices.json         # Faixas de preço auditadas (min/max/store_url)
│   ├── brand_locations.json      # Cidade/UF e coordenadas (map_x/map_y/state_x/state_y)
│   ├── marcas.json               # JSON consolidado (idêntico a assets/data/marcas.json)
│   ├── schema.sql                # Tabelas MySQL: marcas e inscritos_drops
│   └── imagens_sem_link/         # Imagens movidas automaticamente por build_marcas.py se sem vínculo
├── scripts/
│   ├── build_marcas.py           # Gera m4rcas.html + assets/data/marcas.json + database/marcas.json
│   ├── deploy_ftp.py             # Deploy FTPS incremental para Hostinger (lê .env)
│   ├── drops_ai_parser.py        # Extrator Claude API de legendas do IG para .ics
│   └── extract_brazil_border.ps1 # Extrai brazil_map_bounds.json a partir de home-bg.png
├── sonhos/                       # Diretório público de sonhos (/sonhos/index.html)
└── _conversa_emorphosis/         # Histórico e auditorias antigas (ignorado no Git e no FTP)
```

> **Histórico & Contexto Contínuo**: o `GEMINI.md` tem limite rígido de 24.000 bytes no Antigravity e guarda a arquitetura atual; o registro cronológico de alterações de cada dev e o porquê das decisões ficam em [DEVLOG.md](./DEVLOG.md). Consulte-o antes de grandes mudanças e atualize-o ao concluir tarefas.

---

## 4. Decisões de Arquitetura & Convenções de Código

1. **Fonte Única para `M4RCAS`**: `m4rcas.html`, `assets/data/marcas.json` e `database/marcas.json` são **artefatos gerados** por `scripts/build_marcas.py` a partir de `database/marcas.txt`, `MAPPING`/`VIBE_OVERRIDES` (no próprio script), `database/brand_prices.json` e `database/brand_locations.json`. Alterações manuais em `m4rcas.html` serão perdidas no próximo build.
2. **Cache-Busting Manual (`ASSET_VER`)**: `scripts/build_marcas.py` injeta `ASSET_VER` (atualmente `"20261118g"`) em `m4rcas.html`. Ao alterar CSS/JS/JSON globais, atualize `ASSET_VER` em `build_marcas.py`, nos HTMLs (`index.html`, `c4l3ndar10.html`, `s0br3.html`, `marca.html`) e nas URLs de fetch em `assets/js/main.js`.
3. **Privacidade Zero-Leak no Radar**: `presence.php` e `main.js` **nunca** devem gravar IP em texto claro nem coordenadas GPS exatas de rua/bairro. As posições são convertidas localmente em âncoras/células quantizadas (múltiplos de 6px dentro da borda verde do Brasil) e os identificadores em disco usam `hash_hmac('sha256', ...)`.
4. **Convenções PHP**:
   - Sempre iniciar com `<?php declare(strict_types=1);` e `date_default_timezone_set('America/Sao_Paulo');`.
   - Retornar JSON padronizado (`['ok' => true/false, ...]`) com `Content-Type: application/json; charset=utf-8`.
   - Escritas concorrentes em JSON devem usar `LOCK_EX` (ou `flock` + `ftruncate` + `rewind`).
   - Sempre escapar dados em e-mails HTML com `htmlspecialchars(..., ENT_QUOTES, 'UTF-8')`.
5. **Convenções JS & CSS**:
   - Manter scripts encapsulados em IIFE `(function () { ... })();` sem poluir o escopo global (exceto `window.EmorphosisI18n`).
   - Todo novo texto de interface deve possuir chaves `pt` e `en` em `assets/js/i18n.js` e atributo `data-i18n` / `data-i18n-placeholder`.
   - Identidade visual: fundo `#020502`/`#000000`, verde neon `#19f028` / `#39ff48`, fontes `Chakra Petch` e `Share Tech Mono`, efeito glitch automático via `syncGlitchAttributes()` em `main.js`.

---

## 5. Comandos Principais

```powershell
# 1. Reconstruir catálogo (m4rcas.html + assets/data/marcas.json + database/marcas.json)
python scripts/build_marcas.py

# 2. Subir servidor local completo (requer PHP 8+ no PATH; testa APIs PHP)
php -S localhost:8000

# 3. Subir servidor apenas estático (sem execução de APIs PHP)
python -m http.server 8000

# 4. Verificar sintaxe dos scripts PHP (se PHP instalado)
Get-ChildItem api\*.php | ForEach-Object { php -l $_.FullName }

# 5. Regerar limites do mapa do Brasil (somente se assets/img/home-bg.png mudar)
powershell -ExecutionPolicy Bypass -File scripts/extract_brazil_border.ps1

# 6. Extrair evento de legenda de post para .ics usando Claude API (requer ANTHROPIC_API_KEY no .env)
python scripts/drops_ai_parser.py "Texto da legenda do post do drop"

# 7. Deploy para produção Hostinger via FTPS (ATENÇÃO: publica direto no ar!)
python scripts/deploy_ftp.py
# Para forçar reenvio de imagens de marcas mesmo com mesmo tamanho:
python scripts/deploy_ftp.py --force-marcas
```

> **Testes & Lint**: não há suíte automatizada de testes ou linter configurada no momento. Após alterações, rode `python scripts/build_marcas.py` (se afetar catálogo) e valide no navegador (`H0M3`, `M4RCAS`, `C4L3NDAR10`, `marca.html?m=aevus`, `S0BR3`, `/sonhos/`).

---

## 6. Estado Atual & Pendências Conhecidas

### Já implementado
- Todas as páginas principais (`H0M3`, `M4RCAS`, `marca.html`, `C4L3NDAR10`, `S0BR3`, `sair.html`, `/sonhos/`).
- Catálogo completo de **131 marcas** com auditoria de preços (103 com preço, 28 sob consulta) e geolocalização em 10 UFs.
- Radar em tempo real + janela de estados + contador único por IP.
- Quiz Gringa → BR, Fit Lab com 3 recortes reais (`aevus-jaqueta.png`, `aevus-calca.png`, `drestudio-bone.png`) e estúdio de recorte pessoal (`IndexedDB`).
- Calendário de drops com merge `.ics` + formulário + disparo 1h antes (`cron_dispatch_drops.php` via cron ou web-ping a cada 3 min) + exclusão admin.

### Pendências & Melhorias em Aberto
1. **Persistência MySQL**: `database/schema.sql` está criado e `subscribe_drops.php` já suporta `api/db.php`, mas `DB_NAME`/`DB_USER`/`DB_PASS` estão vazios no `.env` e os demais endpoints usam apenas JSON em `api/storage/`.
2. **Fit Lab**: expandir biblioteca de recortes PNG reais de outras marcas além de Atelier Aevus e Drestudio.
3. **Qualidade & Automação**: configurar linter/testes automatizados (ex: PHP syntax check + validação do JSON gerado por `build_marcas.py`).

---

## 7. Armadilhas Conhecidas (O Que Evitar Quebrar)

- **Efeito colateral de `build_marcas.py`**: qualquer `.jpg` em `assets/img/marcas/` que não esteja mapeado em `MAPPING` + `database/marcas.txt` será **movido automaticamente** para `database/imagens_sem_link/`.
- **Coordenadas do mapa acopladas**: `assets/img/home-bg.png` (2560x1440), `assets/data/brazil_map_bounds.json`, `scripts/extract_brazil_border.ps1` e `BRAZIL_MAP_ANCHORS` / `clampInsideBrazilGreenBorder` em `assets/js/main.js` são dependentes entre si.
- **Deploy sobrescreve o servidor remoto**: `scripts/deploy_ftp.py` envia diretamente para `/domains/emorphosis.com.br/public_html` (e gera `api/db.php` e `api/config.php` automaticamente a partir do `.env`). Nunca crie novos arquivos de estado runtime em `api/storage/` sem adicioná-los a `EXCLUDE_NAMES` em `deploy_ftp.py` e ao `.gitignore`, ou o deploy pode sobrescrever dados reais de produção.
- **URLs limpas do `.htaccess`**: em produção, `/m4rcas.html` redireciona (302) para `/m4rcas`. Links relativos funcionam porque rotas sem extensão não adicionam barra final, mas evite quebrar os `RewriteRule` do `.htaccess` raiz.
