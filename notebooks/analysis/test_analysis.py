# Databricks notebook source
# MAGIC %pip install awswrangler

# COMMAND ----------

# Reinicia o Python após o %pip para o import de awswrangler funcionar (evita ModuleNotFoundError)
dbutils.library.restartPython()

# COMMAND ----------

# Nome "humano" de cada pergunta do questionário socioeconômico
PERGUNTAS = {
    "Q001": "Escolaridade do Pai",
    "Q002": "Escolaridade da Mãe",
    "Q003": "Ocupação do Pai",
    "Q004": "Ocupação da Mãe",
    "Q005": "Número de pessoas na residência",
    "Q006": "Renda mensal da família",
    "Q007": "Em sua residência trabalha empregado(a) doméstico(a)?",
    "Q008": "Tem banheiro?",
    "Q009": "Tem quartos para dormir?",
    "Q010": "Tem carro?",
    "Q011": "Tem motocicleta?",
    "Q012": "Tem geladeira?",
    "Q013": "Tem freezer?",
    "Q014": "Tem máquina de lavar roupa?",
    "Q015": "Tem máquina de secar roupa?",
    "Q016": "Tem forno micro-ondas?",
    "Q017": "Tem máquina de lavar louça?",
    "Q018": "Tem aspirador de pó?",
    "Q019": "Tem televisão em cores?",
    "Q020": "Tem aparelho de DVD?",
    "Q021": "Tem TV por assinatura?",
    "Q022": "Tem telefone celular?",
    "Q023": "Tem telefone fixo?",
    "Q024": "Tem computador?",
    "Q025": "Tem acesso à Internet?",
}

SIM_NAO = {"A": "Não", "B": "Sim"}

OCUPACAO = {
    "A": "Grupo 1 — Trabalho rural/extrativista (lavrador, pescador, etc.)",
    "B": "Grupo 2 — Serviços domésticos e comércio básico (diarista, vendedor, porteiro, etc.)",
    "C": "Grupo 3 — Trabalho técnico/industrial (operário, eletricista, motorista, etc.)",
    "D": "Grupo 4 — Nível médio/supervisão (professor médio, técnico, gerente, pequeno empresário, etc.)",
    "E": "Grupo 5 — Nível superior/direção (médico, engenheiro, advogado, diretor, etc.)",
    "F": "Não sei",
}

CONTAGEM_ATE4 = {
    "A": "Não tem",
    "B": "Sim, um(a)",
    "C": "Sim, dois/duas",
    "D": "Sim, três",
    "E": "Sim, quatro ou mais",
}

ALTERNATIVAS = {
    "Q001": {
        "A": "Nunca estudou",
        "B": "Fundamental incompleto (até 4ª série/5º ano)",
        "C": "Fundamental incompleto (até 8ª série/9º ano)",
        "D": "Fundamental completo, sem Ensino Médio",
        "E": "Ensino Médio completo, sem Faculdade",
        "F": "Faculdade completa, sem Pós-graduação",
        "G": "Pós-graduação completa",
        "H": "Não sei",
        "Não informado": "Não informou"
    },
    "Q002": {
        "A": "Nunca estudou",
        "B": "Fundamental incompleto (até 4ª série/5º ano)",
        "C": "Fundamental incompleto (até 8ª série/9º ano)",
        "D": "Fundamental completo, sem Ensino Médio",
        "E": "Ensino Médio completo, sem Faculdade",
        "F": "Faculdade completa, sem Pós-graduação",
        "G": "Pós-graduação completa",
        "H": "Não sei",
        "Não informado": "Não informou"
    },
    "Q003": OCUPACAO,
    "Q004": OCUPACAO,
    "Q006": {
        "A": "Nenhuma renda",
        "B": "Até ~1 salário mínimo",
        "C": "1 a 1,5 salários mínimos",
        "D": "1,5 a 2 salários mínimos",
        "E": "2 a 2,5 salários mínimos",
        "F": "2,5 a 3 salários mínimos",
        "G": "3 a 4 salários mínimos",
        "H": "4 a 5 salários mínimos",
        "I": "5 a 6 salários mínimos",
        "J": "6 a 7 salários mínimos",
        "K": "7 a 8 salários mínimos",
        "L": "8 a 9 salários mínimos",
        "M": "9 a 10 salários mínimos",
        "N": "10 a 12 salários mínimos",
        "O": "12 a 15 salários mínimos",
        "P": "15 a 20 salários mínimos",
        "Q": "Mais de 20 salários mínimos",
        "Não informado": "Não informou"
    },
    "Q007": {
        "A": "Não.",
        "B": "Sim, um ou dois dias por semana.",
        "C": "Sim, três ou quatro dias por semana.",
        "D": "Sim, pelo menos cinco dias por semana.",
    },
    "Q008": CONTAGEM_ATE4,
    "Q009": CONTAGEM_ATE4,
    "Q010": CONTAGEM_ATE4,
    "Q011": CONTAGEM_ATE4,
    "Q012": CONTAGEM_ATE4,
    "Q013": CONTAGEM_ATE4,
    "Q014": CONTAGEM_ATE4,
    "Q015": CONTAGEM_ATE4,
    "Q016": CONTAGEM_ATE4,
    "Q017": CONTAGEM_ATE4,
    "Q018": SIM_NAO,
    "Q019": CONTAGEM_ATE4,
    "Q020": SIM_NAO,
    "Q021": SIM_NAO,
    "Q022": CONTAGEM_ATE4,
    "Q023": SIM_NAO,
    "Q024": CONTAGEM_ATE4,
    "Q025": SIM_NAO,
}

