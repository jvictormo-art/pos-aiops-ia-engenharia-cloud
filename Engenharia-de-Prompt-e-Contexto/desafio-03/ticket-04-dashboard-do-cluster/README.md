# Ticket 04 — Dashboard do Cluster

Este documento mapeia e aponta onde está cada item solicitado no **Entregue** do Ticket 04:

| Item do Entregue | Arquivo / Diretório | Descrição |
|---|---|---|
| **Proposta Aprovada** | [`spec/proposta.md`](./spec/proposta.md) | Escopo, problema dos 10 minutos de reconhecimento e corte multicluster |
| **Spec de Decisões Técnicas** | [`spec/spec-decisoes.md`](./spec/spec-decisoes.md) | Decisões de stack (Textual), cliente oficial, polling e EndpointSlice |
| **Spec de Comportamento** | [`spec/spec-comportamento.md`](./spec/spec-comportamento.md) | Layout, tratamento de ausência vs vazio e cenários de falha |
| **Tarefas de Implementação** | [`spec/tarefas.md`](./spec/tarefas.md) | Sequência de implementação (T1 a T8) e critérios de aceite |
| **Arquivo Final de Encerramento** | [`spec/arquivo-final.md`](./spec/arquivo-final.md) | Verificação contra cluster real e as 5 correções de spec |
| **Interface TUI** | [`dashboard/app.py`](./dashboard/app.py) | Aplicação em Textual com 5 painéis, filtro e busca |
| **Leitor Kubernetes Read-Only** | [`dashboard/k8s_reader.py`](./dashboard/k8s_reader.py) | Camada desacoplada com garantia estrutural de leitura |
| **Dependências** | [`dashboard/requirements.txt`](./dashboard/requirements.txt) | Pacotes necessários (`textual`, `kubernetes`) |
| **Manifests Kube-News** | [`manifests-kube-news/`](./manifests-kube-news/) | Workload real gerado via skill para alimentar o cluster |
| **Evidências Visuais (SVGs)** | [`evidencia/`](./evidencia/) | 8 capturas em SVG cobrindo todos os cenários normais e degradados |
| **Curadoria Técnica** | [`saida/curadoria.md`](./saida/curadoria.md) | Análise de correções, bugs de desserialização e mTLS |
| **Skills no Projeto** | [`saida/skills-neste-projeto.md`](./saida/skills-neste-projeto.md) | Reflexão sobre ciclo de vida e descoberta de skills |

---
- **Agente:** Claude Code
- **Modelos:** Claude Opus 4.8 / Claude Sonnet 4.6
