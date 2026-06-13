# Plano de Trabalho — Projeto Data Major (instruções para o Claude Code)

> Este documento orienta o **Claude Code** a montar, validar e evoluir o repositório do projeto
> Data Major localmente, mantendo sincronia com o Databricks via Git. Leia tudo antes de começar.

---

## Contexto do projeto

Pipeline de Engenharia e Mineração de Dados sobre os microdados do ENEM (2021–2023), trabalho acadêmico
da disciplina Tópicos de Banco de Dados (IESB). Arquitetura Medallion (Bronze→Silver→Gold→Parquet) sobre
AWS S3 + Databricks. A pergunta de negócio é: *o perfil socioeconômico do candidato prevê seu desempenho
no ENEM, e quais fatores mais pesam?* Técnica de mineração: Árvore de Decisão.

**Apresentação final:** 15/06/2026. **Stack:** PySpark (ETL), scikit-learn (mineração), Parquet, PostgreSQL.

---

## Estado atual do repositório

Os arquivos abaixo **já existem** neste pacote e estão prontos:

```
data-major-enem/
├── README.md                      ✅ pronto
├── .gitignore                     ✅ pronto (protege credenciais; ignora dados pesados)
├── requirements.txt               ✅ pronto
├── PLANO_DE_TRABALHO.md           ✅ este arquivo
├── notebooks/
│   ├── 01_extract.py              ⚠️ RECONSTRUÍDO — validar vs. original do Databricks
│   ├── 02_transform_silver.py     ⚠️ RECONSTRUÍDO — validar vs. original do Databricks
│   ├── 03_transform_gold.py       ⚠️ RECONSTRUÍDO — validar vs. original do Databricks
│   ├── 04_load_parquet.py         ⚠️ RECONSTRUÍDO — validar vs. original do Databricks
│   └── 05_mining_arvore.py        ✅ código real (mineração) — funcional
├── docs/
│   ├── dicionario_enem.md         ✅ pronto (dicionário corrigido)
│   └── arquitetura.md             ✅ pronto
└── dashboard/
    └── dashboard_executivo.html   ✅ pronto
```

### Importante sobre os notebooks de ETL (01 a 04)

Os notebooks `01_extract`, `02_transform_silver`, `03_transform_gold` e `04_load_parquet` foram
**reconstruídos a partir da lógica do projeto**, não são os arquivos originais escritos pela equipe no
Databricks. Eles são funcionais e fiéis à arquitetura, mas **podem divergir em detalhes** dos originais.

**Ação recomendada:** exportar os notebooks reais do Databricks (no Databricks: `File → Export → Source file`,
formato `.py`) e comparar/substituir. O notebook `05_mining_arvore.py` é o código real e não precisa disso.

---

## Tarefas para o Claude Code

Execute na ordem. Marque cada uma ao concluir.

### Tarefa 1 — Inicializar o repositório Git local
- [ ] Se o repo ainda não estiver clonado: `git clone https://github.com/gblzera/data-major-enem.git`
- [ ] Copiar todos os arquivos deste pacote para dentro do repo clonado, preservando a estrutura de pastas
- [ ] Conferir que `.gitignore` está na raiz e funcionando (`git status` não deve listar `.csv`, `.parquet`, `.env`)

### Tarefa 2 — Validar a integridade do código
- [ ] Verificar a sintaxe Python de todos os notebooks em `notebooks/` (ignorar linhas `# MAGIC` e `# COMMAND`,
      que são marcadores do Databricks, não Python). Sugestão: extrair as linhas de código e rodar `python -m py_compile`.
- [ ] Confirmar que nenhum notebook tem credenciais hardcoded (devem usar `dbutils.secrets.get(...)`)
- [ ] Validar que `requirements.txt` cobre todos os imports usados

### Tarefa 3 — Primeiro commit
- [ ] `git add .`
- [ ] `git commit -m "estrutura inicial do projeto: pipeline ETL + mineração + docs + dashboard"`
- [ ] `git push origin main`

### Tarefa 4 — Sincronizar com o Databricks
- [ ] No Databricks (já conectado via Repos), dar `pull` para trazer os arquivos
- [ ] Validar que os notebooks aparecem corretamente como notebooks (os `# COMMAND ----------` viram células)

### Tarefa 5 — Substituir os notebooks de ETL pelos originais (quando disponíveis)
- [ ] Pedir ao usuário os notebooks reais de Extract/Transform/Load exportados do Databricks
- [ ] Comparar com os reconstruídos (`git diff`) e substituir, preservando a lógica real da equipe
- [ ] Remover o aviso de "RECONSTRUÍDO" do topo dos arquivos substituídos

---

## Próximos passos do projeto (backlog técnico para a entrega final)

Estas são melhorias previstas. O Claude Code pode ajudar a implementá-las quando solicitado:

1. **Comparação com ensembles** — adicionar Extra Trees e Gradient Boosting ao notebook de mineração,
   com teste de significância (McNemar) e intervalos de confiança bootstrap das métricas.
2. **Clustering de perfis** — K-Means sobre as coordenadas de uma MCA (Análise de Correspondência Múltipla)
   para identificar perfis socioeconômicos e cruzá-los com o desempenho.
3. **Análise temporal** — comparar a associação socioeconômica × nota entre 2021, 2022 e 2023 (efeito da
   pandemia). O Parquet já está particionado por ano, o que facilita.
4. **Concluir a carga PostgreSQL** — finalizar a Carga 2 do notebook `04_load_parquet.py`.
5. **Rótulos legíveis nas regras** — mapear os códigos ordinais de volta para rótulos (ex.: "renda até 2 SM")
   na saída das regras da árvore.

> Referência: existe um notebook de mineração avançada já esboçado nesta conversa (`data_mining_avancado.py`),
> com Spearman+IC, MCA, K-Means, 3 modelos, McNemar e SHAP — pode servir de base para os itens 1, 2 e 3.

---

## Regras de trabalho

- **Nunca commitar credenciais.** As chaves AWS ficam em Databricks Secrets (escopo `aws-credentials`).
  O `.gitignore` já bloqueia padrões de credencial, mas confira antes de cada commit.
- **Não versionar os microdados.** São públicos (INEP) e pesados (GBs); o `.gitignore` os ignora.
- **Notebooks em formato source `.py`** (com `# COMMAND ----------`), que versiona limpo e sincroniza com
  o Databricks Repos.
- **Mensagens de commit descritivas**, em português, no imperativo (ex.: "adiciona teste de McNemar").
- **Branches:** usar uma branch por feature grande (ex.: `feature/ensembles`) e abrir PR para `main`.

---

## Como executar o pipeline (referência)

No Databricks, com as credenciais AWS configuradas como Secrets (escopo `aws-credentials`, chaves
`access-key` e `secret-key`), execute os notebooks na ordem:

```
01_extract.py        →  baixa do INEP e popula a Bronze (S3)
02_transform_silver  →  limpa e trata, gera a Silver
03_transform_gold    →  cria NOTA_MEDIA e TARGET, gera a Gold
04_load_parquet      →  consolida em Parquet (e PostgreSQL)
05_mining_arvore     →  Spearman + Árvore de Decisão + métricas + regras
```

Os microdados devem ser obtidos em:
https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem
