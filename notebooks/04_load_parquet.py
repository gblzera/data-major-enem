# Databricks notebook source
# MAGIC %md
# MAGIC # 04 — Load: armazenamento (Parquet consolidado + PostgreSQL)
# MAGIC ### Projeto Data Major | Responsável: Vinícius
# MAGIC
# MAGIC > ⚠️ **RECONSTRUÇÃO** a partir da lógica acordada no projeto. Exporte o original do Databricks e
# MAGIC > substitua se houver diferenças.
# MAGIC
# MAGIC **Objetivo:** carregar a camada Gold em dois destinos:
# MAGIC 1. **Parquet consolidado** particionado por ano (formato exigido, ~59 MB) — camada de consumo.
# MAGIC 2. **PostgreSQL (RDS)** — banco relacional complementar (decisão do grupo). *Em andamento.*

# COMMAND ----------

from pyspark.sql import functions as F

BUCKET = "enem-data-lake-gblzera"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Leitura da camada Gold

# COMMAND ----------

df_gold = spark.read.parquet(f"s3://{BUCKET}/gold/enem/")
print(f"Gold: {df_gold.count():,} registros.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Carga 1 — Parquet consolidado (camada de consumo)
# MAGIC Particionado por ano: consultas restritas a uma edição leem só a partição correspondente.

# COMMAND ----------

(df_gold.write
 .mode("overwrite")
 .partitionBy("year")
 .parquet(f"s3://{BUCKET}/parquet/enem/"))
print(f"Parquet consolidado gravado em s3://{BUCKET}/parquet/enem/")

# validação de integridade (contagem por ano)
display(df_gold.groupBy("year").count().orderBy("year"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Carga 2 — PostgreSQL (RDS) — EM ANDAMENTO
# MAGIC Carga complementar em banco relacional para prática de modelagem e consultas SQL da equipe.
# MAGIC
# MAGIC > Preencha host/porta/credenciais via Databricks Secrets antes de executar.

# COMMAND ----------

# --- Configuração da conexão (use Secrets, nunca hardcode) ---
# PG_HOST = dbutils.secrets.get(scope="rds-postgres", key="host")
# PG_PORT = "5432"
# PG_DB   = "enem"
# PG_USER = dbutils.secrets.get(scope="rds-postgres", key="user")
# PG_PASS = dbutils.secrets.get(scope="rds-postgres", key="password")
#
# jdbc_url = f"jdbc:postgresql://{PG_HOST}:{PG_PORT}/{PG_DB}"
# props = {"user": PG_USER, "password": PG_PASS, "driver": "org.postgresql.Driver"}
#
# (df_gold.write
#  .mode("overwrite")
#  .jdbc(url=jdbc_url, table="enem_features", properties=props))
# print("Carga no PostgreSQL concluída.")

print("Carga PostgreSQL: pendente de configuração da conexão (ver célula acima).")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Validação final
# MAGIC O Parquet em `parquet/enem/` é a fonte consumida pelo notebook de mineração (05).

# COMMAND ----------

import awswrangler as wr
import boto3
AWS_ACCESS_KEY = dbutils.secrets.get(scope="aws-credentials", key="access-key")
AWS_SECRET_KEY = dbutils.secrets.get(scope="aws-credentials", key="secret-key")
boto3.setup_default_session(aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_KEY, region_name="sa-east-1")

df_check = wr.s3.read_parquet(path=f"s3://{BUCKET}/parquet/enem/", dataset=True)
print(f"Parquet final validado: {df_check.shape[0]:,} registros | {df_check.shape[1]} colunas.")
