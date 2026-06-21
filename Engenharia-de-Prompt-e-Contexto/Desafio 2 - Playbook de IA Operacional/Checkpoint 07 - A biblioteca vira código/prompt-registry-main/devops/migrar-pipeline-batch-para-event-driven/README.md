---
nome: Cadeia de prompts para migração de pipeline batch para event-driven
descricao: Cadeia de três prompts encadeados para diagnosticar, planejar e executar a migração de um pipeline batch para um modelo event-driven de forma incremental e reversível.
versao: 1.0.0
tags: [migração, streaming, event-driven, pipeline, sre]
inputs:
  - nome: SNAPSHOT_FORGE
    descricao: Descrição do pipeline atual — ingestão, etapas de transformação, destino, pontos frágeis e dependentes a jusante (Elo 1)
  - nome: SLAS_E_DEPENDENTES
    descricao: SLAs, janelas críticas e quem consome a saída do pipeline (Elo 1)
  - nome: DIAGNOSTICO_FORGE
    descricao: Saída completa do Elo 1 — mapa de acoplamentos, inventário de etapas, riscos, restrições e handoff (Elo 2)
  - nome: OBJETIVO_ALVO
    descricao: O modelo de destino desejado — consumo contínuo do barramento, processamento em blocos, migração reversível (Elo 2)
  - nome: ESTRATEGIA_FASEADA
    descricao: Saída completa do Elo 2 — todas as fases, coexistência batch+streaming e planos de rollback (Elo 3)
  - nome: FASE_ALVO
    descricao: Identificador da fase a ser detalhada no Elo 3, ex "Fase 2" (Elo 3)
  - nome: CONTEXTO_OPERACIONAL
    descricao: Ferramentas, plataformas e convenções do ambiente — orquestrador, engine de processamento, data warehouse, barramento (Elo 3)
---

# Cadeia de prompts para migração de pipeline batch para event-driven

## Objetivo

Cadeia de três prompts encadeados (elos) para conduzir a migração de um pipeline em lote (batch) para um modelo event-driven de forma incremental, reversível e sem big-bang. O Elo 1 diagnostica o estado atual (acoplamentos, riscos, restrições invioláveis); o Elo 2 converte esse diagnóstico em uma estratégia de migração por fases com coexistência batch+streaming; o Elo 3 detalha uma fase específica em um runbook executável com pré-condições, rollback e critério de saída.

## Quando usar

- Ao iniciar o planejamento de uma migração de pipeline batch para streaming e precisar de um roteiro estruturado que comece pelo diagnóstico, não pela solução.
- Quando a migração envolve múltiplos dependentes com SLAs distintos que não podem ser interrompidos durante a transição.
- Para gerar runbooks auditáveis por fase, com validação de integridade de dados e ponto-de-não-retorno explícito.
- Em revisões de arquitetura de plataformas de dados onde a reversibilidade e o risco de cada fase precisam ser documentados.

## Exemplo de uso

_A preencher_ (depende do snapshot real do pipeline fornecido em `{{SNAPSHOT_FORGE}}` e `{{SLAS_E_DEPENDENTES}}`).

## Limitações conhecidas

- Os inputs estão divididos por elo: `{{SNAPSHOT_FORGE}}` e `{{SLAS_E_DEPENDENTES}}` alimentam o Elo 1; `{{DIAGNOSTICO_FORGE}}` e `{{OBJETIVO_ALVO}}` alimentam o Elo 2; os demais alimentam o Elo 3. A cadeia pressupõe execução em sessões separadas, com cópia manual da saída entre os elos.
- O Elo 3 gera runbooks com marcadores `<<preencher: ...>>` onde o contexto operacional (nomes de jobs, paths, comandos) não foi fornecido — esses marcadores precisam ser completados pelo usuário antes de executar.
- O Elo 1 não propõe soluções; o diagnóstico produzido é a entrada obrigatória do Elo 2 — pular elos invalida a coerência da cadeia.
