---
prompt_avaliado: prompt.md
versao: 1.0.0
tipo: analitica
escala: 0-2 por critério (total 0–8, corte ≥ 6)
avaliador: llm-as-judge (claude-sonnet-4-6)
---

# Rubrica — Diagnóstico de Causa-Raiz de Incidente

Rubrica analítica aplicada sobre outputs do prompt de diagnóstico de causa-raiz. A galeria de cada critério traz âncoras calibradas contra o incidente Cerebro 2026-05-13.

## Regra de decisão

**PASSA quando:**

- Nenhum critério está com nota **0** ⚠️
- A soma dos 4 critérios é **≥ 6 de 8**

Nota 0 em qualquer critério reprova o output inteiro, mesmo que a soma dos demais passe o corte (mecânica de veto).

---

## C1 — Causa-raiz correta (0–2)

Avalia se a resposta aponta a causa real do incidente, não apenas os sintomas observáveis.

| Nota | Descrição |
|------|-----------|
| 2 | Identifica o gatilho inicial pelo nome e traça a cadeia causal completa até os sintomas finais, citando evidências dos artefatos em cada elo. |
| 1 | Menciona o gatilho correto mas não fecha a cadeia, ou confunde um sintoma intermediário com o gatilho inicial. |
| 0 | Aponta apenas sintomas observáveis (latência, erros, cache caindo) sem identificar o gatilho inicial. |

**Âncora para o incidente Cerebro 2026-05-13:**
- Nota 2: identifica o job de reindexação (02:00, ainda em 41% às 10:00) como gatilho e conecta: reindexação prolongada → heap saturado → GC excessivo → circuit breaker → timeouts de busca + queda de cache.
- Nota 1: menciona a reindexação mas não conecta todos os elos, ou diz que o GC foi o gatilho.
- Nota 0: diz que "a latência subiu" ou "o circuit breaker causou a lentidão".

---

## C2 — Correlação × causa (0–2)

Avalia se a resposta distingue o que é causa do que é consequência, sem inverter a direção causal.

| Nota | Descrição |
|------|-----------|
| 2 | Classifica corretamente causas, cascata intermediária e efeitos finais. Deixa explícito que os sintomas visíveis (latência, cache hit baixo) são efeitos, não causas. |
| 1 | Distingue parcialmente causa de efeito mas mistura algum efeito na cadeia causal, ou omite um elo da cascata. |
| 0 | Trata sintomas como causas ("o cache caiu, causando lentidão") ou não apresenta encadeamento causal. |

**Âncora para o incidente Cerebro 2026-05-13:**
- Causa: reindexação prolongada acumulando heap.
- Cascata intermediária: GC pressure, thread pool cheio, throttle de indexação.
- Efeitos finais: circuit breaker, timeouts, cache_hit_pct caindo.
- Nota 0 clássica: "o cache hit caiu de 74% para 29%, o que causou a lentidão".

---

## C3 — Ação proporcional (0–2)

Avalia se as ações propostas são coerentes com o diagnóstico e referenciam os parâmetros concretos do incidente.

| Nota | Descrição |
|------|-----------|
| 2 | Propõe contenção imediata (parar/throttle/suspender o gatilho) **e** ação definitiva estrutural, ambas referenciando parâmetros concretos dos artefatos. |
| 1 | Propõe apenas contenção ou apenas estrutural, mas não as duas; ou não referencia os parâmetros concretos. |
| 0 | Ações genéricas desconexas do diagnóstico (reiniciar o cluster, aumentar réplicas sem contexto) ou ausência de ação. |

**Âncora para o incidente Cerebro 2026-05-13:**
- Parâmetros concretos disponíveis: `schedule: "0 2 * * *"`, `avg_duration_min: 90`, `jvm_heap: 8g`.
- Nota 2: "cancelar a reindexação em andamento (contenção) + reagendar para fora do pico ou aumentar jvm_heap de 8g (estrutural)".
- Nota 0: "reiniciar o Elasticsearch" ou "aumentar o número de réplicas".

---

## C4 — Honestidade epistêmica (0–2)

Avalia se a resposta reconhece explicitamente o que os artefatos disponíveis não permitem concluir com certeza.

| Nota | Descrição |
|------|-----------|
| 2 | Cita ao menos uma lacuna real e específica dos artefatos (ex.: apenas um nó observado; causa do atraso do reindex desconhecida; ausência de dados de disco/rede; outros nós podem ter comportamento diferente). |
| 1 | Reconhece incerteza de forma genérica ("pode haver outros fatores") sem especificar o que os artefatos não cobrem. |
| 0 | Apresenta o diagnóstico como certeza absoluta sem nenhuma lacuna; seção de confiança/lacunas ausente ou vazia. |

**Âncora para o incidente Cerebro 2026-05-13:**
- Lacunas reais dos artefatos: apenas `cerebro-node-3` foi observado; a causa do atraso do reindex (deveria terminar às 03:30) não é explicada nos dados; não há métricas de disco ou rede.

---

## Calibração de referência — incidente Cerebro 2026-05-13

| Critério | Nota | Justificativa |
|----------|------|---------------|
| C1 — Causa-raiz correta | 2/2 | Cadeia completa rastreável pelos 3 artefatos |
| C2 — Correlação × causa | 2/2 | Cache/latência claramente downstream nos logs |
| C3 — Ação proporcional | 2/2 | `schedule`, `avg_duration_min` e `jvm_heap` explícitos na config |
| C4 — Honestidade epistêmica | 2/2 | Nó único; causa do atraso do reindex desconhecida |
| **Total** | **8/8** | Gate em ≥ 6/8 — tolerância de calibração: ≤ 1 ponto/critério |
