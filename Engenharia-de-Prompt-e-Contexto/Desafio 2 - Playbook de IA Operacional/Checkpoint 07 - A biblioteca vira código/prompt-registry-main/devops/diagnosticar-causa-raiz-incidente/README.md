---
nome: Diagnóstico de causa-raiz de incidente SRE
descricao: Analisa artefatos heterogêneos de um incidente (config, métricas e logs) e produz diagnóstico de causa-raiz com linha do tempo, cadeia causal, mitigação imediata e correção definitiva.
versao: 1.0.0
tags: [sre, incidente, causa-raiz, observabilidade, diagnóstico]
inputs:
  - nome: SISTEMA
    descricao: Nome e descrição curta do sistema afetado e seu papel na plataforma
  - nome: SINTOMA_REPORTADO
    descricao: O que o plantão observou antes de escalar o incidente
  - nome: ARTEFATOS
    descricao: Um ou mais blocos com tipo (config/métricas/log/outro), origem e conteúdo bruto dos artefatos do incidente
  - nome: JANELA_TEMPORAL
    descricao: Intervalo de interesse do incidente — opcional
---

# Diagnóstico de causa-raiz de incidente SRE

## Objetivo

Atua como SRE sênior especializado em sistemas distribuídos: recebe um pacote de artefatos de incidente (configuração, métricas e logs) e produz um diagnóstico estruturado em sete seções — resumo executivo, linha do tempo, cadeia causal, causa-raiz, mitigação imediata, correção definitiva e confiança/lacunas — distinguindo o gatilho inicial dos efeitos em cascata.

## Quando usar

- Ao escalar um incidente que já passou da triagem e precisa de análise profunda de causa-raiz.
- Quando artefatos de telemetria heterogêneos (métricas, logs, config) precisam ser correlacionados para encontrar a origem do problema.
- Para produzir um diagnóstico acionável que o próximo turno ou a liderança técnica possam consumir diretamente.
- Em postmortems, para reconstruir a cadeia causal a partir dos artefatos coletados durante o incidente.

## Exemplo de uso

_A preencher_ (depende dos artefatos reais do incidente fornecidos nas variáveis `{{SISTEMA}}`, `{{SINTOMA_REPORTADO}}` e `{{ARTEFATOS}}`).

## Limitações conhecidas

- Opera exclusivamente sobre os artefatos fornecidos na entrada; não tem acesso ao cluster, métricas em tempo real ou histórico fora do snapshot.
- `{{JANELA_TEMPORAL}}` é opcional — sem ela, o modelo infere a janela a partir dos timestamps nos artefatos; resultados podem ser menos precisos se os artefatos não tiverem timestamps consistentes.
- Hipóteses de causa-raiz têm nível de confiança declarado — artefatos incompletos ou sem correlação temporal reduzem a confiança do diagnóstico.
- A seção "Tratamento de Dados Sensíveis" é informativa: o modelo sinaliza dados sensíveis mas não os remove automaticamente do contexto enviado ao modelo externo.
