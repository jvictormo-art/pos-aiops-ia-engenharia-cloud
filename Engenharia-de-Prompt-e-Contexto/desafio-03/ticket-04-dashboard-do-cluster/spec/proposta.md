# Proposta — metacortex-dashboard

**Versão**: 1.0
**Data**: 2026-09-17
**Status**: aprovada

---

## Problema

Toda triagem no parque começa da mesma forma: alguém abre o terminal e roda de seis a dez comandos (`kubectl get pods`, `kubectl get deploy`, `kubectl get svc`, `kubectl get endpoints`, `kubectl get events`, repetidos por namespace) só para montar na cabeça o retrato do que está de pé e do que não está. Isso consome os primeiros dez minutos de todo chamado antes de a investigação de fato começar.

## O que estamos construindo

Uma aplicação que roda na máquina de quem opera, lê o kubeconfig local e o **contexto corrente** — e só ele — e mostra em tela:

- Namespaces do cluster
- Pods: estado, contagem de reinícios, motivo quando em falha
- Deployments: prontos sobre desejados
- Services: se têm endpoint ou não
- Eventos recentes do namespace selecionado
- Filtro por namespace e busca por nome

Não substitui o terminal. Encurta a fase de reconhecimento.

## Corte de escopo — sem multicluster

O kubeconfig do parque tem múltiplos destinos (dev/stg/prod, cada um com seu próprio usuário e certificado). A aplicação **não** oferece seletor de cluster na tela e **não** troca de contexto por conta própria. Quem quiser olhar outro cluster troca o `current-context` por fora (`kubectl config use-context ...`) e reabre a aplicação. Este corte existe porque colocar troca de cluster na tela introduz uma superfície de erro que o ticket não pede resolver (confirmação de qual cluster está no ar, cache por cluster, etc.) e desloca o foco do problema real — o tempo de reconhecimento dentro de UM cluster.

## Invariante inegociável — só lê

A aplicação fala com produção. Nenhuma operação de escrita é executada: sem `apply`, `delete`, `scale`, `patch`, `edit`. A garantia é estrutural — ver `spec-decisoes.md`, seção "Como a garantia de leitura fica visível no projeto".

## Workload real usado como evidência

Para o dashboard ter o que mostrar, dois projetos foram implantados no cluster `kind-metacortex-lab` usando manifests produzidos pela skill `metacortex-manifest` (Ticket 01):

| Projeto | Namespace | Skill usada | Resultado real |
|---|---|---|---|
| kube-news | `nyx-dev` | `metacortex-manifest` (modo escrita, invocado nesta sessão) | 2/2 pods Running, endpoints presentes |
| fake-shop | `orion-prod` | `metacortex-manifest` (modo escrita, Ticket 01) | `Init:ErrImagePull` — o manifest usa `registry.metacortex.io`, que não existe fora da ficção do parque |

Além disso, os três laboratórios quebrados do Ticket 02 (`nyx-prod`, `nyx-stg`, `orion-stg`) continuam no mesmo cluster e servem de evidência adicional de estados de falha: `CrashLoopBackOff`/`OOMKilled`, `ImagePullBackOff`, e Service sem endpoint por seletor divergente.

## Critérios de aceite

- Roda contra o `current-context` do kubeconfig da máquina, sem flag de cluster
- Mostra os 5 objetos exigidos com filtro por namespace e busca por nome
- Distingue campo ausente de campo vazio (nenhum "0/0" fantasma quando o dado não existe)
- Comportamento correto com cluster inalcançável, credencial expirada, e RBAC negando um tipo de recurso enquanto outros continuam acessíveis — sem tela branca, sem stack trace cru
- Nenhuma chamada de escrita em todo o código
- Passa pelo ciclo completo do OpenSpec: proposta → tarefas → specs → implementação → arquivamento

## O que está fora do escopo desta versão

| Item | Motivo |
|---|---|
| Seletor de cluster / multicluster | Corte de escopo explícito do ticket |
| Watch/streaming de eventos em tempo real | Ver `spec-decisoes.md` — decisão de atualização por polling na primeira fatia |
| Edição ou ação a partir da tela | Viola o invariante de leitura |
| Autenticação própria (a aplicação não gerencia credenciais, usa as do kubeconfig) | Fora do problema que o ticket resolve |
| Métricas de CPU/memória (metrics-server) | Não estava nos 5 objetos mínimos exigidos |
