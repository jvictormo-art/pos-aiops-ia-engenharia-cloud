# PROMPT PARAMETRIZÁVEL #

# Cadeia de Prompts — Migração do Forge (Batch → Event-Driven)

> **Como usar:** Execute os elos em ordem. A saída de cada elo é colada como parâmetro de entrada do próximo. Todos os prompts são parametrizáveis: troque apenas os blocos `<...>` pela entrada real (chat, playground ou API). Não edite a estrutura.

---

## ELO 1 — Diagnóstico do Estado Atual


Você é um arquiteto de dados sênior especializado em pipelines de streaming e migrações de sistemas legados de alto volume. Sua tarefa é diagnosticar o estado atual de um pipeline em lote antes de qualquer plano de migração, expondo riscos, acoplamentos e restrições ocultas.

## Entrada
<SNAPSHOT_FORGE>: descrição do pipeline atual (ingestão, etapas de transformação, destino, pontos frágeis, dependentes a jusante).
<SLAS_E_DEPENDENTES>: SLAs, janelas críticas e quem consome a saída do pipeline.

## O Que Produzir
1. **Mapa de acoplamentos**: para cada dependente, identifique COMO ele consome a saída (formato, frequência, granularidade) e o que quebra se isso mudar.
2. **Inventário de etapas**: liste as etapas de transformação, classificando cada uma como (a) trivialmente convertível para streaming, (b) exige reescrita stateful, (c) inerentemente batch (precisa de janela/agregação completa).
3. **Riscos do modelo atual**: enumere os pontos frágeis e o efeito cascata de cada falha.
4. **Restrições invioláveis**: o que NÃO pode mudar durante a migração (contratos de schema, particionamento, janelas de billing, etc).
5. **Lacunas de informação**: dados ausentes no snapshot que serão necessários para planejar a migração.

## Regras
- Não proponha solução ou plano de migração nesta etapa. Apenas diagnostique.
- Para cada afirmação, ancore no que está no snapshot; marque inferências como "[inferência]".
- Seja específico: "etapa 7 agrega por hora, incompatível com micro-batch < 1h sem janela deslizante" > "algumas etapas são batch".

## Formato de Saída
Markdown com as 5 seções acima. Cada item em bullet de no máximo 2 linhas. Termine com um bloco `### Handoff` resumindo, em até 6 bullets, os fatos que o próximo elo (planejamento) precisa carregar adiante.


---

## ELO 2 — Estratégia de Migração Faseada


Você é um arquiteto de migração especializado em transições incrementais e reversíveis de sistemas em produção, sem janelas de big-bang. Sua tarefa é converter um diagnóstico de pipeline batch em uma estratégia de migração por fases para um modelo event-driven.

## Entrada
<DIAGNOSTICO_FORGE>: saída completa do elo de diagnóstico (mapa de acoplamentos, inventário de etapas, riscos, restrições, handoff).
<OBJETIVO_ALVO>: o modelo desejado (consumo contínuo do barramento de eventos, processamento em pequenos blocos, dependentes preservados, migração reversível passo a passo).

## Processo de Raciocínio (faça antes de escrever a saída)
1. Defina a ordem de migração das etapas com base na classificação do diagnóstico (comece pelas trivialmente convertíveis; isole as inerentemente batch).
2. Para cada fase, decida o padrão de coexistência batch+streaming (ex: dual-write, shadow run, leitura espelhada) que mantém os dependentes intactos.
3. Garanta que cada fase seja independentemente reversível: defina o gatilho de rollback e o estado de retorno.

## O Que Produzir
- **Sequência de fases**: lista ordenada de fases. Para cada fase: objetivo, etapas do pipeline envolvidas, o que passa a rodar em streaming, o que permanece em batch, e como os dependentes continuam servidos.
- **Estratégia de coexistência**: como batch e streaming convivem durante cada fase sem divergência de dados.
- **Critério de avanço**: a condição mensurável que autoriza passar para a próxima fase.
- **Gatilho e plano de rollback por fase**: o que observar, quando reverter, para qual estado.
- **Riscos residuais**: o que cada fase não resolve e fica para depois.

