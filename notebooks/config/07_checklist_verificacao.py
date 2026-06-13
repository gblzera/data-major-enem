# Databricks notebook source
# MAGIC %md
# MAGIC # Checklist de Verificação
# MAGIC 
# MAGIC Use este notebook para verificar se você está pronto para trabalhar no projeto.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Checklist do Integrante
# MAGIC 
# MAGIC Marque cada item conforme for completando:
# MAGIC 
# MAGIC ### Acesso ao Ambiente
# MAGIC 
# MAGIC | # | Item | Status |
# MAGIC |---|------|--------|
# MAGIC | 1 | Consegui acessar o workspace do Databricks | ⬜ |
# MAGIC | 2 | Consegui acessar a pasta `Shared/project-data-major` | ⬜ |
# MAGIC | 3 | Consegui abrir e executar notebooks | ⬜ |
# MAGIC | 4 | Tenho um cluster disponível | ⬜ |
# MAGIC 
# MAGIC ### Conexões
# MAGIC 
# MAGIC | # | Item | Status |
# MAGIC |---|------|--------|
# MAGIC | 5 | Executei o teste de conexão S3 com sucesso | ⬜ |
# MAGIC | 6 | Executei o teste de conexão RDS (ou confirmei que está desligado) | ⬜ |
# MAGIC | 7 | Executei o teste Spark + S3 (planejado/referência — não funciona na Free/Community Edition; leitura/escrita é via boto3/awswrangler/pandas) | ⬜ |
# MAGIC 
# MAGIC ### Entendimento do Projeto
# MAGIC 
# MAGIC | # | Item | Status |
# MAGIC |---|------|--------|
# MAGIC | 8 | Li o documento `01_detalhes_projeto.md` | ⬜ |
# MAGIC | 9 | Li o documento `02_pipeline.md` | ⬜ |
# MAGIC | 10 | Li o documento `03_integrantes.md` | ⬜ |
# MAGIC | 11 | Entendi minha responsabilidade específica | ⬜ |
# MAGIC | 12 | Sei quais notebooks dependem do meu trabalho | ⬜ |
# MAGIC 
# MAGIC ### Preparação Técnica
# MAGIC 
# MAGIC | # | Item | Status |
# MAGIC |---|------|--------|
# MAGIC | 13 | Sei como carregar as credenciais | ⬜ |
# MAGIC | 14 | Sei como usar as funções utilitárias | ⬜ |
# MAGIC | 15 | Conheço a estrutura de pastas no S3 | ⬜ |

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Verificação Automática
# MAGIC 
# MAGIC Execute as células abaixo para verificar automaticamente os itens técnicos:

# COMMAND ----------

# ╔══════════════════════════════════════════════════════════════════════╗
# ║                    VERIFICAÇÃO AUTOMÁTICA                            ║
# ╚══════════════════════════════════════════════════════════════════════╝

import sys

print("=" * 60)
print("VERIFICAÇÃO AUTOMÁTICA DO AMBIENTE")
print("=" * 60)
print()

checks = []

# 1. Verificar Python
try:
    python_version = sys.version.split()[0]
    checks.append(("Python instalado", True, python_version))
except:
    checks.append(("Python instalado", False, "Erro"))

# 2. Verificar pandas (motor de processamento do projeto)
try:
    import pandas as _pd
    checks.append(("pandas instalado", True, _pd.__version__))
except ImportError:
    checks.append(("pandas instalado", False, "Não encontrado"))

# 3. Verificar boto3
try:
    import boto3
    checks.append(("boto3 instalado", True, boto3.__version__))
except ImportError:
    checks.append(("boto3 instalado", False, "Não encontrado"))

# 4. Verificar psycopg2
try:
    import psycopg2
    checks.append(("psycopg2 instalado", True, psycopg2.__version__))
except ImportError:
    checks.append(("psycopg2 instalado", False, "Não encontrado"))

# 5. Verificar scikit-learn
try:
    import sklearn
    checks.append(("scikit-learn instalado", True, sklearn.__version__))
