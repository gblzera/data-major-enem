# Databricks notebook source
import boto3
import io
import pandas as pd
import psycopg2
from sqlalchemy import create_engine

# --- 1. CONFIGURAÇÕES E SECRETS ---
AWS_ACCESS_KEY = dbutils.secrets.get(scope="aws-credentials", key="access-key")
AWS_SECRET_KEY = dbutils.secrets.get(scope="aws-credentials", key="secret-key")
RDS_HOST = dbutils.secrets.get(scope="aws-credentials", key="rds-host")
RDS_USER = dbutils.secrets.get(scope="aws-credentials", key="rds-user")
RDS_PASS = dbutils.secrets.get(scope="aws-credentials", key="rds-password")

REGION = "sa-east-1"
BUCKET = "enem-data-lake-gblzera"
RDS_INSTANCE_ID = "enem-db" # Nome da instância na AWS

LAYER_MAPPING = {
    "bronze": "raw",
    "silver": "tru",
    "gold": "ref"
}

FILE_PATTERNS = {
    "bronze": "microdados_enem_{ano}.csv", 
    "silver": "microdados_silver_{ano}.csv",
    "gold": "GOLD_ENEM_{ano}.csv"
}

ANOS = ["2021", "2022", "2023"]

# --- 2. FINOPS: LIGAR BANCO ---
rds_client = boto3.client("rds", aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=REGION)
s3 = boto3.client("s3", aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=REGION)

print("--- Iniciando Protocolo FinOps (RNF-05) ---")
try:
    print(f"Enviando comando START para RDS '{RDS_INSTANCE_ID}'...")
    rds_client.start_db_instance(DBInstanceIdentifier=RDS_INSTANCE_ID)
    waiter = rds_client.get_waiter('db_instance_available')
    # WaiterConfig é um dict (não uma classe): Delay 30s × MaxAttempts 20 = até ~10 min
    waiter.wait(DBInstanceIdentifier=RDS_INSTANCE_ID, WaiterConfig={"Delay": 30, "MaxAttempts": 20})
    print("✅ Banco de Dados ONLINE!")
except Exception as e:
    print("✅ Banco de Dados já estava ONLINE.")

# --- 3. CONEXÕES ---
engine = create_engine(f"postgresql://{RDS_USER}:{RDS_PASS}@{RDS_HOST}:5432/enem_db")
conn = psycopg2.connect(host=RDS_HOST, database="enem_db", user=RDS_USER, password=RDS_PASS, port=5432)

# --- 4. FUNÇÃO DE CARGA RÁPIDA ---
def fast_load_to_rds(df, schema, table_name, connection, engine_sqla, criar_tabela=True):
    cursor = connection.cursor()
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
    connection.commit()

    # Cria tabela vazia só uma vez (no 1º chunk); 'append' não recria se já existir
    if criar_tabela:
        df.head(0).to_sql(name=table_name, con=engine_sqla, schema=schema, if_exists='append', index=False)

    # Transfere via COPY
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, header=False, sep='\t')
    csv_buffer.seek(0)
    
    copy_query = f"COPY {schema}.{table_name} FROM stdin WITH CSV DELIMITER '\t' NULL ''"
    cursor.copy_expert(copy_query, csv_buffer)
    
    connection.commit()
    cursor.close()

# --- 5. EXECUÇÃO SNIPER ---
print("\n--- Iniciando Carga de Dados ---")
for layer, schema in LAYER_MAPPING.items():
    print(f"\n🚀 Processando Camada: {layer.upper()} -> Schema: {schema}")
    
    for ano in ANOS:
        file_key = f"{layer}/enem/{ano}/{FILE_PATTERNS[layer].format(ano=ano)}"
        print(f"   - Baixando ALVO EXATO: {file_key}...")
        
        try:
            resp = s3.get_object(Bucket=BUCKET, Key=file_key)
            # Correção do OOM: lê em CHUNKS direto do stream do S3 (Bronze ~1,4 GB/ano)
            leitor = pd.read_csv(resp['Body'], encoding="latin-1", sep=";",
                                 low_memory=False, chunksize=200_000)
            total = 0
            for i, chunk in enumerate(leitor):
                chunk['year'] = int(ano)
                if "Unnamed: 0" in chunk.columns:
                    chunk.drop(columns=["Unnamed: 0"], inplace=True)
                fast_load_to_rds(chunk, schema, "microdados", conn, engine, criar_tabela=(i == 0))
                total += len(chunk)
            print(f"   ✅ {total} registros inseridos!")

        except Exception as e:
            conn.rollback()
            print(f"   ❌ Erro em {file_key}: {e}")

# --- 6. AUDITORIA E FINOPS FINAL ---
print("\n--- Auditoria Final ---")
cursor = conn.cursor()
for schema in LAYER_MAPPING.values():
    try:
        cursor.execute(f"SELECT count(*) FROM {schema}.microdados")
        print(f"📊 Schema {schema}: {cursor.fetchone()[0]} registros persistidos.")
    except Exception as e:
        print(f"📊 Schema {schema}: Tabela não encontrada ou vazia.")
        conn.rollback()

conn.close()

print("\n--- Finalizando Protocolo FinOps (RNF-05) ---")
try:
    rds_client.stop_db_instance(DBInstanceIdentifier=RDS_INSTANCE_ID)
    print("🔒 RDS em processo de suspensão. Custos interrompidos com sucesso!")
except Exception as e:
    print(f"⚠️ Erro ao desligar: {e}")
