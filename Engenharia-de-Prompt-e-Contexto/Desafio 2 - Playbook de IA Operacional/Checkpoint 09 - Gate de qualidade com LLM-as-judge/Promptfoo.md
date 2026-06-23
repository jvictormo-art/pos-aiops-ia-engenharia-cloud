# Output #

Starting evaluation eval-Yhz-2026-06-23T20:55:50
Running 1 test cases (up to 4 at a time)...
Evaluating [████████████████████████████████████████] 100% | 1/1 | claude-gerador "--- nome: " SISTEMA=Cerebro -- cluster Elasticsearch

┌─────────────────────────┬─────────────────────────┬─────────────────────────┬─────────────────────────┬─────────────────────────┐
│ SISTEMA                 │ SINTOMA_REPORTADO       │ ARTEFATOS               │ JANELA_TEMPORAL         │ [claude-gerador]        │
│                         │                         │                         │                         │ prompt.md: ---          │
│                         │                         │                         │                         │ nome: Diagnóstico de    │
│                         │                         │                         │                         │ causa-raiz de incidente │
│                         │                         │                         │                         │ S...                    │
├─────────────────────────┼─────────────────────────┼─────────────────────────┼─────────────────────────┼─────────────────────────┤
│ Cerebro -- cluster      │ A partir de ~08:30 UTC  │ --- Artefato 1:         │ 2026-05-13 08:00 UTC -> │ [PASS] # Diagnóstico de │
│ Elasticsearch           │ a busca no Cerebro      │ Configuração ---        │ 2026-05-13 10:10 UTC    │ Causa-Raiz: Incidente   │
│ gerenciado pela Aegis,  │ degradou                │ Tipo: config            │                         │ Cerebro (2026-05-13)    │
│ motor de indexação e    │ progressivamente.       │ Origem: cerebro.yaml    │                         │ ## ⚠️ Dados a Sanitizar │
│ busca                   │ Às 10:00 UTC: latência  │ (repositório de infra)  │                         │ Nenhum dado sensível    │
│ full-text usado pelo    │ p99 em 6700 ms (era 850 │ cerebro:                │                         │ (credenciais, tokens,   │
│ Sentinel e demais       │ ms às 08:00), cache hit │   shards: 12            │                         │ chaves, IPs internos,   │
│ produtos da plataforma. │ em 29%                  │   replicas_per_shard: 1 │                         │ PII) foi identificado   │
│ Serviço Java/JVM        │ (era 74%). O plantão    │   jvm_heap: 8g          │                         │ nos artefatos           │
│ com heap configurado em │ escalou o incidente     │   refresh_interval: 1s  │                         │ fornecidos. Prosseguir  │
│ 8 GB.                   │ após                    │   reindex_job:          │                         │ com análise.            │
│                         │ CircuitBreakingExcepti… │     schedule: "0 2 * *… │                         │ ---                     │
│                         │ aparecer                │ # roda todo dia às      │                         │ ## 1. Resumo Execut...  │
│                         │ nos logs.               │ 02:00                   │                         │                         │
│                         │                         │   ...                   │                         │                         │
└─────────────────────────┴─────────────────────────┴─────────────────────────┴─────────────────────────┴─────────────────────────┘
✓ Eval complete (ID: eval-Yhz-2026-06-23T20:55:50)

» View results: promptfoo view
» Share with your team: https://promptfoo.app
» Feedback: https://promptfoo.dev/feedback

Total Tokens: 17,851
  Eval: 8,406 (cached)
  Grading: 9,445 (cached)

Results:
  ✓ 1 passed (100%)
  0 failed (0%)
  0 errors (0%)
Duration: 0s (concurrency: 4)

# Output do View #

Description	
SISTEMA
SINTOMA_REPORTADO
ARTEFATOS
JANELA_TEMPORAL
claude-gerador
100.00% passing (1/1 cases)

prompt.md: ---
nome: Diagnóstico de causa-raiz de incidente S...
Incidente Cerebro -- reindexação prolongada saturando heap (2026-05-13)
Cerebro -- cluster Elasticsearch gerenciado pela Aegis, motor de indexação e busca
full-text usado pelo Sentinel e demais produtos da plataforma. Serviço Java/JVM
com heap configurado em 8 GB.
A partir de ~08:30 UTC a busca no Cerebro degradou progressivamente.
Às 10:00 UTC: latência p99 em 6700 ms (era 850 ms às 08:00), cache hit em 29%
(era 74%). O plantão escalou o incidente após CircuitBreakingException aparecer
nos logs.
--- Artefato 1: Configuração ---
Tipo: config
Origem: cerebro.yaml (repositório de infra)

