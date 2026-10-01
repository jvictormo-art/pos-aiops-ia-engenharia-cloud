# Ticket 03 — Inventário de VM

Este documento mapeia e aponta onde está cada item solicitado no **Entregue** do Ticket 03:

| Item do Entregue | Arquivo / Diretório | Descrição |
|---|---|---|
| **Proposta Aprovada** | [`spec/proposta.md`](./spec/proposta.md) | Escopo, critérios de aceite e definição do problema |
| **Spec de Decisões Técnicas** | [`spec/spec-decisoes.md`](./spec/spec-decisoes.md) | Decisões fechadas pré-código (Python, Paramiko, comandos SSH, portas) |
| **Spec de Comportamento** | [`spec/spec-comportamento.md`](./spec/spec-comportamento.md) | Comportamento esperado da CLI, argumentos e formatação de saídas |
| **Tarefas de Implementação** | [`spec/tarefas.md`](./spec/tarefas.md) | Sequência ordenada de tarefas (T1 a T8) e critérios de entrega |
| **Arquivo Final de Encerramento** | [`spec/arquivo-final.md`](./spec/arquivo-final.md) | Verificação dos critérios de aceite e correções de spec |
| **Código da Ferramenta** | [`ferramenta/inventario.py`](./ferramenta/inventario.py) | CLI agentless via SSH com saídas em JSON e Markdown |
| **Baseline Declarativo** | [`ferramenta/baseline.yaml`](./ferramenta/baseline.yaml) | Regras de conformidade do parque da Metacortex |
| **Ambiente de Testes** | [`ferramenta/Dockerfile.test-vm`](./ferramenta/Dockerfile.test-vm) | Dockerfile Ubuntu com systemd ativo para testes de laboratório |
| **Evidências de Execução** | [`saida/evidencia/`](./saida/evidencia/) | Execuções reais registradas em JSON e Markdown |
| **Documento de Curadoria** | [`saida/curadoria.md`](./saida/curadoria.md) | Lições aprendidas, nuances de boot e divergências tratadas |

---
- **Agente:** Claude Code
- **Modelos:** Claude Opus 4.8 / Claude Sonnet 4.6
