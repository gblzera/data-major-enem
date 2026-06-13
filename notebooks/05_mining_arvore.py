# Databricks notebook source
# MAGIC %md
# MAGIC # 05 — Mineração: Árvore de Decisão (ENEM 2021–2023)
# MAGIC ### Projeto Data Major | Camada de Mineração
# MAGIC
# MAGIC Técnica escolhida: **Árvore de Decisão** (classificação supervisionada) para prever se a nota do
# MAGIC candidato fica acima ou abaixo da mediana, a partir do questionário socioeconômico.
# MAGIC
# MAGIC **Por que Árvore de Decisão?**
# MAGIC 1. **Interpretável** — gera regras legíveis ("se renda ≤ X então tende a ficar abaixo").
# MAGIC 2. **Lida bem com variáveis categóricas** do questionário (Q001–Q025).
# MAGIC 3. **Não exige normalização** nem premissas de distribuição.
# MAGIC 4. **Base para evolução** — comparação futura com ensembles.
# MAGIC
# MAGIC > Target: `1` se `NOTA_MEDIA ≥ mediana`, senão `0`. Balanceada por construção.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Setup e carga do dataset (Parquet consolidado)

# COMMAND ----------

import boto3
import awswrangler as wr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr
from sklearn.tree import DecisionTreeClassifier, plot_tree, export_text
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             roc_auc_score, confusion_matrix, classification_report, roc_curve)

RANDOM_STATE = 42
Q_COLS = [f"Q{str(i).zfill(3)}" for i in range(1, 26)]
sns.set_theme(style="whitegrid")
plt.rcParams['figure.dpi'] = 110

NOMES = {
    "Q001": "Escolaridade do Pai", "Q002": "Escolaridade da Mãe",
    "Q003": "Ocupação do Pai", "Q004": "Ocupação da Mãe",
    "Q005": "Pessoas na residência", "Q006": "Renda da família",
    "Q007": "Empregado doméstico", "Q008": "Banheiros", "Q009": "Quartos",
    "Q010": "Carros", "Q011": "Motocicletas", "Q012": "Geladeira", "Q013": "Freezer",
    "Q014": "Máq. lavar roupa", "Q015": "Máq. secar", "Q016": "Máq. lavar louça",
    "Q017": "Micro-ondas", "Q018": "Aspirador", "Q019": "Televisões",
    "Q020": "DVD", "Q021": "TV assinatura", "Q022": "Celulares",
    "Q023": "Telefone fixo", "Q024": "Computadores", "Q025": "Internet",
}
NAO_SEI = {'Q001': 'H', 'Q002': 'H', 'Q003': 'F', 'Q004': 'F'}

AWS_ACCESS_KEY = dbutils.secrets.get(scope="aws-credentials", key="access-key")
AWS_SECRET_KEY = dbutils.secrets.get(scope="aws-credentials", key="secret-key")
boto3.setup_default_session(aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_KEY, region_name="sa-east-1")

