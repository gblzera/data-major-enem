# Databricks notebook source
# MAGIC %md
# MAGIC # Análise Exploratória — ENEM 2021/2022/2023
# MAGIC
# MAGIC ## Contexto
# MAGIC Notebook complementar ao pipeline ETL. **Não altera** os dados gerados pelas etapas
# MAGIC `extract` → `transform_silver` → `transform_gold` → `load_parquet`. Apenas consome o
# MAGIC Parquet final consolidado no S3 e realiza análise exploratória.
# MAGIC
# MAGIC ## Requisitos atendidos
# MAGIC 1. Visualização do dataset final
# MAGIC 2. Seleção de variáveis da análise
# MAGIC 3. Análise da variável NOTA_MEDIA (futura base da target)
# MAGIC 4. Estatística descritiva completa
# MAGIC 5. Histograma
# MAGIC
# MAGIC ## Entrada
# MAGIC - `s3://enem-data-lake-gblzera/parquet/enem/` (particionado por `year`)
# MAGIC - 26 colunas: Q001–Q025 + NOTA_MEDIA (+ partição `year`)
# MAGIC
# MAGIC > Obs.: a coluna `TARGET` existe no Parquet (gerada na Gold), mas neste notebook
# MAGIC > **não a usamos** — por decisão do time, a definição da target será revisitada
# MAGIC > posteriormente. Aqui analisamos `NOTA_MEDIA` diretamente como variável de desempenho.

# COMMAND ----------

# MAGIC %pip install awswrangler

# COMMAND ----------

# Correção: sem reiniciar o Python após o %pip, o import de awswrangler falhava
# (ModuleNotFoundError) e derrubava todas as células seguintes.
dbutils.library.restartPython()

# COMMAND ----------

import pandas as pd
import numpy as np
import awswrangler as wr
import boto3
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

AWS_ACCESS_KEY = dbutils.secrets.get(scope="aws-credentials", key="access-key")
AWS_SECRET_KEY = dbutils.secrets.get(scope="aws-credentials", key="secret-key")
REGION = "sa-east-1"
BUCKET = "enem-data-lake-gblzera"

boto3.setup_default_session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION
)

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams['figure.dpi'] = 100
plt.rcParams['font.size'] = 10

