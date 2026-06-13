# Data Major — Determinantes Socioeconômicos do Desempenho no ENEM

Pipeline completo de Engenharia e Mineração de Dados sobre os microdados do ENEM (2021–2023), construído com arquitetura Medallion na nuvem. O projeto investiga, a partir do questionário socioeconômico de 7,26 milhões de candidatos, **quais fatores mais influenciam o desempenho na prova — e se é possível prevê-lo**.

> Projeto acadêmico da disciplina de Tópicos de Banco de Dados — Centro Universitário IESB, 2026.

---

## Pergunta de negócio

> O perfil socioeconômico do candidato permite prever se sua nota fica acima ou abaixo da mediana? E quais fatores mais pesam nesse resultado?

**Resposta:** sim, é possível prever (AUC-ROC de 0,749), mas a condição socioeconômica não determina o desempenho por completo. Renda, acesso a computador e escolaridade dos pais lideram — confirmados por duas técnicas independentes (correlação de Spearman e árvore de decisão).

---

## Arquitetura

O projeto adota a **arquitetura Medallion**, organizando os dados em camadas de qualidade crescente sobre AWS S3 e Databricks. O processamento é feito em **pandas** (com `boto3`/`awswrangler` para o S3) — os volumes por edição cabem na memória do driver, então o Spark distribuído não foi necessário.

```
INEP (.zip)  →  BRONZE      →  SILVER       →  GOLD            →  PARQUET / PostgreSQL
  fonte         dado bruto     dado limpo      pronto p/ análise   camada de consumo
                (CSV)          (CSV)           (CSV)               (Parquet ~50 MB,
                                                                   particionado por year)
```

| Camada | Conteúdo | Formato | Tecnologia |
|--------|----------|---------|------------|
| **Bronze** | Microdados brutos do INEP, sem alteração | CSV | boto3 (streaming) → S3 |
| **Silver** | Filtro de presença, tratamento de nulos | CSV | pandas |
| **Gold** | Feature engineering, variável-alvo | CSV | pandas |
| **Consumo** | Parquet particionado por ano + PostgreSQL | Parquet / SQL | awswrangler / psycopg2 |

---

## Stack técnico

- **Armazenamento:** AWS S3 (data lake)
- **Processamento:** Databricks + **pandas** (`boto3`/`awswrangler` para o S3). O Spark foi avaliado, mas dispensado — os dados cabem na memória do driver (~2,4M linhas por edição).
- **Formato analítico:** Apache Parquet (colunar, comprimido) na camada de consumo
- **Banco relacional:** PostgreSQL (RDS) — carga complementar
- **Mineração / ML:** scikit-learn (Árvore de Decisão)
- **Estatística:** SciPy (correlação de Spearman)
- **Versionamento:** Git + Databricks Repos

---

## Estrutura do repositório

