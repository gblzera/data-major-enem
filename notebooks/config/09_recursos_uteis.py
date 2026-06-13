# Databricks notebook source
# MAGIC %md
# MAGIC # Recursos Úteis
# MAGIC 
# MAGIC Este notebook reúne links, referências e materiais de apoio para o projeto.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 1. Dataset — INEP/ENEM
# MAGIC 
# MAGIC ### Links Oficiais
# MAGIC 
# MAGIC | Recurso | Link |
# MAGIC |---------|------|
# MAGIC | **Microdados ENEM** | [gov.br/inep/microdados/enem](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem) |
# MAGIC | **Dicionário de Dados** | Incluído no ZIP de cada ano |
# MAGIC | **Questionário Socioeconômico** | Incluído no ZIP (INPUT_ENEM) |
# MAGIC 
# MAGIC ### Downloads Diretos (2021-2023)
# MAGIC 
# MAGIC | Ano | Tamanho Aprox. | Link |
# MAGIC |-----|----------------|------|
# MAGIC | 2021 | ~2GB | [Download](https://download.inep.gov.br/microdados/microdados_enem_2021.zip) |
# MAGIC | 2022 | ~2GB | [Download](https://download.inep.gov.br/microdados/microdados_enem_2022.zip) |
# MAGIC | 2023 | ~2GB | [Download](https://download.inep.gov.br/microdados/microdados_enem_2023.zip) |

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 2. Colunas do ENEM a Extrair
# MAGIC 
# MAGIC ### Identificação
# MAGIC 
# MAGIC | Coluna | Descrição | Tipo |
# MAGIC |--------|-----------|------|
# MAGIC | `NU_ANO` | Ano do ENEM | INT |
# MAGIC | `NU_INSCRICAO` | Número de inscrição | BIGINT |
# MAGIC 
# MAGIC ### Dados Demográficos
# MAGIC 
# MAGIC | Coluna | Descrição | Tipo |
# MAGIC |--------|-----------|------|
# MAGIC | `TP_SEXO` | Sexo (M/F) | CHAR(1) |
# MAGIC | `TP_COR_RACA` | Cor/Raça declarada | INT |
# MAGIC | `NU_IDADE` | Idade do candidato | INT |
# MAGIC | `SG_UF_PROVA` | UF onde fez a prova | CHAR(2) |
# MAGIC | `CO_MUNICIPIO_PROVA` | Código do município | INT |
# MAGIC 
# MAGIC ### Dados da Escola
# MAGIC 
# MAGIC | Coluna | Descrição | Tipo |
# MAGIC |--------|-----------|------|
# MAGIC | `TP_ESCOLA` | Tipo de escola (pública/privada) | INT |
# MAGIC | `TP_DEPENDENCIA_ADM_ESC` | Dependência administrativa | INT |
# MAGIC 
# MAGIC ### Presença nas Provas
# MAGIC 
# MAGIC | Coluna | Descrição | Valores |
# MAGIC |--------|-----------|---------|
# MAGIC | `TP_PRESENCA_CN` | Presença em Ciências da Natureza | 0=Faltou, 1=Presente, 2=Eliminado |
# MAGIC | `TP_PRESENCA_CH` | Presença em Ciências Humanas | 0=Faltou, 1=Presente, 2=Eliminado |
# MAGIC | `TP_PRESENCA_LC` | Presença em Linguagens | 0=Faltou, 1=Presente, 2=Eliminado |
# MAGIC | `TP_PRESENCA_MT` | Presença em Matemática | 0=Faltou, 1=Presente, 2=Eliminado |
# MAGIC 
# MAGIC ### Notas
# MAGIC 
# MAGIC | Coluna | Descrição | Range |
# MAGIC |--------|-----------|-------|
# MAGIC | `NU_NOTA_CN` | Nota em Ciências da Natureza | 0-1000 |
# MAGIC | `NU_NOTA_CH` | Nota em Ciências Humanas | 0-1000 |
# MAGIC | `NU_NOTA_LC` | Nota em Linguagens | 0-1000 |
# MAGIC | `NU_NOTA_MT` | Nota em Matemática | 0-1000 |
# MAGIC | `NU_NOTA_REDACAO` | Nota na Redação | 0-1000 |
# MAGIC 
# MAGIC ### Questionário Socioeconômico
# MAGIC 
# MAGIC | Colunas | Descrição |
# MAGIC |---------|-----------|
# MAGIC | `Q001` | Escolaridade do pai |
# MAGIC | `Q002` | Escolaridade da mãe |
# MAGIC | `Q003` | Ocupação do pai |
# MAGIC | `Q004` | Ocupação da mãe |
# MAGIC | `Q005` | Quantidade de pessoas no domicílio |
# MAGIC | `Q006` | Renda mensal familiar |
# MAGIC | `Q007` | Possui empregada doméstica |
# MAGIC | `Q008` | Quantidade de banheiros |
# MAGIC | `Q009` | Quantidade de quartos |
# MAGIC | `Q010` | Quantidade de carros |
# MAGIC | `Q011` | Possui motocicleta |
# MAGIC | `Q012` | Possui geladeira |
# MAGIC | `Q013` | Possui freezer |
# MAGIC | `Q014` | Possui máquina de lavar |
# MAGIC | `Q015` | Possui secadora |
# MAGIC | `Q016` | Possui micro-ondas |
# MAGIC | `Q017` | Possui lava-louças |
# MAGIC | `Q018` | Possui aspirador |
# MAGIC | `Q019` | Possui TV |
# MAGIC | `Q020` | Possui DVD |
# MAGIC | `Q021` | Possui TV por assinatura |
# MAGIC | `Q022` | Possui celular |
# MAGIC | `Q023` | Possui telefone fixo |
# MAGIC | `Q024` | Possui computador |
# MAGIC | `Q025` | Possui internet |

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 3. Documentação Técnica
# MAGIC 
# MAGIC ### Databricks
# MAGIC 
# MAGIC | Recurso | Link |
# MAGIC |---------|------|
# MAGIC | Documentação oficial | [docs.databricks.com](https://docs.databricks.com/) |
# MAGIC | Databricks Secrets | [Managing Secrets](https://docs.databricks.com/en/security/secrets/index.html) |
# MAGIC | Conectar ao S3 | [Connect to S3](https://docs.databricks.com/en/connect/storage/amazon-s3.html) |
# MAGIC | Conectar ao PostgreSQL | [JDBC Connection](https://docs.databricks.com/en/connect/external-systems/postgresql.html) |
# MAGIC 
# MAGIC ### PySpark
# MAGIC 
# MAGIC | Recurso | Link |
# MAGIC |---------|------|
# MAGIC | SQL Guide | [spark.apache.org/sql-guide](https://spark.apache.org/docs/latest/sql-programming-guide.html) |
# MAGIC | DataFrame API | [DataFrame Reference](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/dataframe.html) |
# MAGIC | Parquet | [Parquet Files](https://spark.apache.org/docs/latest/sql-data-sources-parquet.html) |
# MAGIC 
# MAGIC ### AWS
# MAGIC 
# MAGIC | Recurso | Link |
# MAGIC |---------|------|
# MAGIC | boto3 (Python SDK) | [boto3.amazonaws.com](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) |
# MAGIC | S3 User Guide | [S3 Documentation](https://docs.aws.amazon.com/s3/) |
# MAGIC | RDS PostgreSQL | [RDS Documentation](https://docs.aws.amazon.com/rds/) |

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 4. Machine Learning
# MAGIC 
# MAGIC ### Scikit-learn
# MAGIC 
# MAGIC | Recurso | Link |
# MAGIC |---------|------|
# MAGIC | Documentação oficial | [scikit-learn.org](https://scikit-learn.org/stable/) |
# MAGIC | Árvore de Decisão | [Decision Tree](https://scikit-learn.org/stable/modules/tree.html) |
# MAGIC | Random Forest | [Random Forest](https://scikit-learn.org/stable/modules/ensemble.html#forest) |
# MAGIC | Métricas de Classificação | [Classification Metrics](https://scikit-learn.org/stable/modules/model_evaluation.html#classification-metrics) |
# MAGIC | Train/Test Split | [Cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) |
# MAGIC 
# MAGIC ### Visualizações
# MAGIC 
# MAGIC | Recurso | Link |
# MAGIC |---------|------|
# MAGIC | Matplotlib | [matplotlib.org](https://matplotlib.org/) |
# MAGIC | Seaborn | [seaborn.pydata.org](https://seaborn.pydata.org/) |
# MAGIC | Plotly | [plotly.com/python](https://plotly.com/python/) |

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 5. Snippets de Código
# MAGIC 
# MAGIC ### Carregar Credenciais

