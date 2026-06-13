# Arquitetura do Projeto Data Major

## Visão geral

O projeto adota a **arquitetura Medallion** (multi-hop), padrão de organização de dados em camadas de qualidade crescente, executada sobre **AWS S3** (armazenamento) e **Databricks / Apache Spark** (processamento).

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────────────────┐
│  INEP    │──▶│  BRONZE  │──▶│  SILVER  │──▶│   GOLD   │──▶│  PARQUET / PostgreSQL │
│  (.zip)  │   │  bruto   │   │  limpo   │   │  pronto  │   │   camada de consumo   │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └─────────────────────┘
   fonte         01_extract     02_silver      03_gold          04_load → 05_mining
```

## Camadas

### Bronze — dado bruto
Microdados do INEP carregados exatamente como obtidos, sem transformação. Armazenados em `s3://enem-data-lake-gblzera/bronze/enem/{ano}/`.

### Silver — dado limpo
- Filtro de presença: apenas candidatos presentes nas 4 provas objetivas (`TP_PRESENCA = 1`)
- Conversão de tipos e remoção de notas inválidas
- Tratamento de nulos: categóricas → "Não informado"; Q005 (numérica) → sentinela `-1`
- Remoção de duplicatas por inscrição + ano
- Saída: `s3://enem-data-lake-gblzera/silver/enem/` (Parquet particionado por ano)

### Gold — dado pronto para análise
- `NOTA_MEDIA`: média aritmética das 5 provas
- `TARGET`: binária — `1` se `NOTA_MEDIA ≥ mediana` (536,0), senão `0`
- Questionário mantido em forma original (encoding feito na mineração)
- Saída: `s3://enem-data-lake-gblzera/gold/enem/`

### Consumo — Parquet + PostgreSQL
- **Parquet consolidado** particionado por ano (~59 MB), fonte da mineração
- **PostgreSQL (RDS)**: carga relacional complementar (em andamento)

## Decisões arquiteturais e justificativas

| Decisão | Justificativa |
|---------|---------------|
| AWS S3 como data lake | Object storage barato e escalável; separa armazenamento de computação |
| Databricks + Spark | Processamento distribuído essencial para 7,26M de registros |
| Parquet (formato final) | Colunar e comprimido: lê só as colunas necessárias; 59 MB vs GBs de CSV |
| Particionamento por ano | Consultas por edição leem só a partição correspondente |
| PostgreSQL complementar | Prática de modelagem relacional (não exigido pelo escopo) |
| Encoding na mineração | Mantém a Gold legível e flexível a diferentes técnicas |

## Stack

- **Armazenamento:** AWS S3
- **Processamento:** Databricks, Apache Spark (PySpark)
- **Formato analítico:** Apache Parquet
- **Banco relacional:** PostgreSQL (RDS)
- **Mineração:** scikit-learn (Árvore de Decisão)
- **Estatística:** SciPy (Spearman)
- **Credenciais:** Databricks Secrets (escopo `aws-credentials`)
