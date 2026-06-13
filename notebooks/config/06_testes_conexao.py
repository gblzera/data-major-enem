# Databricks notebook source
# MAGIC %md
# MAGIC # Testes de Conexão
# MAGIC 
# MAGIC Este notebook testa as conexões com S3 e RDS PostgreSQL.
# MAGIC 
# MAGIC **Execute este notebook após configurar as credenciais!**

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 1. Carregar Credenciais
# MAGIC 
# MAGIC Primeiro, carregamos as credenciais do Databricks Secrets:

# COMMAND ----------

# --- AWS S3 ---
AWS_ACCESS_KEY = dbutils.secrets.get(scope="aws-credentials", key="access-key")
AWS_SECRET_KEY = dbutils.secrets.get(scope="aws-credentials", key="secret-key")
BUCKET_NAME    = "enem-data-lake-gblzera"
REGION         = "sa-east-1"

# --- RDS PostgreSQL ---
RDS_HOST     = dbutils.secrets.get(scope="aws-credentials", key="rds-host")
RDS_USER     = dbutils.secrets.get(scope="aws-credentials", key="rds-user")
RDS_PASSWORD = dbutils.secrets.get(scope="aws-credentials", key="rds-password")
RDS_DATABASE = "enem_db"
RDS_PORT     = 5432

print("Credenciais carregadas!")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 2. Teste de Conexão com S3

# COMMAND ----------

# ╔══════════════════════════════════════════════════════════════════════╗
# ║                        TESTE DE CONEXÃO S3                           ║
# ╚══════════════════════════════════════════════════════════════════════╝

import boto3

def test_s3_connection():
    """Testa a conexão com o S3 e lista os prefixos disponíveis."""
    print("=" * 60)
    print("TESTE DE CONEXÃO S3")
    print("=" * 60)
    
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=REGION
        )
        
        # Lista os prefixos (pastas) no bucket
        response = s3.list_objects_v2(
            Bucket=BUCKET_NAME,
            Delimiter="/",
            MaxKeys=20
        )
        
        print()
        print("✅ CONEXÃO ESTABELECIDA COM SUCESSO!")
        print()
        print(f"   Bucket: {BUCKET_NAME}")
        print(f"   Região: {REGION}")
        print()
        print("   Pastas encontradas:")
        
        if "CommonPrefixes" in response:
            for prefix in response["CommonPrefixes"]:
                # Contar arquivos em cada pasta
                folder_response = s3.list_objects_v2(
                    Bucket=BUCKET_NAME,
                    Prefix=prefix['Prefix'],
                    MaxKeys=100
                )
                file_count = folder_response.get('KeyCount', 0)
                print(f"      └── {prefix['Prefix']} ({file_count} itens)")
        else:
            print("      (nenhuma pasta encontrada)")
        
        print()
        print("=" * 60)
        return True
        
    except Exception as e:
        print()
        print("❌ ERRO NA CONEXÃO!")
        print()
        print(f"   Erro: {str(e)}")
        print()
        print("   Possíveis causas:")
        print("   • Credenciais inválidas")
        print("   • Bucket não existe")
        print("   • Sem permissão de acesso")
        print()
        print("=" * 60)
        return False

# Executar teste
s3_ok = test_s3_connection()

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 3. Teste de Conexão com RDS PostgreSQL
# MAGIC 
# MAGIC > **⚠️ Nota:** O RDS fica desligado por padrão para economizar custos.
# MAGIC > Se o teste falhar com timeout, é esperado. Avise o Tech Lead para ligar.

# COMMAND ----------

# ╔══════════════════════════════════════════════════════════════════════╗
# ║                       TESTE DE CONEXÃO RDS                           ║
# ╚══════════════════════════════════════════════════════════════════════╝

import psycopg2