# COMMAND ----------

# Copie este bloco para seus notebooks:

# AWS S3
AWS_ACCESS_KEY = dbutils.secrets.get(scope="aws-credentials", key="access-key")
AWS_SECRET_KEY = dbutils.secrets.get(scope="aws-credentials", key="secret-key")
BUCKET_NAME    = "enem-data-lake-gblzera"
REGION         = "sa-east-1"

# RDS PostgreSQL
RDS_HOST     = dbutils.secrets.get(scope="aws-credentials", key="rds-host")
RDS_USER     = dbutils.secrets.get(scope="aws-credentials", key="rds-user")
RDS_PASSWORD = dbutils.secrets.get(scope="aws-credentials", key="rds-password")
RDS_DATABASE = "enem_db"
RDS_PORT     = 5432

# COMMAND ----------

# MAGIC %md
# MAGIC ### Configurar Spark para S3 (REFERÊNCIA — não roda no serverless)
# MAGIC
# MAGIC > **Nota:** na Databricks Free/Community Edition o cluster é serverless (Spark Connect)
# MAGIC > e o Spark **não** lê o S3 (erro 403). Este bloco fica apenas como referência.
# MAGIC > O caminho real de leitura/escrita é via **boto3/awswrangler/pandas** com as chaves
# MAGIC > do Databricks Secrets (escopo `aws-credentials`).

# COMMAND ----------