## Regras
- Proibido propor virada única (big-bang). Toda fase entrega valor isolado e é reversível.
- Nenhum dependente pode ficar sem dados durante a transição; explicite como cada um é preservado em cada fase.
- Respeite todas as restrições invioláveis listadas no diagnóstico.
- Não detalhe ainda comandos, jobs ou configs executáveis — isso é o próximo elo. Aqui é a estratégia.

## Formato de Saída
Markdown com as seções acima. Numere as fases. Termine com `### Handoff` listando, por fase, os 3-5 pontos que o elo de detalhamento executável precisa transformar em passos concretos.


---

## ELO 3 — Plano Executável e Reversível por Fase


Você é um SRE/engenheiro de plataforma sênior que escreve runbooks de migração executáveis, testáveis e reversíveis para sistemas em produção. Sua tarefa é detalhar UMA fase da estratégia de migração em um plano de execução passo a passo.

## Entrada
<ESTRATEGIA_FASEADA>: saída do elo de estratégia (todas as fases, coexistência, rollback).
<FASE_ALVO>: identificador da fase a ser detalhada nesta execução (ex: "Fase 2").
<CONTEXTO_OPERACIONAL>: ferramentas, plataformas e convenções do ambiente (orquestrador, engine de processamento, data warehouse, barramento de eventos) — cole o que for conhecido; marque o desconhecido.

## O Que Produzir
1. **Pré-condições**: estado que deve ser verdadeiro antes de iniciar (checagens, backups, flags).
2. **Passos de execução**: sequência numerada e granular. Cada passo com: ação, como validar que deu certo, e tempo/risco estimado. Onde envolver código/config, forneça o trecho concreto; onde faltar contexto, marque `<<preencher: ...>>` indicando exatamente o que falta.
3. **Validação de integridade de dados**: como provar que streaming e batch produzem o mesmo resultado nesta fase (reconciliação, comparação de amostras, métricas de divergência).
4. **Procedimento de rollback**: passos numerados para reverter ESTA fase ao estado anterior, com o ponto-de-não-retorno claramente sinalizado (se houver).
5. **Critério de saída**: a condição objetiva e mensurável que declara a fase concluída e segura.
6. **Monitoramento durante a janela**: o que observar em tempo real e os limiares que disparam abortar/reverter.

## Regras
- Cada passo deve ser reversível ou ter o ponto-de-não-retorno explícito; nunca deixe ambíguo.
- Não pule a validação de integridade: uma fase sem prova de equivalência de dados é inválida.
- Não invente nomes de recursos, comandos ou caminhos não fornecidos; use `<<preencher: ...>>`.
- Não detalhe outras fases — apenas a `<FASE_ALVO>`.

## Formato de Saída
Runbook em markdown com as 6 seções numeradas. Passos como lista ordenada. Use blocos de código para trechos executáveis. Termine com `### Checklist de Ida/Volta`: duas colunas — "para avançar" e "para reverter" — em bullets verificáveis.



# EXECUÇÃO #

### Modelo Utilizado ###
Cloud Sonnet 4.6 para execução e Opus 4.8 para geração do prompt.

### Output Real ###

## ELO 1 — Diagnóstico do Estado Atual

**`<SNAPSHOT_FORGE>`:**
- Ingestão: job cron a cada 60min (`forge-batch-ingest`)
- Transformação: 14 etapas encadeadas em Spark, ~40min no total
- Destino: tabelas no data warehouse, particionadas por hora
- Ponto frágil: falha de lote acumula volume dobrado no próximo ciclo
- Dependentes: Sentinel (lê tabelas agregadas), Cerebro (indexa eventos transformados), relatórios de billing da Pepper (rodam de madrugada)

**`<SLAS_E_DEPENDENTES>`:**
- Sentinel: leitura contínua das tabelas agregadas, sensível a gaps de dados
- Cerebro: indexação dos eventos transformados, depende da consistência do schema
- Billing (Pepper): janela crítica noturna, tolerância zero a dados faltantes ou duplicados

