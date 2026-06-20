# PROMPT PARAMETRIZÁVEL #

# Papel

Você é um engenheiro de segurança de redes Kubernetes especializado em endurecimento de NetworkPolicies para ambientes de produção. Sua tarefa é receber um manifesto de NetworkPolicy permissivo e produzir uma versão corrigida que siga o princípio de default-deny, liberando apenas os fluxos explicitamente legítimos.

# Objetivo

Transformar um manifesto de NetworkPolicy permissivo (com `podSelector: {}` e regras `- {}` que liberam tudo) em uma política endurecida, segmentada e auditável, em conformidade com o padrão de segurança da organização.

# Entradas (parâmetros)

Você receberá:

1. `{{MANIFESTO_PERMISSIVO}}` — o YAML da NetworkPolicy a corrigir.
2. `{{REGRAS_DO_PADRAO}}` — os fluxos de ingress/egress permitidos e os requisitos de conformidade.
3. `{{MAPA_DE_SERVICOS}}` — a identificação de cada serviço no cluster (namespace, labels, portas).

# Processo de Raciocínio

Antes de gerar o YAML, execute internamente estes passos:

1. **Diagnostique o manifesto de entrada.** Liste cada regra permissiva (`podSelector: {}`, `ingress: - {}`, `egress: - {}`) e o risco concreto que ela introduz.
2. **Mapeie os fluxos legítimos.** Para cada regra do padrão, identifique origem/destino, namespace, label e porta correspondentes no mapa de serviços.
3. **Verifique cobertura.** Confirme que todo fluxo exigido está coberto e que nenhum fluxo não solicitado foi liberado.
4. **Confirme o default-deny.** Garanta que `policyTypes` inclui Ingress e Egress e que não há nenhuma regra aberta.

# Regras de Construção do Manifesto

1. **Nunca** use `podSelector: {}` para selecionar todos os pods quando a regra deve ser específica; selecione pelo label do serviço-alvo.
2. **Nunca** emita regras `- {}` ou seletores vazios em ingress/egress — isso recria o allow-all.
3. Para tráfego entre namespaces, combine `namespaceSelector` **e** `podSelector` no mesmo bloco `from`/`to` (objeto único), nunca como itens de lista separados — itens separados são um OR e ampliam indevidamente o acesso.
4. Use `namespaceSelector` baseado no label padrão `kubernetes.io/metadata.name` para identificar namespaces.
5. Toda porta de egress deve ser declarada explicitamente em `ports` com `protocol` e `port`.
6. DNS deve liberar egress para `kube-system` (label `k8s-app=kube-dns`) nas portas 53 UDP **e** 53 TCP.
7. **Cada regra** de ingress e de egress deve ter um comentário YAML imediatamente acima dizendo qual fluxo legítimo ela libera.
8. Inclua, separada ou no mesmo arquivo, uma NetworkPolicy `default-deny` explícita para o namespace (`podSelector: {}`, `policyTypes: [Ingress, Egress]`, sem regras de allow).
9. Preserve `apiVersion`, `kind` e `metadata.namespace` corretos; use nomes de `metadata.name` descritivos.

# Formato de Saída

Produza, nesta ordem:

1. **Diagnóstico** — lista curta dos problemas do manifesto de entrada (1 linha por problema).
2. **Manifesto corrigido (v1)** — um único bloco YAML, válido e aplicável, contendo a NetworkPolicy endurecida e a default-deny, com todos os comentários por regra.
3. **Verificação e Refino** — conduza ao menos duas rodadas:
   - **Rodada de verificação:** assuma a postura de um revisor de segurança e levante as perguntas de verificação que ele faria (ex.: "o egress para o warehouse está restrito à porta 5432 e ao label correto?", "DNS cobre TCP e UDP?", "há algum `from`/`to` que vira OR indevido?", "o default-deny realmente fecha o que não foi liberado?"). Responda cada uma criticando a própria v1.
   - **Versão revisada (v2):** reemita o YAML corrigindo cada ponto levantado. Se a v2 ainda revelar lacunas, produza uma v3.
4. **Registro de Iterações** — tabela ou lista: o que a v1 entregou, o que a verificação apontou, e como a v2 (e v3, se houver) endereçou cada ponto.

# Critérios de Qualidade

- Zero regras allow-all (nenhum `{}` em selector, ingress ou egress).
- Todo fluxo exigido pelo padrão coberto; nenhum fluxo extra.
- Cross-namespace usando `namespaceSelector` + `podSelector` combinados (AND), não OR.
- DNS com TCP e UDP na porta 53.
- Comentário presente em cada regra.
- YAML válido, indentação consistente, aplicável via `kubectl apply` sem edição.

# Edge Cases

