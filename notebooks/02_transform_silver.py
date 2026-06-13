# Databricks notebook source
# MAGIC %md
# MAGIC # 02 — Transform: Camada Silver (limpeza e tratamento)
# MAGIC ### Projeto Data Major | Responsável: Bruno
# MAGIC
# MAGIC > ⚠️ **RECONSTRUÇÃO** a partir da lógica acordada no projeto. Exporte o notebook original do
# MAGIC > Databricks e substitua este arquivo se houver diferenças.
# MAGIC
# MAGIC **Objetivo:** ler a camada Bronze, aplicar filtros de presença, tratar valores ausentes e remover
# MAGIC duplicatas, gerando a camada **Silver** (dado limpo e confiável).

# COMMAND ----------

from pyspark.sql import functions as F

BUCKET = "enem-data-lake-gblzera"
ANOS = [2021, 2022, 2023]
Q_COLS = [f"Q{str(i).zfill(3)}" for i in range(1, 26)]
PROVAS = ["CN", "CH", "LC", "MT"]  # 4 provas objetivas

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Leitura da camada Bronze (CSV bruto do INEP)
# MAGIC O CSV do INEP usa separador `;` e encoding latin1.

# COMMAND ----------

def ler_bronze(ano):
    caminho = f"s3://{BUCKET}/bronze/enem/{ano}/MICRODADOS_ENEM_{ano}.csv"
    dfb = (spark.read
           .option("header", True)
           .option("sep", ";")
           .option("encoding", "latin1")
           .csv(caminho))
    return dfb.withColumn("year", F.lit(ano))

# une as três edições (mantendo só as colunas de interesse)
colunas_nota = [f"NU_NOTA_{p}" for p in PROVAS] + ["NU_NOTA_REDACAO"]
colunas_presenca = [f"TP_PRESENCA_{p}" for p in PROVAS]
colunas_interesse = ["NU_INSCRICAO", "year"] + colunas_presenca + colunas_nota + Q_COLS

dfs = []
for ano in ANOS:
    dfb = ler_bronze(ano)
    existentes = [c for c in colunas_interesse if c in dfb.columns]
    dfs.append(dfb.select(*existentes))

df = dfs[0]
for d in dfs[1:]:
    df = df.unionByName(d, allowMissingColumns=True)

print(f"Bronze unificado: {df.count():,} registros brutos.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Filtro de presença
# MAGIC Mantém apenas candidatos presentes nas 4 provas objetivas (TP_PRESENCA = 1). Ausentes (0) e
# MAGIC eliminados (2) não têm desempenho mensurável.

# COMMAND ----------

cond_presenca = None
for p in PROVAS:
    c = (F.col(f"TP_PRESENCA_{p}") == 1)
    cond_presenca = c if cond_presenca is None else (cond_presenca & c)

df_presente = df.filter(cond_presenca)
print(f"Após filtro de presença: {df_presente.count():,} registros.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Conversão de tipos das notas e remoção de notas inválidas

# COMMAND ----------

for c in colunas_nota:
    df_presente = df_presente.withColumn(c, F.col(c).cast("float"))

# remove registros com nota nula ou negativa em qualquer prova
cond_nota_valida = None
for c in colunas_nota:
    cc = (F.col(c).isNotNull()) & (F.col(c) >= 0)
    cond_nota_valida = cc if cond_nota_valida is None else (cond_nota_valida & cc)
df_limpo = df_presente.filter(cond_nota_valida)
print(f"Após validar notas: {df_limpo.count():,} registros.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Tratamento de valores ausentes no questionário
# MAGIC - **Categóricas (Q001–Q025, exceto Q005):** nulos → "Não informado" (preserva o registro).
# MAGIC - **Q005 (numérica — nº de pessoas na residência):** tratada à parte. Recebe sentinela `-1` para não
# MAGIC   corromper o tipo numérico com texto.

# COMMAND ----------

q_categoricas = [q for q in Q_COLS if q != "Q005"]
for q in q_categoricas:
    if q in df_limpo.columns:
        df_limpo = df_limpo.withColumn(q, F.when(F.col(q).isNull(), F.lit("Não informado")).otherwise(F.col(q)))

# Q005: numérica, sentinela -1 para ausência
if "Q005" in df_limpo.columns:
    df_limpo = df_limpo.withColumn("Q005", F.col("Q005").cast("int"))
    df_limpo = df_limpo.withColumn("Q005", F.when(F.col("Q005").isNull(), F.lit(-1)).otherwise(F.col("Q005")))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Remoção de duplicatas
# MAGIC Um registro único por candidato e edição (NU_INSCRICAO + year).

# COMMAND ----------

df_silver = df_limpo.dropDuplicates(["NU_INSCRICAO", "year"])
print(f"Silver final: {df_silver.count():,} registros.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Gravação da camada Silver (Parquet particionado por ano)

# COMMAND ----------

(df_silver.write
 .mode("overwrite")
 .partitionBy("year")
 .parquet(f"s3://{BUCKET}/silver/enem/"))
print("Silver gravada em s3://enem-data-lake-gblzera/silver/enem/")