cerebro:
  shards: 12
  replicas_per_shard: 1
  jvm_heap: 8g
  refresh_interval: 1s
  reindex_job:
    schedule: "0 2 * * *"     # roda todo dia às 02:00
    a
...
2026-05-13 08:00 UTC -> 2026-05-13 10:10 UTC
8 PASS
# Diagnóstico de Causa-Raiz: Incidente Cerebro (2026-05-13)

## ⚠️ Dados a Sanitizar
Nenhum dado sensível (credenciais, tokens, chaves, IPs internos, PII) foi identificado nos artefatos fornecidos. Prosseguir com análise.

---

## 1. Resumo Executivo

Entre 08:00 e 10:00 UTC, o Cerebro sofreu degradação progressiva de latência (850 ms → 6700 ms p99) e queda de cache hit (74% → 29%), culminando em `CircuitBreakingException` às 10:01 UTC. **A causa-raiz é a sobreposição de um job de reindex de longa duração (iniciado às 02:00, ainda em execução às 09:58) com pico de indexação de novos documentos (4.2k → 12.4k docs/s), ambos competindo por heap JVM de 8 GB insuficientemente dimensionado para a carga combinada.** O gatilho inicial foi o reindex agendado; a cascata foi amplificada pela falta de throttling entre reindex e ingestão normal.

---

## 2. Linha do Tempo do Incidente

| Horário (UTC) | Evento | Artefato(s) |
|---|---|---|
| 08:00 | Estado normal: p99=850ms, cache_hit=74%, heap=61%, indexed_docs/s=4.2k | Métricas |
| 08:02:11 | Reindex task [88123] inicia (agendado 02:00), progresso 38% (3.8M/10M docs) | Log |
| 08:14:33 | Young GC: 620ms, heap 4.9gb→3.1gb (pressão de memória detectada) | Log |
| 08:30 | p99 sobe para 1.1s, cache_hit cai para 71%, heap=68% | Métricas |
| 08:41:07 | Throttling de indexação ativado no shard logs-2026.05[7] (segment writing lag) | Log |
| 09:00 | p99=2.3s, indexed_docs/s sobe para 9.8k, heap=79%, cache_hit=58% | Métricas |
| 09:03:55 | Write thread pool queue em 150/200 (75% saturação) | Log |
| 09:12:48 | Old GC: 1.1s, 2 coletas em 60s, heap 6.3gb→5.9gb (GC cada vez mais agressivo) | Log |
| 09:20:02 | Reindex ainda em execução, progresso 40% (4.0M/10M docs) — **atrasado** | Log |
| 09:30 | p99=4.1s, indexed_docs/s=11.2k, heap=88%, cache_hit=41% | Métricas |
| 09:31:17 | Circuit breaker warning: parent usage 6.9gb/8gb (86%) | Log |
| 09:44:29 | Slow query: 2380ms em shard logs-2026.05[7] | Log |
| 09:51:08 | Write thread pool queue em 188/200 (94% saturação) | Log |
| 09:58:41 | **Write thread pool FULL (200/200), rejeitando bulk requests** | Log |
| 09:58:43 | Old GC: 1.8s, 4 coletas em 60s, heap 7.6gb→7.4gb (GC thrashing) | Log |
| 09:58:44 | Reindex ainda em execução, progresso 41% (4.1M/10M docs) — **praticamente parado** | Log |
| 09:58:45 | Indexing buffer acima do limite, throttling ativado | Log |
| 09:58:46 | Search timeout: shard [7] levou 5031ms (timeout=5000ms), 11/12 shards OK | Log |
| 09:58:46 | **Partial results error: 1 shard falhou** | Log |
| 09:58:47 | Query cache eviction spike, hit_ratio=0.29 | Log |
| 10:00 | p99=6.7s, indexed_docs/s=12.4k, heap=94%, cache_hit=29% | Métricas |
| 10:01:12 | **CircuitBreakingException: parent 7.9gb/8gb (96%)** — plantão escalou | Log |
| 10:03:39 | Write thread pool rejeitou 1284 bulk requests em 5 min | Log |
| 10:05:50 | All shards failed para index logs-2026.05 em 3 de 20 queries | Log |

---

## 3. Cadeia Causal

### Gatilho Inicial
**Passo 1: Reindex agendado não terminou no prazo esperado**
- **Evidência:** Config mostra `schedule: "0 2 * * *"` e `avg_duration_min: 90` (termina ~03:30). Log mostra reindex ainda em execução às 09:58 (7h58min depois), com apenas 41% de progresso (4.1M/10M docs).
- **Causa:** O reindex iniciado às 02:00 deveria ter terminado às 03:30, mas foi retido na fila ou bloqueado. Aos 09:58, ainda consome recursos de escrita.