- Se o padrão exigir um fluxo cujo serviço não aparece no mapa, sinalize explicitamente em vez de inventar labels ou portas.
- Se o manifesto de entrada já contiver regras parcialmente válidas, preserve-as e endureça apenas o que for permissivo.
- Se uma porta não for especificada para um egress exigido, marque como pendência na verificação em vez de assumir uma porta arbitrária.


# EXECUÇÃO #

### Modelo Utilizado ###
Cloud Sonnet 4.6 para execução e Opus 4.8 para geração do prompt.

### Output Real ###

{{MANIFESTO_PERMISSIVO}}
```
yaml

lapiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: sentinel-allow
  namespace: sentinel-prod
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - {}
  egress:
    - {}
```
{{REGRAS_DO_PADRAO}}

Ingress: aceitar tráfego do Relay e do API gateway
Egress: Forge (5432), Cerebro (9200), DNS interno (53)
Nenhum allow-all; default-deny explícito; comentário em cada regra

{{MAPA_DE_SERVICOS}}

Sentinel → sentinel-prod, app=sentinel
Relay → relay-prod, app=relay
API gateway → edge, app=api-gateway
Forge → forge-prod, app=forge, porta 5432
Cerebro → cerebro-prod, app=cerebro, porta 9200
DNS → kube-system, k8s-app=kube-dns, porta 53


1. Diagnóstico

podSelector: {} seleciona todos os pods do namespace sem distinção — deveria selecionar apenas app=sentinel
ingress: - {} libera qualquer origem, qualquer porta — allow-all de entrada
egress: - {} libera qualquer destino, qualquer porta — allow-all de saída
Ausência de default-deny explícito: sem uma política de deny separada, pods não cobertos ficam desprotegidos
Nenhum comentário de fluxo — impossível auditar o que cada regra libera


2. Manifesto Corrigido — v1
```
yaml

# ============================================================
# DEFAULT-DENY: bloqueia todo tráfego no namespace por padrão
# ============================================================
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: sentinel-default-deny
  namespace: sentinel-prod
spec:
  podSelector: {}          # aplica a todos os pods do namespace
  policyTypes:
    - Ingress
    - Egress
---
# ============================================================
# SENTINEL: regras de allow explícitas sobre os pods app=sentinel
# ============================================================
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: sentinel-hardened
  namespace: sentinel-prod
spec:
  podSelector:
    matchLabels:
      app: sentinel          # restringe esta política apenas aos pods do Sentinel
  policyTypes:
    - Ingress
    - Egress

  ingress:
    # Fluxo: Relay → Sentinel (entrega de eventos de telemetry)
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: relay-prod
          podSelector:
            matchLabels:
              app: relay
    # Fluxo: API Gateway → Sentinel (requisições de produto vindas da borda)
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: edge
          podSelector:
            matchLabels:
              app: api-gateway

  egress:
    # Fluxo: Sentinel → Forge (consulta ao data warehouse, Postgres 5432)
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: forge-prod
          podSelector:
            matchLabels:
              app: forge
      ports:
        - protocol: TCP
          port: 5432
    # Fluxo: Sentinel → Cerebro (busca de logs, Elasticsearch 9200)
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: cerebro-prod
          podSelector:
            matchLabels:
              app: cerebro
      ports:
        - protocol: TCP
          port: 9200
    # Fluxo: Sentinel → DNS interno (resolução de nomes, kube-dns 53 TCP+UDP)
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
```

3. Verificação e Refino
Rodada 1 — Perguntas do revisor de segurança
P1. O podSelector da política de allow realmente restringe só os pods do Sentinel?

Sim, matchLabels: app=sentinel está correto. Mas a default-deny usa podSelector: {} — isso é intencional (cobre todos os pods do namespace) e está certo.
P2. Os blocos cross-namespace usam AND (namespaceSelector + podSelector no mesmo objeto) ou OR (itens de lista separados)?

✅ Na v1 estão corretos — namespaceSelector e podSelector estão no mesmo item dentro de from/to, formando AND. Se fossem itens separados, virariam OR e qualquer pod de relay-prod ou qualquer pod com app=relay em qualquer namespace entraria.
P3. O egress de DNS cobre TCP e UDP na 53?

✅ Sim, ambos os protocolos estão declarados explicitamente.
P4. As portas de ingress estão abertas demais?

⚠️ Problema identificado. As regras de ingress do Relay e do API gateway não declaram ports — isso significa que qualquer porta de entrada é aceita de cada uma dessas origens. O padrão da Aegis não especificou a porta exata, mas do ponto de vista de hardening, portas abertas sem restrição são superfície de ataque. Deveria ser levantado como pendência.
P5. O nome sentinel-default-deny é aplicado antes de sentinel-hardened?

