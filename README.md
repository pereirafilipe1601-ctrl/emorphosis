# EMORPHOSIS (`emorphosis.com.br`)

Plataforma e diretório brasileiro de moda independente — catálogo de marcas autorais, mapa/radar interativo do Brasil, Quiz Gringa → BR, Fit Lab (manequim virtual + recorte de peças), calendário de drops com alertas por e-mail e mural de sonhos.

> Para documentação detalhada de arquitetura, convenções e armadilhas do código, leia também o [GEMINI.md](./GEMINI.md).

---

## Pré-requisitos

- **Git**
- **Python 3.12+** (usa apenas biblioteca padrão — não requer `pip install` nem `.venv`)
- **PHP 8.0+** (com extensões `pdo_mysql`, `curl`, `mbstring` habilitadas) — necessário apenas para testar os endpoints em `api/*.php` localmente
- **Windows PowerShell** *(opcional)* — necessário apenas se precisar regerar `assets/data/brazil_map_bounds.json` via `scripts/extract_brazil_border.ps1`

> Não há `Node.js`, `npm`, `Composer` nem etapa de build frontend/bundler.

---

## Configuração do Ambiente do Zero

1. **Clone o repositório** e abra a pasta raiz no **Antigravity** (ou editor de preferência).

2. **Crie o arquivo `.env` local** a partir do modelo:
   ```powershell
   Copy-Item .env.example .env
   ```
   ```bash
   # Linux / macOS
   cp .env.example .env
   ```
   Preencha no `.env` apenas o que você for utilizar:
   - `FTP_*`: credenciais FTPS da Hostinger (necessário só para rodar `scripts/deploy_ftp.py`).
   - `DB_*`: credenciais MySQL (opcional; se preenchidas, `deploy_ftp.py` gera `api/db.php`).
   - `ADMIN_DROP_TOKEN`, `ADMIN_NOTIFY_EMAIL`, `DROP_RADAR_SECRET`, `PRESENCE_*_SALT`: chaves de segurança e notificações dos endpoints PHP (lidas localmente via `api/config_loader.php`; no deploy, `deploy_ftp.py` gera `api/config.php`).
   - `ANTHROPIC_API_KEY`: chave da API da Anthropic (opcional; usada só em `scripts/drops_ai_parser.py`).

3. **(Opcional) Banco MySQL local/remoto**:
   - Se for testar `api/db.php` localmente, copie `api/db.example.php` para `api/db.php` e configure as credenciais, e importe `database/schema.sql`.
   - Sem MySQL, o backend funciona normalmente usando arquivos JSON em `api/storage/`.

---

## Rodando Localmente

### Opção 1: Servidor PHP completo (recomendado — front + APIs `api/*.php`)
Na raiz do projeto:
```bash
php -S localhost:8000
```
Acesse no navegador: `http://localhost:8000/index.html` (ou `m4rcas.html`, `c4l3ndar10.html`, `s0br3.html`, `marca.html?m=aevus`, `sonhos/`).

> **Nota**: o `.htaccess` (URLs limpas sem `.html`) funciona no Apache da Hostinger. No `php -S` embutido, acesse os arquivos com `.html` (ex: `/m4rcas.html`). Além disso, `mail()` no Windows local não envia e-mails reais sem um servidor SMTP configurado.

### Opção 2: Apenas frontend estático (sem APIs PHP)
```bash
python -m http.server 8000
```
Funciona para visualizar layout, catálogo (`m4rcas.html`), Quiz, Fit Lab e `marca.html`, mas chamadas a `api/*.php` (radar, sonhos, inscrição/calendário de drops) não serão processadas.

---

### Sincronização Automática em Equipe (Antigravity + GitHub)

O repositório inclui hooks nativos do Antigravity em [.agents/hooks.json](./.agents/hooks.json) ([git_sync_hook.py](./.agents/hooks/git_sync_hook.py)) e [.gitattributes](./.gitattributes):
- **Ao abrir ou enviar uma mensagem:** faz `git pull --rebase --autostash` automaticamente para trazer alterações do colega.
- **Ao concluir uma tarefa:** exige/atualiza o [DEVLOG.md](./DEVLOG.md), cria o commit e envia para `origin/main` automaticamente.
- **Edição simultânea no mesmo arquivo:** o `.gitattributes` (`DEVLOG.md merge=union`) mescla automaticamente entradas simultâneas no diário; se dois devs editarem exatamente as mesmas linhas de código ao mesmo tempo, o hook mantém o estado seguro e orienta o Antigravity a mesclar o conflito antes do push.

---

## Fluxo de Trabalho Comum

### Atualizar o catálogo de marcas
**Nunca edite `m4rcas.html` ou `assets/data/marcas.json` manualmente.**
1. Edite as fontes em `database/` (`marcas.txt`, `brand_prices.json`, `brand_locations.json`) e o dicionário `MAPPING` / `VIBE_OVERRIDES` em `scripts/build_marcas.py`.
2. Coloque o `.jpg` da marca em `assets/img/marcas/` (se ainda não existir).
3. Execute o gerador:
   ```bash
   python scripts/build_marcas.py
   ```
   Isso atualiza `m4rcas.html`, `assets/data/marcas.json` e `database/marcas.json`.

### Publicar em produção (Hostinger)
> **Cuidado**: o script faz upload direto para o site em produção (`emorphosis.com.br`). Só execute após testar localmente e com aprovação da equipe.
```bash
python scripts/deploy_ftp.py
```

### Controle de Tarefas & Cofre de Ideias (Notion Dev Hub + Antigravity)
O projeto conta com integração híbrida ao **Notion** (**Notion MCP Oficial** + CLI zero-dependências `scripts/notion_hub.py` usando Notion API `2026-03-11` com upload direto de áudios/vídeos/fotos e sync com `DEVLOG.md`).
- Guia completo do zero: [docs/NOTION_HUB_SETUP.md](./docs/NOTION_HUB_SETUP.md)
- Skill do Antigravity: [.agents/skills/emorphosis-notion-hub/SKILL.md](./.agents/skills/emorphosis-notion-hub/SKILL.md)

---

## Estrutura Resumida

- `index.html`, `m4rcas.html`, `marca.html`, `c4l3ndar10.html`, `s0br3.html`, `sair.html`, `sonhos/` — Páginas HTML do site
- `assets/` — CSS (`style.css`), JS Vanilla (`i18n.js`, `main.js`, `marcas-app.js`, `marca-profile.js`), dados JSON e mídias
- `api/` — Endpoints PHP e armazenamento runtime protegido em `api/storage/`
- `database/` — Lista mestre de marcas, preços, localizações e `schema.sql`
- `docs/` — Guias internos de operação e integrações (excluído do deploy FTP)
- `scripts/` — Scripts Python de build (`build_marcas.py`), deploy (`deploy_ftp.py`), Notion Hub (`notion_hub.py`), IA (`drops_ai_parser.py`) e PowerShell (`extract_brazil_border.ps1`)
- `.agents/` — Regras, hooks e skills compartilhadas do Antigravity para este repositório
