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

## Avaliação (promptfoo)

Executado em 2026-07-23 via `promptfoo eval` (`promptfooconfig.yaml`), 3 casos × 2 providers.

| Provider | Resultado | Observação |
|---|---|---|
| `anthropic:claude-sonnet-4-6` | 0/3 (8/9 asserts em média) | Reprova só o assert de `latency` — respostas levaram 5,4s–9,7s, acima do limite de 5s do checkpoint. Todo o conteúdo (rótulos, formato, handle de escalonamento) passa. |
| `ollama:chat:llama3.1:8b` | 0/3 | Reprova `latency` por larga margem (10,5s–29s, hardware sem GPU) e falha formato em 2/3 casos (label `HIPÓTESE INICIAL:` ausente em um caso; limite de 8 linhas estourado em dois). |

### Curadoria

- **Segundo provider**: comecei tentando OpenAI (sem crédito configurado) e depois Google Gemini via AI Studio — mas a key gerada caiu num projeto com free tier zerado (`limit: 0` reportado pela própria API do Google). Optei por Ollama local (`llama3.1:8b`): sem custo, sem dependência de billing de terceiros, satisfaz o requisito de "pelo menos dois provedores distintos" do desafio.
- **Trade-off de latência**: o limite de 5s do checkpoint é apertado até para o Sonnet numa resposta de 5 campos — ele passa em tudo, menos nisso. Não afrouxei o threshold pra forçar aprovação; documentar essa reprovação real é o próprio objetivo do gate (o checkpoint pede exatamente esse tipo de trade-off custo/latência × modelo).
- **Ollama como segundo provider**: cumpre o requisito de diversidade de fornecedor, mas nesse hardware (CPU, sem GPU) não é candidato de produção sob esse SLA — confirma na prática por que o modelo default da biblioteca continua sendo Anthropic.
- **Bug de config corrigido**: o assert nativo `type: cost` do promptfoo lança erro para providers que não reportam custo (caso do Ollama). Troquei por um assert `javascript` que trata custo indefinido como "$0 por definição" (inferência local), preservando o gate de custo para os providers pagos sem quebrar a suíte.
