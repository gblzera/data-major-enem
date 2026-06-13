# Databricks notebook source
# MAGIC %md
# MAGIC # 03 — Transform: Camada Gold (feature engineering e target)
# MAGIC ### Projeto Data Major | Responsável: Bruno
# MAGIC
# MAGIC > ⚠️ **RECONSTRUÇÃO** a partir da lógica acordada no projeto. Exporte o original do Databricks e
# MAGIC > substitua se houver diferenças.
# MAGIC
# MAGIC **Objetivo:** ler a camada Silver, criar a NOTA_MEDIA e a variável-alvo (TARGET) binária pela
# MAGIC mediana, gerando a camada **Gold** (pronta para a mineração).
# MAGIC
# MAGIC > **Decisão de projeto:** o encoding das categóricas NÃO é feito aqui — fica na etapa de mineração,
# MAGIC > para manter a Gold legível e flexível a diferentes técnicas de codificação.

# COMMAND ----------

from pyspark.sql import functions as F

BUCKET = "enem-data-lake-gblzera"
PROVAS = ["CN", "CH", "LC", "MT"]
COLS_NOTA = [f"NU_NOTA_{p}" for p in PROVAS] + ["NU_NOTA_REDACAO"]

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Leitura da camada Silver

# COMMAND ----------

df = spark.read.parquet(f"s3://{BUCKET}/silver/enem/")
print(f"Silver: {df.count():,} registros.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. NOTA_MEDIA — média aritmética das 5 provas
# MAGIC O ENEM não divulga média oficial; calculamos a média das 5 áreas (4 objetivas + redação).

# COMMAND ----------

soma = None
for c in COLS_NOTA:
    soma = F.col(c) if soma is None else (soma + F.col(c))
df = df.withColumn("NOTA_MEDIA", (soma / F.lit(len(COLS_NOTA))).cast("float"))
print("NOTA_MEDIA criada.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Variável-alvo (TARGET) — binária pela mediana
# MAGIC `TARGET = 1` se `NOTA_MEDIA ≥ mediana`, senão `0`.
# MAGIC
# MAGIC > A mediana é calculada de forma global (consolidando as três edições) para um corte único.
# MAGIC > Pela mediana, as classes ficam balanceadas (~50/50), evitando viés de classe.

# COMMAND ----------

# mediana global (aproximada — approxQuantile é eficiente em grande volume)
mediana = df.approxQuantile("NOTA_MEDIA", [0.5], 0.001)[0]
print(f"Mediana global da NOTA_MEDIA: {mediana:.2f}")

df = df.withColumn("TARGET", F.when(F.col("NOTA_MEDIA") >= F.lit(mediana), 1).otherwise(0))

# checagem de balanceamento
display(df.groupBy("TARGET").count().orderBy("TARGET"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Seleção das features finais e gravação da Gold
# MAGIC Mantém o questionário (Q001–Q025), a NOTA_MEDIA, a TARGET e o ano.

# COMMAND ----------

Q_COLS = [f"Q{str(i).zfill(3)}" for i in range(1, 26)]
cols_finais = [c for c in Q_COLS if c in df.columns] + ["NOTA_MEDIA", "TARGET", "year"]
df_gold = df.select(*cols_finais)

(df_gold.write
 .mode("overwrite")
 .partitionBy("year")
 .parquet(f"s3://{BUCKET}/gold/enem/"))
print(f"Gold gravada: {df_gold.count():,} registros em s3://{BUCKET}/gold/enem/")
