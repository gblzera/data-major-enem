# Projeto Data Major — Detalhes e Objetivo

**Disciplina:** Tópicos de Banco de Dados
**Instituição:** Centro Universitário IESB
**Semestre:** 2026
**Professor:** Rodrigo Gonçalves

---

## 1. Visão Geral

O **Projeto Data Major** consolida, de forma prática, os conteúdos de Tópicos de Banco de Dados: Big Data, modelos de dados, engenharia de dados (ETL) e mineração de dados. Construímos um pipeline completo (arquitetura Medallion na nuvem) sobre os microdados do ENEM e aplicamos uma técnica de classificação supervisionada.

---

## 2. Dataset — INEP / Microdados do ENEM

| Característica | Descrição |
|---------------|-----------|
| **Fonte oficial** | [gov.br/inep/microdados/enem](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem) |
| **Anos utilizados** | 2021, 2022, 2023 |
| **Tipo** | Estruturado (CSV, separador `;`, encoding latin-1) |
| **Volume bruto** | ~1,4–1,7 GB de CSV por edição |
| **Volume final (consumo)** | Parquet de ~50 MB (requisito de 30–60 MB do projeto) |

**Por que o ENEM?** Relevância social (principal porta de entrada ao ensino superior), riqueza do questionário socioeconômico, dados públicos e bem documentados, e forte potencial analítico.

---

## 3. Problema de Negócio

> **O perfil socioeconômico do candidato permite prever se sua nota fica acima ou abaixo da mediana — e quais fatores mais pesam?**

**Hipótese:** fatores como renda familiar, escolaridade/ocupação dos pais e acesso a tecnologia são fortes preditores do desempenho. Um modelo de classificação consegue capturar esse padrão com acurácia bem acima do acaso.

**Aplicações:** identificar perfis/grupos que mais precisam de reforço antes do exame; subsidiar políticas educacionais com base em evidência.

---

## 4. Objetivo

**Geral:** desenvolver um pipeline que **extrai** os microdados (2021–2023), **transforma** em features, **carrega** em formato otimizado (Parquet) e **aplica** mineração para classificação preditiva.

**Específicos:**

| # | Objetivo | Entregável |
|---|----------|------------|
| 1 | Automatizar a coleta do INEP | `extract.py` (Bronze no S3) |
| 2 | Implementar a arquitetura Medallion | Data Lake S3 (Bronze/Silver/Gold) |
| 3 | Criar a variável-alvo binária | Camada Gold + Parquet de consumo |
| 4 | Treinar a Árvore de Decisão | `05_mining_arvore.py` |
| 5 | Avaliar com métricas adequadas | Relatório de métricas + matriz/ROC |
| 6 | Identificar os fatores mais influentes | Importância de variáveis + Spearman |

---

## 5. Técnica de Mineração

**Árvore de Decisão** (scikit-learn) — escolhida por ser **interpretável** (gera regras legíveis), lidar bem com variáveis categóricas e não exigir normalização.

- **Features:** o questionário socioeconômico **Q001–Q025** (escolaridade/ocupação dos pais, renda, bens e acesso). O encoding ordinal é feito na mineração, não na Gold.
- **Variável-alvo:** `TARGET = 1` se `NOTA_MEDIA ≥ mediana do ano`, senão `0`. As medianas por edição são 2021 ≈ 527,3 · 2022 ≈ 540,5 · 2023 ≈ 539,2 (global ≈ 536,0); classes ficam ~50/50.
- **`NOTA_MEDIA`:** média aritmética das 5 provas (CN, CH, LC, MT, Redação).
- **Métricas:** Acurácia, Precisão, Recall, F1-Score, AUC-ROC e matriz de confusão; split estratificado 70/30.

> Variáveis demográficas/escola (sexo, cor/raça, UF, tipo de escola) foram **cogitadas**, mas o modelo entregue usa apenas o questionário socioeconômico — possível expansão futura.

---

## 6. Resultados Obtidos

Confirmando a hipótese, no conjunto de teste (2.178.359 candidatos):

| Métrica | Valor |
|---------|-------|
| Acurácia | 0,686 |
| Precisão | 0,692 |
| Recall | 0,672 |
| F1-Score | 0,682 |
| AUC-ROC | **0,749** |

**Hierarquia de fatores** (confirmada por Spearman *e* pela árvore): **Renda da família → Acesso a computador → Escolaridade dos pais** (escolaridade da mãe pesa no ramo de renda baixa; do pai, no de renda alta). Nº de pessoas na residência e motocicletas têm correlação levemente **negativa**.

---

## 7. Limitações e Considerações Éticas

- **Limitações:** a target pela mediana cria uma zona de fronteira; o questionário isolado impõe um teto de previsibilidade (~0,75 de AUC); a Árvore usa hiperparâmetros fixos.
- **Ética:** os dados são públicos e anonimizados pelo INEP; o objetivo é identificar padrões para apoiar políticas públicas, **não** discriminar indivíduos.

---

**Última atualização:** 2026-06-13 · **Autor:** Grupo 3 — Projeto Data Major