# REFERÊNCIA (não funciona no serverless): configurar credenciais no Spark
# spark.conf.set("fs.s3a.access.key", AWS_ACCESS_KEY)
# spark.conf.set("fs.s3a.secret.key", AWS_SECRET_KEY)
# spark.conf.set("fs.s3a.endpoint", f"s3.{REGION}.amazonaws.com")
# spark.conf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Ler CSV do S3 (boto3/pandas — caminho real)

# COMMAND ----------

# Caminho real (serverless): ler CSV com awswrangler/pandas + encoding latin1 (padrão INEP)
# import awswrangler as wr
# df = wr.s3.read_csv(
#     "s3://enem-data-lake-gblzera/bronze/enem/2023/MICRODADOS_ENEM_2023.csv",
#     sep=";",
#     encoding="latin1"
# )
#
# # REFERÊNCIA (não funciona no serverless — Spark não lê o S3, erro 403):
# # df = spark.read.csv(
# #     "s3a://enem-data-lake-gblzera/bronze/enem/2023/MICRODADOS_ENEM_2023.csv",
# #     header=True,
# #     inferSchema=True,
# #     sep=";",
# #     encoding="latin1"
# # )

# COMMAND ----------

# MAGIC %md
# MAGIC ### Escrever Parquet no S3 (awswrangler — caminho real)

# COMMAND ----------

# Caminho real (serverless): escrever Parquet particionado por year via awswrangler
# import awswrangler as wr
# wr.s3.to_parquet(
#     df=df,
#     path="s3://enem-data-lake-gblzera/parquet/enem/",
#     dataset=True,
#     mode="overwrite",
#     partition_cols=["year"]
# )
#
# # REFERÊNCIA (não funciona no serverless — Spark não escreve no S3, erro 403):
# # df.write \
# #     .mode("overwrite") \
# #     .partitionBy("year") \
# #     .parquet("s3a://enem-data-lake-gblzera/parquet/enem/")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Conectar ao RDS com psycopg2

# COMMAND ----------

# import psycopg2
# 
# conn = psycopg2.connect(
#     host=RDS_HOST,
#     database=RDS_DATABASE,
#     user=RDS_USER,
#     password=RDS_PASSWORD,
#     port=RDS_PORT
# )
# cursor = conn.cursor()
# cursor.execute("SELECT * FROM enem_features LIMIT 10")
# rows = cursor.fetchall()
# conn.close()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Ler/Escrever com JDBC (Spark + PostgreSQL) — REFERÊNCIA
# MAGIC
# MAGIC > No serverless o Spark+JDBC não é o caminho usado; a integração real com o RDS
# MAGIC > é via `psycopg2`/`sqlalchemy` (ver `load_postgresql.py`). Bloco mantido como referência.

# COMMAND ----------

# # Ler do PostgreSQL
# df = spark.read \
#     .format("jdbc") \
#     .option("url", f"jdbc:postgresql://{RDS_HOST}:{RDS_PORT}/{RDS_DATABASE}") \
#     .option("dbtable", "enem_features") \
#     .option("user", RDS_USER) \
#     .option("password", RDS_PASSWORD) \
#     .option("driver", "org.postgresql.Driver") \
#     .load()
# 
# # Escrever no PostgreSQL
# df.write \
#     .format("jdbc") \
#     .option("url", f"jdbc:postgresql://{RDS_HOST}:{RDS_PORT}/{RDS_DATABASE}") \
#     .option("dbtable", "enem_features") \
#     .option("user", RDS_USER) \
#     .option("password", RDS_PASSWORD) \
#     .option("driver", "org.postgresql.Driver") \
#     .mode("overwrite") \
#     .save()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Exemplo de Árvore de Decisão

# COMMAND ----------

# from sklearn.model_selection import train_test_split
# from sklearn.tree import DecisionTreeClassifier
# from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
# 
# # Preparar dados
# X = df[features_columns]
# y = df['TARGET']
# 
# # Split
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
# 
# # Treinar
# model = DecisionTreeClassifier(max_depth=10, random_state=42)
# model.fit(X_train, y_train)
# 
# # Avaliar
# y_pred = model.predict(X_test)
# print(f"Acurácia: {accuracy_score(y_test, y_pred):.4f}")
# print(classification_report(y_test, y_pred))

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 6. Contatos
# MAGIC 
# MAGIC ### Equipe Data Major
# MAGIC 
# MAGIC | Papel | Nome |
# MAGIC |-------|------|
# MAGIC | Tech Lead | Gabriel Henrique Kuhn Paz |
# MAGIC | Extract | Davi Serra Bezerra |
# MAGIC | Transform | Bruno Brudó |
# MAGIC | Load | Vinicius von Glehn Severo |
# MAGIC | Data Mining | Gabriel dos Santos Silva |
# MAGIC 
# MAGIC ### Professor
# MAGIC 
# MAGIC - **Disciplina:** Tópicos de Banco de Dados
# MAGIC - **Professor:** Rodrigo Gonçalves
# MAGIC - **Instituição:** Centro Universitário IESB

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC 
# MAGIC **Última atualização:** 2026-06-13
# MAGIC **Mantido por:** Tech Lead (Gabriel H. K. Paz)