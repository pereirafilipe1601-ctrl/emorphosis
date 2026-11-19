---
name: emorphosis-catalog-build
description: >-
  Use this skill when adding, removing, or updating brands, prices, categories,
  vibes, or locations in the Emorphosis catalog, or when regenerating
  m4rcas.html and marcas.json.
---

# Emorphosis Catalog Build Runbook

Use este fluxo sempre que precisar alterar marcas, preços, localizações ou o template da página `M4RCAS`.

## Passos

1. **Atualizar fontes de dados**:
   - `database/marcas.txt`: adicionar/editar a URL do Instagram e categorias entre parênteses (`(roupas)`, `(handmade)`, `(acessorios)`, `(calcados)`, `(sob medida)`, `(upcycling)`, `(diversos)`).
   - `assets/img/marcas/`: garantir que a foto `.jpg` da marca exista com o nome exato declarado em `MAPPING`.
   - `scripts/build_marcas.py`: atualizar `MAPPING` (`handle -> (arquivo.jpg, Nome de Exibição, sort_key)`) e, se necessário, `VIBE_OVERRIDES` e `ASSET_VER`.
   - `database/brand_prices.json` e `database/brand_locations.json`: atualizar faixas de preço (`min_price`, `max_price`, `store_url`) e cidade/UF/coordenadas (`map_x`, `map_y`, `state_x`, `state_y`).

2. **Executar o build**:
   ```bash
   python scripts/build_marcas.py
   ```

3. **Verificar resultados**:
   - Conferir a saída `[OK] m4rcas.html e assets/data/marcas.json gerados com N marcas!`.
   - Verificar se nenhuma imagem válida foi movida acidentalmente para `database/imagens_sem_link/` (isso ocorre se faltar vínculo entre `marcas.txt` e `MAPPING`).
   - Se `ASSET_VER` foi incrementado, sincronizar a versão nos `<link>`/`<script>` de `index.html`, `c4l3ndar10.html`, `s0br3.html`, `marca.html` e nos `fetch()` de `assets/js/main.js`.
   - Validar se `assets/data/marcas.json` e `database/marcas.json` estão idênticos e testar `m4rcas.html` e `marca.html?m=<slug>` no navegador.