except ImportError:
    checks.append(("scikit-learn instalado", False, "Não encontrado"))

# 6. Verificar credenciais
try:
    test_key = dbutils.secrets.get(scope="aws-credentials", key="access-key")
    checks.append(("Credenciais AWS configuradas", True, "OK"))
except:
    checks.append(("Credenciais AWS configuradas", False, "Não encontrado"))

# Exibir resultados
for check_name, passed, detail in checks:
    status = "✅" if passed else "❌"
    print(f"   {status} {check_name}: {detail}")

print()
print("-" * 60)

passed_count = sum(1 for _, passed, _ in checks if passed)
total_count = len(checks)

if passed_count == total_count:
    print()
    print(f"   🎉 TUDO OK! ({passed_count}/{total_count} verificações)")
    print()
else:
    print()
    print(f"   ⚠️ {total_count - passed_count} item(s) precisam de atenção")
    print()

print("=" * 60)

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Verificação de Conexões

# COMMAND ----------

# Carregar credenciais
AWS_ACCESS_KEY = dbutils.secrets.get(scope="aws-credentials", key="access-key")
AWS_SECRET_KEY = dbutils.secrets.get(scope="aws-credentials", key="secret-key")
BUCKET_NAME    = "enem-data-lake-gblzera"
REGION         = "sa-east-1"

# Teste rápido S3
import boto3

print("=" * 60)
print("VERIFICAÇÃO RÁPIDA DE CONEXÕES")
print("=" * 60)
print()

try:
    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION
    )
    s3.list_objects_v2(Bucket=BUCKET_NAME, MaxKeys=1)
    print("   ✅ S3: Conexão OK")
except Exception as e:
    print(f"   ❌ S3: {str(e)[:50]}")

# Teste rápido Spark + S3 (PLANEJADO/REFERÊNCIA)
# NOTA: na Databricks Free/Community Edition (só serverless / Spark Connect)
# o Spark NÃO lê o S3 (erro 403). A leitura/escrita real é feita via
# boto3/awswrangler/pandas com as chaves do Databricks Secrets.
# O bloco abaixo vale apenas como referência.
try:
    spark.conf.set("fs.s3a.access.key", AWS_ACCESS_KEY)
    spark.conf.set("fs.s3a.secret.key", AWS_SECRET_KEY)
    spark.conf.set("fs.s3a.endpoint", f"s3.{REGION}.amazonaws.com")

    # Tentar listar (não precisa ler dados)
    dbutils.fs.ls(f"s3a://{BUCKET_NAME}/")
    print("   ✅ Spark + S3: Conexão OK")
except Exception as e:
    print(f"   ℹ️ Spark + S3: planejado/referência — não funciona na Free/Community Edition ({str(e)[:50]})")

print()
print("   ℹ️ RDS: Verificação ignorada (pode estar desligado)")
print()
print("=" * 60)

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Status Final
# MAGIC 
# MAGIC ### Se todos os testes passaram:
# MAGIC 
# MAGIC Você está pronto para começar a trabalhar!
# MAGIC 
# MAGIC Vá para o notebook da sua responsabilidade:
# MAGIC 
# MAGIC | Responsável | Notebook |
# MAGIC |-------------|----------|
# MAGIC | Davi (Extract) | `pipeline/extract.py` |
# MAGIC | Bruno (Transform Silver) | `pipeline/transform_silver.py` |
# MAGIC | Bruno (Transform Gold) | `pipeline/transform_gold.py` |
# MAGIC | Vinicius (Load) | `pipeline/load_parquet.py` |
# MAGIC | Gabriel S. (Mining) | `pipeline/05_mining_arvore.py` |
# MAGIC 
# MAGIC ### Se algum teste falhou:
# MAGIC 
# MAGIC Entre em contato com o Tech Lead (Gabriel H. K. Paz) para resolver.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC 
# MAGIC **Última atualização:** 2026-06-13
# MAGIC **Mantido por:** Tech Lead (Gabriel H. K. Paz)