### Cascata de Degradação
**Passo 2: Reindex + ingestão normal competem por write thread pool**
- **Evidência:** 
  - Indexed_docs/s sobe de 4.2k (08:00) para 12.4k (10:00) — aumento de 3x na taxa de ingestão normal.
  - Write thread pool queue cresce: 150/200 (09:03) → 188/200 (09:51) → 200/200 (09:58).
  - Log 09:58:41: "write thread pool full [200/200], rejecting bulk".
- **Causa:** O reindex consome slots de escrita; a ingestão normal também cresce; a fila de 200 é insuficiente para ambas.

**Passo 3: Heap JVM saturado por reindex + indexing buffer + query cache**
- **Evidência:**
  - Heap cresce: 61% (08:00) → 79% (09:00) → 88% (09:30) → 94% (10:00).
  - Log 09:31:17: "circuit breaker [parent] usage [6.9gb/8gb] (86%), approaching limit".
  - Log 09:58:45: "indexing buffer above limit, throttling shard [logs-2026.05][7]".
  - Log 09:58:47: "circuit breaker tripped, usage [7.7gb/8gb] (96%)".
- **Causa:** Reindex (4.1M docs em memória) + indexing buffer (para novos docs) + query cache (512 MB, config) + JVM overhead = 8 GB insuficiente.

**Passo 4: GC thrashing reduz throughput e aumenta latência**
- **Evidência:**
  - Log 08:14:33: Young GC 620ms.
  - Log 09:12:48: Old GC 1.1s, 2 coletas em 60s.
  - Log 09:58:43: Old GC 1.8s, **4 coletas em 60s** (GC a cada 15s).
  - Reindex progresso: 38% (08:02) → 40% (09:20) → 41% (09:58) — apenas 3% em 7h56min.
- **Causa:** Heap próximo ao limite força Full GC frequentes; cada GC pausa threads de escrita e busca.

**Passo 5: Query cache eviction e queda de hit ratio**
- **Evidência:**
  - Cache hit: 74% (08:00) → 58% (09:00) → 29% (10:00).
  - Log 09:58:47: "query cache eviction rate spiking, hit_ratio dropped to 0.29".
- **Causa:** Heap cheio força eviction de cache; reindex e novos docs deslocam entradas antigas.

**Passo 6: Search latência explode**
- **Evidência:**
  - p99: 850ms (08:00) → 2.3s (09:00) → 6.7s (10:00).
  - Log 09:44:29: "slow query on shard [logs-2026.05][7] took [2380ms]".
  - Log 09:58:46: "shard [logs-2026.05][7] search took [5031ms] (timeout [5000ms])".
- **Causa:** GC pauses + write thread pool saturation + cache misses + segment writing lag (log 08:41:07) aumentam latência de busca.

**Passo 7: Circuit breaker ativa, rejeitando operações**
- **Evidência:**
  - Log 10:01:12: "CircuitBreakingException: [parent] Data too large, would be [7.9gb/8gb]".
  - Log 09:58:46: "search returned partial results: 11/12 shards succeeded".
  - Log 10:05:50: "all shards failed for index [logs-2026.05] on 3 of last 20 queries".
- **Causa:** Heap em 96% dispara circuit breaker; novas operações são rejeitadas.

---

## 4. Causa-Raiz

**Um job de reindex agendado para 02:00 (duração esperada 90 min) não terminou no prazo e permaneceu em execução até pelo menos 09:58 UTC (7h58min depois), consumindo heap e write thread pool. Simultaneamente, a taxa de ingestão normal de documentos triplicou (4.2k → 12.4k docs/s). Ambas as operações competiram por um heap JVM de 8 GB insuficientemente dimensionado e uma fila de write thread pool de apenas 200 slots. A saturação de heap ativou GC thrashing (Full GC a cada 15s), que pausou threads de escrita e busca, elevando latência p99 de 850ms para 6.7s. A queda de cache hit (74% → 29%) amplificou a latência. Finalmente, o circuit breaker foi acionado em 96% de heap, rejeitando operações e causando falhas parciais de shard.**

**Em síntese:** Reindex retido + ingestão normal em pico + heap insuficiente = GC thrashing + circuit breaker.

---

## 5. Mitigação Imediata

