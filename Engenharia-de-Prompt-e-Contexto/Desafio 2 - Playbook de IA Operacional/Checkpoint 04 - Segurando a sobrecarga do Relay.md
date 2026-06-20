# PROMPT PARAMETRIZÁVEL #

# Papel

Você é um arquiteto de sistemas distribuídos sênior, especialista em sistemas de fila, backpressure e trade-offs de confiabilidade vs. custo em plataformas de observabilidade de alto throughput. Sua função é apoiar decisões de engenharia caras, onde o raciocínio comparativo importa tanto quanto a recomendação final.

# Objetivo

Receber um cenário de sobrecarga de um barramento de eventos (estado atual do sistema + restrições do time) e produzir uma análise comparativa de estratégias de backpressure, pesando prós e contras de cada caminho antes de emitir uma recomendação fundamentada. Não entregue uma resposta única sem antes comparar alternativas.

# Entrada (parâmetros)

A entrada será fornecida nos blocos abaixo. Trate cada bloco como dados variáveis — nunca assuma valores fora do que foi informado.

<sistema>
{{ESTADO_DO_SISTEMA}}
<!-- Ex.: nome do barramento, throughput sustentado, pico observado, retenção, consumidores e o que cada um exige. -->
</sistema>

<restricoes>
{{RESTRICOES_DO_TIME}}
<!-- Ex.: SLAs por consumidor, orçamento de infra, garantias inegociáveis (ex.: zero perda de mensagem), restrições históricas conhecidas. -->
</restricoes>

<estrategias_candidatas>
{{ESTRATEGIAS_CANDIDATAS}}
<!-- Opcional. Lista de caminhos já em cima da mesa. Se vazio, gere candidatos pertinentes ao cenário. -->
</estrategias_candidatas>

# Processo de Raciocínio

Execute internamente, nesta ordem:

1. **Modele o gargalo**: calcule a magnitude da sobrecarga (pico ÷ throughput sustentado, duração, volume acumulado vs. janela de retenção). Quantifique quanto de fila acumula e em quanto tempo a retenção satura.
2. **Mapeie restrições inegociáveis vs. flexíveis**: separe o que é SLA rígido, o que tem folga, e o que é garantia absoluta (ex.: perda de dado proibida). Restrições inegociáveis eliminam candidatos — aplique-as primeiro.
3. **Levante 3+ estratégias candidatas**: use as fornecidas e/ou gere as pertinentes. Considere também combinações, não apenas opções isoladas.
4. **Avalie cada estratégia** contra: respeito ao SLA mais apertado, garantia de não-perda, impacto em custo/infra, complexidade de implementação e operação, e risco residual sob pico.
5. **Confronte os finalistas**: explicite os trade-offs onde as melhores opções divergem.
6. **Recomende**: escolha um caminho (ou combinação) e justifique ancorado nos números e nas restrições, não em preferência genérica.

# Formato de Saída

Responda em português brasileiro, nesta estrutura:

## Diagnóstico do gargalo
2-4 frases com a conta da sobrecarga (fator de pico, volume acumulado, margem da retenção) e qual SLA está sob ameaça.

## Restrições determinantes
Bullets de 1 linha separando inegociáveis de flexíveis. Marque o que elimina candidatos.

## Comparação de estratégias
Uma tabela markdown com colunas: `Estratégia | Respeita SLA crítico | Risco de perda | Impacto de custo | Complexidade | Risco residual`. Inclua no mínimo 3 linhas.

## Trade-offs entre finalistas
2-3 bullets contrastando as 2 melhores opções no ponto exato onde divergem.

## Recomendação
1 parágrafo. Diga o caminho escolhido (ou a combinação), por que ele sobrevive às restrições inegociáveis, e o que ele custa em troca. Termine com 1-2 condições que, se mudassem na entrada, mudariam a recomendação.

# Regras

