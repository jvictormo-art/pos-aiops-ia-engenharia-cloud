# Triagem — Chamado 3: nyx-stg, kube-news responde 503

**Sintoma declarado**: o kube-news responde 503 para chamadas externas. A aplicação está de pé e saudável.

---

## Passo 1 — Estado dos pods

```
kubectl get pods -n nyx-stg
```

```
NAME                           READY   STATUS    RESTARTS    AGE
nyx-api-7f4487c6ff-bl899       0/1     Running   3           63s
nyx-api-7f4487c6ff-dv9z8       1/1     Running   2           63s
nyx-postgres-f6fdc6dbf-224xn   1/1     Running   0           63s
```

Pods em Running (um deles 1/1 Ready) — a app não está crashando. Sintoma é 503 externo com pod aparentemente saudável → camada Roteamento (Passo 2d).

## Passo 2d — Verificação dos endpoints

```
kubectl get endpoints nyx-api -n nyx-stg
```

```
NAME      ENDPOINTS   AGE
nyx-api   <none>      63s
```

Endpoints vazios — o Service não está entregando tráfego para nenhum pod. O 503 é do ingress/caller, não da app.

## Passo 2d — Cruzamento seletor × rótulos

```
kubectl get service nyx-api -n nyx-stg -o yaml  →  spec.selector: {app: nyx-api}
kubectl get pods -n nyx-stg -o yaml              →  metadata.labels: {app: nyxapi}
kubectl get deployment nyx-api -n nyx-stg -o yaml → spec.selector.matchLabels: {app: nyxapi}
```

| Campo | Valor |
|---|---|
| Service.spec.selector | `{app: nyx-api}` (com hífen) |
| Pod.metadata.labels | `{app: nyxapi}` (sem hífen) |
| Deployment.matchLabels | `{app: nyxapi}` (sem hífen) |

O Deployment está internamente consistente (matchLabels casa com os rótulos do pod, por isso os pods sobem). O Service usa `nyx-api` com hífen — diverge dos pods por um único caractere. Resultado: zero endpoints, 503 para todo tráfego externo.

---

## Resultado

```
CAUSA:     Service.spec.selector não casa com os rótulos do pod — diferem em um caractere
EVIDÊNCIA: Service nyx-api — selector: {app: "nyx-api"}
           Pod nyx-api-* — labels: {app: "nyxapi"}
           kubectl get endpoints nyx-api -n nyx-stg → ENDPOINTS: <none>
CAMADA:    roteamento (metadado)
O QUE ESTÁ OK: pods sobem e um já está 1/1 Ready; nyx-postgres Running; Deployment internamente
               consistente — o problema está apenas no seletor do Service
AÇÃO SUGERIDA: corrigir Service.spec.selector para {app: nyxapi} ou alinhar os dois lados;
               após a correção os endpoints aparecem automaticamente
```

**Triagem encerrada.** Causa identificada sem precisar de logs ou describe — bastou cruzar endpoints com labels.

---

## Nota sobre o método

Este chamado é o que separa triagem de chute: os pods estão Running (um até 1/1 Ready), o que levaria quem começa por logs ou describe a concluir "a app está OK" — e estaria certa a respeito da app, mas errada a respeito da causa do 503. O método exige checar endpoints antes de descartar a hipótese de roteamento quando o sintoma é falha no tráfego externo com pods aparentemente saudáveis.
