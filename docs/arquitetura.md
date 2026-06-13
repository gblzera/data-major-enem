# Arquitetura do Projeto Data Major

## Visão geral

O projeto adota a **arquitetura Medallion** (multi-hop), padrão de organização de dados em camadas de qualidade crescente, executada sobre **AWS S3** (armazenamento) e **Databricks** com processamento em **pandas** (`boto3`/`awswrangler` para o S3). O Spark foi avaliado, mas dispensado — os volumes por edição (~2,4M linhas) cabem na memória do driver.

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────────────────┐
│  INEP    │──▶│  BRONZE  │──▶│  SILVER  │──▶│   GOLD   │──▶│  PARQUET / PostgreSQL │
│  (.zip)  │   │  CSV     │   │  CSV     │   │  CSV     │   │   camada de consumo   │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └─────────────────────┘
   fonte         extract     transform_silver  transform_gold  load_parquet → 05_mining_arvore
```

## Camadas

### Bronze — dado bruto
Microdados do INEP carregados exatamente como obtidos, sem transformação. O `extract` baixa o `.zip` do INEP e sobe o CSV para `s3://enem-data-lake-gblzera/bronze/enem/{ano}/MICRODADOS_ENEM_{ano}.csv` (streaming via boto3, sem gravar em disco local).

### Silver — dado limpo
- Filtro de presença: apenas candidatos presentes nas 4 provas objetivas (`TP_PRESENCA = 1`)
- Tratamento de nulos: categóricas → "Não informado"; Q005 (numérica) → sentinela `-1`
- Remoção de duplicatas por inscrição + ano
- Saída: `s3://enem-data-lake-gblzera/silver/enem/{ano}/microdados_silver_{ano}.csv` (CSV por ano)

### Gold — dado pronto para análise
- `NOTA_MEDIA`: média aritmética das 5 provas
- `TARGET`: binária — `1` se `NOTA_MEDIA ≥ mediana do ano` (2021 ≈ 527,3 · 2022 ≈ 540,5 · 2023 ≈ 539,2; global ≈ 536,0), senão `0`
- Questionário mantido em forma original (encoding feito na mineração)
- Saída: `s3://enem-data-lake-gblzera/gold/enem/{ano}/GOLD_ENEM_{ano}.csv` (CSV por ano; 27 colunas: Q001–Q025 + NOTA_MEDIA + TARGET)

### Consumo — Parquet + PostgreSQL
- **Parquet consolidado** em `parquet/enem/` — `load_parquet` une os 3 CSVs da Gold via `awswrangler` (zstd, ~50 MB, particionado por `year`); é a fonte da mineração
- **PostgreSQL (RDS)**: carga relacional complementar (`load_postgresql`, opcional — liga/desliga a instância por custo)

## Decisões arquiteturais e justificativas

| Decisão | Justificativa |
|---------|---------------|
| AWS S3 como data lake | Object storage barato e escalável; separa armazenamento de computação |
| Databricks + pandas | Os dados cabem na memória do driver (~2,4M linhas/edição); Spark distribuído seria over-engineering para este volume |
| Parquet na camada de consumo | Colunar e comprimido: ~50 MB vs GBs de CSV; lido pela mineração via awswrangler |
| Particionamento por ano (`year`) | Consultas por edição leem só a partição correspondente |
| PostgreSQL complementar | Prática de modelagem relacional (não exigido pelo escopo) |
| Encoding na mineração | Mantém a Gold legível e flexível a diferentes técnicas |

## Stack

- **Armazenamento:** AWS S3
- **Processamento:** Databricks + pandas (`boto3`/`awswrangler` para o S3)
- **Formato analítico:** Apache Parquet (camada de consumo)
- **Banco relacional:** PostgreSQL (RDS)
- **Mineração:** scikit-learn (Árvore de Decisão)
- **Estatística:** correlação de Spearman via pandas (`rank` + `corrwith`)
- **Credenciais:** Databricks Secrets (escopo `aws-credentials`)
