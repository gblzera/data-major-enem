# Dicionário de Variáveis — Questionário Socioeconômico do ENEM

Mapeamento das variáveis Q001–Q025 dos microdados do ENEM (2021–2023), conforme o dicionário oficial do INEP.

> **Nota de correção:** uma versão preliminar do dicionário do grupo estava deslocada a partir de Q003 (tratava Q003/Q004 como "situação de trabalho/tipo de escola"). A verificação cruzada com os dados — a presença da categoria "F" em Q003/Q004, impossível sob o mapeamento errado — confirmou o desalinhamento. Este documento reflete o mapeamento **corrigido**.

| Variável | Descrição | Tipo | Categorias |
|----------|-----------|------|------------|
| Q001 | Escolaridade do Pai | Categórica ordinal | A–H (H = não sei) |
| Q002 | Escolaridade da Mãe | Categórica ordinal | A–H (H = não sei) |
| Q003 | Ocupação do Pai (grupo) | Categórica | A–F (F = não sei) |
| Q004 | Ocupação da Mãe (grupo) | Categórica | A–F (F = não sei) |
| Q005 | Pessoas na residência | **Numérica** | inteiro (−1 = ausente) |
| Q006 | Renda mensal da família | Categórica ordinal | A–Q (17 faixas) |
| Q007 | Empregado(a) doméstico(a) | Categórica | A–D |
| Q008 | Banheiros | Categórica ordinal | A–E |
| Q009 | Quartos para dormir | Categórica ordinal | A–E |
| Q010 | Carros | Categórica ordinal | A–E |
| Q011 | Motocicletas | Categórica ordinal | A–E |
| Q012 | Geladeira | Categórica | A–B (ou níveis) |
| Q013 | Freezer | Categórica | A–B |
| Q014 | Máquina de lavar roupa | Categórica | A–B |
| Q015 | Máquina de secar roupa | Categórica | A–B |
| Q016 | Máquina de lavar louça | Categórica | A–B |
| Q017 | Forno micro-ondas | Categórica | A–B |
| Q018 | Aspirador de pó | Categórica | A–B |
| Q019 | Televisões | Categórica ordinal | A–E |
| Q020 | Aparelho de DVD | Categórica | A–B |
| Q021 | TV por assinatura | Categórica | A–B |
| Q022 | Telefones celulares | Categórica ordinal | A–E |
| Q023 | Telefone fixo | Categórica | A–B |
| Q024 | Computadores | Categórica ordinal | A–E |
| Q025 | Acesso à Internet | Categórica | A–B |

## Tratamento de "não sei"

Os códigos abaixo representam **ausência de informação** (não um nível ordinal) e são convertidos para `NaN` antes das análises:

| Variável | Código "não sei" |
|----------|------------------|
| Q001 | H |
| Q002 | H |
| Q003 | F |
| Q004 | F |

## Verificação de consistência

A correção do mapeamento acima partiu de uma **verificação cruzada manual** com os próprios dados — a presença da categoria "F" em Q003/Q004, impossível sob o mapeamento preliminar, denunciou o desalinhamento. Uma **trava automática** que confira o número de categorias reais de cada variável contra o esperado, detectando desalinhamentos antes da análise, ainda **não** está implementada no notebook de mineração — é uma melhoria prevista.
