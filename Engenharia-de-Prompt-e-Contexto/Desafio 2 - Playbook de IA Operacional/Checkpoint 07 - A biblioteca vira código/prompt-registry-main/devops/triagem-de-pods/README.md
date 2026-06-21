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
