# Origem da Skill e Curadoria

## Como a skill nasceu

### Fluxo percorrido (modo conferência primeiro)

**Passo 1 — Ler o padrão antes de qualquer ferramenta**  
O documento `Padrao de Manifests da Metacortex.md` foi lido integralmente antes de escrever qualquer linha de script. Cada regra foi anotada mentalmente com uma pergunta: *isso depende de saber algo sobre a aplicação, ou é verificável olhando só para o YAML?*

**Passo 2 — Criar o manifesto barrado em disco e rodar o Trivy**  
O manifesto `nyx-barrado.yaml` foi gravado em `/tmp` e rodado:

```
trivy config /tmp/metacortex-work/manifests/
```

Resultado: 18 achados. Esse número foi o ponto de partida para a divisão de baldes. Antes de escrever o script, a pergunta era: *o que o Trivy já cobre?* A resposta saiu da execução, não de suposição.

**Passo 3 — Mapear cada regra para um balde (ver `regras-buckets.md`)**  
Regra por regra:
- O que o Trivy já detectou → balde **trivy**
- O que é mecânico e agnóstico à app → balde **script**
- O que exige abrir o repositório → balde **instrução**
- O que é recomendado/educacional e não precisa de automação → balde **fora**

**Passo 4 — Escrever o script cobrindo apenas o que o Trivy não cobre**  
`check-manifest.py` não reimplementa nada que o Trivy já faz. Ele testa: 1.1, 1.2, 1.3, 1.4, 1.5, 2.2 (presença), 2.3, 2.4, 3.3 (heurística), 3.4, 3.7.

**Passo 5 — Rodar o modo escrita para validar no sentido oposto**  
O fake-shop foi escolhido por ser o mais exigente: sem endpoints de saúde, migração embutida no entrypoint, banco com variáveis explícitas no código. Os manifests foram gerados, rodados contra Trivy e contra o script, falhas corrigidas iterativamente até saída limpa.

**Ferramenta usada para produzir a skill**: Claude Code (Claude Opus 4.8), operando em modo interativo dentro do repositório do desafio. O fluxo acima foi executado manualmente, passo a passo — a skill é o destilado desse fluxo, não uma geração direta.

---

## Curadoria: onde está cada regra

### O que virou script empacotado (`check-manifest.py`)

| Regra | Lógica |
|---|---|
| 1.1 | Regex `^[a-z][a-z0-9-]*$` em `metadata.name` |
| 1.2 | Regex `^[a-z]+-(?:dev\|stg\|prod)$` em `metadata.namespace` |
| 1.3 | Presença dos 4 keys `app.kubernetes.io/*` em `metadata.labels` |
| 1.4 | Comparação `matchLabels ⊆ pod.template.metadata.labels` (Deployment) |
| 1.5 | Presença de `annotations["metacortex.io/owner"]` — emite WARN |
| 2.2 | Presença de `readinessProbe` e `livenessProbe` em cada container |
| 2.3 | `spec.replicas >= 2` quando namespace termina em `-prod` |
| 2.4 | `strategy.type == RollingUpdate`, `maxUnavailable == 0`, `maxSurge == 1` em prod |
| 3.3 | Heurística: nome da var `env` casa com padrão `password\|token\|secret\|credential`, ou `env.value` contém URL com credencial (`user:pass@host`) |
| 3.4 | `spec.automountServiceAccountToken == False` no pod spec |
| 3.7 | Todo `image:` começa com `registry.metacortex.io/` |

**Limitação conhecida do script**: a regra 1.4 verifica consistência interna do Deployment (matchLabels vs pod labels), mas não cruza o seletor do Service com o pod do Deployment. Essa verificação requer correlacionar objetos de kinds diferentes — foi mantida como instrução.

### O que ficou no corpo da skill (`SKILL.md`)

- Instrução para ler o projeto antes de escrever ou conferir qualquer manifesto
- Tabela de "o que buscar" no repositório (porta, endpoints, vars de ambiente, migração)
- Árvore de decisão para probes quando não há `/health` e `/ready`
- Padrão de separação migração → initContainer quando o entrypoint mistura migração e app
- Instrução explícita para conferir 1.4 (cruzamento Service × Deployment), 2.2 (probe correctness), 2.6 e 3.5 manualmente

### O que virou arquivo de apoio (`regras-buckets.md`)

Tabela completa regra × balde, com justificativa por linha e notas sobre o Trivy. Não está no corpo da skill para não poluir o fluxo principal; é consultado sob demanda quando há dúvida sobre por que uma regra está ausente do script.

### O que foi decidido NÃO empacotar

| Item | Motivo |
|---|---|
| **Bloco 4 — Vocabulário** | Conteúdo de onboarding: explica Pod, Deployment, Service etc. para quem está chegando. Não é um checklist de conformidade. Empacotar transformaria a skill num tutorial, que não é o papel dela. O documento-fonte é o lugar certo para esse conteúdo. |
| **2.5 — PodDisruptionBudget** | Recomendado, não obrigatório. Depende de saber o padrão de tráfego do workload. O script não tem como inferir `minAvailable` correto. Mencionado na instrução como recomendação a avaliar. |
| **2.6 — terminationGracePeriodSeconds** | Recomendado. O valor correto depende de quanto tempo a app precisa para drenar. Só o desenvolvedor ou SRE que operou o workload sabe isso. |
| **3.5 — ServiceAccount dedicada** | Recomendado. A skill gera um ServiceAccount por workload (boas práticas), mas a configuração de RBAC é escopo separado que exige análise das permissões necessárias da app. |

### Permissões que a skill pede

| Permissão | Motivo |
|---|---|
| Leitura de repositório (GitHub) | Modo escrita e modo conferência exigem abrir o código para confirmar porta, endpoints e variáveis de ambiente |
| Execução de `trivy` | Conferência mecânica das regras 3.1, 2.1, 3.2, 3.6 |
| Execução de `python3 skill/check-manifest.py` | Conferência das regras que o Trivy não cobre |
| Escrita no diretório de manifests | Modo escrita gera arquivos YAML no destino indicado |

---

## Nota sobre o KSV-0125 (falso positivo)

O Trivy (KSV-0125) flageia `registry.metacortex.io` como "untrusted registry". Isso acontece porque o Trivy não tem uma lista de registries confiáveis configurada para este contexto — ele compara contra registries públicos conhecidos. A regra 3.7 do padrão da Metacortex faz o oposto: **exige** que todas as imagens venham de `registry.metacortex.io`. O script verifica essa regra na direção correta. O KSV-0125 é suprimido via `.trivyignore` em todos os diretórios de manifests.
