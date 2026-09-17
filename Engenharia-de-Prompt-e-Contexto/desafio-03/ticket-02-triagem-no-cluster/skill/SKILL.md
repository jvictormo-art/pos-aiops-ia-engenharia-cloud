---
name: metacortex-triage
description: Investiga e identifica a causa raiz de falhas em workloads Kubernetes já aplicados no cluster da Metacortex. Use ao receber chamados sobre pods que não sobem, deployments travados, serviços sem tráfego ou qualquer sintoma de "fora do ar" após o deploy. Nunca aplica correções — identifica e para.
---

# metacortex-triage

**Limite absoluto**: a triagem lê, nunca escreve. As únicas ferramentas usadas são `mcp__kubernetes__kubectl_get`, `mcp__kubernetes__kubectl_describe` e `mcp__kubernetes__kubectl_logs`. Nenhuma correção é aplicada no cluster, mesmo que a causa seja óbvia e o agente tenha permissão para isso.

---

## Entrada esperada

O chamado chega como: namespace + sintoma declarado pelo cliente (ex: "pods não sobem", "serviço retorna 503", "deploy travou"). Se o namespace não vier, pergunte antes de começar.

---

## Método de triagem — camadas em ordem

### Passo 1 — Estado dos pods

```
mcp__kubernetes__kubectl_get  resource=pods  namespace=<namespace>
```

Leia a coluna STATUS e decida a camada:

| STATUS | Camada provável | Próximo passo |
|---|---|---|
| `OOMKilled` ou `CrashLoopBackOff` (saindo rápido) | Container | Passo 2a |
| `ErrImagePull` ou `ImagePullBackOff` | Registry | Passo 2b |
| `Pending` | Agendamento | Passo 2c |
| `Running` com 0/N Ready e serviço retorna 503 | Roteamento | Passo 2d |
| `Running` com 0/N Ready sem queixas de 503 | Readiness/App | Passo 2e |

---

### Passo 2a — Container morre rápido (OOMKilled / CrashLoopBackOff)

```
mcp__kubernetes__kubectl_describe  resource=pod/<nome-do-pod>  namespace=<namespace>
```

Olhe em ordem:
1. `Last State.Reason` — se `OOMKilled`, **causa identificada: memory.limits muito baixo**. Registre o valor de `Limits.memory` e o exit code (137). PARE.
2. `Last State.Exit Code` — se != 137 e != 1, é sinal de crash do processo. Vá para Passo 3 (logs).
3. Se exit code 1 ou outro código de aplicação → Passo 3.

---

### Passo 2b — Imagem não baixa (ErrImagePull / ImagePullBackOff)

```
mcp__kubernetes__kubectl_get  resource=events  namespace=<namespace>
```

Filtre os eventos `Warning` sobre o pod. Leia a mensagem de erro:
- `not found` → **causa identificada: tag de imagem não existe no registry**. Registre a imagem e a tag exatas. PARE.
- `unauthorized` ou `403` → problema de credencial de pull. Registre. PARE.
- `timeout` → problema de rede. Registre. PARE.

---

### Passo 2c — Pod em Pending

```
mcp__kubernetes__kubectl_describe  resource=pod/<nome-do-pod>  namespace=<namespace>
```

Olhe a seção `Events` no final:
- `Insufficient memory` / `Insufficient cpu` → **causa identificada: namespace sem recursos suficientes no nó**. PARE.
- `Unschedulable` com node selector / taint → problema de agendamento. PARE.

---

### Passo 2d — Pods Running mas Service retorna 503 (zero endpoints)

Primeiro confirme que o Service não tem endpoints:
```
mcp__kubernetes__kubectl_get  resource=endpoints/<nome-do-service>  namespace=<namespace>
```

Se a lista de endereços estiver vazia:
```
mcp__kubernetes__kubectl_get  resource=service/<nome-do-service>  namespace=<namespace>  output=yaml
mcp__kubernetes__kubectl_get  resource=pods  namespace=<namespace>  output=yaml
```

Compare `Service.spec.selector` com `Pod.metadata.labels`. Se diferirem por qualquer caractere:
**Causa identificada: seletor do Service não casa com os rótulos do pod**. Registre os dois valores lado a lado. PARE.

Se os seletores casarem e endpoints ainda estiverem vazios → pods não estão Ready. Vá para Passo 2e.

---

### Passo 2e — Pod Running mas não Ready (probe failing)

```
mcp__kubernetes__kubectl_logs  pod=<nome-do-pod>  namespace=<namespace>
```

Procure erros de conexão com banco, porta errada, crash de aplicação. Se os logs mostrarem a causa → PARE e registre.

Se os logs estiverem limpos, verifique se a readinessProbe aponta para endpoint que existe:
```
mcp__kubernetes__kubectl_describe  resource=pod/<nome-do-pod>  namespace=<namespace>
```
Olhe `Readiness` — path e port. Confirme que a aplicação expõe esse endpoint.

---

### Passo 3 — Logs (quando a causa não aparece em describe)

Só chegue aqui se os passos anteriores não fecharam a causa.

```
mcp__kubernetes__kubectl_logs  pod=<nome-do-pod>  namespace=<namespace>
```

Leia as últimas 50 linhas. Se o pod já morreu, use `previous=true` para ver o log do container anterior.

---

## Quando parar

Pare assim que identificar a causa. Não continue investigando outras camadas por completude. A triagem acabou quando uma frase descreve a causa: *o quê* falhou, *onde* (qual recurso/campo), e *o valor observado* que deveria ser diferente.

---

## Formato do relatório final

```
CAUSA: <uma frase descrevendo o problema>
EVIDÊNCIA: <recurso + campo + valor observado>
CAMADA: container | registry | agendamento | roteamento | aplicação
AÇÃO SUGERIDA: <o que o time deve corrigir — sem aplicar>
```

Inclua também o que está funcionando ao lado do que quebrou (o banco sobe? as outras réplicas?)  — isso separa triagem de chute.
