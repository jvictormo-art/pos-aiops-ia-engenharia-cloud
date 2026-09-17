# Origem e Curadoria — metacortex-triage

---

## De qual fluxo a skill nasceu

A skill não foi escrita de cabeça. Foi destilada de um fluxo de triagem real executado nos três chamados deste desafio.

**Ordem de execução:**

1. Os três manifests de lab (`chamado-01-nyx-prod.yaml`, `chamado-02-orion-stg.yaml`, `chamado-03-nyx-stg.yaml`) foram aplicados no cluster `metacortex-lab` (kind).

2. Para cada chamado, o diagnóstico foi feito manualmente via `kubectl` — sem script, sem automação — seguindo a mesma sequência: `get pods` → identificar camada pelo STATUS → aprofundar com `describe` ou `get events` → cruzar com informações adicionais quando necessário.

3. Cada passo executado e cada saída relevante foi registrada nos arquivos de triagem (`saida/triagem-chamado-0*.md`).

4. **Só após os três diagnósticos fechados**, o método foi extraído: os padrões que se repetiram nos três casos (começar pelo STATUS do pod, ir para o campo certo no describe, parar assim que a causa fechar) viraram a tabela de decisão da skill.

**A skill é o método, não o procedimento.** Ela não prescreve "faça exatamente esses comandos" — prescreve a lógica de decisão (qual STATUS leva a qual camada, qual campo confirma a causa).

---

## O que o método fixou

O método fixou os pontos onde, sem ele, o agente tomaria o caminho errado:

**1. Ordem de investigação: STATUS antes de logs**

Sem método definido, o reflexo natural de um agente (e de um humano iniciante) é pedir logs primeiro — é onde a "história" aparece. O método inverte: log é o último recurso, não o primeiro. `get pods` é o primeiro movimento sempre. Se o STATUS já indica a causa (OOMKilled, ErrImagePull), nenhum log é necessário.

**2. O caso do 503 com pods Running (a armadilha do Chamado 3)**

Este é o caso que o método mais importa. Sem ele, o agente vê `1/1 Running`, conclui "pod saudável", e vai procurar o problema fora do cluster. O método fixa: quando o sintoma é 503 com pods aparentemente saudáveis, a investigação começa pelos endpoints — não pelos logs, não pelo describe do pod. A causa estava no seletor do Service, a dois comandos de distância, e nunca apareceria em logs ou describe do pod.

**3. O critério de parada**

Sem método, o agente investiga por completude — "vou checar tudo para ter certeza". Com método, a triagem para assim que a causa for identificada. Isso é crítico para evitar que o agente derive para análises paralelas desnecessárias ou, pior, para ações corretivas fora do escopo da triagem.

---

## O que foi deixado para o agente decidir

Nem tudo foi fixado. Estes pontos ficaram com o agente por design:

**1. Qual pod inspecionar quando há múltiplos em estados diferentes**

No Chamado 3, havia `nyx-api-*-bl899` (0/1 Running) e `nyx-api-*-dv9z8` (1/1 Running). A skill não prescreve qual dos dois descrever — o agente escolhe o que está em estado anômalo. Esta é uma decisão contextual que seria artificial fixar.

**2. Leitura de logs para causas de aplicação (Passo 2e e Passo 3)**

A skill define que o agente deve "procurar erros de conexão com banco, porta errada, crash de aplicação". O que exatamente buscar e como correlacionar com a causa é julgamento do agente. Fixar padrões de log aqui seria frágil — cada app loga diferente.

**3. O texto da AÇÃO SUGERIDA**

A skill define o formato (o que o time deve corrigir), mas a redação da sugestão é do agente. A triagem identifica a causa e o campo — como corrigi-lo em termos de negócio depende de contexto que só o agente (lendo o chamado completo) tem.

---

## Como foi garantido que a skill não escreve no cluster

A garantia é estrutural, não comportamental.

**A skill não lista ferramentas de escrita.** A seção "Limite absoluto" no início do SKILL.md nomeia explicitamente as três ferramentas permitidas:
- `mcp__kubernetes__kubectl_get`
- `mcp__kubernetes__kubectl_describe`
- `mcp__kubernetes__kubectl_logs`

Ferramentas de escrita (`kubectl_apply`, `kubectl_delete`, `kubectl_create`, `kubectl_patch`, `kubectl_scale`) não aparecem em nenhum passo da skill. Um agente seguindo o método não tem como chegar a um passo que instrua a usar essas ferramentas.

**Por que não basta dizer "não escreva"?** Porque uma instrução negativa ("não faça X") é mais fraca do que uma prescrição positiva que nunca inclui X. Se a skill apenas dissesse "não aplique correções", o agente poderia decidir que "uma pequena correção óbvia" é uma exceção razoável. Como a skill nunca menciona ferramentas de escrita, não há ambiguidade para interpretar.

**Formato do relatório reforça o limite**: a saída da triagem tem o campo `AÇÃO SUGERIDA` — não "CORREÇÃO APLICADA". O nome do campo sinaliza que a ação é para o time, não para o agente.

---

## O que ficou fora da skill por decisão de curadoria

| O que ficou fora | Por quê |
|---|---|
| Triagem de falhas de Ingress/DNS | Fora do escopo do mcp-server-kubernetes; requer acesso a outros sistemas |
| Análise de HPA e autoscaling | Casos raros nos cenários deste lab; adicionaria ruído ao método principal |
| Correlação entre chamados simultâneos | Exige visão cross-namespace que não foi exercitada no fluxo real |
| Sugestão de valores corretos para resource limits | Requer dados de telemetria (Prometheus) não disponíveis na triagem |

Tudo o que está na skill foi exercitado nos três chamados reais. O que não foi exercitado não foi incluído — a skill nasceu do fluxo, não da imaginação de casos futuros.