---

### 1. Mapa de Acoplamentos

- **Sentinel**: consome tabelas agregadas por hora; qualquer mudança de granularidade ou particionamento quebra suas queries e alertas.
- **Cerebro**: indexa eventos transformados conforme schema atual; mudança de schema ou timing de gravação exige reindexação ou adaptação do consumer.
- **Billing (Pepper)**: job noturno lê partições horárias fechadas; depende de completude garantida antes da janela — partial writes ou partições abertas corrompem os relatórios.

### 2. Inventário de Etapas

- **Trivialmente convertíveis para streaming** (sem estado entre eventos): etapas de parsing, validação de schema, enriquecimento por lookup estático — estimado ~4–5 etapas. [inferência]
- **Exigem reescrita stateful** (janela deslizante, dedup, joins temporais): etapas de deduplicação, joins entre streams de telemetry, agregações com janela de tempo — estimado ~6–7 etapas. [inferência]
- **Inerentemente batch** (dependem do lote fechado para agregar): etapas de agregação horária que alimentam as partições do data warehouse e o billing — estimado ~2–3 etapas. [inferência]

> ⚠️ O snapshot não nomeia as 14 etapas individualmente. A classificação acima é inferência estrutural. **Lacuna crítica** — ver seção 5.

### 3. Riscos do Modelo Atual

- **Efeito cascata de falha**: um lote falho dobra o volume do ciclo seguinte, podendo causar timeout em cascata e latência crescente em todos os dependentes.
- **Janela cega de 60min**: dados chegam no Relay mas só ficam disponíveis para Sentinel e Cerebro após até 1h + 40min de processamento — gap de ~100min no pior caso.
- **Acoplamento temporal rígido**: o cron é o único mecanismo de disparo; não há backpressure nem retry granular por evento.
- **Particionamento horário como contrato implícito**: todos os dependentes assumem partições fechadas por hora; não está documentado como contrato formal.

### 4. Restrições Invioláveis

- Particionamento horário das tabelas do data warehouse não pode mudar enquanto Sentinel e Billing dependerem dele.
- Schema dos eventos transformados entregues ao Cerebro deve ser preservado (ou versionado com retrocompatibilidade).
- Janela de billing noturna exige dados 100% completos e sem duplicatas antes de rodar.
- Nenhuma fase pode deixar Sentinel sem dados por mais do que o SLA de alerting atual (valor exato **não fornecido no snapshot** — lacuna).

### 5. Lacunas de Informação

- Nomes e lógica das 14 etapas Spark: imprescindível para classificar corretamente convertíveis vs. batch.
- SLA explícito do Sentinel: sem ele, não é possível definir o tempo máximo de indisponibilidade tolerável.
- Mecanismo atual de retry/reprocessamento de lotes falhos.
- Volume médio e pico de eventos por hora no Relay: determina o dimensionamento do consumer streaming.
- Tecnologia do data warehouse (Redshift, BigQuery, Snowflake, etc.): condiciona a estratégia de escrita incremental.

### Handoff

- Três etapas são inerentemente batch (agregação horária para DW e billing) e **não podem ser simplesmente convertidas** — a migração precisa preservar ou emular essa semântica.
- Sentinel e Billing têm acoplamento de schema e particionamento; qualquer fase precisa manter esses contratos.
- A janela cega de ~100min é o principal motivador de negócio para a migração — a estratégia deve reduzi-la progressivamente.
- A falha em cascata de lotes é o principal risco operacional atual — o modelo event-driven resolve isso apenas se introduzir retry por evento desde o início.
- As lacunas (nomes das etapas, SLA do Sentinel, volume de eventos) precisam ser preenchidas antes de comprometer datas de fase.

---

## ELO 2 — Estratégia de Migração Faseada

**`<DIAGNOSTICO_FORGE>`:** saída completa do Elo 1 acima.

**`<OBJETIVO_ALVO>`:** consumo contínuo do Relay, processamento em micro-batches, dependentes preservados, migração reversível fase a fase.

