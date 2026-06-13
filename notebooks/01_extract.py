# Databricks notebook source
# MAGIC %md
# MAGIC # 01 — Extract: coleta dos microdados do ENEM (INEP → S3 Bronze)
# MAGIC ### Projeto Data Major | Responsável: Davi
# MAGIC
# MAGIC > ⚠️ **RECONSTRUÇÃO** a partir da lógica acordada no projeto. Se o notebook original no Databricks
# MAGIC > tiver detalhes adicionais, exporte-o (File → Export → Source file) e substitua este arquivo.
# MAGIC
# MAGIC **Objetivo:** baixar os arquivos `.zip` de cada edição do ENEM no portal do INEP, extrair o CSV de
# MAGIC microdados correto e carregá-lo na camada **Bronze** do data lake (S3), sem qualquer transformação.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Setup e credenciais

# COMMAND ----------

import boto3
import requests
import zipfile
import io
import os

BUCKET = "enem-data-lake-gblzera"
REGION = "sa-east-1"
ANOS = [2021, 2022, 2023]

AWS_ACCESS_KEY = dbutils.secrets.get(scope="aws-credentials", key="access-key")
AWS_SECRET_KEY = dbutils.secrets.get(scope="aws-credentials", key="secret-key")
s3 = boto3.client("s3", aws_access_key_id=AWS_ACCESS_KEY,
                  aws_secret_access_key=AWS_SECRET_KEY, region_name=REGION)
print("Setup concluído. Bucket:", BUCKET)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. URLs dos microdados (portal INEP)
# MAGIC As URLs seguem o padrão de dados abertos do INEP. Confira o link atual em:
# MAGIC https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem

# COMMAND ----------

URLS = {
    2021: "https://download.inep.gov.br/microdados/microdados_enem_2021.zip",
    2022: "https://download.inep.gov.br/microdados/microdados_enem_2022.zip",
    2023: "https://download.inep.gov.br/microdados/microdados_enem_2023.zip",
}

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Download, extração e upload para a Bronze
# MAGIC
# MAGIC **Pontos de atenção (lições do projeto):**
# MAGIC - `verify=False` contorna o erro de certificado SSL do servidor do INEP no cluster.
# MAGIC - A seleção do CSV é **exata** pelo nome `MICRODADOS_ENEM_{ano}.csv`. A primeira versão pegava o
# MAGIC   primeiro CSV do zip e acabava capturando arquivos auxiliares (itens de prova) em 2022/2023.

# COMMAND ----------

def baixar_e_subir(ano, url):
    print(f"[{ano}] baixando de {url} ...")
    # verify=False por causa do certificado SSL do INEP no ambiente do cluster
    resp = requests.get(url, verify=False, stream=True, timeout=600)
    resp.raise_for_status()
    conteudo = io.BytesIO(resp.content)
    print(f"[{ano}] download concluído ({len(resp.content)/1e9:.2f} GB). Abrindo o zip...")

    with zipfile.ZipFile(conteudo) as z:
        # seleção EXATA do CSV de microdados (evita pegar ITENS_PROVA etc.)
        alvo = None
        for nome in z.namelist():
            base = os.path.basename(nome)
            if base == f"MICRODADOS_ENEM_{ano}.csv":
                alvo = nome
                break
        if alvo is None:
            raise FileNotFoundError(f"[{ano}] CSV MICRODADOS_ENEM_{ano}.csv não encontrado no zip. "
                                    f"Conteúdo: {z.namelist()[:10]}")
        print(f"[{ano}] CSV correto: {alvo}")

        # upload direto para o S3 Bronze (streaming, sem gravar em disco local)
        key = f"bronze/enem/{ano}/MICRODADOS_ENEM_{ano}.csv"
        with z.open(alvo) as f:
            s3.upload_fileobj(f, BUCKET, key)
        print(f"[{ano}] enviado para s3://{BUCKET}/{key}")

for ano in ANOS:
    baixar_e_subir(ano, URLS[ano])

print("\nExtract concluído. Dados brutos na camada Bronze.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Validação da carga (Bronze)

# COMMAND ----------

print("Arquivos na camada Bronze:")
for ano in ANOS:
    prefixo = f"bronze/enem/{ano}/"
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefixo)
    for obj in resp.get("Contents", []):
        print(f"  {obj['Key']}  —  {obj['Size']/1e9:.2f} GB")
