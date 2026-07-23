---
nome: Triagem de pods Kubernetes
descricao: Analisa um snapshot de cluster Kubernetes e identifica pods problemáticos com causa provável, evidência e próxima ação do plantão.
versao: 1.0.0
tags: [kubernetes, sre, devops, incidente, pods]
inputs:
  - nome: snapshot_cluster
    descricao: Snapshot do cluster contendo status, eventos e logs dos pods relevantes
---

## Objetivo

Fazer triagem de saúde de pods a partir de um snapshot de cluster Kubernetes. O modelo atua como SRE sênior de plantão: filtra ruído, cruza status + eventos + logs e entrega diagnóstico com causa provável, evidência concreta e próxima ação executável.

## Quando usar

- Durante ou após um incidente para priorizar qual pod investigar primeiro.
- Em revisões periódicas de saúde do cluster.
- Quando um snapshot já foi coletado por alguém com acesso e precisa de análise rápida.

## Como usar

Substitua `{{snapshot_cluster}}` pelo conteúdo coletado do cluster, incluindo para cada pod relevante:

- saída de `kubectl get pods`
- saída de `kubectl describe pod <nome>`
- logs da aplicação (`kubectl logs`)

## Exemplo de saída

```
Resumo: 12 pods avaliados, 2 problemáticos.

---
**`payments/payment-worker-7d9f`** — `CrashLoopBackOff` · restarts: `14`
- **Causa provável:** falha de conexão com o banco na inicialização — a aplicação não encontra a variável DATABASE_URL.
- **Evidência:** log `panic: dial tcp: connection refused` imediatamente após o boot, evento `BackOff restarting failed container`.
- **Próxima ação:** verificar o Secret montado no pod (`kubectl describe pod payment-worker-7d9f -n payments`) e confirmar se a variável DATABASE_URL está presente.
- **Severidade:** 🔴 Crítico
---
```

## Limitações conhecidas

- Opera sobre snapshot estático — diagnósticos são hipóteses prováveis, não certezas.
- Se logs, eventos ou status estiverem incompletos no snapshot, o modelo declara a causa como indeterminada e indica como obter o sinal faltante.
- Não executa comandos nem acessa o cluster diretamente.

## Avaliação (promptfoo)

Executado em 2026-07-23 via `promptfoo eval` (`promptfooconfig.yaml`), 3 casos × 2 providers.

| Provider | Resultado | Observação |
|---|---|---|
| `anthropic:claude-haiku-4-5-20251001` | 1/3 (Entrada 1 passa) | Entradas 2 e 3 reprovam só por `latency` (8,5s e 9,7s vs limite de 5s); conteúdo correto nos três casos. |
| `ollama:chat:llama3.1:8b` | 0/3 | Reprova `latency` em todos os casos, com degradação severa conforme o snapshot cresce (36s → 65s → 98s). Também erra conteúdo: não cita "Insufficient" na Entrada 2 e não reconhece o cluster saudável na Entrada 3. |

### Curadoria

- **Latência escala mal no Ollama local**: mesmo a Entrada 3 (cluster saudável, snapshot menor) levou quase 100s — evidência de gargalo de hardware (CPU-only), não do tamanho do prompt. O modelo fica carregado em memória entre chamadas, mas ainda assim fica bem longe do budget de 5s.
- **Confiabilidade de formato**: no snapshot saudável (Entrada 3), o Haiku reconhece corretamente "sem pods problemáticos"; o Llama 3.1 8B local não segue essa distinção com a mesma consistência — reforça manter o modelo Anthropic como default de produção e tratar o Ollama como prova de portabilidade/segundo provider, não como substituto.
- **Bug de config corrigido**: os dois asserts `type: regex` com flag inline `(?i)` (inválida no engine JS do promptfoo, causava `Invalid group`) foram trocados por `type: javascript` com `/…/i.test(output)` — confirmado sem mais erros nesta rodada.
- **Bug de custo corrigido**: mesmo ajuste do `nota-de-triagem` — assert `javascript` tolera providers sem custo reportado (Ollama) em vez de quebrar a suíte.