# Q005 é numérica: o número JÁ é a resposta (quantas pessoas moram na casa).
# O valor -1 é uma marca técnica ("sentinela") que significa "candidato não respondeu".
LEGENDA_Q005 = "Número inteiro = quantas pessoas moram na casa (incluindo o candidato). -1 = não respondeu."


def traduzir(codigo_pergunta, letra):
    """Recebe o código da pergunta (ex: 'Q006') e a letra ('B') e devolve o texto legível."""
    if codigo_pergunta == "Q005":
        return LEGENDA_Q005
    mapa = ALTERNATIVAS.get(codigo_pergunta, {})
    return mapa.get(str(letra), f"(código {letra} sem tradução)")


def legenda_pergunta(codigo_pergunta):
    """Devolve uma linha de cabeçalho explicando a pergunta."""
    return f"{codigo_pergunta} = {PERGUNTAS.get(codigo_pergunta, 'pergunta desconhecida')}"


print("Dicionário de tradução carregado.")
print("Perguntas mapeadas:", len(PERGUNTAS))
print("Exemplo  ->", legenda_pergunta("Q006"))
print("Tradução ->", "Q006 = 'B' significa:", traduzir("Q006", "B"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Visualização do dataset final
# MAGIC
# MAGIC Leitura do Parquet consolidado (resultado do pipeline ETL). Aqui só inspecionamos: tamanho, colunas,
# MAGIC quantos candidatos por ano e se sobrou algum dado faltando.

# COMMAND ----------

import pandas as pd
import numpy as np
import awswrangler as wr
import boto3
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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

parquet_path = f"s3://{BUCKET}/parquet/enem/"
print(f"--- Lendo dataset final de {parquet_path} ---")

Q_COLS = [f"Q{str(i).zfill(3)}" for i in range(1, 26)]
colunas_analise = Q_COLS + ['NOTA_MEDIA']

df = wr.s3.read_parquet(
    path=parquet_path,
    dataset=True,
    columns=colunas_analise
)

q_cols_texto = [c for c in Q_COLS if c != 'Q005']
for col in q_cols_texto:
    df[col] = df[col].astype('object')
df['NOTA_MEDIA'] = df['NOTA_MEDIA'].astype('float32')

print(f"Dataset carregado: {df.shape[0]:,} registros | {df.shape[1]} colunas")
print(f"Anos presentes: {sorted(df['year'].unique().tolist())}")

# COMMAND ----------

print("--- Primeiras linhas do dataset (códigos crus, ainda sem tradução) ---")
display(df.head(20))

# COMMAND ----------

# Cria uma cópia traduzida apenas para exibição (NÃO altera o df original)
df_amostra_legivel = df.head(20).copy()
for col in q_cols_texto:
    df_amostra_legivel[col] = df_amostra_legivel[col].apply(lambda v: traduzir(col, v))
# Renomeia as colunas para o nome "humano" da pergunta
df_amostra_legivel = df_amostra_legivel.rename(columns={c: f"{c} — {PERGUNTAS[c]}" for c in Q_COLS})
print("--- Primeiras linhas TRADUZIDAS (pronto para leitura) ---")
display(df_amostra_legivel)

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
# MAGIC As variáveis socioeconômicas foram organizadas em grupos temáticos para facilitar a interpretação das análises e identificar possíveis relações com o desempenho dos candidatos no ENEM.
# MAGIC
# MAGIC | Grupo | Perguntas | O que esse grupo mede |
# MAGIC |-------|-----------|------------------------|
# MAGIC | **Escolaridade dos pais** | Q001, Q002 | Nível de escolaridade do pai e da mãe |
# MAGIC | **Ocupação dos pais** | Q003, Q004 | Tipo de ocupação profissional exercida pelos responsáveis |
# MAGIC | **Composição familiar e renda** | Q005, Q006 | Quantidade de moradores na residência e renda mensal familiar |
# MAGIC | **Condições domésticas e infraestrutura** | Q007–Q025 | Presença de empregado doméstico, acesso a bens de consumo e infraestrutura da residência |
# MAGIC | **Variável-alvo de desempenho** | NOTA_MEDIA | Média das notas do candidato no ENEM |

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
# MAGIC `NOTA_MEDIA` é a variável-chave. Abaixo, suas estatísticas gerais. **Consulte o glossário da Seção 0.1**
# MAGIC para o significado de cada termo (mean, std, mediana, skew, etc.).

# COMMAND ----------

print("--- Estatísticas gerais da NOTA_MEDIA ---")

stats_nm = df[variavel_desempenho].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).round(2)
stats_nm = stats_nm.to_frame(name='valor')

descricao_metricas = {
    'count': 'Número de candidatos (tamanho da amostra)',
    'mean': 'Média das notas (valor típico)',
    'std': 'Desvio padrão (dispersão das notas)',
    'min': 'Menor nota observada',
    '10%': 'Percentil 10 (10% abaixo deste valor)',
    '25%': 'Primeiro quartil (Q1)',
    '50%': 'Mediana (metade abaixo, metade acima)',
    '75%': 'Terceiro quartil (Q3)',
    '90%': 'Percentil 90 (10% acima deste valor)',
    'max': 'Maior nota observada'
}

stats_nm['descricao'] = stats_nm.index.map(descricao_metricas)
stats_nm = stats_nm[['valor', 'descricao']]

print(stats_nm.to_string())
print(f"\nAssimetria (skew): {df[variavel_desempenho].skew():.3f}")
print(f"Curtose:           {df[variavel_desempenho].kurtosis():.3f}")

# COMMAND ----------

print("--- Pontos de corte candidatos para definição futura da target ---")

cortes = pd.DataFrame({
    'Descricao': [
        'Valor central da distribuição (50% abaixo / 50% acima)',
        'Primeiro quartil - 25% menores valores',
        'Terceiro quartil - 75% menores valores',
        'Limite inferior dos tercis',
        'Limite superior dos tercis'
    ],
    'NOTA_MEDIA': [
        df[variavel_desempenho].median(),
        df[variavel_desempenho].quantile(0.25),
        df[variavel_desempenho].quantile(0.75),
        df[variavel_desempenho].quantile(1/3),
        df[variavel_desempenho].quantile(2/3),
    ]
}, index=[
    'Mediana (corte binário)',
    'Q1 (25%)',
    'Q3 (75%)',
    'Tercil inferior (33%)',
    'Tercil superior (66%)'
]).round(2)

display(cortes)

# COMMAND ----------

print("--- NOTA_MEDIA por ano (estatísticas comparativas) ---")
desc_ano = df.groupby('year', observed=True)[variavel_desempenho].agg(
    contagem='count',
    media='mean',
    mediana='median',
    desvio='std',
    minimo='min',
    q25=lambda x: x.quantile(0.25),
    q75=lambda x: x.quantile(0.75),
    maximo='max'
).round(2)

desc_ano = desc_ano.reset_index()
desc_ano = desc_ano.rename(columns={'year': 'ano'})

display(desc_ano)

# COMMAND ----------

fig, ax = plt.subplots(figsize=(11, 5))
sns.boxplot(data=df, x='year', y=variavel_desempenho, hue='year', palette='muted', legend=False, ax=ax)
ax.set_title('NOTA_MEDIA por ano — comparação de dispersão e medianas', fontsize=13, fontweight='bold')
ax.set_xlabel('Ano')
ax.set_ylabel('NOTA_MEDIA (média das 5 provas)')
# Caixa de legenda FORA da área do gráfico (à direita), para não cobrir as barras
texto_box = ("COMO LER O BOXPLOT:\n"
             "• Linha do meio da caixa = MEDIANA (nota do meio)\n"
             "• Caixa = metade central dos\n"
             "  candidatos (25% a 75%)\n"
             "• Hastes = alcance típico das notas\n"
             "• Pontos soltos = casos\n"
             "  extremos (outliers)")
fig.text(1.0, 0.5, texto_box, fontsize=8.5, va='center', ha='left',
         bbox=dict(boxstyle="round", facecolor="lightyellow", edgecolor="gray"))
plt.tight_layout()
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Estatística descritiva completa

# COMMAND ----------

print("--- 4.1 Estatística descritiva — variáveis numéricas ---")
numericas = [variavel_desempenho, 'Q005']
desc_num = df[numericas].describe().T
desc_num.insert(
    0,
    'variavel',
    ['NOTA_MEDIA', 'Q005']
)
desc_num['skew'] = df[numericas].skew()
desc_num['kurtosis'] = df[numericas].kurtosis()
desc_num = desc_num.round(3)
display(desc_num)

# COMMAND ----------

print("--- 4.2 Estatística descritiva — variáveis categóricas (Q001-Q025 exceto Q005) ---")
desc_cat = df[features_categoricas].describe().T
desc_cat.insert(0, 'questao', desc_cat.index)
desc_cat['freq_top_%'] = (desc_cat['freq'] / desc_cat['count'] * 100).round(2)
display(desc_cat)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Mesma tabela categórica, agora com NOME e MODA traduzidos
# MAGIC A tabela acima mostra a moda como letra (top = "E", por exemplo). A célula abaixo acrescenta o **nome
# MAGIC da pergunta** e **traduz a letra da moda** para texto, para leitura direta.

# COMMAND ----------

desc_cat_legivel = desc_cat.copy()
desc_cat_legivel.insert(0, 'Pergunta', [PERGUNTAS[c] for c in desc_cat_legivel.index])
desc_cat_legivel['top_traduzido'] = [traduzir(cod, letra)
                                     for cod, letra in zip(desc_cat_legivel.index, desc_cat_legivel['top'])]
display(desc_cat_legivel[['Pergunta', 'unique', 'top', 'top_traduzido', 'freq', 'freq_top_%']])

# COMMAND ----------

print("--- 4.3 Distribuição de Q001 (escolaridade do pai) — exemplo detalhado ---")
freq_q001 = df['Q001'].value_counts(normalize=True).sort_index() * 100
freq_q001 = freq_q001.round(2).rename('frequência (%)')
# Versão traduzida
tabela_q001 = freq_q001.to_frame()
tabela_q001.insert(0, 'Significado', [traduzir('Q001', letra) for letra in tabela_q001.index])
print(legenda_pergunta('Q001'))
display(tabela_q001)

# COMMAND ----------

print("--- 4.4 Distribuição de Q006 (renda familiar) — exemplo detalhado ---")
freq_q006 = df['Q006'].value_counts(normalize=True).sort_index() * 100
freq_q006 = freq_q006.round(2).rename('frequência (%)')
tabela_q006 = freq_q006.to_frame()
tabela_q006.insert(0, 'Faixa de renda', [traduzir('Q006', letra) for letra in tabela_q006.index])
print(legenda_pergunta('Q006'))
display(tabela_q006)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Histogramas (com legenda de leitura em cada gráfico)
# MAGIC
# MAGIC **O que é um histograma?** É um gráfico de barras que mostra **quantas vezes cada valor aparece**.
# MAGIC Barras mais altas = mais candidatos naquele ponto. Serve para ver o "formato" dos dados.

# COMMAND ----------

# Histograma da NOTA_MEDIA — global
plt.figure(figsize=(11, 5))
sns.histplot(data=df, x=variavel_desempenho, bins=60, kde=True, color='steelblue')
media_val = df[variavel_desempenho].mean()
mediana_val = df[variavel_desempenho].median()
plt.axvline(media_val, color='red', linestyle='--', linewidth=1.5, label=f'Média: {media_val:.1f}')
plt.axvline(mediana_val, color='green', linestyle='--', linewidth=1.5, label=f'Mediana: {mediana_val:.1f}')
plt.title('Histograma da NOTA_MEDIA — todos os anos consolidados', fontsize=13, fontweight='bold')
plt.xlabel('NOTA_MEDIA (média das 5 provas, de 0 a 1000)')
plt.ylabel('Número de candidatos')
plt.legend()
texto = ("COMO LER:\n"
         "• Eixo horizontal = faixa de nota\n"
         "• Altura da barra = quantos candidatos\n"
         "• Linha vermelha = média | verde = mediana\n"
         "• Estarem quase juntas confirma simetria")
plt.gcf().text(1.01, 0.5, texto, fontsize=8, va='center',
               bbox=dict(boxstyle="round", facecolor="lightyellow", edgecolor="gray"))
plt.tight_layout()
plt.show()

# COMMAND ----------

# Histograma da NOTA_MEDIA — facet por ano
g = sns.FacetGrid(df, col='year', height=4, aspect=1.1, sharey=False)
g.map_dataframe(sns.histplot, x=variavel_desempenho, bins=50, kde=True, color='steelblue')
g.set_titles('Ano: {col_name}')
g.set_axis_labels('NOTA_MEDIA (0 a 1000)', 'Número de candidatos')
g.fig.suptitle('Histograma da NOTA_MEDIA por ano — compare o deslocamento das curvas',
               fontsize=13, fontweight='bold', y=1.03)
plt.tight_layout()
plt.show()

# COMMAND ----------

# Histograma de Q005 (pessoas na residência)
plt.figure(figsize=(10, 5))
q005_valid = df[df['Q005'] >= 0]  # remove sentinela -1
sns.histplot(data=q005_valid, x='Q005', bins=range(1, 22), discrete=True, color='coral')
plt.title('Histograma de Q005 — Número de pessoas na residência', fontsize=13, fontweight='bold')
plt.xlabel('Q005 = quantas pessoas moram na casa (incluindo o candidato)')
plt.ylabel('Número de candidatos')
texto = ("COMO LER:\n"
         "• Cada barra = um tamanho de família\n"
         "• Pico em 3-4 pessoas = mais comum\n"
         "• Famílias de 10+ são raras\n")
plt.gcf().text(1.01, 0.5, texto, fontsize=8, va='center',
               bbox=dict(boxstyle="round", facecolor="lightyellow", edgecolor="gray"))
plt.tight_layout()
plt.show()

# COMMAND ----------

# Histograma de Q006 (renda familiar) — com legenda traduzida
plt.figure(figsize=(13, 6))
ordem_q006 = sorted(df['Q006'].dropna().unique())
sns.countplot(data=df, x='Q006', order=ordem_q006, color='mediumseagreen')
plt.title('Histograma de Q006 — Renda mensal da família', fontsize=13, fontweight='bold')
plt.xlabel('Faixa de renda (veja legenda à direita)')
plt.ylabel('Número de candidatos')
# Legenda traduzindo cada letra para a faixa de renda
linhas_legenda = [f"{letra} = {traduzir('Q006', letra)}" for letra in ordem_q006]
texto_legenda = "LEGENDA DAS FAIXAS (Q006):\n" + "\n".join(linhas_legenda)
plt.gcf().text(1.01, 0.5, texto_legenda, fontsize=8, va='center',
               bbox=dict(boxstyle="round", facecolor="honeydew", edgecolor="gray"))
plt.tight_layout()
plt.show()

# COMMAND ----------

# Histograma de Q001 (escolaridade do pai) — com legenda traduzida
plt.figure(figsize=(13, 6))
ordem_q001 = sorted(df['Q001'].dropna().unique())
sns.countplot(data=df, x='Q001', order=ordem_q001, color='slateblue')
plt.title('Histograma de Q001 — Escolaridade do Pai', fontsize=13, fontweight='bold')
plt.xlabel('Grau de escolaridade (veja legenda à direita)')
plt.ylabel('Número de candidatos')
linhas_legenda = [f"{letra} = {traduzir('Q001', letra)}" for letra in ordem_q001]
texto_legenda = "LEGENDA (Q001):\n" + "\n".join(linhas_legenda)
plt.gcf().text(1.01, 0.5, texto_legenda, fontsize=8, va='center',
               bbox=dict(boxstyle="round", facecolor="lavender", edgecolor="gray"))
plt.tight_layout()
plt.show()
