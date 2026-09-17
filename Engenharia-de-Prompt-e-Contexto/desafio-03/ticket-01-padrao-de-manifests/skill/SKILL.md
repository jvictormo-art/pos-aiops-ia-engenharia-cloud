---
name: metacortex-manifest
description: Escreve ou confere manifests de Kubernetes para workloads da Metacortex seguindo o padrão interno de identidade, resiliência e segurança. Use ao pedir para gerar, escrever, revisar ou validar um manifest de workload da Metacortex.
---

# metacortex-manifest

**Permissões**: leitura do repositório do workload (GitHub), execução de `trivy` e `python3`, escrita no diretório de manifests.

---

## Modo 1 — Escrever manifests para um novo workload

### Passo 1: Ler o projeto

Abra o repositório do workload e colete, sem suposições:

| O que buscar | Onde encontrar |
|---|---|
| Porta que o processo escuta | `Dockerfile`, `entrypoint.sh`, código da app |
| Endpoints de saúde disponíveis | Rotas registradas no código (ex: `/health`, `/ready`) |
| Variáveis de ambiente do banco | Código de configuração (ex: `os.getenv(...)`) |
| Algum processo roda antes da app? | `entrypoint.sh` ou `CMD` do Dockerfile (ex: `flask db upgrade`) |

Se o workload não expõe `/health` e `/ready`, **documente a decisão de probe** antes de escrever o manifesto:

- Sem endpoint de saúde → use `httpGet` no endpoint mais próximo de indicar que a app está servindo (ex: `/metrics`, `/`), e justifique.
- Para liveness, prefira `tcpSocket` a endpoints que dependam de banco; liveness que checa banco reinicia a app quando o banco está lento — não conserta nada e derruba tudo.
- Se o workload roda migração de banco no `entrypoint` (ex: `flask db upgrade && gunicorn …`), separe a migração em **initContainer** no manifest para que o container principal possa ter `readOnlyRootFilesystem: true`.

### Passo 2: Decisões obrigatórias antes de escrever

Responda cada item antes de digitar o primeiro YAML:

1. **Namespace**: `<cliente>-<env>` — qual ambiente? (`dev` / `stg` / `prod`)
2. **Tag da imagem**: qual versão imutável ou digest? (nunca `:latest`)
3. **Resources**: qual é o consumo real em regime? (`limits.memory` entre 1,5× e 2× esse valor)
4. **Probe correctness**: os endpoints das probes existem no código do projeto?
5. **Segredos**: quais vars de ambiente contêm senhas ou tokens? → `secretKeyRef`; as demais → `configMapKeyRef` ou `env.value`
6. **readOnlyRootFilesystem**: o processo principal precisa gravar em disco? → monte `emptyDir` no caminho necessário (ex: `/tmp`)

### Passo 3: Gerar os manifests

Produza, nesta ordem, todos os objetos necessários:

```
Secret          → credenciais do banco (stringData com valor CHANGE_ME se não fornecido)
ConfigMap       → configuração não-sensível
ServiceAccount  → uma por workload, automountServiceAccountToken: false
Deployment      → veja template abaixo
Service         → ClusterIP padrão; porta 80 → targetPort da app
```

**Template de Deployment — campos obrigatórios:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: <cliente>-<componente>          # kebab-case
  namespace: <cliente>-<env>
  labels:
    app.kubernetes.io/name: <componente>
    app.kubernetes.io/instance: <cliente>-<env>
    app.kubernetes.io/part-of: <cliente>
    app.kubernetes.io/managed-by: platform
  annotations:
    metacortex.io/owner: "<time responsável>"