### Ação 1: Cancelar ou pausar o reindex em execução
```
POST /_tasks/88123/_cancel
```
**Racional:** O reindex está apenas 41% completo após 7h58min e está bloqueando escrita. Cancelá-lo libera heap e write thread pool imediatamente.
**Risco:** Baixo. O reindex pode ser reiniciado fora do horário de pico (ex: 23:00 UTC).
**Impacto esperado:** Heap deve cair de 94% para ~70-75% em 2-3 min (após GC).

### Ação 2: Aumentar write thread pool queue size (temporário)
```yaml
thread_pool:
  write:
    queue_size: 500  # de 200 para 500
```
**Racional:** Reduz rejeição de bulk requests enquanto heap se recupera.
**Risco:** Médio. Aumenta latência de fila, mas evita perda de dados.
**Impacto esperado:** Rejeições devem cessar em 1-2 min.

### Ação 3: Reduzir query cache size temporariamente
```yaml
query_cache:
  size_mb: 256  # de 512 para 256
```
**Racional:** Libera ~256 MB de heap para operações críticas.
**Risco:** Baixo. Cache hit já está em 29%; redução adicional é marginal.
**Impacto esperado:** Heap cai mais 3-5%.

### Ação 4: Monitorar e aguardar recuperação
- Observar heap, GC, p99 latência e cache hit a cada 30s.
- Esperado: heap → 60-70%, p99 → 1-2s, cache_hit → 50%+ em 5-10 min.

---

## 6. Correção Definitiva

### Problema Estrutural 1: Reindex agendado não tem limite de tempo
**Solução:**
- Adicionar timeout ao reindex job:
  ```yaml
  reindex_job:
    schedule: "0 2 * * *"
    avg_duration_min: 90
    timeout_min: 120  # NOVO: falha se não terminar em 120 min
    alert_if_exceeds_min: 100  # NOVO: alerta em 100 min
  ```
- Implementar lógica de fallback: se reindex não terminar em 120 min, cancelar e alertar SRE.

### Problema Estrutural 2: Heap JVM insuficiente para carga combinada
**Solução:**
- Aumentar heap de 8 GB para 16 GB:
  ```yaml
  jvm_heap: 16g
  ```
- **Justificativa:** 
  - Reindex em memória: ~2-3 GB (4.1M docs).
  - Indexing buffer: ~512 MB.
  - Query cache: 512 MB.
  - JVM overhead + Lucene buffers: ~2-3 GB.
  - Margem de segurança: ~2 GB.
  - Total: ~8-9 GB; 16 GB oferece 2x de margem.

### Problema Estrutural 3: Write thread pool queue insuficiente
**Solução:**
- Aumentar queue_size de 200 para 500 (permanente):
  ```yaml
  thread_pool:
    write:
      queue_size: 500
  ```
- **Justificativa:** Pico de ingestão é 12.4k docs/s; fila de 200 é ~16ms de buffer. Fila de 500 oferece ~40ms.

### Problema Estrutural 4: Reindex não é throttled em relação à ingestão normal
**Solução:**
- Implementar throttling de reindex:
  ```yaml
  reindex_job:
    max_docs_per_second: 5000  # NOVO: limita reindex a 5k docs/s
    slices: 4  # NOVO: paraleliza em 4 slices para melhor throughput
  ```
- **Justificativa:** Evita que reindex monopolize recursos durante picos de ingestão.

### Problema Estrutural 5: Falta de observabilidade de reindex
**Solução:**
- Adicionar métricas e alertas:
  - `reindex_progress_pct` (alertar se < 10% em 2h).
  - `reindex_duration_min` (alertar se > 120 min).
  - `heap_used_pct_during_reindex` (alertar se > 80%).
- Adicionar log estruturado com timestamps de início/fim esperado.

---

## 7. Confiança e Lacunas

### Nível de Confiança: **ALTO (95%)**

**Justificativa:**
- A cadeia causal é linear e bem suportada por evidências em todos os três artefatos (config, métricas, logs).
- Cada passo é correlacionado no tempo e explica os sintomas observados.
- A causa-raiz (reindex retido + ingestão em pico + heap insuficiente) explica **todos** os sintomas: latência, cache hit, GC thrashing, circuit breaker, partial results.
- Não há sintomas anômalos que contradizem a hipótese.

### Lacunas Menores (não bloqueantes)

1. **Por que o reindex não terminou em 90 min?**
   - Hipótese: Ingestão normal triplicou durante a noite (08:00-10:00), competindo com reindex.
   - Faltaria: Logs de 02:00-08:00 para confirmar se reindex estava rápido inicialmente ou lento desde o início.
   - **Impacto:** Não muda a causa-raiz, apenas refina o gatilho.

