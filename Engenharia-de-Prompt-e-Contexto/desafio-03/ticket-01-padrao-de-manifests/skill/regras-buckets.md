# Tabela de Regras × Baldes

Mapeamento de cada regra do Padrão de Manifests da Metacortex para seu balde de verificação.
Produzido após execução real do `trivy config` e leitura regra a regra do padrão.

| Regra | Descrição | Balde | Justificativa |
|---|---|---|---|
| 1.1 | Nome em kebab-case | **script** | Verificação sintática pura via regex — agnóstica ao workload |
| 1.2 | Namespace `<cliente>-<env>` | **script** | Regex `^[a-z]+-(?:dev\|stg\|prod)$` — sem saber nada da app |
| 1.3 | Quatro rótulos `app.kubernetes.io/*` | **script** | Presença de chave fixa — verificação mecânica |
| 1.4 | Seletor casa com rótulos do pod | **script** | Parse YAML + comparação de dicionários — puramente estrutural |
| 1.5 | Anotação `metacortex.io/owner` | **script** | Presença de chave — emite WARN (recomendado, não obrigatório) |
| 1.6 | Nome do container = componente | **instrução** | Exige saber qual é o nome do componente — não está no YAML |
| 2.1 | `resources.requests` e `limits` | **trivy** | KSV-0011, 0015, 0016, 0018 já cobrem os quatro campos |
| 2.2 | `readinessProbe` e `livenessProbe` presentes | **script** | Presença no YAML — verificação mecânica |
| 2.2 | Probes apontam para endpoints reais | **instrução** | Exige abrir o repositório e confirmar que o path existe no código |
| 2.3 | `replicas >= 2` em prod | **script** | Namespace termina com `-prod` + valor de `replicas` |
| 2.4 | Estratégia RollingUpdate em prod | **script** | `strategy.type`, `maxUnavailable` e `maxSurge` são campos YAML |
| 2.5 | PodDisruptionBudget em prod | **fora** | Recomendado; depende do padrão de tráfego — não se infere do YAML |
| 2.6 | `terminationGracePeriodSeconds` | **fora** | Recomendado; depende do comportamento de shutdown da app |
| 3.1 | Tag `:latest` proibida | **trivy** | KSV-0013 |
| 3.2 | `securityContext` completo | **trivy** | KSV-0001, 0003, 0004, 0012, 0014, 0020, 0106, 0118 |
| 3.3 | Segredo em texto puro proibido | **script** | Heurística: `SECRET_KEY` no nome da var + URL com credencial em `value` |
| 3.4 | `automountServiceAccountToken: false` | **script** | Campo booleano no `spec` do Pod — verificação mecânica |
| 3.5 | ServiceAccount dedicada | **fora** | Recomendado; exige análise de RBAC fora do manifest |
| 3.6 | `hostNetwork`, `hostPID`, `privileged` proibidos | **trivy** | Trivy verifica esses campos mesmo quando ausentes (PASS implícito) |
| 3.7 | Imagem só de `registry.metacortex.io` | **script** | KSV-0125 do Trivy é **falso positivo** — ele não sabe que `registry.metacortex.io` é o registry confiável da Metacortex, então flageia como "untrusted". O script faz a verificação no sentido correto: toda imagem DEVE começar com `registry.metacortex.io/` |
| Bloco 4 | Vocabulário (Pod, Deployment, Service…) | **fora** | Conteúdo educacional de onboarding — não é checklist |

## Notas sobre o Trivy

Rodado sobre o manifesto barrado do nyx. Saída relevante:

- **18 achados** totais no `nyx-barrado.yaml`
- KSV-0013: tag `:latest` → cobre regra 3.1 ✓
- KSV-0011/0015/0016/0018: resources ausentes → cobre regra 2.1 ✓
- KSV-0001/0003/0004/0012/0014/0020/0106/0118: securityContext → cobre regra 3.2 ✓
- KSV-0125: flageia `registry.metacortex.io` como "untrusted" → **falso positivo** para o contexto da Metacortex; suprimido com `--skip-checks KSV-0125`
- Trivy **não detectou**: 1.1 (NyxAPI não é kebab-case), 1.3 (rótulos ausentes), 1.4 (seletor/label mismatch), 2.2 (probes ausentes), 2.3 (replica=1 em prod), 2.4 (strategy ausente), 3.3 (DATABASE_URL em texto puro), 3.4 (automountServiceAccountToken não declarado)
