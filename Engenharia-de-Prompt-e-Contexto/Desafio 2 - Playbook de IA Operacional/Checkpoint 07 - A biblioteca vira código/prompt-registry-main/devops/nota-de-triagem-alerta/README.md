---
nome: Nota de triagem de alerta SRE
descricao: Transforma um alerta cru em uma nota de triagem padronizada com impacto, hipótese inicial, ação imediata e escalonamento.
versao: 1.0.0
tags: [sre, observabilidade, incidente, alerta, devops]
inputs:
  - nome: ALERTA
    descricao: Alerta cru a ser triado — texto livre, JSON, payload do Sentinel ou descrição informal
---

# Nota de triagem de alerta SRE

## Objetivo

Atua como plantonista sênior de SRE da plataforma Aegis: recebe um alerta cru disparado pelo Sentinel e produz uma nota de triagem padronizada em cinco campos (ALERTA, IMPACTO, HIPÓTESE INICIAL, AÇÃO IMEDIATA, ESCALAR PARA), em português brasileiro, clara o suficiente para que o próximo turno assuma sem reconstruir contexto.

## Quando usar

- Durante o plantão, ao receber um alerta do Sentinel que precisa ser documentado antes de passar para o próximo turno.
- Para padronizar a comunicação de incidentes entre times (Relay, Forge, Cerebro).
- Quando um alerta ambíguo precisa ser racionalizado antes de escalar.
- Para gerar múltiplas notas em lote quando vários alertas chegam simultaneamente.

## Exemplo de uso

_A preencher_ (depende do payload real do Sentinel enviado na variável `{{ALERTA}}`).

## Limitações conhecidas

- O prompt pressupõe o contexto específico da plataforma Aegis (Relay, Forge, Sentinel, Cerebro) — não se aplica diretamente a outros stacks sem adaptação dos times de escalonamento.
- Opera sobre o texto do alerta fornecido; não tem acesso ao cluster, métricas ou logs em tempo real.
- Hipóteses são inferências iniciais, não diagnósticos definitivos.