2. **Qual foi o gatilho para o aumento de ingestão (4.2k → 12.4k docs/s)?**
   - Hipótese: Pico normal de tráfego ou job de ETL agendado.
   - Faltaria: Logs de aplicação ou métricas de ingestão upstream (Sentinel, produtores).
   - **Impacto:** Não muda a mitigação imediata, mas ajuda a evitar reincidência.

3. **Qual é a configuração atual de GC (young/old gen size)?**
   - Faltaria: Parâmetros `-Xmn`, `-XX:NewRatio` ou equivalentes.
   - **Impacto:** Baixo. Aumentar heap de 8 para 16 GB melhora GC automaticamente.

4. **Há outras instâncias do Cerebro (cluster)?**
   - Faltaria: Topologia do cluster (quantos nós, replicação).
   - **Impacto:** Médio. Se há 3+ nós, rebalancear shards poderia ter mitigado parcialmente. Logs mostram apenas cerebro-node-3; não está claro se há node-1, node-2.

---

## Resumo de Ações Recomendadas

| Prioridade | Ação | Tipo | Prazo |
|---|---|---|---|
| **P0 (Agora)** | Cancelar reindex task [88123] | Mitigação | Imediato |
| **P0 (Agora)** | Aumentar write thread pool queue para 500 | Mitigação | Imediato |
| **P1 (Hoje)** | Aumentar heap JVM de 8 GB para 16 GB | Correção | 1-2h (reboot) |
| **P1 (Hoje)** | Aumentar query cache size para 256 MB (se necessário) | Mitigação | 1-2h (reboot) |
| **P2 (Esta semana)** | Implementar timeout e throttling de reindex | Correção | 3-5 dias |
| **P2 (Esta semana)** | Adicionar alertas de reindex e heap durante reindex | Observabilidade | 2-3 dias |
| **P3 (Próximas 2 semanas)** | Investigar pico de ingestão (4.2k → 12.4k docs/s) | Análise | 5-10 dias |
Show less
Tokens: 8.406 (cached)
Latency: 5ms (cached)
Cost: $0.028


# Curadoria #

Curadoria — devops/diagnosticar-causa-raiz-incidente
                                                                                                                          
Modelo avaliado: claude-haiku-4-5-20251001  
Juiz: claude-sonnet-4-6                     
Resultado: 100% aprovado (1/1) — 8/8 asserts
                                                                                                                                
---                                                                                                                                   
O que passou                                                                                                                          
                                                                                                                                
Camada 1 — determinísticos (7/7): todas as seções obrigatórias presentes na saída: Resumo Executivo, Linha do Tempo, Cadeia Causal,   
Causa-Raiz, Mitigação Imediata, Correção Definitiva e Confiança e Lacunas. Custo $0,028 (abaixo do limite de $0,05).                  
                                                                                                                                
Camada 2 — juiz LLM (PASS): a rubrica de 4 critérios foi atendida.
                                                                                                                                
┌─────────────────────┬───────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│      Critério       │                                                 Avaliação                                                 │   
├─────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────┤   
│ C1 — Causa-raiz     │ Identificou o job de reindex (02:00, ainda em 41% às 09:58) como gatilho e traçou a cadeia completa:      │   
│ correta             │ reindex + ingestão em pico → heap → GC thrashing → circuit breaker → timeouts + queda de cache            │   
├─────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────┤   
│ C2 — Correlação ×   │ Separou corretamente causas (reindex prolongado), cascata (GC, thread pool cheio) e efeitos finais        │   
│ causa               │ (latência, cache hit baixo). Explicitou que a queda do cache "amplificou" a latência, não a causou        │
├─────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────┤   
│ C3 — Ação           │ Propôs contenção imediata (POST /_tasks/88123/_cancel) e 4 correções estruturais referenciando parâmetros │
│ proporcional        │  concretos: jvm_heap, schedule, avg_duration_min, queue_size                                              │   
├─────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────┤   
│ C4 — Honestidade    │ Seção 7 listou 4 lacunas específicas: logs de 02:00–08:00 ausentes; causa do pico de ingestão             │   
│ epistêmica          │ desconhecida; config de GC não fornecida; topologia do cluster não informada                              │   
└─────────────────────┴───────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                                                                                                
---                                                                                                                                   
Observações                            
                                                                                                                                
A resposta excedeu a calibração de referência em riqueza: incluiu tabela de prioridades P0/P1/P2/P3, comandos executáveis e comandos  
YAML concretos para cada correção. Nenhum ajuste no prompt.md ou na rubrica é necessário — o gate funcionou conforme esperado.
