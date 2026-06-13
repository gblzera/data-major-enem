# Databricks notebook source
import boto3

# CONFIGURAÇÃO AWS
 
AWS_ACCESS_KEY = dbutils.secrets.get(scope="aws-credentials", key="access-key")
AWS_SECRET_KEY = dbutils.secrets.get(scope="aws-credentials", key="secret-key")
 
# Configurações do bucket
REGION = "sa-east-1"
BUCKET = "enem-data-lake-gblzera"
 
# Cliente S3
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION
)
 
print("Cliente S3 configurado")
print(f"   Bucket: {BUCKET}")
print(f"   Região: {REGION}")
