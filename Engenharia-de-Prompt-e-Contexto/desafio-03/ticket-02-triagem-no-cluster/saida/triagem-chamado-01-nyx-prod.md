# Triagem — Chamado 1: nyx-prod, API reinicia sozinha

**Sintoma declarado**: a API do kube-news reinicia sozinha.  
**Contexto**: limites de recurso foram apertados em toda a namespace de uma vez.

---

## Passo 1 — Estado dos pods

```
kubectl get pods -n nyx-prod
```

```
NAME                           READY   STATUS      RESTARTS    AGE
nyx-api-656789474b-vm2jh       0/1     OOMKilled   2           37s
nyx-api-656789474b-znchx       0/1     OOMKilled   2           37s
nyx-postgres-f6fdc6dbf-x7wvv   1/1     Running     0           37s
```

STATUS `OOMKilled` → camada Container. Banco sobe normal — o problema é isolado na API.

## Passo 2a — Describe do pod

```
kubectl describe pod nyx-api-656789474b-vm2jh -n nyx-prod
```

Seção relevante:
```
State:      Terminated
  Reason:   OOMKilled
  Exit Code: 137
Last State: Terminated
  Reason:   OOMKilled
  Exit Code: 137
Limits:
  cpu:     200m
  memory:  24Mi
Requests:
  cpu:      50m
  memory:   16Mi
```

Exit code 137 = SIGKILL do kernel por estouro de memória. O limite de 24Mi é insuficiente para uma aplicação Node.js — o runtime do Node sozinho consome mais que isso antes de processar qualquer requisição.

---

## Resultado

```
CAUSA:     Container da API (nyx-api) é terminado pelo kernel por exceder o limite de memória
EVIDÊNCIA: Pod nyx-api-656789474b-vm2jh — resources.limits.memory=24Mi — exit code 137 (OOMKilled)
CAMADA:    container
O QUE ESTÁ OK: nyx-postgres sobe e fica Running; o problema é exclusivo do Deployment nyx-api
AÇÃO SUGERIDA: aumentar resources.limits.memory para >= 128Mi (e requests.memory para >= 64Mi)
               — os valores atuais foram resultado de corte de custo sem medição de consumo real
```

**Triagem encerrada.** Causa identificada no Passo 2a sem precisar de logs.
