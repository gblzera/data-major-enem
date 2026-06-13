# Data Major — Determinantes Socioeconômicos do Desempenho no ENEM

Pipeline completo de Engenharia e Mineração de Dados sobre os microdados do ENEM (2021–2023), construído com arquitetura Medallion na nuvem. O projeto investiga, a partir do questionário socioeconômico de 7,26 milhões de candidatos, **quais fatores mais influenciam o desempenho na prova — e se é possível prevê-lo**.

> Projeto acadêmico da disciplina de Tópicos de Banco de Dados — Centro Universitário IESB, 2026.

---

## Pergunta de negócio

> O perfil socioeconômico do candidato permite prever se sua nota fica acima ou abaixo da mediana? E quais fatores mais pesam nesse resultado?

**Resposta:** sim, é possível prever (AUC-ROC de 0,747), mas a condição socioeconômica não determina o desempenho por completo. Renda, acesso a computador e escolaridade dos pais lideram — confirmados por duas técnicas independentes (correlação de Spearman e árvore de decisão).

---

## Arquitetura

O projeto adota a **arquitetura Medallion**, organizando os dados em camadas de qualidade crescente sobre AWS S3 e Databricks (Apache Spark):

```
INEP (.zip)  →  BRONZE      →  SILVER       →  GOLD            →  PARQUET / PostgreSQL
  fonte         dado bruto     dado limpo      pronto p/ análise   camada de consumo
                (CSV)          (filtros +      (NOTA_MEDIA +       (colunar, 59 MB,
                                tratamento)     TARGET)             particionado por ano)
```

| Camada | Conteúdo | Tecnologia |
|--------|----------|------------|
| **Bronze** | Microdados brutos do INEP, sem alteração | AWS S3 |
| **Silver** | Filtro de presença, tratamento de nulos | PySpark |
| **Gold** | Feature engineering, variável-alvo | PySpark |
| **Consumo** | Parquet particionado + PostgreSQL | Parquet / PostgreSQL |

---

## Stack técnico

- **Armazenamento:** AWS S3 (data lake)
- **Processamento:** Databricks + Apache Spark (PySpark)
- **Formato analítico:** Apache Parquet (colunar, comprimido)
- **Banco relacional:** PostgreSQL (RDS) — carga complementar
- **Mineração / ML:** scikit-learn (Árvore de Decisão)
- **Estatística:** SciPy (correlação de Spearman)
- **Versionamento:** Git + Databricks Repos

---

## Estrutura do repositório

```
data-major-enem/
├── notebooks/                 # Pipeline na ordem de execução
│   ├── 01_extract.py          # Coleta automatizada INEP → S3 (Bronze)
│   ├── 02_transform_silver.py # Limpeza e tratamento de nulos (Silver)
│   ├── 03_transform_gold.py   # Feature engineering e target (Gold)
│   ├── 04_load_parquet.py     # Consolidação em Parquet + PostgreSQL
│   └── 05_mining_arvore.py    # Mineração: Spearman + Árvore de Decisão
├── docs/
│   ├── dicionario_enem.md     # Dicionário de variáveis (corrigido)
│   └── arquitetura.md         # Detalhamento da arquitetura
├── dashboard/
│   └── dashboard_executivo.html  # Painel executivo dos resultados
├── .gitignore
└── README.md
```

---

## Pipeline (ETL → Mineração)

### 1. Extract
Script automatizado baixa os arquivos `.zip` de cada edição do INEP e os carrega na camada Bronze do S3. Trata a identificação do CSV correto de microdados dentro do compactado.

### 2. Transform — Silver
- Filtro de presença: mantém apenas candidatos presentes nas 4 provas objetivas (de ~3,4M para ~2,2M por edição)
- Tratamento de nulos: questões categóricas recebem "Não informado"; `Q005` (numérica) recebe sentinela `-1`
- Remoção de duplicatas por inscrição e ano

### 3. Transform — Gold
- `NOTA_MEDIA`: média aritmética das 5 provas
- `TARGET`: binária — `1` se `NOTA_MEDIA ≥ mediana` (536,0), senão `0`. Classes balanceadas (50,1% / 49,9%)
- Encoding ordinal das variáveis categóricas (preserva a ordem natural)

### 4. Load
Consolidação em Parquet único particionado por ano (59 MB) e carga complementar em PostgreSQL.

### 5. Mineração
- **Estatística:** correlação de Spearman de cada variável com a nota
- **Modelo:** Árvore de Decisão (critério de entropia, `max_depth=6`, classes balanceadas), split estratificado 70/30

---

## Resultados

Métricas da Árvore de Decisão no conjunto de teste (2.178.359 registros):

| Métrica | Valor |
|---------|-------|
| Acurácia | 0,685 |
| Precisão | 0,692 |
| Recall | 0,671 |
| F1-Score | 0,681 |
| AUC-ROC | 0,747 |

**Hierarquia de fatores aprendida pela árvore:** Renda da família → Acesso a computador → Escolaridade dos pais (mãe pesa mais na renda baixa; pai na renda alta).

---

## Reprodução

1. Configure as credenciais AWS como **Secrets** no Databricks (escopo `aws-credentials`, chaves `access-key` e `secret-key`)
2. Conecte este repositório via **Databricks Repos**
3. Execute os notebooks de `notebooks/` na ordem numérica (01 → 05)

> Os microdados não estão versionados (são públicos e pesados). Baixe-os em [dados abertos do INEP](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem).

---

## Limitações e próximos passos

- **Limitações:** a target pela mediana cria uma zona de fronteira; o questionário isolado impõe um teto de previsibilidade; tuning feito em subamostra.
- **Próximos passos:** comparação com ensembles (Extra Trees, Gradient Boosting) + teste de significância; clustering de perfis (K-Means); análise temporal 2021–2023.

---

## Equipe

| Responsabilidade | Integrante |
|------------------|------------|
| Extract | Davi |
| Transform | Bruno |
| Load | Vinícius |
| Mineração / Tech Lead | Gabriel |

---

*Centro Universitário IESB · Tópicos de Banco de Dados · 2026*
