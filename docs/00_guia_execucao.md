# Projeto Data Major — Guia de Execução dos Notebooks

Guia rápido de como rodar o pipeline no Databricks (Free/Community Edition, serverless). A arquitetura é Medallion sobre AWS S3; o processamento é em **pandas** (`boto3`/`awswrangler` para o S3), não PySpark.

---

## Pré-requisitos

1. Credenciais AWS como **Databricks Secrets** (escopo `aws-credentials`, chaves `access-key` e `secret-key`; para o RDS, `rds-host`/`rds-user`/`rds-password`).
2. Repositório conectado via **Databricks Repos**.
3. Dependências instaladas no notebook que precisar (a 1ª célula já trata): `awswrangler`, `pyarrow` recente e, quando o pandas do runtime exigir, `numpy<2`; para o RDS, `psycopg2-binary` + `sqlalchemy`.

> ⚠️ No serverless o **Spark não acessa o S3** (erro 403). A leitura/escrita é sempre via `boto3`/`awswrangler`/`pandas` com as chaves do Secrets.

---

## Pipeline — ordem de execução (`notebooks/pipeline/`)

| # | Notebook | Responsável | Entrada → Saída | Observações |
|---|----------|-------------|------------------|-------------|
| 1 | `extract.py` | Davi | INEP → `bronze/` (CSV) | Baixa o `.zip` do INEP e sobe o CSV `MICRODADOS_ENEM_{ano}.csv` em streaming (sem disco local) |
| 2 | `transform_silver.py` | Bruno | `bronze/` → `silver/` (CSV) | Filtro de presença nas 4 provas, trata nulos (Q005 numérica à parte), remove duplicatas |
| 3 | `transform_gold.py` | Bruno | `silver/` → `gold/` (CSV) | Cria `NOTA_MEDIA` e `TARGET` (mediana **por ano**); mantém Q001–Q025 originais (sem encoding) |
| 4 | `load_parquet.py` | Vinicius | `gold/` → `parquet/enem/` | Consolida os 3 CSVs num Parquet (`awswrangler`, zstd, ~50 MB, particionado por `year`) |
| 4b | `load_postgresql.py` | Vinicius | `gold/` (+ bronze/silver) → RDS | **Opcional** — carga complementar no PostgreSQL; liga/desliga a instância por custo |
| 5 | `05_mining_arvore.py` | Gabriel | `parquet/enem/` → modelo + métricas | Spearman + Árvore de Decisão + matriz/ROC/importâncias/regras |

Utilitários em `pipeline/`: `exemplo_config_aws_s3.py`, `exemplo_config_aws_rds.py`, `exemplo_delete_s3.py`.

> **Regra de ouro:** os notebooks de `analysis/` **apenas leem** o Parquet — nunca alteram bronze/silver/gold.

---

## Análise exploratória (`notebooks/analysis/`)

- `analysis.py` — EDA do dataset final (head, schema, nulos, estatística descritiva de `NOTA_MEDIA`, histogramas). Não usa a `TARGET`.
- `test_analysis.py` — mesma análise com dicionário de tradução dos códigos (renda, escolaridade etc.) para leitura por público não técnico.

> Ambos começam com `%pip install awswrangler` seguido de `dbutils.library.restartPython()` — necessário para o `import awswrangler` funcionar.

---

## Resultados (referência rápida)

Árvore de Decisão no teste (2.178.359 candidatos, 30%): Acurácia **0,686** · Precisão **0,692** · Recall **0,672** · F1 **0,682** · **AUC-ROC 0,749**. Hierarquia de fatores: **Renda → Computador → Escolaridade dos pais** (mãe pesa na renda baixa; pai na renda alta).

---

## Dicionário de variáveis

Use **`docs/dicionario_enem.md`** (mapeamento corrigido de Q001–Q025). O dicionário preliminar do time estava deslocado a partir de Q003 — ver a nota de correção no próprio arquivo.

---

*Centro Universitário IESB · Tópicos de Banco de Dados · 2026 · Grupo 3*
