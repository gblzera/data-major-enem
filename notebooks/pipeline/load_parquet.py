# Databricks notebook source
import pandas as pd
import awswrangler as wr
import boto3
import io
from datetime import datetime

# RNF-01 e RN-04: Segurança via Secret Scopes
AWS_ACCESS_KEY = dbutils.secrets.get(scope="aws-credentials", key="access-key")
AWS_SECRET_KEY = dbutils.secrets.get(scope="aws-credentials", key="secret-key")
REGION = "sa-east-1"
BUCKET = "enem-data-lake-gblzera"

# Configurando sessão padrão do Boto3 (exigência do AWS Wrangler)
boto3.setup_default_session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION
)

# Mantemos o cliente s3 instanciado para leituras em memória
s3 = boto3.client("s3")
print("Bibliotecas importadas e sessão AWS configurada com sucesso!")

# COMMAND ----------

ANOS = ["2021", "2022", "2023"]

# Define exatamente as 27 colunas permitidas (RF-06)
Q_COLS = [f"Q{str(i).zfill(3)}" for i in range(1, 26)]
COLUNAS_GOLD = Q_COLS + ['NOTA_MEDIA', 'TARGET']
dfs = []

print("--- Lendo arquivos Gold e aplicando Extreme Downcasting ---")
for ano in ANOS:
    gold_key = f"gold/enem/{ano}/GOLD_ENEM_{ano}.csv"
    print(f"[{ano}] Lendo na memória {gold_key}...")
    
    response = s3.get_object(Bucket=BUCKET, Key=gold_key)
    raw_bytes = response['Body'].read()
    
    # 1. USECOLS: O lixo (Unnamed: 0) não entra na RAM
    df_temp = pd.read_csv(io.BytesIO(raw_bytes), encoding="latin-1", sep=";", usecols=COLUNAS_GOLD, low_memory=False)
    
    # 2. TARGET boolean (1 bit de peso no Parquet)
    df_temp['TARGET'] = df_temp['TARGET'].astype('bool')
    
    # 3. O SEGREDO: float16 corta o peso da coluna numérica pela metade!
    df_temp['NOTA_MEDIA'] = df_temp['NOTA_MEDIA'].round(2).astype('float16')
    
    # Q005 cabe no menor inteiro possível (int8)
    df_temp['Q005'] = df_temp['Q005'].astype('int8')
    df_temp['year'] = int(ano)
    
    dfs.append(df_temp)

# Consolidação dos 3 anos
df_gold = pd.concat(dfs, ignore_index=True)

# 4. Dictionary Encoding Global (Aplica category APÓS o concat para não quebrar)
print("--- Aplicando Dicionário de Compressão Categórica ---")
q_cols_texto = [col for col in Q_COLS if col != 'Q005']
for col in q_cols_texto:
    df_gold[col] = df_gold[col].astype('category')

print(f"Consolidação concluída! Total de registros: {len(df_gold)}")

# COMMAND ----------

registro = df_gold[df_gold['Q005'] == -1]

print(registro.T)

# COMMAND ----------

print("--- Iniciando gravação em formato Parquet no S3 ---")

# RF-07: Carga Gold -> S3 Parquet (Snappy, particionado por year)
parquet_path = f"s3://{BUCKET}/parquet/enem/"

res = wr.s3.to_parquet(
    df=df_gold,
    path=parquet_path,
    dataset=True,
    partition_cols=["year"],
    compression="zstd",
    mode="overwrite",
    index=False  # <--- A MÁGICA ACONTECE AQUI! Corta o peso morto.
)

print(f"Gravação concluída! {len(res['paths'])} partições criadas/atualizadas no S3.")

# COMMAND ----------

# RNF-04: Verificação programática do tamanho do Parquet final
print("--- Validação de Volume (RNF-04) ---")

response = s3.list_objects_v2(Bucket=BUCKET, Prefix="parquet/enem/")
tamanho_total_bytes = sum(obj["Size"] for obj in response.get("Contents", []))
tamanho_total_mb = tamanho_total_bytes / (1024 * 1024)

print("Arquivos gerados na pasta Parquet:")
for obj in response.get("Contents", []):
    # Omitindo logs de arquivos extremamente pequenos (arquivos _SUCCESS de metadados do Spark/Wrangler)
    if obj['Size'] > 1024:
        print(f"-> {obj['Key']} : {obj['Size'] / (1024 * 1024):.2f} MB")

print("-" * 45)
print(f"TAMANHO TOTAL CONSOLIDADO: {tamanho_total_mb:.2f} MB")

# Validação automatizada contra os limites do DR
if 30 <= tamanho_total_mb <= 60:
    print("STATUS RNF-04: APROVADO! O volume está estritamente dentro da meta estipulada.")
else:
    print(f"STATUS RNF-04: ALERTA! O volume final ({tamanho_total_mb:.2f} MB) está fora da margem de 30-60 MB.")
