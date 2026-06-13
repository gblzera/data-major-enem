# Databricks notebook source
# MAGIC %md
# MAGIC # Cronograma do Projeto
# MAGIC 
# MAGIC Este notebook apresenta o cronograma de atividades do Projeto Data Major.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 1. Datas Importantes
# MAGIC 
# MAGIC | Evento | Data | Status |
# MAGIC |--------|------|--------|
# MAGIC | Início do projeto | 22/03/2026 | ✅ Concluído |
# MAGIC | Apresentação da arquitetura | 23/03/2026 | ✅ Concluído |
# MAGIC | **Seminário Turma 1** | **15/06/2026** | ⬜ Pendente |
# MAGIC | **Seminário Turma 2** | **22/06/2026** | ⬜ Pendente |

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 2. Cronograma por Semana
# MAGIC 
# MAGIC ### Semana 1 (22/03 - 28/03)
# MAGIC 
# MAGIC | Atividade | Responsável | Status |
# MAGIC |-----------|-------------|--------|
# MAGIC | Configurar ambiente Databricks | Tech Lead | ✅ |
# MAGIC | Configurar bucket S3 | Tech Lead | ✅ |
# MAGIC | Configurar RDS PostgreSQL | Tech Lead | ✅ |
# MAGIC | Adicionar membros ao workspace | Tech Lead | ✅ |
# MAGIC | Documentar arquitetura | Tech Lead | ✅ |
# MAGIC | Apresentar arquitetura para o grupo | Tech Lead | ✅ |
# MAGIC 
# MAGIC ### Semana 2 (29/03 - 04/04)
# MAGIC 
# MAGIC | Atividade | Responsável | Status |
# MAGIC |-----------|-------------|--------|
# MAGIC | Download microdados ENEM 2021 | Extract (Davi) | ✅ |
# MAGIC | Download microdados ENEM 2022 | Extract (Davi) | ✅ |
# MAGIC | Download microdados ENEM 2023 | Extract (Davi) | ✅ |
# MAGIC | Upload para S3 Bronze | Extract (Davi) | ✅ |
# MAGIC | Documentar extração | Extract (Davi) | ✅ |
# MAGIC 
# MAGIC ### Semana 3 (05/04 - 11/04)
# MAGIC 
# MAGIC | Atividade | Responsável | Status |
# MAGIC |-----------|-------------|--------|
# MAGIC | Limpeza e filtros (Silver) | Transform (Bruno) | ✅ |
# MAGIC | Tratamento de nulos | Transform (Bruno) | ✅ |
# MAGIC | Conversão de tipos | Transform (Bruno) | ✅ |
# MAGIC | Salvar em Parquet | Transform (Bruno) | ✅ |
# MAGIC 
# MAGIC ### Semana 4 (12/04 - 18/04)
# MAGIC 
# MAGIC | Atividade | Responsável | Status |
# MAGIC |-----------|-------------|--------|
# MAGIC | Feature engineering (Gold) | Transform (Bruno) | ✅ |
# MAGIC | Criar variável target | Transform (Bruno) | ✅ |
# MAGIC | Encoding categórico | Transform (Bruno) | ✅ |
# MAGIC | Validar volume (30-60MB) | Transform (Bruno) | ✅ |
# MAGIC 
# MAGIC ### Semana 5 (19/04 - 25/04)
# MAGIC 
# MAGIC | Atividade | Responsável | Status |
# MAGIC |-----------|-------------|--------|
# MAGIC | Criar tabela no RDS | Load (Vinicius) | ✅ |
# MAGIC | Carregar dados no RDS | Load (Vinicius) | ✅ |
# MAGIC | Validar integridade | Load (Vinicius) | ✅ |
# MAGIC | Exportar para Parquet final | Load (Vinicius) | ✅ |
# MAGIC 
# MAGIC ### Semana 6 (26/04 - 02/05)
# MAGIC 
# MAGIC | Atividade | Responsável | Status |
# MAGIC |-----------|-------------|--------|
# MAGIC | Split treino/teste | Mining (Gabriel S.) | ✅ |
# MAGIC | Treinar Árvore de Decisão | Mining (Gabriel S.) | ✅ |
# MAGIC | Calcular métricas | Mining (Gabriel S.) | ✅ |
# MAGIC | Gerar visualizações | Mining (Gabriel S.) | ✅ |
# MAGIC 
# MAGIC ### Semana 7-8 (03/05 - 16/05)
# MAGIC 
# MAGIC | Atividade | Responsável | Status |
# MAGIC |-----------|-------------|--------|
# MAGIC | Integração end-to-end | Todos | ✅ |
# MAGIC | Testes do pipeline completo | Todos | ✅ |
# MAGIC | Correções e ajustes | Todos | ✅ |
# MAGIC 
# MAGIC ### Semana 9-10 (17/05 - 30/05)
# MAGIC 
# MAGIC | Atividade | Responsável | Status |
# MAGIC |-----------|-------------|--------|
# MAGIC | Documentação final | Todos | ✅ |
# MAGIC | Preparar apresentação | Todos | ✅ |
# MAGIC | Ensaio do seminário | Todos | ✅ |
# MAGIC 
# MAGIC ### Semana 11-12 (31/05 - 14/06)
# MAGIC 
# MAGIC | Atividade | Responsável | Status |
# MAGIC |-----------|-------------|--------|
# MAGIC | Revisão final | Todos | ⏳ |
# MAGIC | Ajustes pós-ensaio | Todos | ⏳ |
# MAGIC | **SEMINÁRIO TURMA 1 (15/06)** | Todos | ⬜ |
# MAGIC | **SEMINÁRIO TURMA 2 (22/06)** | Todos | ⬜ |

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 3. Dependências entre Etapas
# MAGIC 
# MAGIC ```
# MAGIC ┌─────────────────────────────────────────────────────────────────┐
# MAGIC │                    FLUXO DE DEPENDÊNCIAS                        │
# MAGIC └─────────────────────────────────────────────────────────────────┘
# MAGIC 
# MAGIC     Semana 1-2          Semana 3          Semana 4          Semana 5          Semana 6
# MAGIC         │                   │                 │                 │                 │
# MAGIC         ▼                   ▼                 ▼                 ▼                 ▼
# MAGIC    ┌─────────┐        ┌─────────┐       ┌─────────┐       ┌─────────┐       ┌─────────┐
# MAGIC    │ EXTRACT │ ─────▶ │ SILVER  │ ────▶ │  GOLD   │ ────▶ │  LOAD   │ ────▶ │ MINING  │
# MAGIC    │  Davi   │        │  Bruno  │       │  Bruno  │       │Vinicius │       │Gabriel S│
# MAGIC    └─────────┘        └─────────┘       └─────────┘       └─────────┘       └─────────┘
# MAGIC                              │                                   │
# MAGIC                              │                                   │
# MAGIC                              ▼                                   ▼
# MAGIC                        Depende de               Depende de Gold + RDS ligado
# MAGIC                        Bronze estar             para fazer as duas cargas
# MAGIC                        completo
# MAGIC ```
# MAGIC 
# MAGIC **Importante:** Cada etapa só pode começar quando a anterior estiver completa!

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 4. Marcos (Milestones)
# MAGIC 
# MAGIC | Marco | Data Limite | Critério de Sucesso | Status |
# MAGIC |-------|-------------|---------------------|--------|
# MAGIC | **M1: Infraestrutura** | 28/03/2026 | Databricks, S3 e RDS configurados e acessíveis | ✅ |
# MAGIC | **M2: Dados Bronze** | 04/04/2026 | Microdados 2021-2023 no S3 | ✅ |
# MAGIC | **M3: Dados Silver** | 11/04/2026 | Dados limpos em Parquet | ✅ |
# MAGIC | **M4: Dados Gold** | 18/04/2026 | Features prontas para ML | ✅ |
# MAGIC | **M5: Load Completo** | 25/04/2026 | Dados no RDS e Parquet final | ✅ |
# MAGIC | **M6: Modelo Treinado** | 02/05/2026 | Métricas calculadas | ✅ |
# MAGIC | **M7: Pipeline Integrado** | 16/05/2026 | Execução end-to-end OK | ✅ |
# MAGIC | **M8: Apresentação Pronta** | 07/06/2026 | Slides e ensaio concluídos | ✅ |

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 5. Contagem Regressiva

