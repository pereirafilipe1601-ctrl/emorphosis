---
name: emorphosis-ftp-deploy
description: >-
  Use this skill when preparing or executing a production deployment of the
  Emorphosis site to Hostinger via FTPS using scripts/deploy_ftp.py.
---

# Emorphosis Hostinger FTPS Deploy Runbook

O script `scripts/deploy_ftp.py` envia os arquivos locais diretamente para `/domains/emorphosis.com.br/public_html` na Hostinger usando as credenciais de `.env`.

## Checklist Pré-Deploy

1. **Confirmação explícita**: nunca executar deploy em produção sem confirmação clara do usuário.
2. **Catálogo atualizado**: se houve mudança em marcas, preços, localizações ou layout de `M4RCAS`, rodar antes:
   ```bash
   python scripts/build_marcas.py
   ```
3. **Verificação de sintaxe PHP** (se `php` estiver disponível localmente):
   ```powershell
   Get-ChildItem api\*.php | ForEach-Object { php -l $_.FullName }
   ```
4. **Proteção de dados de produção (`EXCLUDE_NAMES`)**:
   - Conferir em `scripts/deploy_ftp.py` se qualquer novo arquivo JSON/TXT/JSONL de `api/storage/` está listado em `EXCLUDE_NAMES` para não sobrescrever dados reais do servidor.
5. **Verificar `.env` sem expor segredos**:
   - Confirmar apenas que `.env` existe e possui `FTP_HOST`, `FTP_USER`, `FTP_PASS` preenchidos (nunca imprimir o conteúdo de `.env` no terminal ou na conversa).

## Execução do Deploy

```bash
python scripts/deploy_ftp.py
```

- Mídias (`.mp4`, `.jpg`, `.png`, `.webp`) com o mesmo tamanho no servidor são puladas automaticamente.
- Para forçar reenvio de imagens de marcas mesmo com mesmo tamanho:
  ```bash
  python scripts/deploy_ftp.py --force-marcas
  ```

## Pós-Deploy

- Validar no ar: `https://emorphosis.com.br/`, `/m4rcas`, `/c4l3ndar10`, `/s0br3` e `/sonhos/`.
