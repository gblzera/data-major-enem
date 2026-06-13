# Databricks notebook source
# MAGIC %md
# MAGIC # Configuração do Ambiente
# MAGIC 
# MAGIC Este notebook documenta a configuração do ambiente Databricks e a estrutura de pastas do projeto.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 1. Pré-requisitos
# MAGIC 
# MAGIC Antes de começar, certifique-se de que:
# MAGIC 
# MAGIC | # | Requisito | Status |
# MAGIC |---|-----------|--------|
# MAGIC | 1 | Você foi adicionado ao workspace do Databricks | ⬜ |
# MAGIC | 2 | Você consegue acessar a pasta `Workspace/Shared/project-data-major` | ⬜ |
# MAGIC | 3 | Você tem um cluster disponível para executar os notebooks | ⬜ |
# MAGIC | 4 | Você executou os testes de conexão com sucesso | ⬜ |
# MAGIC 
# MAGIC > **Problemas de acesso?** Entre em contato com o Tech Lead (Gabriel H. K. Paz).

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 2. Estrutura de Pastas no Databricks
# MAGIC 
# MAGIC ```
# MAGIC Workspace/
# MAGIC └── Shared/
# MAGIC     └── project-data-major/
# MAGIC         │
# MAGIC         ├── docs/
# MAGIC         │   ├── 00_guia_execucao.md
# MAGIC         │   ├── 01_detalhes_projeto.md
# MAGIC         │   ├── 02_pipeline.md
# MAGIC         │   ├── 03_integrantes.md
# MAGIC         │   ├── arquitetura.md
# MAGIC         │   └── dicionario_enem.md
# MAGIC         │
# MAGIC         └── notebooks/
# MAGIC             ├── config/
# MAGIC             │   ├── 04_config_ambiente.py       ← VOCÊ ESTÁ AQUI
# MAGIC             │   ├── 05_config_credenciais.py
# MAGIC             │   ├── 06_testes_conexao.py
# MAGIC             │   ├── 07_checklist_verificacao.py
# MAGIC             │   ├── 08_cronograma.py
# MAGIC             │   └── 09_recursos_uteis.py
# MAGIC             │
# MAGIC             ├── pipeline/
# MAGIC             │   ├── extract.py
# MAGIC             │   ├── transform_silver.py
# MAGIC             │   ├── transform_gold.py
# MAGIC             │   ├── load_parquet.py
# MAGIC             │   ├── load_postgresql.py
# MAGIC             │   ├── 05_mining_arvore.py
# MAGIC             │   ├── exemplo_config_aws_s3.py
# MAGIC             │   ├── exemplo_config_aws_rds.py
# MAGIC             │   └── exemplo_delete_s3.py
# MAGIC             │
# MAGIC             └── analysis/
# MAGIC                 ├── analysis.py
# MAGIC                 └── test_analysis.py
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 3. Estrutura de Pastas no S3
# MAGIC 
# MAGIC ```
# MAGIC s3://enem-data-lake-gblzera/
# MAGIC │
# MAGIC ├── bronze/
# MAGIC │   └── enem/
# MAGIC │       ├── 2021/
# MAGIC │       │   └── MICRODADOS_ENEM_2021.csv
# MAGIC │       ├── 2022/
# MAGIC │       │   └── MICRODADOS_ENEM_2022.csv
# MAGIC │       └── 2023/
# MAGIC │           └── MICRODADOS_ENEM_2023.csv
# MAGIC │
# MAGIC ├── silver/
# MAGIC │   └── enem/
# MAGIC │       ├── 2021/
# MAGIC │       │   └── microdados_silver_2021.csv
# MAGIC │       ├── 2022/
# MAGIC │       │   └── microdados_silver_2022.csv
# MAGIC │       └── 2023/
# MAGIC │           └── microdados_silver_2023.csv   (dados limpos, CSV por ano)
# MAGIC │
# MAGIC ├── gold/
# MAGIC │   └── enem/
# MAGIC │       ├── 2021/
# MAGIC │       │   └── GOLD_ENEM_2021.csv
# MAGIC │       ├── 2022/
# MAGIC │       │   └── GOLD_ENEM_2022.csv
# MAGIC │       └── 2023/
# MAGIC │           └── GOLD_ENEM_2023.csv            (features prontas, CSV por ano)
# MAGIC │
# MAGIC └── parquet/
# MAGIC     └── enem/
# MAGIC         └── (dataset final para mineração, Parquet via awswrangler, particionado por year)
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 4. Configuração do Cluster
# MAGIC 
# MAGIC ### Cluster Utilizado
# MAGIC
# MAGIC | Configuração | Valor |
# MAGIC |--------------|-------|
# MAGIC | **Edição** | Databricks Free / Community Edition |
# MAGIC | **Compute** | Apenas serverless (Spark Connect) — não há criação de cluster próprio |
# MAGIC | **Motor de processamento** | pandas + boto3/awswrangler (os dados cabem em memória) |
# MAGIC
# MAGIC > **Atenção:** nesta edição o Spark **não acessa o S3** (retorna erro 403). Toda leitura/escrita
# MAGIC > do data lake é feita via `boto3`/`awswrangler`/`pandas`, usando as chaves do Databricks Secrets
# MAGIC > (escopo `aws-credentials`). Helpers de Spark + S3 (`fs.s3a`, `spark.read` de `s3://...`) valem
# MAGIC > apenas como **referência** — o caminho real é pandas/boto3/awswrangler.
# MAGIC
# MAGIC ### Bibliotecas Necessárias
# MAGIC
# MAGIC Instale via `%pip` no início do notebook. Bibliotecas necessárias:
# MAGIC
# MAGIC | Biblioteca | Uso |
# MAGIC |------------|-----|
# MAGIC | `boto3` | Conexão com S3 |
# MAGIC | `awswrangler` | Leitura/escrita de CSV e Parquet no S3 |
# MAGIC | `pyarrow` (recente) | Engine de Parquet |
# MAGIC | `psycopg2-binary` + `sqlalchemy` | Conexão com PostgreSQL (RDS) |
# MAGIC | `scikit-learn` | Modelos de ML (Árvore de Decisão) |
# MAGIC | `matplotlib` | Visualizações |
# MAGIC | `seaborn` | Visualizações estatísticas |
# MAGIC
# MAGIC > Em alguns runtimes pode ser necessário fixar `numpy<2` para compatibilidade com o pandas instalado.

