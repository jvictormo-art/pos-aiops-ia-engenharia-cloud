# Arquivo Final — metacortex-dashboard

**Data de encerramento**: 2026-09-17
**Status**: todos os critérios de aceite da proposta verificados contra cluster real

---

## O que foi entregue conforme o spec

| Critério | Status | Evidência |
|---|---|---|
| Roda contra o `current-context`, sem flag de cluster | ✓ | `dashboard/app.py` não aceita flag de cluster; só `--kubeconfig` (caminho do arquivo) e `--namespace` (inicial) |
| Mostra os 5 objetos com filtro e busca | ✓ | `evidencia/01-nyx-dev-saudavel.svg` a `05-orion-prod-fake-shop.svg` |
| Distingue campo ausente de campo vazio | ✓ | `readyReplicas` ausente → `0/N` (não `None/N`); `EndpointSlice` com `endpoints: null` → "sem endpoint" (não erro) |
| Cluster inalcançável — sem stack trace | ✓ | `evidencia/06-cluster-inalcancavel.svg` |
| Credencial expirada/inválida — sem stack trace | ✓ | `evidencia/07-credencial-invalida.svg` |
| RBAC nega um recurso, outros continuam | ✓ | `evidencia/08-rbac-restrito-platform-ro.svg` — Pods/Eventos funcionam, Deployments/Services mostram 403 |
| Nenhuma chamada de escrita | ✓ | `grep -E '\.(create\|patch\|delete\|replace)_' dashboard/*.py` retorna vazio |
| Ciclo OpenSpec completo | ✓ | proposta → tarefas → specs → implementação → este arquivo |

---

## Onde o spec precisou ser corrigido durante a implementação

### 1. Versão mínima do Python

`spec-decisoes.md` fixava "Python 3.10+" — decisão razoável no papel, mas a máquina onde a ferramenta foi de fato implementada e testada tem Python 3.9.6. A sintaxe `str | None` (PEP 604) só funciona sem `from __future__ import annotations` a partir do 3.10. Corrigido adicionando o import futuro em `app.py` (já estava em `k8s_reader.py`). A decisão de linguagem não mudou — só o número da versão mínima suportada, para bater com o ambiente real em vez do ambiente ideal.

### 2. O cliente tipado quebra exatamente no dado que o ticket avisou ser sensível

O ticket já alertava: "o campo dos endereços não vem vazio — ele simplesmente não vem". O que o spec não previu é que o **cliente oficial do Kubernetes**, ao desserializar um `EndpointSlice` com `endpoints: null`, lança `ValueError` — porque o modelo gerado trata `endpoints` como campo obrigatório não-nulo. E o erro não fica isolado no objeto afetado: ele derruba a desserialização de **toda a lista** de EndpointSlices do namespace, porque o cliente tenta converter todos os itens da resposta de uma vez.

Isso significa que a decisão "usar o cliente oficial porque ele resolve tipagem corretamente" (Decisão 2 do `spec-decisoes.md`) tinha uma exceção real que só apareceu ao rodar contra o cluster de verdade — a Decisão 3 de `nyx-stg`, que já existia como evidência do Ticket 02. **Correção**: `_contar_endpoints_prontos` usa `_preload_content=False` e faz o parsing do JSON bruto manualmente só para esta chamada, contornando o modelo tipado no ponto exato onde ele se mostrou frágil demais para o dado real.

### 3. Pods presos em initContainer precisam de uma fonte de motivo que o spec não mencionou

`spec-comportamento.md` falava em `containerStatuses[].state.waiting.reason` como fonte do campo MOTIVO — replicando o exemplo do próprio ticket. O ticket não usa um exemplo com `initContainers`, e o fake-shop (gerado no Ticket 01) usa exatamente esse padrão para separar a migração de banco. Um pod com o initContainer em `ImagePullBackOff` reporta, no container principal, `waiting.reason: PodInitializing` — tecnicamente verdadeiro, praticamente inútil. **Correção**: `_resumir_pod` agora verifica `initContainerStatuses` primeiro, e prefixa o motivo com `Init:` quando a causa está lá — replicando a mesma convenção que o `kubectl` já usa na coluna STATUS.

### 4. Credencial inválida nem sempre é um 401

O spec (Decisão 4/Cenário 2 de `spec-comportamento.md`) descrevia "credencial expirada" como `ApiException` com `status == 401`. Isso vale para autenticação por token. O cluster usado como evidência (`kind-metacortex-lab`) autentica por certificado de cliente (mTLS) — e um certificado corrompido ou inválido nunca chega a completar o handshake TLS, então nunca existe uma resposta HTTP para ter um código de status. A falha aparece como `SSLError` dentro de um `MaxRetryError`, na mesma família de exceção que "cluster inalcançável". **Correção**: `_classificar_excecao` agora inspeciona a causa do `MaxRetryError` e separa o caso de SSL/certificado inválido, mostrando a mensagem de credencial em vez da de conexão.

### 5. Bug estrutural na primeira versão da tela (não é correção de spec, é correção de código)

A primeira versão de `app.py` tentava trocar o painel de "conectando" por um painel de erro ou pelos painéis de dados usando `remove_children()` seguido de `mount()` com o mesmo `id`. `remove_children()` é assíncrono e não tinha terminado quando o `mount()` seguinte rodava, causando `DuplicateIds`. Corrigido restruturando `compose()` para criar os widgets de erro e de dados uma única vez, alternando visibilidade (`.display = True/False`) em vez de remontar.

---

## O que ficou para uma versão futura

Ver `spec/proposta.md`, seção "O que está fora do escopo desta versão" — nenhum item foi adicionado além do que já estava listado antes da implementação começar.