spec:
  replicas: 2                           # prod: >= 2; dev/stg: 1 aceitável
  selector:
    matchLabels:
      app.kubernetes.io/name: <componente>
      app.kubernetes.io/instance: <cliente>-<env>
  strategy:                             # obrigatório em prod
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  template:
    metadata:
      labels:
        app.kubernetes.io/name: <componente>
        app.kubernetes.io/instance: <cliente>-<env>
        app.kubernetes.io/part-of: <cliente>
        app.kubernetes.io/managed-by: platform
    spec:
      automountServiceAccountToken: false
      serviceAccountName: <cliente>-<componente>
      initContainers:                   # inclua se houver migração de banco
        - name: migrate
          image: registry.metacortex.io/<cliente>/<componente>:<tag>
          command: [...]                # apenas o comando de migração
          securityContext: &sc          # mesmos campos do container principal
            runAsNonRoot: true
            runAsUser: 10001
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
          resources:
            requests: {cpu: 100m, memory: 128Mi}
            limits:   {cpu: 500m, memory: 256Mi}
          volumeMounts:
            - {name: tmp, mountPath: /tmp}
      containers:
        - name: <componente>            # nome do componente, não "api" genérico
          image: registry.metacortex.io/<cliente>/<componente>:<tag>
          ports:
            - containerPort: <porta>
          envFrom: []                   # ou env: com valueFrom
          readinessProbe:               # endpoint real da app, porta real
            httpGet: {path: <endpoint>, port: <porta>}
            initialDelaySeconds: 10
            periodSeconds: 10
            failureThreshold: 3
          livenessProbe:                # não checar banco aqui
            tcpSocket: {port: <porta>}
            initialDelaySeconds: 30
            periodSeconds: 30
            failureThreshold: 3
          securityContext:
            runAsNonRoot: true
            runAsUser: 10001
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
          resources:
            requests: {cpu: 200m, memory: 256Mi}
            limits:   {cpu: 1000m, memory: 512Mi}
          volumeMounts:
            - {name: tmp, mountPath: /tmp}
      volumes:
        - name: tmp
          emptyDir: {}
```

### Passo 4: Validar o manifesto gerado

```bash
# 1 — Trivy: regras de segurança e resources (ignora KSV-0125, falso positivo)
trivy config --skip-checks KSV-0125 <diretório-dos-manifests>/

# 2 — Script mecânico: regras de identidade, nomenclatura, probes e segredos
python3 skill/check-manifest.py <diretório-dos-manifests>/
```

Corrija todas as falhas antes de abrir PR.

---

## Modo 2 — Conferir um manifesto existente

### Passo 1: Abrir o projeto referenciado

Antes de rodar qualquer ferramenta, **abra o repositório do workload** que o manifesto empacota. Você precisa saber:

- Qual porta o processo realmente escuta?
- Os endpoints declarados nas probes (`/health`, `/ready`, etc.) **existem no código**?
- As variáveis de ambiente sensíveis estão em `secretKeyRef`, não em `value`?

### Passo 2: Rodar as ferramentas

```bash
# Trivy — cobre 3.1 (tag :latest), 2.1 (resources), 3.2 (securityContext), 3.6 (host*)
trivy config --skip-checks KSV-0125 <manifesto.yaml>

# Script mecânico — cobre o que o Trivy não pega
python3 skill/check-manifest.py <manifesto.yaml>
```

### Passo 3: Completar a revisão com julgamento

Após as ferramentas, confira manualmente:

| Regra | O que verificar | Ferramenta |
|---|---|---|
| 2.2 probe correctness | O path e a porta da probe existem no código do workload? | Leitura do projeto |
| 2.6 terminationGracePeriod | A app processa tarefas longas? O valor cobre o tempo de drenagem? | Leitura do projeto |
| 3.5 ServiceAccount | O workload usa a `default`? Há RBAC desnecessário? | kubectl (se tiver acesso) |
| 1.6 nome do container | O container se chama `api`, `main` ou `container`? → renomeie para o componente | Leitura do manifest |

### Passo 4: Produzir o relatório

Liste cada achado no formato:

```
[FALHA|AVISO|OK] Regra X.Y — <descrição> — <evidência no YAML ou no código>
```

---

## O que está FORA desta skill

| Item | Motivo |
|---|---|
| Bloco 4 do padrão (vocabulário) | Conteúdo educacional, não checklist. Use o documento-fonte para onboarding. |
| Geração de PDB (2.5) | Depende do padrão de tráfego do workload; não se infere do YAML. Mencione na revisão como recomendação. |
| Criação de RBAC para ServiceAccount (3.5) | Escopo de segurança separado; exige análise de permissões da app. |
| Configuração de `terminationGracePeriodSeconds` (2.6) | Depende do comportamento da aplicação em shutdown. |

---

## Arquivo de apoio

Consulte `regras-buckets.md` para a tabela completa de cada regra do padrão → balde (trivy / script / instrução / fora).