df = wr.s3.read_parquet(path="s3://enem-data-lake-gblzera/parquet/enem/", dataset=True)
df['Q005'] = df['Q005'].astype(int)
df['NOTA_MEDIA'] = df['NOTA_MEDIA'].astype('float32')
print(f"Registros: {df.shape[0]:,} | Colunas: {df.shape[1]}")
print(f"Anos: {sorted(df['year'].astype(str).unique().tolist())}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Estatística parcial — quais fatores se associam à nota? (Spearman)

# COMMAND ----------

qs = [q for q in Q_COLS if q != 'Q005']
dfs = df.copy()
for q in qs:
    s = dfs[q].astype(object)
    # sentinela de ausência da Silver ("Não informado") → NaN, para não virar um
    # nível ordinal espúrio no meio da escala (capital "N" ordena entre as letras)
    s = s.where(s != "Não informado", other=np.nan)
    if q in NAO_SEI:
        s = s.where(s != NAO_SEI[q], other=np.nan)
    dfs[q] = pd.Series(pd.Categorical(s, ordered=True).codes, index=dfs.index).replace(-1, np.nan)
dfs['Q005'] = dfs['Q005'].replace(-1, np.nan).astype(float)

res = []
for q in qs + ['Q005']:
    rho, pval = spearmanr(dfs[q], dfs['NOTA_MEDIA'], nan_policy='omit')
    res.append({'variavel': q, 'fator': NOMES.get(q, q),
                'spearman_rho': round(rho, 4), 'magnitude': abs(round(rho, 4))})
spearman_df = pd.DataFrame(res).sort_values('magnitude', ascending=False)
display(spearman_df)

# COMMAND ----------

top = spearman_df.head(15).iloc[::-1]
cores = ['seagreen' if v > 0 else 'salmon' for v in top['spearman_rho']]
plt.figure(figsize=(9, 7))
plt.barh(top['fator'], top['spearman_rho'], color=cores)
plt.axvline(0, color='black', linewidth=0.8)
plt.title('Correlação de Spearman com a NOTA_MEDIA (Top 15 fatores)', fontsize=12, fontweight='bold')
plt.xlabel('ρ de Spearman (positivo = mais do fator, maior a nota)')
plt.tight_layout()
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Preparação dos dados para a Árvore de Decisão

# COMMAND ----------

features = [c for c in Q_COLS if c != 'Q005'] + ['Q005']
X = df[features].copy()

# Fonte única da verdade: consome a TARGET já engenheirada na Gold (03_transform_gold),
# em vez de recalcular a mediana aqui — evita duas definições de corte no mesmo pipeline.
y = df['TARGET'].astype(int)
# Mediana recalculada apenas para conferência/relatório (em float64, deve bater com a Gold ≈ 536,0).
mediana = df['NOTA_MEDIA'].astype('float64').median()
print(f"Mediana da nota (conferência): {mediana:.1f}")
print(f"Distribuição da target (da Gold):\n{y.value_counts(normalize=True).round(3)}")

cat_cols = [c for c in Q_COLS if c != 'Q005']
# sentinela de ausência da Silver ("Não informado") → NaN em todas as categóricas,
# para o OrdinalEncoder não lhe atribuir um código ordinal no meio da escala
X[cat_cols] = X[cat_cols].replace("Não informado", np.nan)
for col, letra in NAO_SEI.items():
    X[col] = X[col].astype(object)
    X.loc[X[col] == letra, col] = np.nan
# Q005 (numérica): sentinela -1 de ausência → NaN, espelhando o tratamento do Spearman
# (DecisionTreeClassifier do scikit-learn ≥1.4 lida com NaN nativamente)
X['Q005'] = X['Q005'].replace(-1, np.nan)
encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1, encoded_missing_value=-1)
X[cat_cols] = encoder.fit_transform(X[cat_cols])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.30, random_state=RANDOM_STATE, stratify=y)
print(f"Treino: {len(X_train):,} | Teste: {len(X_test):,}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Treino da Árvore de Decisão

# COMMAND ----------

arvore = DecisionTreeClassifier(
    criterion='entropy', max_depth=6, min_samples_leaf=5,
    random_state=RANDOM_STATE, class_weight='balanced')
arvore.fit(X_train, y_train)
print("Árvore de Decisão treinada.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Resultados — métricas no teste

# COMMAND ----------

y_pred = arvore.predict(X_test)
y_proba = arvore.predict_proba(X_test)[:, 1]

metricas = {
    'Acurácia':  accuracy_score(y_test, y_pred),
    'Precisão':  precision_score(y_test, y_pred),
    'Recall':    recall_score(y_test, y_pred),
    'F1-Score':  f1_score(y_test, y_pred),
    'AUC-ROC':   roc_auc_score(y_test, y_proba),
}
print("--- Métricas da Árvore de Decisão (conjunto de teste) ---")
for nome, val in metricas.items():
    print(f"  {nome:<10}: {val:.4f}")
print("\n--- Relatório de classificação ---")
print(classification_report(y_test, y_pred, digits=4, target_names=['Abaixo', 'Acima']))

# COMMAND ----------

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax1,
            xticklabels=['Abaixo', 'Acima'], yticklabels=['Abaixo', 'Acima'])
ax1.set_title('Matriz de Confusão'); ax1.set_xlabel('Predito'); ax1.set_ylabel('Real')

fpr, tpr, _ = roc_curve(y_test, y_proba)
ax2.plot(fpr, tpr, color='steelblue', linewidth=2, label=f"AUC = {metricas['AUC-ROC']:.3f}")
ax2.plot([0, 1], [0, 1], 'k--', alpha=0.4, label='Aleatório (0.50)')
ax2.set_xlabel('Falsos Positivos'); ax2.set_ylabel('Verdadeiros Positivos')
ax2.set_title('Curva ROC'); ax2.legend(loc='lower right'); ax2.grid(alpha=0.3)
plt.tight_layout()
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Interpretabilidade — a árvore e suas regras

# COMMAND ----------

imp = pd.DataFrame({
    'fator': [NOMES.get(c, c) for c in X.columns],
    'importancia': arvore.feature_importances_
}).sort_values('importancia', ascending=False).head(10)
plt.figure(figsize=(9, 6))
plt.barh(imp['fator'][::-1], imp['importancia'][::-1], color='steelblue')
plt.title('Variáveis mais importantes para a Árvore de Decisão (Top 10)', fontsize=12, fontweight='bold')
plt.xlabel('Importância')
plt.tight_layout()
plt.show()
display(imp)

# COMMAND ----------

plt.figure(figsize=(20, 9))
plot_tree(arvore, max_depth=3, feature_names=[NOMES.get(c, c) for c in X.columns],
          class_names=['Abaixo', 'Acima'], filled=True, rounded=True, fontsize=9, proportion=True)
plt.title('Árvore de Decisão — primeiros 3 níveis', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()

# COMMAND ----------

print("REGRAS DE DECISÃO (primeiros 3 níveis):\n")
print(export_text(arvore, feature_names=[NOMES.get(c, c) for c in X.columns], max_depth=3))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Conclusões parciais
# MAGIC - **Fatores socioeconômicos se associam à nota** — renda, computador e infraestrutura lideram.
# MAGIC - **Árvore atinge ~0,685 de acurácia / 0,747 AUC** — coerente com a literatura.
# MAGIC - **A técnica entrega regras legíveis** — além de prever, explica.
# MAGIC
# MAGIC ### Próximos passos
# MAGIC - Comparar com ensembles (Extra Trees, Gradient Boosting) + teste de significância.
# MAGIC - Clustering de perfis (K-Means). Análise temporal (2021 vs 2022 vs 2023).
