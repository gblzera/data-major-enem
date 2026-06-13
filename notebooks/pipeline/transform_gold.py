# Databricks notebook source
import pandas as pd
import boto3
import io
from datetime import datetime

# RNF-01 e RN-04: Segurança via Secret Scopes
AWS_ACCESS_KEY = dbutils.secrets.get(scope="aws-credentials", key="access-key")
AWS_SECRET_KEY = dbutils.secrets.get(scope="aws-credentials", key="secret-key")
BUCKET = "enem-data-lake-gblzera"

# Cliente S3 explícito
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name="sa-east-1"
)

print("Ambiente configurado! Usaremos Boto3 nativo para evitar erros do s3fs.")

# COMMAND ----------

# RN-01: Anos incluídos no projeto
ANOS = ["2021", "2022", "2023"]

# RF-06: Definição exata das 27 colunas finais
Q_COLS = [f"Q{str(i).zfill(3)}" for i in range(1, 26)]
COLUNAS_GOLD = Q_COLS + ['NOTA_MEDIA', 'TARGET']

def process_gold(ano):
    print(f"--- Iniciando Camada Gold: {ano} ---")
    silver_key = f"silver/enem/{ano}/microdados_silver_{ano}.csv"
    gold_key = f"gold/enem/{ano}/GOLD_ENEM_{ano}.csv"

    # 1. Leitura direta via Boto3 e BytesIO (Resolve o erro de UTF-8)
    print(f"[{ano}] Lendo dados da Silver...")
    response = s3.get_object(Bucket=BUCKET, Key=silver_key)
    
    # Lemos os bytes crus primeiro e encapsulamos em um buffer de memória
    raw_bytes = response['Body'].read()
    df = pd.read_csv(io.BytesIO(raw_bytes), encoding="latin-1", sep=";", low_memory=False)
    
    # 2. RF-05 e RN-02: Transformações
    provas = ['NU_NOTA_CN', 'NU_NOTA_CH', 'NU_NOTA_LC', 'NU_NOTA_MT', 'NU_NOTA_REDACAO']
    df['NOTA_MEDIA'] = df[provas].mean(axis=1).astype('float32') 
    
    mediana = df['NOTA_MEDIA'].median()
    df['TARGET'] = (df['NOTA_MEDIA'] >= mediana).astype('int8') 
    print(f"[{ano}] Mediana calculada: {mediana:.2f}")

    # RF-06: Filtro de colunas
    df_gold = df[COLUNAS_GOLD]
    
    # 3. Escrita direta via buffer de memória e Boto3
    print(f"[{ano}] Salvando no S3...")
    csv_buffer = io.StringIO()
    df_gold.to_csv(csv_buffer, encoding="latin-1", sep=";", index=False)
    
    s3.put_object(
        Bucket=BUCKET, 
        Key=gold_key, 
        Body=csv_buffer.getvalue().encode('latin-1')
    )
    
    # 4. RNF-03 e RNF-04: Validação de Volume
    tamanho_mb = s3.head_object(Bucket=BUCKET, Key=gold_key)['ContentLength'] / (1024 * 1024)
    print(f"[{ano}] Dataset Gold gerado: {df_gold.shape[1]} colunas | {tamanho_mb:.2f} MB\n")

# COMMAND ----------

for ano in ANOS:
    process_gold(ano)

# COMMAND ----------

print(f"""
Pipeline Gold Finalizado com Sucesso
---------------------------------------------------
Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M')}
Conformidade RF-05/RF-06: Sim (27 colunas + Target)
Conformidade RN-02: Sim (Mediana por ano)
Conformidade RNF-04: Volume monitorado por ano
Status: Pronto para carga Parquet/RDS
""")

# COMMAND ----------

# MAGIC %md
# MAGIC # Gold Layer — ENEM 2021/2022/2023
# MAGIC
# MAGIC ## Objetivo
# MAGIC Feature engineering sobre os dados da camada Silver, gerando as variáveis finais para o modelo de Machine Learning.
# MAGIC
# MAGIC ## Entrada
# MAGIC - `silver/enem/{ano}/microdados_silver_{ano}.csv`
# MAGIC - Anos processados: 2021, 2022, 2023
# MAGIC
# MAGIC ## Saída
# MAGIC - `gold/enem/{ano}/GOLD_ENEM_{ano}.csv`
# MAGIC - 27 colunas: Q001–Q025 + NOTA_MEDIA + TARGET
# MAGIC
# MAGIC ## Transformações aplicadas
# MAGIC
# MAGIC ### 1. Nota média geral
# MAGIC - Nova coluna: `NOTA_MEDIA`
# MAGIC - Cálculo: média aritmética de `NU_NOTA_CN`, `NU_NOTA_CH`, `NU_NOTA_LC`, `NU_NOTA_MT`, `NU_NOTA_REDACAO`
# MAGIC - Justificativa: representa o desempenho geral do candidato em uma única variável
# MAGIC
# MAGIC ### 2. Variável target binária
# MAGIC - Nova coluna: `TARGET`
# MAGIC - Valor 1: candidato com `NOTA_MEDIA` acima ou igual à mediana
# MAGIC - Valor 0: candidato com `NOTA_MEDIA` abaixo da mediana
# MAGIC - Justificativa: transforma o problema em classificação binária, facilitando a interpretação e o treinamento do modelo
# MAGIC
# MAGIC ### 3. Seleção de colunas
# MAGIC - Mantidas apenas as colunas relevantes para o modelo: Q001–Q025 + NOTA_MEDIA + TARGET
# MAGIC - One-hot encoding **não** aplicado nessa camada — deve ser feito no momento do treinamento
# MAGIC - Justificativa: evita explosão de colunas (222+), garante compatibilidade entre anos e mantém o arquivo em tamanho gerenciável
# MAGIC
# MAGIC ## Resultado
# MAGIC | Ano | Candidatos | Mediana | Colunas |
# MAGIC |-----|------------|---------|---------|
# MAGIC | 2021 | 2.238.107 | 527.32 | 27 |
# MAGIC | 2022 | 2.344.823 | 540.54 | 27 |
# MAGIC | 2023 | 2.678.264 | 539.18 | 27 |
