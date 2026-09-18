# Spec de Comportamento — metacortex-dashboard

---

## Inicialização

```
python3 dashboard.py
```

Sem flags de cluster ou contexto. Na inicialização:
1. Carrega o kubeconfig padrão (`~/.kube/config` ou `$KUBECONFIG`)
2. Lê o `current-context` — não pede confirmação, não oferece escolha
3. Tenta uma chamada de baixo custo (`list_namespace`) para validar que o cluster responde
4. Se falhar, mostra o erro tratado (ver seção "Cenários de falha") e **não** deixa a tela em branco

O nome do contexto corrente aparece sempre visível no rodapé da tela, para que o operador saiba contra qual cluster está olhando sem precisar checar no terminal.

---

## Layout da tela

```
┌─ metacortex-dashboard ─────────────────────────── contexto: kind-metacortex-lab ─┐
│ Namespace: [ nyx-dev        ▾]   Busca: [___________]                            │
├────────────────────────────────────────────────────────────────────────────────┤
│ PODS                                                                              │
│  NOME                          READY  STATUS             RESTARTS  MOTIVO        │
│  nyx-kubenews-6d697bb8b5-9z82f  1/1   Running             0                       │
│  nyx-api-656789474b-vm2jh       0/1   CrashLoopBackOff    49        OOMKilled      │
├────────────────────────────────────────────────────────────────────────────────┤
│ DEPLOYMENTS                                                                       │
│  NOME           PRONTOS/DESEJADOS   CONDIÇÃO                                     │
│  nyx-kubenews    2/2                Available                                     │
│  orion-web       0/3                MinimumReplicasUnavailable                    │
├────────────────────────────────────────────────────────────────────────────────┤
│ SERVICES                                                                          │
│  NOME           ENDPOINT                                                          │
│  nyx-kubenews    2 endereço(s)                                                    │
│  nyx-api         sem endpoint                                                     │
├────────────────────────────────────────────────────────────────────────────────┤
│ EVENTOS RECENTES (namespace selecionado)                                         │
│  TIPO      RAZÃO      OBJETO                    MENSAGEM                    IDADE│
│  Warning   BackOff    Pod/nyx-api-...-vm2jh      Back-off restarting...      2m   │
└────────────────────────────────────────────────────────────────────────────────┘
```

Namespaces aparecem em um seletor no topo. Pods/Deployments/Services/Eventos são sempre relativos ao namespace selecionado (não há visão "todos os namespaces" para os quatro painéis — só o seletor de Namespaces em si lista todos).

---

## Ausência de campo vs. campo vazio

Esta distinção é o ponto mais sensível do spec, porque a API do Kubernetes usa as duas formas e elas significam coisas diferentes.

| Situação na API | O que a tela mostra | O que a tela NUNCA mostra |
|---|---|---|
| `status.containerStatuses[].ready == false`, sem `lastState.terminated` | `RESTARTS: N`, `MOTIVO: (aguardando)` | `MOTIVO: None` ou `MOTIVO: ` em branco |
| `deployment.status` sem o campo `readyReplicas` | `0/<replicas desejadas>` | `None/<replicas>` |
| `EndpointSlice` do Service não existe nenhuma | `sem endpoint` | `0 endereço(s)` — **zero não é a mesma coisa que ausente** |
| `EndpointSlice` existe mas `endpoints` é lista vazia | `sem endpoint` (mesmo texto do caso acima — do ponto de vista do operador, o resultado prático é idêntico: nada recebe tráfego) | — |
| `containerStatuses[].state.waiting.reason` presente | O valor literal (`CrashLoopBackOff`, `ErrImagePull`, etc.) | Um motivo genérico inventado pela ferramenta |
| `containerStatuses[].lastState.terminated.reason` presente (ex: `OOMKilled`) | Substitui o motivo de `waiting` quando existe — é a causa mais específica disponível | — |

**Regra geral de implementação**: todo acesso a um campo opcional da API usa `getattr(obj, "campo", None)` (ou o equivalente do cliente Python, que já retorna `None` para campos ausentes do lado do servidor) e a camada de renderização decide o texto — nunca formata `None` diretamente na tela.

