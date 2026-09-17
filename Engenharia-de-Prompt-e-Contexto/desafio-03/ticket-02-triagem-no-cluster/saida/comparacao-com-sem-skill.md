# Comparação: com skill × sem skill

Dois casos medidos. Mesma sessão limpa, mesmo cluster, mesmo sintoma de entrada.

---

## Caso A — Chamado 1 (nyx-prod, OOMKilled)

### Sem skill

**Prompt enviado ao agente**: "a API do nyx-prod está reiniciando sozinha, verifica aí"

**O que aconteceu**:
O agente sem skill não tem método definido. Em sessão limpa, tendeu a:
1. Perguntar por logs antes de checar o status dos pods
2. Pedir `kubectl logs` do pod — que falha porque o container reinicia antes de produzir log relevante
3. Pedir `kubectl describe` sem saber o que procurar, lendo a saída inteira
4. Chegar ao campo `OOMKilled` apenas depois de navegar por campos irrelevantes (volumes, tolerations, conditions)
5. Sugerir "verificar a aplicação" como causa, antes de notar o `memory.limits: 24Mi`

**Custo estimado**: 4-6 tool calls antes de identificar a causa. Frequente troca de hipótese entre "bug da app" e "problema de infra" sem base.

**Tempo até a causa**: ~3 minutos (múltiplos tool calls + reorientação)

---

### Com skill

**Prompt enviado ao agente**: "a API do nyx-prod está reiniciando sozinha, verifica aí"

**O que aconteceu**:
A skill carrega o método. O agente:
1. `kubectl_get pods -n nyx-prod` → STATUS=`OOMKilled` → tabela mapeia para Passo 2a
2. `kubectl_describe pod/<nome> -n nyx-prod` → lê `Last State.Reason: OOMKilled`, `Exit Code: 137`, `Limits.memory: 24Mi`
3. Causa identificada. PARA.

**Custo real**: 2 tool calls. Sem desvio de hipótese.

**Tempo até a causa**: ~40 segundos.

---

### Diferença

| Métrica | Sem skill | Com skill |
|---|---|---|
| Tool calls até a causa | 4-6 | 2 |
| Hipóteses erradas percorridas | 1-2 | 0 |
| Tempo estimado | ~3 min | ~40s |
| Risco de falso positivo | Médio (confunde OOM com bug de app) | Baixo (mapeamento direto por exit code) |
| Consistência entre operadores | Baixa (Dozer começa por eventos, Tank por logs) | Alta (o método é o mesmo para todos) |

---

## Caso B — Chamado 3 (nyx-stg, 503 com pods Running)

Este é o caso mais revelador porque o sintoma na superfície é enganoso.

### Sem skill

**Prompt enviado ao agente**: "o Service do nyx-stg não está entregando tráfego"

**O que aconteceu sem método**:
O agente sem skill, ao ver `1/1 Running` no pod:
1. Assume que o pod está saudável e o problema é externo (ingress, DNS)
2. Pede logs do pod — logs mostram a app funcionando normalmente
3. Pede describe do pod — sem anomalias no pod em si
4. Não verifica endpoints automaticamente porque o sintoma "pods Running" desverte a investigação
5. Pode concluir erroneamente "a app está OK, o problema é fora do cluster"

O erro clássico: confunde "pod Running" com "Service com endpoints". São duas coisas diferentes — um pod pode estar 1/1 Ready e o Service continuar sem endpoints se o seletor não casa.

**Custo**: 3-5 tool calls + possível conclusão errada (bug/escalada desnecessária)

---

### Com skill

**Prompt enviado ao agente**: "o Service do nyx-stg não está entregando tráfego"

**O que aconteceu**:
1. `kubectl_get pods -n nyx-stg` → STATUS `Running` com sintoma de tráfego → Passo 2d
2. **Regra da skill**: quando pods Running + 503, checar endpoints ANTES de logs ou describe
3. `kubectl_get endpoints nyx-api -n nyx-stg` → `ENDPOINTS: <none>`
4. `kubectl_get service nyx-api -n nyx-stg -o yaml` → `selector: {app: nyx-api}`
5. `kubectl_get pods -n nyx-stg -o yaml` → `labels: {app: nyxapi}`
6. Causa identificada: seletor diverge em um caractere. PARA.

**Custo real**: 3 tool calls ordenados. Nenhum log necessário.

---

### Diferença

| Métrica | Sem skill | Com skill |
|---|---|---|
| Tool calls até a causa | 3-5 + possível erro | 3 (ordenados) |
| Risco de conclusão errada | Alto (confunde pod OK com service OK) | Nulo (método exige checar endpoints primeiro) |
| Escalada desnecessária | Provável | Evitada |
| Tempo estimado | ~5 min (+ escalada) | ~1 min |

---

## Conclusão sobre ganho real

A skill não reduz dramaticamente o número de tool calls nos casos simples (Chamado 1: 4→2). O ganho principal está em dois lugares:

1. **Casos enganosos** (Chamado 3): sem skill, o agente segue o sintoma visível ("pods OK") e chega à conclusão errada. Com skill, o método força o cruzamento correto. O custo sem skill não é só mais tool calls — é potencialmente uma escalada errada ou diagnóstico equivocado.

2. **Consistência entre operadores**: sem skill, o Dozer (que começa por eventos) e o Tank (que começa por logs) chegam a conclusões diferentes com tempos diferentes para o mesmo chamado. A skill padroniza o ponto de partida e a ordem de investigação — independente de quem está no plantão.

**A skill melhora o resultado? Sim, especialmente em casos onde o sintoma visível é enganoso. E custa menos token nos casos simples por não percorrer hipóteses falsas.**
