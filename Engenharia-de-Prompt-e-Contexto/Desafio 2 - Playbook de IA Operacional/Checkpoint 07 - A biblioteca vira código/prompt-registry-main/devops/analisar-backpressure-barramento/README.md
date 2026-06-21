---
nome: Análise comparativa de backpressure em barramento de eventos
descricao: Recebe um cenário de sobrecarga de barramento de eventos e produz análise comparativa de estratégias de backpressure com recomendação fundamentada em trade-offs.
versao: 1.0.0
tags: [sre, arquitetura, backpressure, barramento, confiabilidade]
inputs:
  - nome: ESTADO_DO_SISTEMA
    descricao: Nome do barramento, throughput sustentado, pico observado, retenção, consumidores e o que cada um exige
  - nome: RESTRICOES_DO_TIME
    descricao: SLAs por consumidor, orçamento de infra, garantias inegociáveis e restrições históricas conhecidas
  - nome: ESTRATEGIAS_CANDIDATAS
    descricao: Lista de caminhos já em cima da mesa — opcional; se vazio, o modelo gera candidatos pertinentes ao cenário
---

# Análise comparativa de backpressure em barramento de eventos

## Objetivo

Atua como arquiteto de sistemas distribuídos sênior: recebe o estado atual de um barramento de eventos sob sobrecarga e as restrições do time (SLAs, orçamento, garantias inegociáveis) e produz uma análise comparativa estruturada de pelo menos três estratégias de backpressure — com tabela de trade-offs, contraste entre os finalistas e uma recomendação rastreável aos números do cenário.

## Quando usar

- Ao enfrentar picos de throughput que ameaçam saturar a retenção do barramento e precisar decidir a estratégia de contenção antes de agir.
- Quando há múltiplos consumidores com SLAs diferentes e a decisão de backpressure impacta uns mais do que outros.
- Para documentar e justificar uma decisão de arquitetura cara, com trade-offs explícitos para revisão pelo time ou liderança.
- Em postmortems de sobrecarga, para avaliar retrospectivamente as alternativas que existiam no momento do incidente.

## Exemplo de uso

_A preencher_ (depende dos valores reais fornecidos em `{{ESTADO_DO_SISTEMA}}`, `{{RESTRICOES_DO_TIME}}` e `{{ESTRATEGIAS_CANDIDATAS}}`).

## Limitações conhecidas

- O campo `{{ESTRATEGIAS_CANDIDATAS}}` é opcional: se omitido, o modelo gera candidatos com base no cenário, mas eles podem não contemplar restrições arquiteturais internas não declaradas em `{{RESTRICOES_DO_TIME}}`.
- Toda afirmação de impacto é derivada dos números fornecidos na entrada; se os dados forem incompletos ou imprecisos, as contas e a recomendação perdem acurácia — o modelo declara as premissas assumidas, mas não pode validá-las.
- O prompt não acessa o barramento em tempo real: opera exclusivamente sobre o snapshot textual fornecido.
