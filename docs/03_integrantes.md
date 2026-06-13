# Projeto Data Major — Integrantes e Responsabilidades

## 1. Composição do Grupo

| # | Nome | Papel | Notebook(s) |
|---|------|-------|-------------|
| 01 | Davi Serra Bezerra | Extract | `pipeline/extract.py` |
| 02 | Bruno Brudó | Transform (Silver + Gold) | `pipeline/transform_silver.py`, `pipeline/transform_gold.py` |
| 03 | Vinicius von Glehn Severo | Load | `pipeline/load_parquet.py`, `pipeline/load_postgresql.py` |
| 04 | Gabriel dos Santos Silva | Data Mining | `pipeline/05_mining_arvore.py` |
| 05 | Gabriel Henrique Kuhn Paz | Tech Lead | Infra, integração e apoio geral |

> Bruno acumula Transform Silver e Gold. A análise exploratória (`analysis/`) é material de apoio que apenas lê o Parquet.

---

## 2. Responsabilidades

### Extract — Davi
Baixar os microdados do INEP (2021–2023) e subir o CSV para a Bronze do S3 em streaming (sem disco local), identificando o CSV correto dentro do ZIP.

### Transform Silver — Bruno
Ler a Bronze, filtrar presença nas 4 provas, tratar nulos (categóricas → "Não informado"; Q005 → `-1`), remover duplicatas e gravar a Silver em CSV por ano.

### Transform Gold — Bruno
Criar `NOTA_MEDIA` (média das 5 provas) e `TARGET` (mediana **por ano**), selecionar as 27 colunas finais (Q001–Q025 + NOTA_MEDIA + TARGET) e gravar a Gold em CSV. O encoding é deixado para a mineração.

### Load — Vinicius
- **`load_parquet.py`** (obrigatório): consolida os 3 CSVs da Gold num Parquet único em `parquet/enem/` (`awswrangler`, zstd, particionado por `year`, ~50 MB) — é o que a mineração consome.
- **`load_postgresql.py`** (complementar/opcional): carga relacional no RDS PostgreSQL (schemas `raw`/`tru`/`ref`, tabela `microdados`), com a instância ligada/desligada por custo. Leitura dos CSVs em chunks para não estourar memória.

### Data Mining — Gabriel dos Santos Silva
Ler o Parquet, codificar as categóricas (OrdinalEncoder), treinar a Árvore de Decisão, avaliar (Acurácia/Precisão/Recall/F1/AUC + matriz/ROC), e interpretar (importância de variáveis, Spearman, regras da árvore).

### Tech Lead — Gabriel Henrique Kuhn Paz
Infraestrutura (S3, RDS, Databricks, Secrets), acessos, integração end-to-end, code review, apoio técnico e coordenação da apresentação.

---

## 3. Fluxo de Dependências

```
extract (Davi) → transform_silver (Bruno) → transform_gold (Bruno) → load_parquet (Vinicius) → 05_mining_arvore (Gabriel S.)
                                                                          └→ load_postgresql (Vinicius, opcional)
```

Cada etapa depende da anterior estar completa.

---

## 4. Avaliação

> "O professor poderá atribuir parte da nota ao domínio individual a partir de perguntas direcionadas a cada integrante sobre sua responsabilidade e sobre o projeto como um todo."

**Todos devem entender o pipeline completo**, não apenas a própria etapa.

---

**Última atualização:** 2026-06-13 · **Autor:** Tech Lead (Gabriel H. K. Paz)
