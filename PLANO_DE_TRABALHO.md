# Plano de Trabalho — Projeto Data Major (concluído)

> Este documento foi o **plano de trabalho inicial** do projeto. As tarefas abaixo já foram
> executadas — ele fica como registro histórico. Para a documentação atual e correta, veja a
> pasta [`docs/`](docs/) e o [`README.md`](README.md).

---

## Contexto

Pipeline de Engenharia e Mineração de Dados sobre os microdados do ENEM (2021–2023), trabalho acadêmico de Tópicos de Banco de Dados (IESB). Arquitetura **Medallion** (Bronze → Silver → Gold → Parquet) sobre **AWS S3 + Databricks**. Pergunta de negócio: *o perfil socioeconômico do candidato prevê seu desempenho no ENEM, e quais fatores mais pesam?* Técnica: **Árvore de Decisão**.

**Apresentação:** 15/06/2026. **Stack real:** **pandas** + boto3/awswrangler (ETL no Databricks — o Spark foi avaliado, mas dispensado: os dados cabem em memória), scikit-learn (mineração), Parquet (consumo), PostgreSQL (carga complementar).

---

## O que foi entregue

- **Pipeline real** em `notebooks/pipeline/` (pandas): `extract` → `transform_silver` → `transform_gold` → `load_parquet` (+ `load_postgresql` opcional) → `05_mining_arvore`. Camadas Bronze/Silver/Gold em CSV; consumo em Parquet (`parquet/enem/`, particionado por `year`).
- **Apoio** em `notebooks/config/` (ambiente, credenciais, testes, checklist, cronograma, recursos) e **análise exploratória** em `notebooks/analysis/`.
- **Mineração validada:** Árvore de Decisão — Acurácia 0,686 · AUC-ROC 0,749 · mediana por ano (corte da TARGET). Fatores que mais pesam: renda → computador → escolaridade dos pais (confirmado por Spearman e pela árvore).
- **Documentação** reconciliada com o código em `docs/` (00–03 + arquitetura + dicionário) e `README.md`; painel em `dashboard/`.

---

## Regras de trabalho (mantidas)

- **Nunca commitar credenciais** — chaves AWS ficam em Databricks Secrets (escopo `aws-credentials`); o `.gitignore` bloqueia padrões de credencial e dados.
- **Não versionar os microdados** (públicos no INEP, pesados) — ignorados pelo `.gitignore`.
- Notebooks versionados em formato source `.py` (`# COMMAND ----------`), que sincroniza limpo com o Databricks Repos.
- Mensagens de commit descritivas, em português, no imperativo; branch por feature + PR para `main`.

---

*Plano original concluído. Documentação viva em [`docs/`](docs/).*
