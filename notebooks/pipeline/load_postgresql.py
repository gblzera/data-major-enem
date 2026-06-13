# Databricks notebook source
# MAGIC %pip install psycopg2-binary sqlalchemy

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

import boto3
import io
import pandas as pd
import psycopg2
from sqlalchemy import create_engine

# ==========================================
# 1. CREDENCIAIS E CONFIGURAÇÕES
# ==========================================
AWS_ACCESS_KEY = dbutils.secrets.get(scope="aws-credentials", key="access-key")
AWS_SECRET_KEY = dbutils.secrets.get(scope="aws-credentials", key="secret-key")
RDS_HOST = dbutils.secrets.get(scope="aws-credentials", key="rds-host")
RDS_USER = dbutils.secrets.get(scope="aws-credentials", key="rds-user")
RDS_PASS = dbutils.secrets.get(scope="aws-credentials", key="rds-password")

REGION = "sa-east-1"
BUCKET = "enem-data-lake-gblzera"
RDS_INSTANCE_ID = "enem-db" # Nome da sua instância lá na AWS

LAYER_MAPPING = {
    "bronze": "raw",
    "silver": "tru",
    "gold": "ref"
}

FILE_PATTERNS = {
    "bronze": "MICRODADOS_ENEM_{ano}.csv", 
    "silver": "microdados_silver_{ano}.csv",
    "gold": "GOLD_ENEM_{ano}.csv"
}

ANOS = ["2021", "2022", "2023"]

# ==========================================
# 2. FINOPS: LIGAR O BANCO DE DADOS
# ==========================================
print("--- Iniciando Protocolo FinOps (RNF-05) ---")
rds_client = boto3.client("rds", aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=REGION)
s3 = boto3.client("s3", aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=REGION)

try:
    print(f"Enviando comando START para a instância RDS '{RDS_INSTANCE_ID}'...")
    rds_client.start_db_instance(DBInstanceIdentifier=RDS_INSTANCE_ID)
    waiter = rds_client.get_waiter('db_instance_available')
    waiter.wait(DBInstanceIdentifier=RDS_INSTANCE_ID)
    print("✅ Banco de Dados ONLINE e pronto para receber conexões!")
except Exception as e:
    print("✅ Banco de Dados já estava ONLINE.")

# ==========================================
# 3. CONEXÕES COM O BANCO
# ==========================================
engine = create_engine(f"postgresql://{RDS_USER}:{RDS_PASS}@{RDS_HOST}:5432/enem_db")
conn = psycopg2.connect(host=RDS_HOST, database="enem_db", user=RDS_USER, password=RDS_PASS, port=5432)

def fast_load_to_rds(df, schema, table_name, connection, engine_sqla, criar_tabela=True):
    """Cria a tabela (no 1º chunk) com SQLAlchemy e injeta dados com COPY nativo"""
    cursor = connection.cursor()

    # Garante que o schema existe
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
    connection.commit()

    # Cria a estrutura da tabela vazia só uma vez (no 1º chunk); 'append' não recria se já existir
    if criar_tabela:
        df.head(0).to_sql(name=table_name, con=engine_sqla, schema=schema, if_exists='append', index=False)

    # Prepara os dados em memória e executa o COPY
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, header=False, sep='\t')
    csv_buffer.seek(0)
    
    copy_query = f"COPY {schema}.{table_name} FROM stdin WITH CSV DELIMITER '\t' NULL ''"
    cursor.copy_expert(copy_query, csv_buffer)
    
    connection.commit()
    cursor.close()

# ==========================================
# 4. LOOP PRINCIPAL DE CARGA
# ==========================================
print("\n--- Iniciando Carga de Dados para o RDS ---")
for layer, schema in LAYER_MAPPING.items():
    print(f"\n🚀 Processando Camada: {layer.upper()} -> Schema: {schema}")
    
    for ano in ANOS:
        # Monta exatamente o nome do arquivo, ignorando lixo na pasta
        file_key = f"{layer}/enem/{ano}/{FILE_PATTERNS[layer].format(ano=ano)}"
        print(f"   - Baixando ALVO: {file_key}...")
        
        try:
            resp = s3.get_object(Bucket=BUCKET, Key=file_key)
            # Correção do OOM: lê em CHUNKS direto do stream do S3. A Bronze tem ~1,4 GB/ano,
            # que estourava a memória do driver (exit 137 / SIGKILL) ao ser carregada inteira.
            leitor = pd.read_csv(resp['Body'], encoding="latin-1", sep=";",
                                 low_memory=False, chunksize=200_000)
            total = 0
            for i, chunk in enumerate(leitor):
                chunk['year'] = int(ano)
                if "Unnamed: 0" in chunk.columns:
                    chunk.drop(columns=["Unnamed: 0"], inplace=True)
                fast_load_to_rds(chunk, schema, "microdados", conn, engine, criar_tabela=(i == 0))
                total += len(chunk)
            print(f"   ✅ {total} registros inseridos com sucesso!")

        except Exception as e:
            conn.rollback()  # evita deixar a transação em estado abortado (cascata de erros)
            print(f"   ❌ Erro ao processar {file_key}: {e}")

# ==========================================
# 5. AUDITORIA E DESLIGAMENTO FINOPS
# ==========================================
print("\n--- Auditoria Final de Carga ---")
cursor = conn.cursor()
for schema in LAYER_MAPPING.values():
    try:
        cursor.execute(f"SELECT count(*) FROM {schema}.microdados")
        total = cursor.fetchone()[0]
        print(f"📊 Schema {schema}: {total} registros persistidos.")
    except Exception as e:
        print(f"📊 Schema {schema}: Tabela não encontrada ou vazia.")
        conn.rollback()

conn.close()

print("\n--- Finalizando Protocolo FinOps (RNF-05) ---")
try:
    rds_client.stop_db_instance(DBInstanceIdentifier=RDS_INSTANCE_ID)
    print("🔒 Comando de STOP enviado. O banco está sendo suspenso para poupar custos.")
except Exception as e:
    print(f"⚠️ Aviso ao desligar (pode já estar desligando): {e}")

print("\n🔥 Pipeline de Engenharia de Dados Concluído!")
