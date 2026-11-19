# Regras de Desenvolvimento — Emorphosis

Estas regras aplicam-se a todos os agentes e desenvolvedores operando neste repositório.

1. **Catálogo via gerador (`build_marcas.py`)**:
   - Nunca edite `m4rcas.html`, `assets/data/marcas.json` ou `database/marcas.json` manualmente.
   - Sempre atualize `database/marcas.txt`, `database/brand_prices.json`, `database/brand_locations.json` e `scripts/build_marcas.py` (`MAPPING` / `VIBE_OVERRIDES`), e então execute `python scripts/build_marcas.py`.
2. **Cache-busting (`ASSET_VER`)**:
   - Sempre que alterar `assets/css/style.css`, `assets/js/*.js` ou `assets/data/*.json`, atualize o parâmetro `?v=` em `scripts/build_marcas.py` (`ASSET_VER`), nos arquivos HTML (`index.html`, `c4l3ndar10.html`, `s0br3.html`, `marca.html`) e nas chamadas `fetch(...)` em `assets/js/main.js`.
3. **Privacidade Zero-Leak no Radar**:
   - Em `api/presence.php` e `assets/js/main.js`, nunca persista nem exponha IP em texto claro ou coordenadas GPS exatas; use apenas cidade/UF, célula quantizada de 6px dentro de `brazil_map_bounds.json` e hashes HMAC-SHA256.
4. **Internacionalização (PT/EN)**:
   - Toda nova string visível na interface deve ter tradução `pt` e `en` em `assets/js/i18n.js` e atributo `data-i18n` (ou `data-i18n-placeholder`).
5. **Segurança e Deploy**:
   - Nunca leia/imprima senhas de `.env` ou `api/db.php` em logs ou respostas.
   - Nunca rode `python scripts/deploy_ftp.py` sem solicitação explícita do usuário, pois envia diretamente para produção (`emorphosis.com.br`).
   - Ao criar qualquer novo arquivo de persistência runtime em `api/storage/`, adicione-o tanto em `EXCLUDE_NAMES` (`scripts/deploy_ftp.py`) quanto no `.gitignore`.
