# Databricks notebook source
# MAGIC %md
# MAGIC # Configuração de Credenciais
# MAGIC 
# MAGIC Este notebook configura as credenciais de acesso ao AWS S3 e RDS PostgreSQL.
# MAGIC 
# MAGIC > **IMPORTANTE:** Nunca exponha credenciais em código! Sempre use `dbutils.secrets.get()`.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 1. Sobre o Databricks Secrets
# MAGIC 
# MAGIC O Databricks Secrets é um serviço seguro para armazenar credenciais sensíveis. As credenciais são:
# MAGIC 
# MAGIC - **Criptografadas** em repouso
# MAGIC - **Mascaradas** nos logs (aparecem como `[REDACTED]`)
# MAGIC - **Acessíveis** apenas por usuários autorizados
# MAGIC 
# MAGIC ### Scope Configurado
# MAGIC 
# MAGIC O Tech Lead configurou o scope `aws-credentials` com as seguintes chaves:
# MAGIC 
# MAGIC | Chave | Descrição | Uso |
# MAGIC |-------|-----------|-----|
# MAGIC | `access-key` | AWS Access Key ID | Acesso ao S3 |
# MAGIC | `secret-key` | AWS Secret Access Key | Acesso ao S3 |
# MAGIC | `rds-host` | Endpoint do RDS | Conexão PostgreSQL |
# MAGIC | `rds-user` | Usuário do banco | Conexão PostgreSQL |
# MAGIC | `rds-password` | Senha do banco | Conexão PostgreSQL |

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 2. Carregar Credenciais
# MAGIC 
# MAGIC Execute a célula abaixo para carregar todas as credenciais:

# COMMAND ----------

# ╔══════════════════════════════════════════════════════════════════════╗
# ║                     CONFIGURAÇÃO DE CREDENCIAIS                      ║
# ║                   (Copie este bloco para seu notebook)               ║
# ╚══════════════════════════════════════════════════════════════════════╝

# --- AWS S3 ---
AWS_ACCESS_KEY = dbutils.secrets.get(scope="aws-credentials", key="access-key")
AWS_SECRET_KEY = dbutils.secrets.get(scope="aws-credentials", key="secret-key")
BUCKET_NAME    = "enem-data-lake-gblzera"
REGION         = "sa-east-1"

# --- RDS PostgreSQL ---
RDS_HOST     = dbutils.secrets.get(scope="aws-credentials", key="rds-host")
RDS_USER     = dbutils.secrets.get(scope="aws-credentials", key="rds-user")
RDS_PASSWORD = dbutils.secrets.get(scope="aws-credentials", key="rds-password")
RDS_DATABASE = "enem_db"
RDS_PORT     = 5432

print("=" * 60)
print("CREDENCIAIS CARREGADAS COM SUCESSO!")
print("=" * 60)
print()
print("AWS S3:")
print(f"  • Bucket: {BUCKET_NAME}")
print(f"  • Região: {REGION}")
print(f"  • Access Key: ****{AWS_ACCESS_KEY[-4:] if len(AWS_ACCESS_KEY) > 4 else '****'}")
print()
print("RDS PostgreSQL:")
print(f"  • Host: {RDS_HOST}")
print(f"  • Database: {RDS_DATABASE}")
print(f"  • User: {RDS_USER}")
print(f"  • Port: {RDS_PORT}")
print()
print("=" * 60)

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 3. Configurar Spark para S3
# MAGIC
# MAGIC > **⚠️ ATENÇÃO — APENAS REFERÊNCIA (NÃO FUNCIONA NESTE PROJETO):**
# MAGIC >
# MAGIC > Os helpers de **Spark + S3** abaixo (`configure_spark_s3`, e mais adiante
# MAGIC > `read_csv_from_s3`, `read_parquet_from_s3`, `write_parquet_to_s3`) usam
# MAGIC > `fs.s3a` / `spark.read` de `s3://...` e **NÃO funcionam** no Databricks
# MAGIC > **Free/Community Edition** (cluster serverless / Spark Connect). Nesse
# MAGIC > ambiente o Spark **não acessa o S3** (retorna erro **403**).
# MAGIC >
# MAGIC > Na prática, este projeto **lê e grava no S3 via `boto3` / `awswrangler` /
# MAGIC > `pandas`** (os dados cabem em memória), usando as chaves do
# MAGIC > **Databricks Secrets** (escopo `aws-credentials`). Estas funções ficam
# MAGIC > apenas como **referência** para um cenário com cluster clássico.

# COMMAND ----------

# ╔══════════════════════════════════════════════════════════════════════╗
# ║                   CONFIGURAÇÃO SPARK + S3                            ║
# ╚══════════════════════════════════════════════════════════════════════╝

def configure_spark_s3():
    """Configura o Spark para acessar o S3."""
    spark.conf.set("fs.s3a.access.key", AWS_ACCESS_KEY)
    spark.conf.set("fs.s3a.secret.key", AWS_SECRET_KEY)
    spark.conf.set("fs.s3a.endpoint", f"s3.{REGION}.amazonaws.com")
    spark.conf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    print("Spark configurado para S3!")

# Executar configuração
configure_spark_s3()

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 4. Funções Utilitárias
# MAGIC 
# MAGIC Funções prontas para usar nos notebooks do pipeline:

# COMMAND ----------

