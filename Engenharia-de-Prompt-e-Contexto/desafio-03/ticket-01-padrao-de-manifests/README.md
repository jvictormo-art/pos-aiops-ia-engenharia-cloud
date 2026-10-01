# Ticket 01 — Padrão de Manifests da Metacortex

Este documento mapeia e aponta onde está cada item solicitado no **Entregue** do Ticket 01:

| Item do Entregue | Arquivo / Diretório | Descrição |
|---|---|---|
| **Skill de Manifests** | [`skill/SKILL.md`](./skill/SKILL.md) | Skill `metacortex-manifest` com os modos de escrita e conferência |
| **Script Mecânico** | [`skill/check-manifest.py`](./skill/check-manifest.py) | Script de validação mecânica das regras que o Trivy não cobre |
| **Matriz de Regras** | [`skill/regras-buckets.md`](./skill/regras-buckets.md) | Mapeamento regra × balde (trivy, script, instrução, fora) |
| **Manifesto Barrado Auditado** | [`saida/conferencia-nyx-barrado.md`](./saida/conferencia-nyx-barrado.md) | Relatório de conferência do `nyx-barrado.yaml` (12 falhas + 1 aviso) |
| **YAML Defeituoso de Teste** | [`saida/nyx-barrado.yaml`](./saida/nyx-barrado.yaml) | Manifesto com falhas obrigatórias e proibidas para validação |
| **Manifests Conformes (Orion)** | [`saida/manifests-orion/`](./saida/manifests-orion/) | Conjunto completo gerado no padrão (deployment, service, secret, etc.) |
| **Origem e Curadoria** | [`origem-e-curadoria.md`](./origem-e-curadoria.md) | Memorial do fluxo percorrido, falso positivo KSV-0125 e decisões |
| **Padrão da Metacortex** | [`Padrao de Manifests da Metacortex.md`](./Padrao%20de%20Manifests%20da%20Metacortex.md) | Documento-fonte corporativo de regras de manifests |

---
- **Agente:** Claude Code
- **Modelos:** Claude Opus 4.8 / Claude Sonnet 4.6