# COMMAND ----------

from datetime import datetime, date

# Datas dos seminários
seminario_turma1 = date(2026, 6, 15)
seminario_turma2 = date(2026, 6, 22)
hoje = date.today()

dias_turma1 = (seminario_turma1 - hoje).days
dias_turma2 = (seminario_turma2 - hoje).days

print("=" * 60)
print("CONTAGEM REGRESSIVA")
print("=" * 60)
print()
print(f"   📅 Hoje: {hoje.strftime('%d/%m/%Y')}")
print()
print(f"   🎯 Seminário Turma 1: {seminario_turma1.strftime('%d/%m/%Y')}")
print(f"      → Faltam {dias_turma1} dias")
print()
print(f"   🎯 Seminário Turma 2: {seminario_turma2.strftime('%d/%m/%Y')}")
print(f"      → Faltam {dias_turma2} dias")
print()

if dias_turma1 <= 14:
    print("   ⚠️ ATENÇÃO: Menos de 2 semanas para o Seminário Turma 1!")
elif dias_turma1 <= 30:
    print("   ℹ️ Menos de 1 mês para o Seminário Turma 1")

print()
print("=" * 60)

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 6. Reuniões Sugeridas
# MAGIC 
# MAGIC | Reunião | Frequência | Objetivo |
# MAGIC |---------|------------|----------|
# MAGIC | Daily (rápida) | Diária (5 min) | Status e bloqueios |
# MAGIC | Weekly | Semanal | Revisão do progresso e planejamento |
# MAGIC | Review | A cada marco | Validação das entregas |
# MAGIC | Ensaio | 2 semanas antes | Praticar apresentação |

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC 
# MAGIC **Última atualização:** 2026-06-13
# MAGIC **Mantido por:** Tech Lead (Gabriel H. K. Paz)