def test_rds_connection():
    """Testa a conexão com o RDS PostgreSQL."""
    print("=" * 60)
    print("TESTE DE CONEXÃO RDS POSTGRESQL")
    print("=" * 60)
    
    try:
        print()
        print("   Conectando...")
        
        conn = psycopg2.connect(
            host=RDS_HOST,
            database=RDS_DATABASE,
            user=RDS_USER,
            password=RDS_PASSWORD,
            port=RDS_PORT,
            connect_timeout=30
        )
        
        # Executa queries de verificação
        cursor = conn.cursor()
        
        # Versão do PostgreSQL
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        # Listar tabelas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        
        print()
        print("✅ CONEXÃO ESTABELECIDA COM SUCESSO!")
        print()
        print(f"   Host: {RDS_HOST}")
        print(f"   Database: {RDS_DATABASE}")
        print(f"   User: {RDS_USER}")
        print(f"   PostgreSQL: {version[:50]}...")
        print()
        print("   Tabelas no schema public:")
        if tables:
            for table in tables:
                print(f"      └── {table[0]}")
        else:
            print("      (nenhuma tabela encontrada)")
        
        cursor.close()
        conn.close()
        
        print()
        print("=" * 60)
        return True
        
    except psycopg2.OperationalError as e:
        print()
        print("⚠️ CONEXÃO FALHOU (TIMEOUT)")
        print()
        print("   Isso é ESPERADO se o RDS estiver desligado.")
        print()
        print("   O que fazer:")
        print("   • Avise o Tech Lead para ligar o RDS")
        print("   • Aguarde alguns minutos após ligar")
        print("   • Execute este teste novamente")
        print()
        print("=" * 60)
        return False
        
    except Exception as e:
        print()
        print("❌ ERRO NA CONEXÃO!")
        print()
        print(f"   Erro: {str(e)}")
        print()
        print("=" * 60)
        return False

# Executar teste
rds_ok = test_rds_connection()

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 4. Teste de Conexão Spark + S3 (referência — NÃO usado no projeto)
# MAGIC
# MAGIC > **⚠️ Importante:** Este projeto **NÃO usa Spark + S3**. O acesso real ao
# MAGIC > data lake é feito via **boto3 / awswrangler / pandas** (ver teste 2).
# MAGIC >
# MAGIC > No Databricks Free/Community Edition (serverless / Spark Connect), o Spark
# MAGIC > **não consegue ler/escrever no S3** (retorna erro 403 / fs.s3a indisponível).
# MAGIC > Por isso, **falhar neste teste no serverless é ESPERADO** e não bloqueia o
# MAGIC > projeto. O bloco abaixo fica apenas como **referência** de como seria a
# MAGIC > integração Spark+S3 em um cluster dedicado.

# COMMAND ----------

# ╔══════════════════════════════════════════════════════════════════════╗
# ║          TESTE SPARK + S3 (REFERÊNCIA — NÃO USADO NO PROJETO)        ║
# ╚══════════════════════════════════════════════════════════════════════╝
#
# NOTA: O projeto NÃO usa Spark + S3. O acesso real ao data lake é via
# boto3 / awswrangler / pandas (teste 2). No serverless (Free/Community
# Edition) este teste FALHA — e isso é ESPERADO, não é um bloqueio.