# COMMAND ----------

# Verificar bibliotecas instaladas
import sys
print(f"Python version: {sys.version}")

# Verificar pandas (motor principal de processamento)
try:
    import pandas
    print(f"pandas version: {pandas.__version__}")
except ImportError:
    print("pandas: NÃO INSTALADO")

# Verificar boto3
try:
    import boto3
    print(f"boto3 version: {boto3.__version__}")
except ImportError:
    print("boto3: NÃO INSTALADO - executar: %pip install boto3")

# Verificar awswrangler (leitura/escrita S3 e Parquet)
try:
    import awswrangler
    print(f"awswrangler version: {awswrangler.__version__}")
except ImportError:
    print("awswrangler: NÃO INSTALADO - executar: %pip install awswrangler")

# Verificar pyarrow (engine de Parquet)
try:
    import pyarrow
    print(f"pyarrow version: {pyarrow.__version__}")
except ImportError:
    print("pyarrow: NÃO INSTALADO - executar: %pip install pyarrow")

# Verificar psycopg2
try:
    import psycopg2
    print(f"psycopg2 version: {psycopg2.__version__}")
except ImportError:
    print("psycopg2: NÃO INSTALADO - executar: %pip install psycopg2-binary")

# Verificar scikit-learn
try:
    import sklearn
    print(f"scikit-learn version: {sklearn.__version__}")
except ImportError:
    print("scikit-learn: NÃO INSTALADO - executar: %pip install scikit-learn")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Instalar Bibliotecas (se necessário)
# MAGIC 
# MAGIC Execute a célula abaixo apenas se alguma biblioteca estiver faltando:

# COMMAND ----------

# Descomente as linhas necessárias:

