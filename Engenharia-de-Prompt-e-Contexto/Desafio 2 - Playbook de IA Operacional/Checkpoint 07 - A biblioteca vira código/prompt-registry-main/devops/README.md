# DevOps

Prompts voltados a **infraestrutura, automação e operação** de sistemas: pipelines de CI/CD, containers, orquestração, provisionamento, observabilidade, confiabilidade e segurança operacional.

## Escopo

Entram aqui prompts relacionados a:

- Pipelines de CI/CD (GitHub Actions, GitLab CI, Jenkins etc.).
- Containers e orquestração (Docker, Kubernetes, Helm).
- Infraestrutura como código (Terraform, Pulumi, Ansible).
- Provedores de nuvem (AWS, GCP, Azure) e seus recursos.
- Observabilidade (logs, métricas, tracing, alertas, dashboards).
- Confiabilidade, SRE, postmortems e análise de incidentes.
- Segurança operacional (hardening, secrets, políticas de acesso).

## Fora de escopo

- Escrita de código de aplicação → usar `desenvolvimento/`.
- Conteúdo educacional sobre DevOps (aulas, artigos, vídeos) → usar `criacao-conteudo/`.

## Prompts

- [analisar-backpressure-barramento](./analisar-backpressure-barramento/) — Recebe um cenário de sobrecarga de barramento de eventos e produz análise comparativa de estratégias de backpressure com recomendação fundamentada em trade-offs.
- [diagnosticar-causa-raiz-incidente](./diagnosticar-causa-raiz-incidente/) — Analisa artefatos heterogêneos de um incidente (config, métricas e logs) e produz diagnóstico de causa-raiz com linha do tempo, cadeia causal, mitigação imediata e correção definitiva.
- [endurecer-networkpolicy-kubernetes](./endurecer-networkpolicy-kubernetes/) — Transforma uma NetworkPolicy permissiva em uma política endurecida com default-deny, liberando apenas fluxos explicitamente legítimos, com verificação iterativa.
- [migrar-pipeline-batch-para-event-driven](./migrar-pipeline-batch-para-event-driven/) — Cadeia de três prompts encadeados para diagnosticar, planejar e executar a migração de um pipeline batch para um modelo event-driven de forma incremental e reversível.
- [nota-de-triagem-alerta](./nota-de-triagem-alerta/) — Transforma um alerta cru em uma nota de triagem padronizada com impacto, hipótese inicial, ação imediata e escalonamento.
- [triagem-de-pods](./triagem-de-pods/) — Analisa um snapshot de cluster Kubernetes e identifica pods problemáticos com causa provável, evidência e próxima ação do plantão.