def test_spark_s3():
    """Testa a leitura/escrita do Spark no S3.

    REFERÊNCIA APENAS. Não é usado no pipeline real (que roda em
    boto3/awswrangler/pandas). No serverless do Databricks Free/Community
    Edition o Spark não acessa o S3 (erro 403), então é esperado que falhe.
    """
    print("=" * 60)
    print("TESTE SPARK + S3")
    print("=" * 60)
    
    try:
        # Configurar credenciais
        spark.conf.set("fs.s3a.access.key", AWS_ACCESS_KEY)
        spark.conf.set("fs.s3a.secret.key", AWS_SECRET_KEY)
        spark.conf.set("fs.s3a.endpoint", f"s3.{REGION}.amazonaws.com")
        
        # Criar DataFrame de teste
        test_data = [
            (1, "teste", 100.0),
            (2, "spark", 200.0),
            (3, "s3", 300.0)
        ]
        df = spark.createDataFrame(test_data, ["id", "nome", "valor"])
        
        # Escrever no S3
        test_path = f"s3a://{BUCKET_NAME}/test/spark_test"
        df.write.mode("overwrite").parquet(test_path)
        print()
        print(f"   ✅ Escrita OK: {test_path}")
        
        # Ler do S3
        df_read = spark.read.parquet(test_path)
        count = df_read.count()
        print(f"   ✅ Leitura OK: {count} registros")
        
        # Limpar arquivo de teste
        import boto3
        s3 = boto3.resource(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=REGION
        )
        bucket = s3.Bucket(BUCKET_NAME)
        bucket.objects.filter(Prefix="test/").delete()
        print(f"   ✅ Limpeza OK: arquivos de teste removidos")
        
        print()
        print("✅ SPARK + S3 FUNCIONANDO CORRETAMENTE!")
        print()
        print("=" * 60)
        return True
        
    except Exception as e:
        print()
        print("⚠️ SPARK + S3 FALHOU (ESPERADO no serverless)")
        print()
        print(f"   Erro: {str(e)}")
        print()
        print("   Isso é ESPERADO no Databricks Free/Community Edition:")
        print("   o Spark serverless não acessa o S3 (erro 403 / fs.s3a).")
        print()
        print("   O projeto NÃO depende disto — o acesso real ao data lake")
        print("   é via boto3 / awswrangler / pandas (ver teste 2).")
        print()
        print("=" * 60)
        return False

# Executar teste (apenas referência — não bloqueia o projeto)
spark_ok = test_spark_s3()

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 5. Resumo dos Testes

# COMMAND ----------

# ╔══════════════════════════════════════════════════════════════════════╗
# ║                        RESUMO DOS TESTES                             ║
# ╚══════════════════════════════════════════════════════════════════════╝

print("=" * 60)
print("RESUMO DOS TESTES DE CONEXÃO")
print("=" * 60)
print()

# Testes IMPEDITIVOS (acesso real ao data lake é via boto3/awswrangler/pandas).
# RDS pode estar desligado; Spark+S3 é apenas referência e NÃO bloqueia.
tests = [
    ("S3 (boto3)", s3_ok),
    ("RDS PostgreSQL", rds_ok),
    ("Spark + S3 (referência — não usado)", spark_ok)
]

for test_name, result in tests:
    if "Spark + S3" in test_name:
        # Falha aqui é esperada no serverless e NÃO é impeditiva.
        status = "✅ OK" if result else "⚠️ N/A (esperado falhar no serverless)"
    else:
        status = "✅ OK" if result else "❌ FALHOU"
    print(f"   {test_name}: {status}")

# Prontidão do projeto depende do S3 via boto3 (Spark+S3 não conta).
all_ok = s3_ok and rds_ok

print()
print("-" * 60)

if all_ok:
    print()
    print("🎉 TESTES ESSENCIAIS PASSARAM!")
    print()
    print("   Você está pronto para começar a trabalhar no projeto.")
    print("   (Spark + S3 é apenas referência e não é usado no pipeline.)")
    print()
elif s3_ok:
    print()
    print("⚠️ S3 FUNCIONANDO, RDS DESLIGADO")
    print()
    print("   Você pode trabalhar normalmente com S3 (boto3/awswrangler/pandas).")
    print("   O RDS será necessário apenas na etapa de Load.")
    print("   Avise o Tech Lead quando precisar do RDS.")
    print()
    print("   Obs: a falha do Spark + S3 é esperada no serverless e não bloqueia.")
    print()
else:
    print()
    print("❌ TESTE ESSENCIAL FALHOU (S3 via boto3)")
    print()
    print("   O acesso ao data lake (boto3/awswrangler/pandas) não funcionou.")
    print("   Entre em contato com o Tech Lead para resolver.")
    print()
    print("   Obs: a falha do Spark + S3 é esperada no serverless e não bloqueia.")
    print()

print("=" * 60)

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC 
# MAGIC **Última atualização:** 2026-06-13  
# MAGIC **Mantido por:** Tech Lead (Gabriel H. K. Paz)