# %pip install boto3
# %pip install awswrangler pyarrow
# %pip install psycopg2-binary sqlalchemy
# %pip install scikit-learn
# %pip install matplotlib seaborn
# %pip install "numpy<2"   # apenas se o pandas do runtime exigir

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 5. Variáveis de Ambiente
# MAGIC 
# MAGIC As seguintes variáveis são utilizadas em todo o projeto:

# COMMAND ----------

# ╔══════════════════════════════════════════════════════════════════════╗
# ║                     VARIÁVEIS DO PROJETO                             ║
# ║              (Referência - não execute, apenas consulte)             ║
# ╚══════════════════════════════════════════════════════════════════════╝

# --- Configurações do S3 ---
BUCKET_NAME = "enem-data-lake-gblzera"
REGION = "sa-east-1"

# --- Paths no S3 (acesso real via boto3/awswrangler/pandas, prefixo s3://) ---
S3_BRONZE_PATH = f"s3://{BUCKET_NAME}/bronze/enem"
S3_SILVER_PATH = f"s3://{BUCKET_NAME}/silver/enem"
S3_GOLD_PATH = f"s3://{BUCKET_NAME}/gold/enem"
S3_PARQUET_PATH = f"s3://{BUCKET_NAME}/parquet/enem"  # Parquet final (awswrangler, particionado por year)

# --- Configurações do RDS ---
RDS_DATABASE = "enem_db"
RDS_PORT = 5432
# load_postgresql.py grava a tabela 'microdados' nos schemas raw/tru/ref (bronze/silver/gold)
RDS_TABLE = "microdados"

# --- Anos do ENEM ---
ANOS_ENEM = [2021, 2022, 2023]

# --- Colunas a extrair (CONJUNTO COGITADO — referência, não corresponde 1:1 à Gold entregue) ---
# NOTA: este é o conjunto amplo originalmente cogitado para extração, incluindo features
# demográficas/escola/presença. A camada Gold efetivamente entregue para a mineração contém
# apenas Q001-Q025 + NOTA_MEDIA + TARGET. As demográficas ficaram como planejado/referência.
COLUNAS_ENEM = [
    # Identificação
    "NU_ANO", "NU_INSCRICAO",
    # Demográficas (planejado/referência — não estão na Gold final)
    "TP_SEXO", "TP_COR_RACA", "NU_IDADE", "SG_UF_PROVA", "CO_MUNICIPIO_PROVA",
    # Escola (planejado/referência — não estão na Gold final)
    "TP_ESCOLA", "TP_DEPENDENCIA_ADM_ESC",
    # Presença
    "TP_PRESENCA_CN", "TP_PRESENCA_CH", "TP_PRESENCA_LC", "TP_PRESENCA_MT",
    # Notas
    "NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT", "NU_NOTA_REDACAO",
    # Questionário socioeconômico
    "Q001", "Q002", "Q003", "Q004", "Q005",
    "Q006", "Q007", "Q008", "Q009", "Q010",
    "Q011", "Q012", "Q013", "Q014", "Q015",
    "Q016", "Q017", "Q018", "Q019", "Q020",
    "Q021", "Q022", "Q023", "Q024", "Q025"
]

print("Variáveis de referência carregadas!")
print(f"Total de colunas no conjunto cogitado: {len(COLUNAS_ENEM)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 6. Próximos Passos
# MAGIC 
# MAGIC Após verificar este notebook:
# MAGIC 
# MAGIC 1. **Execute** o notebook `05_config_credenciais.py` para carregar as credenciais
# MAGIC 2. **Execute** o notebook `06_testes_conexao.py` para validar S3 e RDS
# MAGIC 3. **Verifique** o notebook `07_checklist_verificacao.py` para confirmar que está tudo OK
# MAGIC 4. **Consulte** o notebook `08_cronograma.py` para ver os prazos
# MAGIC 5. **Comece** a trabalhar no seu notebook de responsabilidade!

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC 
# MAGIC **Última atualização:** 2026-06-13
# MAGIC **Mantido por:** Tech Lead (Gabriel H. K. Paz)