---

### Sequência de Fases

**Fase 1 — Shadow Consumer (sem impacto em produção)**
- **Objetivo**: provar que é possível consumir o Relay continuamente sem afetar o batch atual.
- **Etapas envolvidas**: nenhuma etapa de transformação ainda — apenas ingestão.
- **O que vai para streaming**: um consumer paralelo lê o Relay e grava os eventos raw em uma tabela de staging separada.
- **O que permanece em batch**: tudo — o `forge-batch-ingest` continua rodando normalmente.
- **Dependentes**: intocados, consomem exatamente como hoje.

**Fase 2 — Streaming das etapas trivialmente convertíveis**
- **Objetivo**: mover as ~4–5 etapas stateless (parsing, validação, enriquecimento) para o pipeline de streaming.
- **O que vai para streaming**: etapas trivialmente convertíveis, rodando sobre o consumer do Relay.
- **O que permanece em batch**: etapas stateful, agregações horárias, escrita no DW e entrega ao Cerebro.
- **Coexistência**: o batch continua como fonte de verdade para os dependentes; o resultado streaming vai para staging (dual-write) para validação de equivalência.

**Fase 3 — Streaming das etapas stateful (janela deslizante)**
- **Objetivo**: migrar deduplicação, joins e agregações com janela para o modelo de streaming com janela deslizante.
- **O que vai para streaming**: etapas stateful reescritas para micro-batch com janela deslizante de X min. [inferência — tamanho da janela depende do SLA do Sentinel, lacuna do Elo 1]
- **O que permanece em batch**: agregação horária fechada para billing e partições do DW.
- **Coexistência**: shadow run com comparação de resultados entre batch e streaming por 1+ ciclos completos antes de promover.

**Fase 4 — Cutover dos dependentes primários (Sentinel e Cerebro)**
- **Objetivo**: Sentinel e Cerebro passam a consumir da saída do pipeline streaming, não mais do batch.
- **O que vai para streaming**: escrita no DW e entrega ao Cerebro via pipeline streaming.
- **O que permanece em batch**: apenas a agregação horária fechada para billing.
- **Coexistência**: batch ainda roda em paralelo por N ciclos como fallback; Sentinel tem flag de feature toggle para reverter à leitura batch.

**Fase 5 — Migração do billing e descomissionamento do batch**
- **Objetivo**: adaptar o job de billing para consumir partições geradas pelo streaming e desligar o `forge-batch-ingest`.
- **O que vai para streaming**: escrita das partições horárias a partir do streaming (janela fechada por watermark).
- **O que permanece em batch**: nada — esta é a fase final.
- **Coexistência**: billing roda em paralelo contra as duas fontes (batch e streaming) por pelo menos 2 ciclos noturnos antes do descomissionamento.

---

### Estratégia de Coexistência

- **Fases 1–2**: dual-write. O batch é a fonte de verdade; o streaming escreve em staging para validação.
- **Fase 3**: shadow run. O streaming processa em paralelo, os resultados são comparados mas não servidos.
- **Fase 4**: feature toggle por dependente. Cada dependente tem um flag para escolher a fonte (streaming ou batch), permitindo rollback granular.
- **Fase 5**: parallel run do billing com reconciliação manual antes do corte final.

---

### Critério de Avanço por Fase

| Fase | Condição de avanço |
|---|---|
| 1 | Consumer rodando por 72h sem lag acumulado, zero perda de eventos |
| 2 | Divergência entre staging e batch < 0,1% por 3 ciclos consecutivos |
| 3 | Resultados stateful equivalentes ao batch por 5 ciclos; latência p99 dentro do SLA |
| 4 | Sentinel e Cerebro servidos por streaming por 48h sem alertas de gap ou inconsistência |
| 5 | Billing reconciliado contra batch por 2 noites consecutivas; diferença = 0 |

---

### Gatilho e Plano de Rollback por Fase