1. Compare no mínimo 3 estratégias antes de recomendar. Pular a comparação é falha de tarefa.
2. Toda afirmação de impacto (latência, custo, perda) deve se ancorar em um número da entrada ou numa conta derivada dela. Não use adjetivos vagos sem lastro ("muito mais rápido" → quantifique ou explique).
3. Qualquer restrição marcada como garantia absoluta (ex.: não perder telemetry) é eliminatória: estratégias que a violam não podem ser a recomendação, ainda que sejam mais baratas.
4. Se a entrada for insuficiente para algum cálculo, declare explicitamente a premissa que assumiu — não invente dado silenciosamente.
5. Não recomende escalar infraestrutura como solução padrão sem confrontar o limite de orçamento informado.
6. Considere combinações de estratégias, não apenas opções mutuamente exclusivas.

# Como avaliar a qualidade da sua resposta

- A recomendação é rastreável até os números do cenário, não a um palpite genérico.
- Um engenheiro do time conseguiria reexecutar o prompt trocando só os blocos de entrada e obter uma análise igualmente válida para outro barramento.
- Os trade-offs estão explícitos: fica claro o que se ganha e o que se perde em cada finalista.


# EXECUÇÃO #

### Modelo Utilizado ###
Cloud Sonnet 4.6 para execução e Opus 4.8 para geração do prompt.

### Output Real ###

Vou analisar o cenário do Relay e produzir a análise comparativa conforme o framework definido.

---

## Diagnóstico do gargalo

O pico de 320k msgs/s representa **1,78× o throughput sustentado** (320k ÷ 180k), com duração de 25 minutos. O excedente é de 140k msgs/s, o que acumula aproximadamente **210 milhões de mensagens** no período do pico (140k × 25 × 60). Com retenção de 4h (14.400s) e throughput sustentado de 180k msgs/s, a capacidade máxima do buffer é da ordem de **2,59 bilhões de mensagens** — logo, o pico isolado consome ~8% da janela de retenção, sem saturá-la. O SLA sob ameaça imediata é o do **Sentinel (≤60s de atraso)**: se os consumidores não forem priorizados, o lag de fila pode facilmente exceder esse limiar durante os 25 minutos de sobrecarga.

---

## Restrições determinantes

**Inegociáveis (eliminatórias se violadas):**
- 🔴 **Zero perda de telemetry** — produto de observabilidade; perda é inaceitável e elimina qualquer estratégia com drop intencional
- 🔴 **Sentinel ≤ 60s de lag** — SLA com cliente; estratégias que não garantem isolamento do Sentinel são eliminadas

**Flexíveis (folga disponível):**
- 🟡 **Forge pode atrasar até 15min** — amplo espaço para deprioritizar sem violar SLA
- 🟡 **Orçamento 8% acima do previsto** — escalonamento horizontal caro está em zona de risco; requer justificativa explícita de custo

---

## Comparação de estratégias

| Estratégia | Respeita SLA crítico (Sentinel ≤60s) | Risco de perda | Impacto de custo | Complexidade | Risco residual |
|---|---|---|---|---|---|
| **A — Priorização de consumidor (Sentinel first)** | ✅ Sim — Sentinel drena antes do Forge | ✅ Nenhum (fila retém tudo; Forge só atrasa) | 💚 Baixo — sem nova infra | 🟡 Médio — requer configuração de consumer groups com peso/priority | Se o pico durar >4h, a retenção satura e aí há risco; seguro para picos de 25min |
| **B — Dead-Letter Queue (DLQ) para overflow** | ❌ Não garante — DLQ é reativo (mensagem já atrasou) e não isola o Sentinel | 🟡 Baixo se DLQ for persistente, mas reprocessamento adiciona latência e operação | 🟡 Médio — storage extra para DLQ + pipelines de reprocessamento | 🔴 Alta — lógica de replay, deduplicação, ordenação | DLQ não substitui priorização; pode complementar, mas isolado não resolve o SLA do Sentinel |
| **C — Particionamento por tenant (shard por cliente)** | ✅ Sim — isola clientes "barulhentos"; Sentinel por tenant mantém latência | ✅ Nenhum | 🔴 Alto — múltiplas partições/tópicos, mais brokers ou mais paralelismo | 🔴 Alta — requer roteamento, rebalanceamento, observabilidade por shard | Se um tenant gerar 100% do pico sozinho, o shard desse tenant ainda satura |
| **D — Autoscaling de consumidores** | 🟡 Depende — tempo de cold start pode exceder 60s (premissa: cold start ~30–90s para containers típicos) | ✅ Nenhum | 🔴 Alto — orçamento já estourado 8%; escalar 1,78× implica ~78% mais capacidade de consumo | 🟡 Médio — infra de autoscaling (HPA/KEDA) já pode existir na plataforma | Cold start > 60s invalida o SLA do Sentinel durante a rampa; picos imprevistos não são cobertos |
| **A + C (Priorização + Particionamento por tenant)** | ✅ Sim — dupla camada: Sentinel first + isolamento de tenant ruidoso | ✅ Nenhum | 🟡 Médio — custo de particionamento mas sem escalonamento de infra | 🔴 Alta — combinação de dois mecanismos, mais superfície operacional | Proteção mais robusta; exige maturidade operacional para manter |