```
data-major-enem/
├── notebooks/
│   ├── pipeline/                  # ETL + mineração (ordem de execução)
│   │   ├── extract.py             # Coleta INEP → S3 (Bronze)
│   │   ├── transform_silver.py    # Limpeza e tratamento de nulos (Silver)
│   │   ├── transform_gold.py      # Feature engineering e target (Gold)
│   │   ├── load_parquet.py        # Consolida a Gold em Parquet (camada de consumo)
│   │   ├── load_postgresql.py     # Carga complementar no PostgreSQL (RDS)
│   │   ├── 05_mining_arvore.py    # Mineração: Spearman + Árvore de Decisão
│   │   └── exemplo_*.py           # Utilitários (config AWS S3/RDS, limpeza S3)
│   ├── config/                    # Apoio: ambiente, credenciais, testes, checklist, cronograma
│   └── analysis/                  # Análise exploratória (analysis.py, test_analysis.py)
├── docs/
│   ├── 00_guia_execucao.md        # Guia de execução dos notebooks
│   ├── 01_detalhes_projeto.md     # Detalhes e objetivo do projeto
│   ├── 02_pipeline.md             # Arquitetura do pipeline
│   ├── 03_integrantes.md          # Integrantes e responsabilidades
│   ├── arquitetura.md             # Detalhamento da arquitetura
│   └── dicionario_enem.md         # Dicionário de variáveis (corrigido)
├── dashboard/
│   └── dashboard_executivo.html   # Painel executivo dos resultados
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Pipeline (ETL → Mineração)

### 1. Extract
Script automatizado baixa os arquivos `.zip` de cada edição do INEP e os carrega na camada Bronze do S3. Trata a identificação do CSV correto de microdados dentro do compactado.

### 2. Transform — Silver
- Filtro de presença: mantém apenas candidatos presentes nas 4 provas objetivas (de ~3,4–3,9M para ~2,2–2,7M por edição; **7.261.194** no total)
- Tratamento de nulos: questões categóricas recebem "Não informado"; `Q005` (numérica) recebe sentinela `-1`
- Remoção de duplicatas por inscrição e ano

### 3. Transform — Gold
- `NOTA_MEDIA`: média aritmética das 5 provas
- `TARGET`: binária — `1` se `NOTA_MEDIA ≥ mediana **do ano**`, senão `0`. Medianas por edição: 2021 ≈ 527,3 · 2022 ≈ 540,5 · 2023 ≈ 539,2 (mediana global ≈ 536,0). Classes balanceadas (≈ 50% / 50%)
- Questionário mantido em forma original — o encoding **não** é feito aqui, e sim na etapa de mineração (mantém a Gold legível e flexível a diferentes técnicas de codificação)

### 4. Load
O `load_parquet` consolida os três CSVs da Gold em um Parquet único (via `awswrangler`, compressão zstd, ~50 MB, particionado por `year`) — a fonte da mineração. O `load_postgresql` faz a carga complementar no PostgreSQL (RDS).

### 5. Mineração
- **Estatística:** correlação de Spearman de cada variável com a nota
- **Codificação:** encoding ordinal das variáveis categóricas (preserva a ordem natural) — aplicado aqui, não na Gold
- **Modelo:** Árvore de Decisão (critério de entropia, `max_depth=6`, classes balanceadas), split estratificado 70/30

---

## Resultados

Métricas da Árvore de Decisão no conjunto de teste (2.178.359 registros):

| Métrica | Valor |
|---------|-------|
| Acurácia | 0,686 |
| Precisão | 0,692 |
| Recall | 0,672 |
| F1-Score | 0,682 |
| AUC-ROC | 0,749 |

**Hierarquia de fatores aprendida pela árvore:** Renda da família → Acesso a computador → Escolaridade dos pais (mãe pesa mais na renda baixa; pai na renda alta).

---

## Reprodução

1. Configure as credenciais AWS como **Secrets** no Databricks (escopo `aws-credentials`, chaves `access-key` e `secret-key`)
2. Conecte este repositório via **Databricks Repos**
3. Execute os notebooks de `notebooks/pipeline/` na ordem: `extract` → `transform_silver` → `transform_gold` → `load_parquet` → `05_mining_arvore` (a carga `load_postgresql` é opcional)

> Os microdados não estão versionados (são públicos e pesados). Baixe-os em [dados abertos do INEP](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem).

---

## Limitações e próximos passos

- **Limitações:** a target pela mediana cria uma zona de fronteira; o questionário socioeconômico isolado impõe um teto de previsibilidade (~0,75 de AUC); a Árvore usa hiperparâmetros fixos (sem tuning extensivo).
- **Próximos passos:** comparação com ensembles (Extra Trees, Gradient Boosting) + teste de significância; clustering de perfis (K-Means); análise temporal 2021–2023.

---

## Equipe

| Responsabilidade | Integrante |
|------------------|------------|
| Extract | Davi Serra Bezerra |
| Transform (Silver + Gold) | Bruno Brudó |
| Load | Vinicius von Glehn Severo |
| Mineração | Gabriel dos Santos Silva |
| Tech Lead | Gabriel Henrique Kuhn Paz |

---

*Centro Universitário IESB · Tópicos de Banco de Dados · 2026*