- **Fase 1**: rollback = desligar o consumer paralelo. Sem impacto. Ponto-de-não-retorno: inexistente.
- **Fase 2**: rollback = parar o pipeline streaming de staging. Batch continua intocado.
- **Fase 3**: rollback = descartar resultados de staging e retornar ao batch como único pipeline. Janela de ~1 ciclo de latência.
- **Fase 4**: rollback = feature toggle de volta ao batch para cada dependente individualmente. Ponto-de-não-retorno: remoção do batch — não executar antes de 72h de estabilidade.
- **Fase 5**: rollback = reativar `forge-batch-ingest` a partir do último snapshot. Ponto-de-não-retorno: destruição das tabelas batch — exige backup prévio obrigatório.

---

### Riscos Residuais por Fase

- Fase 1: nenhum risco para produção; risco de falsa confiança se o volume de teste for menor que pico real.
- Fase 2: etapas mal classificadas como triviais podem ter estado oculto — só evidenciado na comparação.
- Fase 3: tamanho da janela deslizante não definido sem o SLA do Sentinel; escolha errada causa falsos alertas ou dados defasados.
- Fase 4: feature toggle mal implementado pode criar leituras mistas (parte batch, parte streaming) e inconsistências difíceis de debugar.
- Fase 5: o billing tem tolerância zero a erro — qualquer divergência exige investigação antes do corte.

---

### Handoff

- **Fase 1**: detalhar o consumer do Relay (tecnologia, configuração de consumer group, política de retry e dead-letter).
- **Fase 2**: mapear exatamente quais das 14 etapas são trivialmente convertíveis e o schema de saída para staging.
- **Fase 3**: definir o tamanho da janela deslizante (depende do SLA do Sentinel — preencher lacuna) e a estratégia de watermark para eventos atrasados.
- **Fase 4**: especificar o mecanismo de feature toggle (config centralizada, env var, feature flag service) e o processo de promoção por dependente.
- **Fase 5**: definir o procedimento de backup das tabelas batch antes do descomissionamento e o script de reconciliação do billing.

---

## ELO 3 — Plano Executável e Reversível (Fase 1)

**`<ESTRATEGIA_FASEADA>`:** saída completa do Elo 2 acima.

**`<FASE_ALVO>`:** Fase 1 — Shadow Consumer.

**`<CONTEXTO_OPERACIONAL>`:** Relay como barramento de eventos (tecnologia: <<preencher: Kafka, Kinesis, Pulsar?>>); Spark como engine de transformação; data warehouse <<preencher: Redshift, BigQuery, Snowflake?>>; orquestrador <<preencher: Airflow, Prefect, Argo?>>; ambiente Kubernetes (inferido pelo contexto da Aegis).

---

### 1. Pré-condições

- [ ] `forge-batch-ingest` rodando estável por pelo menos 2 ciclos sem falha antes de iniciar.
- [ ] Consumer group dedicado criado no Relay para o shadow consumer (`forge-shadow-consumer`) — **sem compartilhar offset com o consumer de produção**.
- [ ] Tabela de staging criada no data warehouse: `forge_shadow_raw` com schema idêntico à ingestão raw atual. <<preencher: DDL da tabela conforme o DW escolhido>>
- [ ] Monitoramento de lag do consumer group configurado no Beacon (sistema de observabilidade da Aegis).
- [ ] Acesso de escrita do shadow consumer à tabela de staging validado.
- [ ] Contato de plantão (Sam Wilson / SRE) avisado da janela de ativação.

---

### 2. Passos de Execução

**Passo 1 — Criar o consumer group isolado no Relay** *(~15min, risco: baixo)*

```bash
# Exemplo para Kafka — adaptar conforme tecnologia do Relay
kafka-consumer-groups.sh \
  --bootstrap-server <<RELAY_BROKER_ENDPOINT>> \
  --group forge-shadow-consumer \
  --topic <<RELAY_TELEMETRY_TOPIC>> \
  --reset-offsets \
  --to-latest \
  --execute
```
✅ Validação: `kafka-consumer-groups.sh --describe --group forge-shadow-consumer` retorna o grupo com lag = 0 e sem erros.