NetworkPolicies no Kubernetes são aditivas — a ordem de aplicação não importa; o que importa é que a default-deny existe. ✅ Está correta.
P6. Há algum fluxo de egress não coberto que o Sentinel precise para funcionar (ex.: métricas, scraping externo)?

O padrão fornecido não menciona outros destinos. A v1 cobre exatamente o especificado. Se houver outros fluxos operacionais (ex.: push de métricas para um sistema externo), são pendência de levantamento — o prompt sinaliza lacuna em vez de inventar.
P7. O label kubernetes.io/metadata.name está disponível nos namespaces do cluster?

Esse label é adicionado automaticamente pelo Kubernetes a partir da versão 1.21. É a forma recomendada de selecionar namespaces. ✅ Correto.

Versão Revisada — v2
A única correção material da verificação foi o item P4: ingress sem restrição de porta. A v2 adiciona a declaração de porta nos blocos de ingress. Como o padrão não especificou as portas exatas do Sentinel, declaro a porta HTTP padrão de serviços internos (8080) e adiciono comentário de pendência explícita para o time confirmar.
```
yaml

# ============================================================
# DEFAULT-DENY: bloqueia todo tráfego no namespace por padrão
# ============================================================
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: sentinel-default-deny
  namespace: sentinel-prod
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
---
# ============================================================
# SENTINEL: regras de allow explícitas sobre os pods app=sentinel
# ============================================================
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: sentinel-hardened
  namespace: sentinel-prod
spec:
  podSelector:
    matchLabels:
      app: sentinel
  policyTypes:
    - Ingress
    - Egress

  ingress:
    # Fluxo: Relay → Sentinel (entrega de eventos de telemetry)
    # PENDÊNCIA: confirmar porta de ingestão do Sentinel com o time (assumido 8080)
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: relay-prod
          podSelector:
            matchLabels:
              app: relay
      ports:
        - protocol: TCP
          port: 8080
    # Fluxo: API Gateway → Sentinel (requisições de produto vindas da borda)
    # PENDÊNCIA: confirmar porta de serviço do Sentinel com o time (assumido 8080)
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: edge
          podSelector:
            matchLabels:
              app: api-gateway
      ports:
        - protocol: TCP
          port: 8080

  egress:
    # Fluxo: Sentinel → Forge (consulta ao data warehouse, Postgres 5432)
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: forge-prod
          podSelector:
            matchLabels:
              app: forge
      ports:
        - protocol: TCP
          port: 5432
    # Fluxo: Sentinel → Cerebro (busca de logs, Elasticsearch 9200)
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: cerebro-prod
          podSelector:
            matchLabels:
              app: cerebro
      ports:
        - protocol: TCP
          port: 9200
    # Fluxo: Sentinel → DNS interno (resolução de nomes, kube-dns 53 TCP+UDP)
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
```

4. Registro de Iterações
#O que a versão entregou x O que a verificação apontou x Como foi endereçado
- v1: Default-deny + allow com AND cross-namespace correto, DNS TCP+UDP, comentários em todas as regras x Ingress sem restrição de porta — qualquer porta aceita das origens autorizadas v2 x adicionou ports: TCP 8080 nos blocos de ingress com pendência explícita para confirmação
- v2: Ingress com porta declarada, pendência sinalizada no comentário, todos os demais pontos mantidos x Nenhum novo problema estrutural identificado — pendência de porta é operacional, não de segurança x Versão final; pendência vai para o time confirmar a porta real antes do kubectl apply

Pendência aberta para o time (Sam Wilson / Steve Rogers): confirmar a porta de exposição interna dos pods do Sentinel antes de aplicar a v2 em produção. Se a porta for diferente de 8080, substituir nas duas regras de ingress e remover os comentários de pendência.


# CURADORIA #
Escolhi meta-prompting com Chain-of-Thought + self-critique iterativo (gerar/refinar via IA + raciocínio em etapas + ciclos de verificação v1→v2→v3). A tarefa é um artefato de segurança crítico que não pode sair certo na primeira tentativa, então o framework precisava forçar a IA a criticar a própria saída sob a ótica de um revisor de segurança e registrar as iterações — exatamente o valor que o checkpoint pede.
O que precisei refinar até ficar bom: a v1 do prompt era genérica demais e deixava a IA inventar labels e portas, então adicionei o mapa de serviços como parâmetro explícito e a regra de sinalizar lacunas em vez de assumir. O ponto que mais exigiu refino foi o AND vs OR em cross-namespace: a falha clássica de NetworkPolicy é separar namespaceSelector e podSelector como itens de lista (vira OR e amplia o acesso), então virou regra dura combiná-los no mesmo bloco. Também tive que tornar o default-deny e o DNS (TCP e UDP na 53) requisitos explícitos, porque sem isso a IA omitia ambos. Por fim, fixei a estrutura de saída com registro de iterações para que o refino não fosse opcional, mas parte da entrega.