print("Bibliotecas importadas e sessão AWS configurada.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Visualização do dataset final
# MAGIC
# MAGIC Leitura do Parquet consolidado gerado pela etapa `04_load_parquet` e inspeção inicial:
# MAGIC primeiras linhas, dimensões, schema, distribuição por ano e checagem de nulos.

# COMMAND ----------

parquet_path = f"s3://{BUCKET}/parquet/enem/"
print(f"--- Lendo dataset final de {parquet_path} ---")

# Lê apenas as colunas necessárias para a análise (ignora TARGET por decisão de projeto)
Q_COLS = [f"Q{str(i).zfill(3)}" for i in range(1, 26)]
colunas_analise = Q_COLS + ['NOTA_MEDIA']

df = wr.s3.read_parquet(
    path=parquet_path,
    dataset=True,
    columns=colunas_analise
)

# Garantia de tipos para análise (category → object facilita describe e value_counts)
q_cols_texto = [c for c in Q_COLS if c != 'Q005']
for col in q_cols_texto:
    df[col] = df[col].astype('object')
df['NOTA_MEDIA'] = df['NOTA_MEDIA'].astype('float32')

print(f"Dataset carregado: {df.shape[0]:,} registros | {df.shape[1]} colunas")
print(f"Anos presentes: {sorted(df['year'].unique().tolist())}")

# COMMAND ----------

print("--- Primeiras linhas do dataset ---")
display(df.head(20))

# COMMAND ----------

print("--- Dimensões e schema ---")
print(f"Linhas: {df.shape[0]:,}")
print(f"Colunas: {df.shape[1]}")
print()
print("Schema (dtypes):")
print(df.dtypes.to_string())
print()
print(f"Uso de memória total: {df.memory_usage(deep=True).sum() / (1024*1024):.2f} MB")

# COMMAND ----------

print("--- Distribuição de registros por ano ---")
contagem_ano = df['year'].value_counts().sort_index()
for ano, qtd in contagem_ano.items():
    print(f"   {ano}: {qtd:,} candidatos")
print(f"   TOTAL: {contagem_ano.sum():,}")

# COMMAND ----------

print("--- Verificação de nulos ---")
nulos = df.isna().sum()
nulos_nao_zero = nulos[nulos > 0]
if len(nulos_nao_zero) == 0:
    print("Nenhuma coluna apresenta valores nulos (tratamento da Silver foi efetivo).")
else:
    print(nulos_nao_zero.to_string())

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Seleção de variáveis da análise
# MAGIC
# MAGIC O dataset final tem 26 colunas analisadas + a partição `year`. Para fins de análise
# MAGIC exploratória e futura modelagem, separamos:
# MAGIC
# MAGIC - **Variável de desempenho:** `NOTA_MEDIA` — média das 5 provas; será a base para
# MAGIC   definição posterior da target.
# MAGIC - **Features categóricas:** Q001–Q004 e Q006–Q025 (questionário socioeconômico).
# MAGIC - **Feature numérica:** Q005 (quantidade de pessoas na residência).
# MAGIC - **Variável de partição:** `year` — usada para comparação temporal, não como feature direta.
# MAGIC
# MAGIC ### Justificativa por grupo
# MAGIC
# MAGIC | Grupo | Variáveis | Por que entram |
# MAGIC |-------|-----------|----------------|
# MAGIC | Escolaridade dos pais | Q001, Q002, Q003, Q004 | Literatura aponta forte correlação com desempenho escolar |
# MAGIC | Renda / trabalho | Q005, Q006, Q007, Q008 | Indicadores diretos de condição socioeconômica |
# MAGIC | Bens e acesso | Q009–Q024 | Proxy de capital econômico e cultural da família |
# MAGIC | Tipo de escola | Q025 | Distingue ensino público de privado |

# COMMAND ----------

features_categoricas = [c for c in Q_COLS if c != 'Q005']
features_numericas = ['Q005']
variavel_desempenho = 'NOTA_MEDIA'

print(f"Variável de desempenho: {variavel_desempenho}")
print(f"Features categóricas ({len(features_categoricas)}): {features_categoricas}")
print(f"Features numéricas ({len(features_numericas)}): {features_numericas}")
print(f"Total de variáveis explicativas potenciais: {len(features_categoricas) + len(features_numericas)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Análise da variável NOTA_MEDIA
# MAGIC
# MAGIC `NOTA_MEDIA` é a variável-chave do dataset: representa o desempenho geral do candidato
# MAGIC e será a base para qualquer definição futura da variável-alvo (classificação binária
# MAGIC por mediana, classificação multiclasse por quartis, regressão direta, etc.).
# MAGIC
# MAGIC Aqui analisamos sua distribuição global, por ano, e os principais pontos de corte
# MAGIC candidatos (mediana, quartis, terços).

# COMMAND ----------

print("--- Estatísticas gerais da NOTA_MEDIA ---")
stats_nm = df[variavel_desempenho].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).round(2)
print(stats_nm.to_string())
print(f"\nAssimetria (skew): {df[variavel_desempenho].skew():.3f}")
print(f"Curtose:           {df[variavel_desempenho].kurtosis():.3f}")

# COMMAND ----------

print("--- Pontos de corte candidatos para definição futura da target ---")
cortes = pd.DataFrame({
    'Mediana (corte binário)': [df[variavel_desempenho].median()],
    'Q1 (25%)': [df[variavel_desempenho].quantile(0.25)],
    'Q3 (75%)': [df[variavel_desempenho].quantile(0.75)],
    'Tercil inferior (33%)': [df[variavel_desempenho].quantile(1/3)],
    'Tercil superior (66%)': [df[variavel_desempenho].quantile(2/3)],
}).T.round(2)
cortes.columns = ['NOTA_MEDIA']
display(cortes)

# COMMAND ----------

print("--- NOTA_MEDIA por ano (estatísticas comparativas) ---")
desc_ano = df.groupby('year')[variavel_desempenho].agg(
    contagem='count',
    media='mean',
    mediana='median',
    desvio='std',
    minimo='min',
    q25=lambda x: x.quantile(0.25),
    q75=lambda x: x.quantile(0.75),
    maximo='max'
).round(2)
display(desc_ano)

# COMMAND ----------

# Boxplot da NOTA_MEDIA por ano — visualiza variação temporal e dispersão
plt.figure(figsize=(10, 5))
sns.boxplot(data=df, x='year', y=variavel_desempenho, palette='muted')
plt.title('NOTA_MEDIA por ano — comparação de dispersão e medianas',
          fontsize=13, fontweight='bold')
plt.xlabel('Ano')
plt.ylabel('NOTA_MEDIA (média das 5 provas)')
plt.tight_layout()
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Estatística descritiva completa

# COMMAND ----------

print("--- 4.1 Estatística descritiva — variáveis numéricas ---")
numericas = [variavel_desempenho, 'Q005']
desc_num = df[numericas].describe().T
desc_num['skew'] = df[numericas].skew()
desc_num['kurtosis'] = df[numericas].kurtosis()
desc_num = desc_num.round(3)
display(desc_num)

# COMMAND ----------

print("--- 4.2 Estatística descritiva — variáveis categóricas (Q001-Q025 exceto Q005) ---")
desc_cat = df[features_categoricas].describe().T
desc_cat['freq_top_%'] = (desc_cat['freq'] / desc_cat['count'] * 100).round(2)
display(desc_cat)

# COMMAND ----------

print("--- 4.3 Distribuição de Q001 (escolaridade do pai) — exemplo detalhado ---")
freq_q001 = df['Q001'].value_counts(normalize=True).sort_index() * 100
freq_q001 = freq_q001.round(2).rename('frequência (%)')
display(freq_q001.to_frame())

# COMMAND ----------

print("--- 4.4 Distribuição de Q006 (renda familiar) — exemplo detalhado ---")
freq_q006 = df['Q006'].value_counts(normalize=True).sort_index() * 100
freq_q006 = freq_q006.round(2).rename('frequência (%)')
display(freq_q006.to_frame())

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Histogramas
# MAGIC
# MAGIC - **NOTA_MEDIA:** distribuição geral e por ano — mostra a forma da distribuição
# MAGIC   (aproximadamente normal, com leve cauda à direita).
# MAGIC - **Q005:** distribuição numérica direta (pessoas na residência).
# MAGIC - **Q006:** distribuição categórica ordinal (renda familiar de A a Q).
# MAGIC - **Q001:** distribuição categórica ordinal (escolaridade do pai de A a H).

# COMMAND ----------

# Histograma da NOTA_MEDIA — global, com linhas de média e mediana
plt.figure(figsize=(11, 5))
sns.histplot(data=df, x=variavel_desempenho, bins=60, kde=True, color='steelblue')
plt.axvline(df[variavel_desempenho].mean(), color='red', linestyle='--', linewidth=1.5,
            label=f'Média: {df[variavel_desempenho].mean():.1f}')
plt.axvline(df[variavel_desempenho].median(), color='green', linestyle='--', linewidth=1.5,
            label=f'Mediana: {df[variavel_desempenho].median():.1f}')
plt.title('Histograma da NOTA_MEDIA — todos os anos consolidados',
          fontsize=13, fontweight='bold')
plt.xlabel('NOTA_MEDIA (média das 5 provas)')
plt.ylabel('Frequência')
plt.legend()
plt.tight_layout()
plt.show()

# COMMAND ----------

# Histograma da NOTA_MEDIA — facet por ano
g = sns.FacetGrid(df, col='year', height=4, aspect=1.1, sharey=False)
g.map_dataframe(sns.histplot, x=variavel_desempenho, bins=50, kde=True, color='steelblue')
g.set_titles('Ano: {col_name}')
g.set_axis_labels('NOTA_MEDIA', 'Frequência')
g.fig.suptitle('Histograma da NOTA_MEDIA por ano',
               fontsize=13, fontweight='bold', y=1.03)
plt.tight_layout()
plt.show()

# COMMAND ----------

# Histograma de Q005 (pessoas na residência — única variável numérica do questionário)
plt.figure(figsize=(10, 5))
q005_valid = df[df['Q005'] >= 0]  # remove sentinela -1, se houver
sns.histplot(data=q005_valid, x='Q005', bins=range(1, 22),
             discrete=True, color='coral')
plt.title('Histograma de Q005 — Número de pessoas na residência',
          fontsize=13, fontweight='bold')
plt.xlabel('Q005 (pessoas)')
plt.ylabel('Frequência')
plt.tight_layout()
plt.show()

# COMMAND ----------

# Histograma de Q006 (renda familiar — categórica ordinal)
plt.figure(figsize=(12, 5))
ordem_q006 = sorted(df['Q006'].dropna().unique())
sns.countplot(data=df, x='Q006', order=ordem_q006, color='mediumseagreen')
plt.title('Histograma de Q006 — Renda familiar mensal (A = sem renda, Q = maior faixa)',
          fontsize=13, fontweight='bold')
plt.xlabel('Q006 (faixa de renda)')
plt.ylabel('Frequência')
plt.tight_layout()
plt.show()

# COMMAND ----------

# Histograma de Q001 (escolaridade do pai — categórica ordinal)
plt.figure(figsize=(11, 5))
ordem_q001 = sorted(df['Q001'].dropna().unique())
sns.countplot(data=df, x='Q001', order=ordem_q001, color='slateblue')
plt.title('Histograma de Q001 — Escolaridade do pai (A = nunca estudou, H = pós-graduação)',
          fontsize=13, fontweight='bold')
plt.xlabel('Q001 (faixa de escolaridade)')
plt.ylabel('Frequência')
plt.tight_layout()
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Resumo
# MAGIC
# MAGIC | # | Item solicitado | Onde foi atendido |
# MAGIC |---|------------------|-------------------|
# MAGIC | 1 | Visualização do dataset final | Seção 1 (head, schema, contagens, nulos) |
# MAGIC | 2 | Seleção de variáveis da análise | Seção 2 (separação explícita por grupo) |
# MAGIC | 3 | Análise da NOTA_MEDIA (base da futura target) | Seção 3 (estatísticas, cortes candidatos, boxplot por ano) |
# MAGIC | 4 | Estatística descritiva completa | Seção 4 (numéricas, categóricas, exemplos detalhados) |
# MAGIC | 5 | Histograma | Seção 5 (NOTA_MEDIA global e por ano, Q005, Q006, Q001) |

# COMMAND ----------

print(f"""
Análise Exploratória Finalizada
---------------------------------------------------
Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M')}
Registros analisados: {len(df):,}
Variáveis explicativas mapeadas: {len(features_categoricas) + len(features_numericas)}
Pipeline ETL: não alterado
Definição da target: pendente (decisão do time)
Status: Análise pronta para apoiar a próxima decisão de modelagem
""")