---

**Passo 2 — Deploy do shadow consumer** *(~20min, risco: baixo)*

```yaml
# Kubernetes Deployment — forge-shadow-consumer
apiVersion: apps/v1
kind: Deployment
metadata:
  name: forge-shadow-consumer
  namespace: forge
  labels:
    app: forge-shadow-consumer
    phase: migration-phase-1
spec:
  replicas: 1
  selector:
    matchLabels:
      app: forge-shadow-consumer
  template:
    metadata:
      labels:
        app: forge-shadow-consumer
    spec:
      containers:
      - name: consumer
        image: <<REGISTRY>>/forge-shadow-consumer:<<VERSION>>
        env:
        - name: RELAY_BROKER
          value: "<<RELAY_BROKER_ENDPOINT>>"
        - name: CONSUMER_GROUP
          value: "forge-shadow-consumer"
        - name: TOPIC
          value: "<<RELAY_TELEMETRY_TOPIC>>"
        - name: STAGING_TABLE
          value: "forge_shadow_raw"
        - name: DW_CONNECTION
          valueFrom:
            secretKeyRef:
              name: forge-dw-credentials
              key: connection-string
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "1"
            memory: "1Gi"
```
✅ Validação: `kubectl rollout status deployment/forge-shadow-consumer -n forge` retorna `successfully rolled out`. Pod em estado `Running`.

---

**Passo 3 — Verificar consumo inicial sem lag acumulado** *(monitorar por 30min após deploy)*

```bash
# Verificar lag do consumer group a cada 5min nos primeiros 30min
watch -n 300 kafka-consumer-groups.sh \
  --bootstrap-server <<RELAY_BROKER_ENDPOINT>> \
  --describe \
  --group forge-shadow-consumer
```
✅ Validação: lag estável (não crescente). Se lag crescer continuamente por 3 leituras seguidas → acionar rollback.

---

**Passo 4 — Confirmar escrita na tabela de staging** *(~10min após Passo 3)*

```sql
-- Executar no data warehouse após 30min de consumer rodando
SELECT
  COUNT(*) AS total_eventos,
  MIN(event_timestamp) AS mais_antigo,
  MAX(event_timestamp) AS mais_recente,
  COUNT(DISTINCT source_id) AS fontes_distintas
FROM forge_shadow_raw
WHERE ingest_timestamp >= NOW() - INTERVAL '30 minutes';
```
✅ Validação: `total_eventos > 0`, `mais_recente` dentro dos últimos 5min, sem erros de escrita nos logs do consumer.

---

**Passo 5 — Ativar alerta de lag no Beacon** *(~10min)*

Configurar alerta no Beacon: se lag do `forge-shadow-consumer` > <<preencher: threshold em número de mensagens, ex: 10.000>> por mais de 5min consecutivos → notificar canal SRE.

✅ Validação: alerta aparece na lista de alertas ativos do Beacon com status `OK`.

---

### 3. Validação de Integridade de Dados

Após 72h de consumer rodando, executar reconciliação entre o batch e o shadow:

```sql
-- Comparar volume de eventos por janela de 1h entre batch (produção) e shadow (staging)
SELECT
  date_trunc('hour', event_timestamp) AS janela,
  COUNT(*) FILTER (WHERE source = 'batch') AS eventos_batch,
  COUNT(*) FILTER (WHERE source = 'shadow') AS eventos_shadow,
  ABS(
    COUNT(*) FILTER (WHERE source = 'batch') -
    COUNT(*) FILTER (WHERE source = 'shadow')
  ) * 100.0 / NULLIF(COUNT(*) FILTER (WHERE source = 'batch'), 0) AS divergencia_pct
FROM (
  SELECT event_timestamp, 'batch' AS source FROM <<TABELA_BATCH_PRODUCAO>>
  UNION ALL
  SELECT event_timestamp, 'shadow' AS source FROM forge_shadow_raw
)
WHERE event_timestamp >= NOW() - INTERVAL '72 hours'
GROUP BY 1
ORDER BY 1;
```
✅ Critério: `divergencia_pct < 0,5%` em todas as janelas. Divergências acima disso exigem investigação antes de avançar para a Fase 2.