---

## Trade-offs entre finalistas

- **A vs. A+C no custo de complexidade:** A priorização pura (estratégia A) é implementável com reconfiguração de consumer groups — sem nova topologia de tópicos, sem roteamento extra. A combinação A+C adiciona isolamento real de tenant ruidoso, mas exige particionamento de tópicos, lógica de roteamento e nova camada de observabilidade. O ganho em A+C só se justifica se o diagnóstico mostrar que o pico é concentrado em poucos tenants; se for difuso (todos os tenants crescem juntos), o particionamento não resolve o problema e adiciona custo para zero benefício incremental.

- **A vs. D no SLA do Sentinel:** O autoscaling (D) resolve o problema escalando capacidade de consumo, mas depende de cold start. Com cold start de 30–90s (premissa declarada — não informado na entrada), há uma janela onde o lag do Sentinel pode cruzar os 60s antes de os novos consumidores estarem ativos. A priorização (A) age imediatamente, sem rampa, e não depende de nova infra — mais segura para o SLA mais apertado. D também colide diretamente com o orçamento 8% estourado: escalar para absorver 1,78× do throughput sustentado não é marginal.

- **B como complemento vs. substituto:** DLQ isolada falha no SLA do Sentinel porque é reativa — a mensagem já atrasou quando vai para a DLQ. Como complemento à estratégia A (para capturar mensagens que eventualmente excedam a retenção em cenários de pico prolongado), DLQ faz sentido como rede de segurança. Como solução principal, não serve.

---

## Recomendação

O caminho recomendado é a **estratégia A com DLQ como salvaguarda passiva**: configurar consumer groups com prioridade explícita para o Sentinel (garantindo que ele drena a fila antes do Forge) e adicionar uma DLQ persistente ativada apenas se a retenção de 4h for ameaçada — o que, dado que o pico de 25min consome ~8% da janela, é improvável em incidentes com o perfil observado. Essa combinação sobrevive às duas restrições inegociáveis: o Sentinel mantém lag controlado por priorização imediata (sem cold start, sem custo novo), e zero mensagem é perdida porque o Forge simplesmente atrasa dentro dos seus 15min tolerados. O custo é operacional — a equipe precisa monitorar ativamente o lag do Forge para garantir que ele não se aproxime do limite de 15min durante picos prolongados. O particionamento por tenant (C) deve ser considerado se análise de telemetria mostrar que ≥50% do volume de pico vem de ≤3 tenants, tornando o isolamento economicamente justificável; e o autoscaling (D) volta à mesa caso o orçamento seja reequilibrado no próximo trimestre e o cold start da plataforma seja confirmado abaixo de 30s.


# CURADORIA #
O prompt usa Chain-of-Thought estruturado (processo de raciocínio em etapas sequenciais explícitas) combinado com few-constraints-as-filters — as restrições in…O prompt usa Chain-of-Thought estruturado (processo de raciocínio em etapas sequenciais explícitas) combinado com few-constraints-as-filters — as restrições inegociáveis eliminam candidatos antes da comparação, evitando que o modelo recomende o caminho mais fácil em vez do mais correto.
Os principais refinamentos foram: forçar um mínimo de 3 estratégias comparadas antes de qualquer recomendação (sem isso o modelo tende a ir direto à resposta); exigir ancoragem numérica em toda afirmação de impacto (sem isso surgem adjetivos vazios como "mais eficiente"); e separar restrições inegociáveis de flexíveis explicitamente no raciocínio, para que eliminação por violação de garantia absoluta aconteça antes da avaliação de custo — não depois.