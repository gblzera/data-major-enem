# Projeto Data Major — Arquitetura do Pipeline

Arquitetura **Medallion** (Bronze → Silver → Gold → consumo) no **Databricks**, com armazenamento no **AWS S3** e carga relacional complementar no **AWS RDS PostgreSQL**. O processamento é em **pandas** (`boto3`/`awswrangler`), não PySpark.

```
INEP (.zip)
   │  extract.py
   ▼
S3 BRONZE (CSV)  ── transform_silver.py ──▶  S3 SILVER (CSV)  ── transform_gold.py ──▶  S3 GOLD (CSV)
                                                                                           │ load_parquet.py
                                                          ┌────────────────────────────────┤
                                                          ▼                                ▼
                                                 S3 PARQUET (parquet/enem/)        RDS PostgreSQL (opcional)
                                                 particionado por year             load_postgresql.py
                                                          │
                                                          │ 05_mining_arvore.py
                                                          ▼
                                                 Árvore de Decisão + métricas
```

---

## 1. Por que pandas (e não PySpark)?

Os dados cabem na memória do driver: ~2,2–2,7M linhas por edição (≈7,26M no total), e o Parquet final tem ~50 MB. Para esse volume, pandas + `awswrangler` é simples e suficiente; o Spark distribuído seria over-engineering. Além disso, no Databricks **Free/Community Edition** o cluster é apenas serverless e o Spark **não acessa o S3** diretamente (erro 403) — a leitura/escrita é feita via `boto3`/`awswrangler` com as credenciais do Databricks Secrets.

---

## 2. Componentes

| Componente | Detalhe |
|------------|---------|
| **Fonte (INEP)** | ZIP com CSV; encoding latin-1; separador `;`; anos 2021–2023 |
| **Data Lake (S3)** | Bucket `enem-data-lake-gblzera`, região `sa-east-1` |
| **RDS (PostgreSQL)** | Banco `enem_db`; carga **opcional** (liga/desliga por custo) |
| **Processamento** | Databricks serverless + pandas / boto3 / awswrangler |
| **Credenciais** | Databricks Secrets, escopo `aws-credentials` |

---

## 3. Camadas

### Bronze — dado bruto (CSV)
- `extract.py` baixa o `.zip` do INEP e sobe `MICRODADOS_ENEM_{ano}.csv` em streaming para `bronze/enem/{ano}/` (sem disco local).

### Silver — dado limpo (CSV)
- Filtro de presença nas 4 provas (`TP_PRESENCA_* = 1`); nulos categóricos → "Não informado"; Q005 (numérica) → `-1`; remoção de duplicatas por inscrição + ano.
- Saída: `silver/enem/{ano}/microdados_silver_{ano}.csv`.

### Gold — features (CSV)
- `NOTA_MEDIA` (média das 5 provas) e `TARGET` (`1` se `NOTA_MEDIA ≥ mediana do ano`). 27 colunas: Q001–Q025 + NOTA_MEDIA + TARGET. **Encoding não é feito aqui** — fica na mineração.
- Saída: `gold/enem/{ano}/GOLD_ENEM_{ano}.csv`.

### Consumo — Parquet + PostgreSQL
- **Parquet:** `load_parquet.py` une os 3 CSVs da Gold em `parquet/enem/` (`awswrangler`, zstd, particionado por `year`, ~50 MB) — fonte da mineração.
- **PostgreSQL:** `load_postgresql.py` (opcional) carrega bronze/silver/gold nos schemas `raw`/`tru`/`ref` (tabela `microdados`), lendo os CSVs do S3 em chunks.

---

## 4. Estrutura no S3

```
enem-data-lake-gblzera/
├── bronze/enem/{ano}/MICRODADOS_ENEM_{ano}.csv
├── silver/enem/{ano}/microdados_silver_{ano}.csv
├── gold/enem/{ano}/GOLD_ENEM_{ano}.csv
└── parquet/enem/year={2021,2022,2023}/*.parquet   (Parquet final, zstd)
```

---

## 5. Tecnologias e justificativas

| Decisão | Justificativa |
|---------|---------------|
| AWS S3 como data lake | Object storage barato; separa armazenamento de computação |
| pandas (não Spark) | Dados cabem em memória; serverless da Free Edition não dá acesso S3 ao Spark |
| boto3 / awswrangler | Acesso ao S3 com as chaves do Secrets (streaming na Bronze; Parquet na consumo) |
| Parquet na consumo | Colunar e comprimido (~50 MB vs GBs de CSV); particionado por `year` |
| PostgreSQL complementar | Prática de modelagem relacional; não exigido pelo escopo |
| Encoding na mineração | Mantém a Gold legível e flexível a diferentes técnicas |

---

**Última atualização:** 2026-06-13 · **Autor:** Grupo 3 — Projeto Data Major
