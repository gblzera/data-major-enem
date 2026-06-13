# Databricks notebook source
import pandas as pd
import boto3
import os
from datetime import datetime

print("Bibliotecas carregadas para a camada Silver")

# COMMAND ----------

AWS_ACCESS_KEY = dbutils.secrets.get(scope="aws-credentials", key="access-key")
AWS_SECRET_KEY = dbutils.secrets.get(scope="aws-credentials", key="secret-key")

# O Pandas/S3FS usa variáveis de ambiente para acessar o S3 diretamente
os.environ["AWS_ACCESS_KEY_ID"] = AWS_ACCESS_KEY
os.environ["AWS_SECRET_ACCESS_KEY"] = AWS_SECRET_KEY
os.environ["AWS_DEFAULT_REGION"] = "sa-east-1"

s3 = boto3.client(
    "s3",
    aws_secret_access_key=AWS_SECRET_KEY,
    aws_access_key_id=AWS_ACCESS_KEY,
    region_name="sa-east-1"
)

BUCKET = "enem-data-lake-gblzera"

print("Credenciais configuradas no ambiente")

# COMMAND ----------

# validação

print("Arquivo no S3")

response = s3.list_objects_v2(Bucket=BUCKET, Prefix="bronze/enem/")

for obj in response.get("Contents", []):
    print(obj["Key"], "~", round(obj["Size"] / (1024 * 1024), 2), "MB")

# COMMAND ----------

ANOS = ["2021", "2022", "2023"] 

# Mapeando colunas do questionário socioeconômico (Q001 a Q025)
q_categoricas = [f"Q{str(i).zfill(3)}" for i in range(1, 26) if i != 5]

print("Parâmetros do fluxo Silver definidos")

# COMMAND ----------

def process_silver(ano):
    bronze_path = f"s3://{BUCKET}/bronze/enem/{ano}/MICRODADOS_ENEM_{ano}.csv"
    silver_path = f"s3://{BUCKET}/silver/enem/{ano}/microdados_silver_{ano}.csv"
    
    print(f"[{ano}] Lendo dados da Bronze...")
    df = pd.read_csv(bronze_path, sep=";", encoding="latin-1", low_memory=False)
    
    # -------------------------------------------------------------------
    # RF-03: Filtrar presença e remover duplicatas
    # -------------------------------------------------------------------
    df.drop_duplicates(subset=['NU_INSCRICAO', 'NU_ANO'], inplace=True)
    
    # ADICIONAMOS O .copy() AQUI NO FINAL DO FILTRO 👇
    df = df[
        (df['TP_PRESENCA_CN'] == 1) & 
        (df['TP_PRESENCA_CH'] == 1) & 
        (df['TP_PRESENCA_LC'] == 1) & 
        (df['TP_PRESENCA_MT'] == 1)
    ].copy()
    
    # -------------------------------------------------------------------
    # RF-04: Tratar nulos socioeconômicos
    # -------------------------------------------------------------------
    # Q001 a Q025 (exceto Q005) -> 'Não informado'
    for col in q_categoricas:
        if col in df.columns:
            df[col] = df[col].fillna('Não informado')
            
    # Q005 (numérica) -> -1
    if 'Q005' in df.columns:
        df['Q005'] = df['Q005'].fillna(-1)
        
    print(f"[{ano}] Transformações aplicadas. Linhas resultantes: {len(df)}")
    
    # -------------------------------------------------------------------
    # Salvando na Silver (com index=False para evitar o Unnamed: 0)
    # -------------------------------------------------------------------
    print(f"[{ano}] Salvando na camada Silver...")
    df.to_csv(silver_path, encoding="latin-1", sep=";", index=False)
    print(f"[{ano}] OK -> {silver_path}")

# COMMAND ----------

for ano in ANOS:
    print(f"--- Iniciando processamento de {ano} ---")
    process_silver(ano)

# COMMAND ----------

print("Amostra dos dados finais da camada Silver:")

# Correção: `df_viz` não estava definido (df era local em process_silver) — lê uma
# amostra do último arquivo Silver gravado para a pré-visualização.
amostra_path = f"s3://{BUCKET}/silver/enem/2023/microdados_silver_2023.csv"
df_viz = pd.read_csv(amostra_path, sep=";", encoding="latin-1", nrows=100, low_memory=False)

colunas_amostra = ['NU_INSCRICAO', 'NU_ANO', 'TP_PRESENCA_CN', 'Q001', 'Q002', 'Q005', 'Q025']
colunas_presentes = [col for col in colunas_amostra if col in df_viz.columns]

# print no lugar de display(): no serverless o display() de DataFrame pandas roteia pelo Spark e pode falhar
print(df_viz[colunas_presentes].to_string())

# COMMAND ----------

print(f"""
Processo Finalizado com Sucesso (Pipeline Data Major)
---------------------------------------------------
Status: Concluído
Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}
Camada: Silver (Cleaned Data)
Ajustes Aplicados:
- index=False implementado no to_csv()
- Filtros de presença e remoção de duplicatas (RF-03)
- Tratamento de nulos categóricos/numéricos (RF-04)
""")

# COMMAND ----------

# MAGIC %md
# MAGIC # Silver Layer — ENEM 2021/2022/2023
# MAGIC
# MAGIC ## Objetivo
# MAGIC Limpeza e tratamento dos dados brutos da camada Bronze, gerando dados confiáveis para a camada Gold.
# MAGIC
# MAGIC ## Entrada
# MAGIC - `bronze/enem/{ano}/MICRODADOS_ENEM_{ano}.csv`
# MAGIC - Anos processados: 2021, 2022, 2023
# MAGIC
# MAGIC ## Saída
# MAGIC - `silver/enem/{ano}/microdados_silver_{ano}.csv`
# MAGIC
# MAGIC ## Transformações aplicadas
# MAGIC
# MAGIC ### 1. Filtro de presença
# MAGIC Mantidos apenas candidatos com presença em todas as 4 áreas do ENEM.
# MAGIC - Colunas: `TP_PRESENCA_CN`, `TP_PRESENCA_CH`, `TP_PRESENCA_LC`, `TP_PRESENCA_MT`
# MAGIC - Critério: todas iguais a 1
# MAGIC - Justificativa: candidatos ausentes não possuem notas válidas e distorceriam o modelo
# MAGIC
# MAGIC ### 2. Tratamento de nulos — Questionário socioeconômico
# MAGIC - Colunas categóricas (Q001–Q025, exceto Q005): nulos preenchidos com `'Não informado'`
# MAGIC - Justificativa: preservar o máximo de registros válidos sem descartar candidatos por ausência em campos do questionário
# MAGIC
# MAGIC ### 3. Tratamento de nulos — Q005
# MAGIC - Coluna numérica (quantidade de pessoas na residência)
# MAGIC - Nulos preenchidos com `-1`
# MAGIC - Justificativa: valor sentinela que indica ausência de informação sem conflitar com valores reais
# MAGIC
# MAGIC ### 4. Verificação de tipos
# MAGIC - Notas (`NU_NOTA_*`): já em `float64`, nenhuma conversão necessária
# MAGIC - Questionário (Q001–Q025): já em `object` (string), nenhuma conversão necessária
# MAGIC
# MAGIC ## Resultado
# MAGIC | Ano | Candidatos originais | Após filtro |
# MAGIC |-----|---------------------|-------------|
# MAGIC | 2021 | 3.389.832 | 2.238.107 |
# MAGIC | 2022 | ~3.5M | 2.344.823 |
# MAGIC | 2023 | ~3.9M | 2.678.264 |
