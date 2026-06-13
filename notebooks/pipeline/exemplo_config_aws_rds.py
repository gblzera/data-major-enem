# Databricks notebook source
# MAGIC %pip install psycopg2-binary sqlalchemy 

# COMMAND ----------

import psycopg2

RDS_HOST = dbutils.secrets.get(scope="aws-credentials", key="rds-host")
RDS_USER = dbutils.secrets.get(scope="aws-credentials", key="rds-user")
RDS_PASS = dbutils.secrets.get(scope="aws-credentials", key="rds-password")
RDS_PORT = 5432
RDS_DB   = "enem_db"

conn = psycopg2.connect(
    host=RDS_HOST, database=RDS_DB,
    user=RDS_USER, password=RDS_PASS,
    port=RDS_PORT, connect_timeout=10 #se der timeout é porque o banco esta desligado
)
print("teste de conexao efeutado")
conn.close()
