# Conferência — manifesto barrado do nyx

Manifesto auditado: `nyx-barrado.yaml` (Deployment NyxAPI + Service nyx-api, namespace nyx-prod)  
Workload de referência: kube-news (https://github.com/KubeDev/kube-news), porta 8080, `/health` e `/ready` implementados em `src/system-life.js`.

---

## Saída do Trivy

`trivy config --ignorefile .trivyignore nyx-barrado.yaml`  
17 falhas (KSV-0125 suprimido por ser falso positivo — veja regras-buckets.md).

| KSV | Severidade | Regra do padrão | Achado |
|---|---|---|---|
| 0013 | MEDIUM | 3.1 | `image: registry.metacortex.io/nyx/api:latest` — tag `:latest` proibida |
| 0011 | LOW | 2.1 | `resources.limits.cpu` ausente |
| 0015 | LOW | 2.1 | `resources.requests.cpu` ausente |
| 0016 | LOW | 2.1 | `resources.requests.memory` ausente |
| 0018 | LOW | 2.1 | `resources.limits.memory` ausente |
| 0001 | MEDIUM | 3.2 | `securityContext.allowPrivilegeEscalation` não declarado |
| 0003 | LOW | 3.2 | `capabilities.drop` não declarado |
| 0004 | LOW | 3.2 | `capabilities.drop` ausente |
| 0012 | MEDIUM | 3.2 | `securityContext.runAsNonRoot` não declarado |
| 0014 | HIGH | 3.2 | `securityContext.readOnlyRootFilesystem` não declarado |
| 0020 | LOW | 3.2 | `securityContext.runAsUser` não declarado |
| 0021 | LOW | 3.2 | `securityContext.runAsGroup` não declarado |
| 0106 | LOW | 3.2 | capabilities não dropadas |
| 0118 (x2) | HIGH | 3.2 | securityContext padrão no container e no pod |
| 0030 | LOW | (extra) | `seccompProfile.type: RuntimeDefault` ausente |
| 0104 | MEDIUM | (extra) | seccomp profile não declarado |

---

## Saída do script mecânico

`python3 skill/check-manifest.py nyx-barrado.yaml`  
9 falhas, 2 avisos.

| Status | Regra | Achado |
|---|---|---|
| FAIL | 1.1 | `name: NyxAPI` — camelCase, não kebab-case. Correto: `nyx-api` |
| OK | 1.2 | Namespace `nyx-prod` válido |
| FAIL | 1.3 | Deployment e Service não têm nenhum dos 4 rótulos `app.kubernetes.io/*` |
| WARN | 1.5 | `metacortex.io/owner` ausente em ambos os objetos |
| OK | 1.4 | Deployment interno consistente: `matchLabels: {app: nyxapi}` casa com `labels: {app: nyxapi}` no pod |
| FAIL | 2.3 | `replicas: 1` em `nyx-prod` — obrigatório >= 2 |
| FAIL | 2.4 | `strategy` não declarada — falta RollingUpdate com maxUnavailable=0, maxSurge=1 |
| FAIL | 3.4 | `automountServiceAccountToken` não declarado (default: true) |
| FAIL | 2.2 | `readinessProbe` ausente no container `api` |
| FAIL | 2.2 | `livenessProbe` ausente no container `api` |
| FAIL | 3.3 | `DATABASE_URL` com credencial em texto puro: `postgres://nyx:s3nh4-do-banco@...` |
| OK | 3.7 | Imagem de `registry.metacortex.io` ✓ |

---

## Achados que exigem leitura do projeto (instrução)

### 1.4 — Seletor do Service não casa com rótulos do pod

O script não cruza Service com Deployment (limitação documentada). Inspeção manual:

- Service.spec.selector: `{app: nyx-api}`
- Pod template labels: `{app: nyxapi}`

**Um hífen de diferença** — o Service não tem endpoints. Tráfego nunca chega ao pod. Este é o "erro mais silencioso do parque" descrito na regra 1.4.

### 2.2 — Probes: endpoints confirmados no código do kube-news

Antes de corrigir as probes, foi necessário abrir `src/system-life.js` do kube-news:
- `/ready` → retorna 200 quando `readTime < now()` (app pronta para receber tráfego)
- `/health` → retorna JSON `{state: "up", machine: hostname}` (processo vivo)
- Porta: 8080 (confirmado em `server.js`: `app.listen(8080)`)

Correção correta para as probes:

```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 10
  failureThreshold: 3

livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 30
  failureThreshold: 3
```

Apontar as duas probes para o mesmo endpoint ou para o banco seria erro de projeto: a liveness falharia durante lentidão do banco, reiniciaria o container, e o reinício não conserta o banco (regra 2.2 do padrão).

---

## Resumo consolidado

| Regra | Obrig./Proib./Rec. | Status | Ferramenta |
|---|---|---|---|
| 1.1 nome kebab-case | obrigatório | **FALHA** | script |
| 1.2 namespace | obrigatório | OK | script |
| 1.3 rótulos | obrigatório | **FALHA** | script |
| 1.4 seletor = labels | obrigatório | **FALHA** | inspeção manual |
| 1.5 owner annotation | recomendado | aviso | script |
| 2.1 resources | obrigatório | **FALHA** | Trivy (4 achados) |
| 2.2 probes presentes | obrigatório | **FALHA** | script |
| 2.2 probe correctness | obrigatório | **FALHA** | instrução (leitura do kube-news) |
| 2.3 replicas >= 2 | obrigatório | **FALHA** | script |
| 2.4 RollingUpdate | obrigatório | **FALHA** | script |
| 3.1 tag imutável | proibido | **FALHA** | Trivy KSV-0013 |
| 3.2 securityContext | obrigatório | **FALHA** | Trivy (8 achados) |
| 3.3 segredo em texto | proibido | **FALHA** | script |
| 3.4 automountToken | obrigatório | **FALHA** | script |
| 3.7 registry interno | obrigatório | OK | script |

**Total: 12 falhas obrigatórias/proibidas, 1 aviso recomendado.** O Seraph acertou o barramento — e tinha ainda mais para barrar além do que foi registrado.