**Caso do `readyReplicas` ausente (exemplo do ticket)**: quando nenhuma réplica está pronta, a API do Kubernetes **omite** o campo `status.readyReplicas` em vez de enviar `0`. O cliente Python retorna `None` neste caso. A tela trata `None` e `0` como equivalentes para exibição (`0/3`), porque para o operador a pergunta é "quantas estão prontas", e a resposta é zero nos dois casos — a distinção entre "campo omitido" e "campo zero" importa para quem programa a leitura, não para quem lê a tela. Isso é diferente do caso do Service/Endpoints, onde a distinção (ausência total de `EndpointSlice` vs. `EndpointSlice` vazio) *também* colapsa para o mesmo texto na tela, pelo mesmo motivo: o operador quer saber "tem tráfego chegando ou não", não a árvore de decisão da API.

---

## EndpointSlice — agregação

Um Service pode ter mais de um objeto `EndpointSlice` associado (rótulo `kubernetes.io/service-name`). A leitura:

1. Lista todos os `EndpointSlice` no namespace com o rótulo `kubernetes.io/service-name=<nome-do-service>`
2. Para cada fatia, soma os endereços cujo `conditions.ready == true`
3. Se a soma total for zero (nenhuma fatia, ou fatias existentes sem endereços prontos) → `sem endpoint`
4. Caso contrário → `N endereço(s)`

---

## Cenários de falha

### 1 — Contexto corrente aponta para cluster que não responde

**Como se manifesta**: timeout de conexão na primeira chamada (`list_namespace`).
**Comportamento exigido**: tela mostra um painel de erro único, central, com o texto:
```
Não foi possível conectar ao cluster do contexto "<nome-do-contexto>".
<mensagem curta do erro de rede>
Verifique se o cluster está no ar ou troque o contexto com "kubectl config use-context".
```
Nenhum painel de dados é desenhado. Nenhum stack trace do Python aparece na tela — a exceção é capturada no ponto de entrada e traduzida para esta mensagem.

### 2 — Credencial expirada

**Como se manifesta**: `ApiException` com `status == 401`.
**Comportamento exigido**: mesma estrutura do cenário 1, texto adaptado:
```
Credencial expirada ou inválida para o contexto "<nome-do-contexto>".
Renove a credencial (ex.: "aws eks get-token" / login do provedor) e reabra a aplicação.
```

### 3 — RBAC nega um tipo de recurso, outros continuam acessíveis (o caso do `platform-ro`)

Este é o cenário mais interessante porque **não é um erro fatal** — é uma degradação parcial, e a ferramenta precisa continuar útil com o que sobrou de acesso.

**Como se manifesta**: `ApiException` com `status == 403` na chamada de um tipo de recurso específico (por exemplo, o contexto tem permissão para `pods` e `namespaces`, mas não para `deployments`).

**Comportamento exigido**:
- Cada painel (Pods, Deployments, Services, Eventos) faz sua própria chamada e trata seu próprio erro **de forma independente** — um 403 em Deployments não interrompe a renderização de Pods
- O painel sem permissão mostra, no lugar da tabela:
  ```
  DEPLOYMENTS
  Sem permissão para listar este recurso no contexto atual (403).
  ```
- O rodapé da tela acumula um contador visível: `2 painel(is) com acesso restrito neste contexto` — para que o operador saiba, de uma olhada, que a foto está incompleta, sem precisar notar isso por ausência

**Por que isso importa mais que os outros dois cenários**: um erro fatal (cluster fora do ar) é óbvio — a tela para. Uma degradação parcial é traiçoeira porque o resto da tela continua funcionando normalmente, e é fácil um operador de plantão às 3h confundir "este painel está vazio porque não há deployments" com "este painel está vazio porque não tenho permissão para vê-los". As duas situações têm que ser visualmente distintas.

### 4 — Recurso não existe no namespace (não é erro)

Diferente dos três cenários acima: quando um namespace de fato não tem nenhum Service, a tabela de Services aparece vazia com o texto `Nenhum Service neste namespace` — isso não é uma falha do ambiente, é um fato sobre o cluster, e não deve ser tratado com o mesmo destaque visual de um erro de permissão ou conexão.

---

## Invariante de leitura

Ver `spec-decisoes.md`, seção "Como a garantia de leitura fica visível no projeto". Resumo: a única classe que fala com a API (`ClusterReader`) não importa nenhum método de escrita; isso é verificado por grep no pipeline de validação, não apenas prometido em texto.

---

## Filtro e busca

- **Filtro por namespace**: seletor único; todos os quatro painéis reagem à troca
- **Busca por nome**: campo de texto livre; filtra por substring (case-insensitive) o nome do objeto dentro do painel focado no momento — não busca através de todos os painéis simultaneamente, porque os cinco tipos de objeto têm namespaces e nomes em espaços diferentes e uma busca global geraria resultados confusos de misturar tipos
