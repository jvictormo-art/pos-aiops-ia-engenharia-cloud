# Matriz de Roteamento — metacortex-manifest × metacortex-triage

As duas skills moram no mesmo território (Kubernetes, YAML, coisa que quebra) e o agente escolhe qual carregar lendo apenas o texto do pedido.

---

## Teste das frases

| Frase | Disparo esperado | Disparo real | Erro? | Análise |
|---|---|---|---|---|
| "o pod do nyx-prod não sobe" | **triage** | triage | — | "pod não sobe" é sintoma de cluster → triage |
| "por que esse deployment está 0/3" | **triage** | triage | — | pergunta sobre estado atual → triage |
| "o service do nyx-stg não tem endpoint" | **triage** | triage | — | "não tem endpoint" é observação de cluster → triage |
| "revisa esse deployment antes de eu subir" | **manifest** | manifest | — | "antes de subir" = pre-flight review do YAML → manifest |
| "esse manifesto está no padrão da casa?" | **manifest** | manifest | — | conformidade com padrão = conferência de manifesto → manifest |
| "cria um Deployment novo do zero pra mim" | **manifest** | manifest | — | geração de YAML → manifest |
| "esse manifesto não sobe no cluster" | **ambígua** | *depende* | ⚠ | ambígua: pode ser YAML inválido (manifest) ou pod crashando (triage) |
| "o Service do nyx não está entregando tráfego" | **triage** | triage | — | comportamento em cluster → triage |
| "o que é um DaemonSet?" | **nenhuma** | nenhuma | — | pergunta conceitual — fora de escopo de ambas |
| "provisiona uma VM nova no Construct pro cliente orion" | **nenhuma** | nenhuma | — | Construct é outro sistema — fora de escopo de ambas |

---

## Casos ambíguos e decisões

### "esse manifesto não sobe no cluster"

Esta frase pode significar duas coisas completamente diferentes:
- **YAML com erro de sintaxe ou campo inválido** → o `kubectl apply` rejeitou → job do `metacortex-manifest`
- **Manifesto aplicado, pod não sobe** → problema em cluster → job do `metacortex-triage`

**Resolução**: quando a frase mencionar "manifesto" + "não sobe" sem indicar se o apply já foi feito, perguntar: *"O apply foi executado com sucesso ou o erro aconteceu no apply?"* Se no apply → manifest. Se depois → triage.

**Ajuste nas descriptions:**
- `metacortex-manifest`: adicionada clareza de que cobre "antes de aplicar" — escrever, revisar, validar o YAML
- `metacortex-triage`: adicionada clareza de que cobre "depois de aplicado" — investigar comportamento em cluster

### "o que é um DaemonSet?" e "provisiona uma VM"

Fora do escopo de ambas. O agente responde com conhecimento geral (DaemonSet) ou redireciona para o sistema correto (Construct para VMs). Nenhuma skill é acionada.

---

## Ajuste aplicado nas descriptions após o teste

**Antes (manifest):**
> Escreve ou confere manifests de Kubernetes para workloads da Metacortex...

**Depois (manifest):**
> Escreve, confere ou valida manifests de Kubernetes **antes de aplicar** no cluster...

**Antes (triage):**
> Investiga e identifica a causa raiz de falhas em workloads Kubernetes...

**Depois (triage):**
> Investiga e identifica a causa raiz de falhas em workloads Kubernetes **já aplicados** no cluster...

A adição de "antes de aplicar" / "já aplicados" elimina a ambiguidade da frase "esse manifesto não sobe no cluster" sem tornar as descriptions longas demais.