# ╔══════════════════════════════════════════════════════════════════════╗
# ║                      FUNÇÕES UTILITÁRIAS                             ║
# ╚══════════════════════════════════════════════════════════════════════╝

import boto3
import psycopg2

# ============================================
# FUNÇÕES S3
# ============================================

def get_s3_client():
    """Retorna um cliente S3 configurado."""
    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION
    )

def list_s3_files(prefix):
    """Lista arquivos em um prefixo do S3."""
    s3 = get_s3_client()
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
    
    if "Contents" in response:
        return [obj["Key"] for obj in response["Contents"]]
    return []

def upload_to_s3(data, s3_key):
    """Faz upload de dados para o S3."""
    s3 = get_s3_client()
    if isinstance(data, str):
        data = data.encode("utf-8")
    s3.put_object(Bucket=BUCKET_NAME, Key=s3_key, Body=data)
    print(f"Upload concluído: s3://{BUCKET_NAME}/{s3_key}")

def download_from_s3(s3_key):
    """Faz download de um arquivo do S3."""
    s3 = get_s3_client()
    response = s3.get_object(Bucket=BUCKET_NAME, Key=s3_key)
    return response["Body"].read()

# ============================================
# FUNÇÕES SPARK + S3
# ------------------------------------------------------------------
# ⚠️ APENAS REFERÊNCIA — NÃO FUNCIONA NESTE PROJETO.
# As funções abaixo usam fs.s3a / spark.read de "s3://..." e NÃO
# funcionam no Databricks Free/Community Edition (serverless / Spark
# Connect): o Spark não acessa o S3 (erro 403). O projeto lê/grava
# via boto3 / awswrangler / pandas com as chaves do Databricks Secrets
# (escopo aws-credentials). Mantidas só como referência para cluster
# clássico.
# ============================================

def read_csv_from_s3(s3_path, sep=";", encoding="latin1"):
    """Lê um CSV do S3 e retorna um DataFrame Spark."""
    configure_spark_s3()
    full_path = f"s3a://{BUCKET_NAME}/{s3_path}"
    return spark.read.csv(full_path, header=True, inferSchema=True, sep=sep, encoding=encoding)

def read_parquet_from_s3(s3_path):
    """Lê um Parquet do S3 e retorna um DataFrame Spark."""
    configure_spark_s3()
    full_path = f"s3a://{BUCKET_NAME}/{s3_path}"
    return spark.read.parquet(full_path)

def write_parquet_to_s3(df, s3_path, partition_by=None, mode="overwrite"):
    """Escreve um DataFrame Spark como Parquet no S3."""
    configure_spark_s3()
    full_path = f"s3a://{BUCKET_NAME}/{s3_path}"
    
    writer = df.write.mode(mode)
    if partition_by:
        writer = writer.partitionBy(partition_by)
    writer.parquet(full_path)
    print(f"Parquet salvo: {full_path}")

# ============================================
# FUNÇÕES RDS
# ============================================

def get_rds_connection():
    """Retorna uma conexão com o RDS PostgreSQL."""
    return psycopg2.connect(
        host=RDS_HOST,
        database=RDS_DATABASE,
        user=RDS_USER,
        password=RDS_PASSWORD,
        port=RDS_PORT,
        connect_timeout=30
    )

def execute_rds_query(query, fetch=True):
    """Executa uma query no RDS e retorna os resultados."""
    conn = get_rds_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    
    if fetch:
        result = cursor.fetchall()
    else:
        conn.commit()
        result = cursor.rowcount
    
    cursor.close()
    conn.close()
    return result

def get_rds_jdbc_url():
    """Retorna a URL JDBC para conexão com Spark."""
    return f"jdbc:postgresql://{RDS_HOST}:{RDS_PORT}/{RDS_DATABASE}"

def get_rds_properties():
    """Retorna as propriedades de conexão para Spark JDBC."""
    return {
        "user": RDS_USER,
        "password": RDS_PASSWORD,
        "driver": "org.postgresql.Driver"
    }

print("Funções utilitárias carregadas!")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 5. Exemplo de Uso
# MAGIC 
# MAGIC ### Listar arquivos no S3

# COMMAND ----------

# Exemplo: listar arquivos na pasta bronze
arquivos = list_s3_files("bronze/")
print("Arquivos na pasta bronze/:")
for arq in arquivos[:10]:  # Limitar a 10 para não poluir
    print(f"  • {arq}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Ler Parquet do S3 com Spark

# COMMAND ----------

# Exemplo: ler dados da camada silver (descomente quando houver dados)
# df = read_parquet_from_s3("silver/enem/")
# df.show(5)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Executar query no RDS

# COMMAND ----------

# Exemplo: verificar versão do PostgreSQL (descomente quando RDS estiver ligado)
# version = execute_rds_query("SELECT version();")
# print(f"PostgreSQL: {version[0][0]}")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 6. Nota sobre o RDS
# MAGIC 
# MAGIC > **⚠️ IMPORTANTE:** O banco PostgreSQL fica **desligado por padrão** para economizar custos.
# MAGIC > 
# MAGIC > Quando precisar usar o RDS, avise o Tech Lead para ligar a instância.
# MAGIC > 
# MAGIC > O erro de timeout é esperado quando o RDS está desligado.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC 
# MAGIC **Última atualização:** 2026-06-13
# MAGIC **Mantido por:** Tech Lead (Gabriel H. K. Paz)