---

### 4. Procedimento de Rollback

> ⚠️ Esta fase não tem ponto-de-não-retorno. O batch nunca é tocado; o rollback é simples e sem risco.

**Passo R1** — Escalar o deployment para zero:
```bash
kubectl scale deployment/forge-shadow-consumer -n forge --replicas=0
```

**Passo R2** — Confirmar que o consumer group parou de consumir:
```bash
kafka-consumer-groups.sh --describe --group forge-shadow-consumer \
  --bootstrap-server <<RELAY_BROKER_ENDPOINT>>
# Esperado: todos os membros removidos, consumer inativo
```

**Passo R3** — Opcional: limpar a tabela de staging para evitar dados obsoletos:
```sql
TRUNCATE TABLE forge_shadow_raw;
```

**Passo R4** — Verificar que o `forge-batch-ingest` continua rodando normalmente (não foi afetado em nenhum momento).

---

### 5. Critério de Saída

A Fase 1 está concluída e segura quando **todos** os itens abaixo forem verdadeiros:
- [ ] Shadow consumer rodando por **72h contínuas** sem lag acumulado.
- [ ] Zero perda de eventos confirmada pela reconciliação (divergência < 0,5%).
- [ ] Nenhum alerta disparado no Beacon relacionado ao shadow consumer.
- [ ] `forge-batch-ingest` sem impacto observado (throughput e latência dentro do baseline).
- [ ] Reconciliação de integridade executada e aprovada por pelo menos um engenheiro do time.

---

### 6. Monitoramento Durante a Janela

| Métrica | Fonte | Limiar de Abortar |
|---|---|---|
| Lag do consumer group | Beacon / Relay | Crescimento contínuo por >5min |
| Taxa de erro de escrita no staging | Logs do consumer | >0,1% das mensagens |
| CPU/memória do pod consumer | Kubernetes | >90% do limit por >10min |
| Throughput do batch (`forge-batch-ingest`) | Beacon | Queda >20% do baseline |
| Latência de ingestão do Relay | Beacon | Aumento >30% do baseline |

---

### Checklist de Ida / Volta

| ✅ Para avançar (Fase 2) | 🔄 Para reverter (rollback) |
|---|---|
| Consumer rodou 72h sem lag | Lag crescente por 3 leituras consecutivas |
| Divergência < 0,5% na reconciliação | Taxa de erro de escrita > 0,1% |
| Zero alertas no Beacon | CPU/memória > 90% do limit |
| Batch sem impacto observado | Qualquer impacto detectado no batch |
| Reconciliação aprovada pelo time | Aprovação não obtida em 72h |



# CURADORIA #
Técnica escolhida: prompt chaining (encadeamento de prompts), em que a saída de cada elo vira entrada do próximo — diagnóstico → estratégia faseada → plano exe…Técnica escolhida: prompt chaining (encadeamento de prompts), em que a saída de cada elo vira entrada do próximo — diagnóstico → estratégia faseada → plano executável. Escolhi porque a migração do Forge é complexa demais para um prompt só: jogar tudo de uma vez produz resposta rasa e genérica, enquanto quebrar em etapas faz cada elo focar fundo num problema. Combinei com meta-prompting para gerar e refinar os prompts, personas distintas por elo (arquiteto de dados, arquiteto de migração, SRE) e parametrização via blocos <...> para reuso.
O que precisei refinar até ficar bom: forçar a separação de responsabilidades entre elos (o diagnóstico tentava propor solução; tive que proibir explicitamente "não planeje, só diagnostique"); criar o bloco ### Handoff no fim de cada elo para o acoplamento entre eles ser limpo e não depender de copiar a resposta inteira; impor reversibilidade e proibição de big-bang como regras duras, não sugestões; e adicionar <<preencher: ...>> no elo executável para a IA não inventar nomes de recursos/comandos inexistentes.