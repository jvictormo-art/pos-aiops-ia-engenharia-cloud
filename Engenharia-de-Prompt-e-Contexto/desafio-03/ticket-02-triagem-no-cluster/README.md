# Ticket 02 — Triagem no Cluster

Este documento mapeia e aponta onde está cada item solicitado no **Entregue** do Ticket 02:

| Item do Entregue | Arquivo / Diretório | Descrição |
|---|---|---|
| **Skill de Triagem** | [`skill/SKILL.md`](./skill/SKILL.md) | Skill `metacortex-triage` (método de 5 camadas, estritamente read-only) |
| **Triagem Chamado 01** | [`saida/triagem-chamado-01-nyx-prod.md`](./saida/triagem-chamado-01-nyx-prod.md) | Diagnóstico completo: OOMKilled (Exit Code 137, limits.memory baixo) |
| **Triagem Chamado 02** | [`saida/triagem-chamado-02-orion-stg.md`](./saida/triagem-chamado-02-orion-stg.md) | Diagnóstico completo: ImagePullBackOff (tag inexistente no registry) |
| **Triagem Chamado 03** | [`saida/triagem-chamado-03-nyx-stg.md`](./saida/triagem-chamado-03-nyx-stg.md) | Diagnóstico completo: 503 com pods Running (discrepância Service × labels) |
| **Matriz de Roteamento** | [`saida/matriz-roteamento.md`](./saida/matriz-roteamento.md) | Desambiguação de disparo entre `metacortex-manifest` e `metacortex-triage` |
| **Comparação Com/Sem Skill** | [`saida/comparacao-com-sem-skill.md`](./saida/comparacao-com-sem-skill.md) | Benchmarking de tool calls, hipóteses e tempo em dois incidentes |
| **Origem e Curadoria** | [`origem-e-curadoria.md`](./origem-e-curadoria.md) | Gênese do método, garantia estrutural de não-escrita e limites |
| **Manifests dos Laboratórios** | [`manifests/`](./manifests/) | Manifests aplicados no cluster `kind-metacortex-lab` para os 3 chamados |

---
- **Agente:** Claude Code
- **Modelos:** Claude Opus 4.8 / Claude Sonnet 4.6
