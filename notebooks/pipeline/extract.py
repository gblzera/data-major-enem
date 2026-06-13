# Databricks notebook source
import boto3
import requests
import zipfile
import io
import os
from datetime import datetime

print("Bibliotecas carregadas e prontas para processamento em memória")

# COMMAND ----------

AWS_ACCESS_KEY = dbutils.secrets.get(scope="aws-credentials", key="access-key")
AWS_SECRET_KEY = dbutils.secrets.get(scope="aws-credentials", key="secret-key")
REGION = "sa-east-1"
BUCKET = "enem-data-lake-gblzera"

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION
)

print(f"Conectado ao bucket: {BUCKET}")

# COMMAND ----------

ANOS = ["2021", "2022", "2023"]

URLS = {
    "2021": "https://download.inep.gov.br/microdados/microdados_enem_2021.zip",
    "2022": "https://download.inep.gov.br/microdados/microdados_enem_2022.zip",
    "2023": "https://download.inep.gov.br/microdados/microdados_enem_2023.zip"
}

print("Parâmetros de extração definidos")

# COMMAND ----------

def upload_stream_s3(url, bucket, key):
    print(f"[STREAMING] Iniciando: {url}")
    
    # Request com streaming habilitado
    with requests.get(url, stream=True, verify=True) as r:
        r.raise_for_status()
        s3.upload_fileobj(r.raw, bucket, key)
        
    print(f"[OK] ZIP salvo em: {key}")

print("Importado com sucesso!")

# COMMAND ----------

for ano in ANOS:
    zip_key = f"bronze/enem/{ano}/microdados_{ano}.zip"

    try:
        s3.head_object(Bucket=BUCKET, Key=zip_key)
        print(f"[SKIP] Objeto já existe no S3: {zip_key}")
    except:
        upload_stream_s3(URLS[ano], BUCKET, zip_key)

# COMMAND ----------

for ano in ANOS:
    zip_key = f"bronze/enem/{ano}/microdados_{ano}.zip"
    target_csv = f"MICRODADOS_ENEM_{ano}.csv"
    destination_key = f"bronze/enem/{ano}/{target_csv}"
    
    print(f"[MEMÓRIA] Extraindo {target_csv} de {zip_key}")
    
    # Busca o ZIP do S3 para a memória
    obj = s3.get_object(Bucket=BUCKET, Key=zip_key)
    
    # Abre o ZIP em memória
    with zipfile.ZipFile(io.BytesIO(obj['Body'].read())) as z:
        # Localiza o arquivo CSV dentro da estrutura do ZIP
        for file_info in z.infolist():
            if file_info.filename.endswith(target_csv):
                with z.open(file_info) as f:
                    # Upload direto do stream de memória
                    s3.upload_fileobj(f, BUCKET, destination_key)
                    print(f"[OK] CSV extraído e salvo: {destination_key}")
                break

# COMMAND ----------

print("Listagem de arquivos na Camada Bronze:")

response = s3.list_objects_v2(Bucket=BUCKET, Prefix="bronze/enem/")
metadata = []

for obj in response.get("Contents", []):
    item = {
        "arquivo": obj["Key"],
        "tamanho_mb": round(obj["Size"] / (1024 * 1024), 2),
        "ultima_modificacao": obj["LastModified"].strftime("%Y-%m-%d %H:%M:%S")
    }
    metadata.append(item)
    print(f"-> {item['arquivo']} | {item['tamanho_mb']} MB")

# Opcional: registrar logs de volume em uma tabela de controle futura

# COMMAND ----------

print(f"""
Processo Finalizado com Sucesso (Pipeline Data Major)
---------------------------------------------------
Status: Concluído
Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}
Conformidade RF-01: Integral (Zero disco local)
Camada: Bronze (Raw Data)
""")
