# Catálogo de prompts

Coleção de prompts em Markdown organizados por categoria/área de domínio. Cada prompt vive em sua própria pasta, contendo o arquivo `prompt.md` (texto puro, pronto para copiar e colar) e um `README.md` com metadados, variáveis e exemplos de uso.

Este repositório faz parte do material dos projetos da pós-graduação em AIOps e Inteligência Artificial com Engenharia Cloud: [pos.veronez.io/pos-aiops](https://pos.veronez.io/pos-aiops/).

Convenções de estrutura, nomenclatura e manutenção estão em [`CLAUDE.md`](./CLAUDE.md).

## Como usar

1. Navegar até a categoria de interesse.
2. Abrir o `README.md` do prompt para entender objetivo, variáveis esperadas e limitações.
3. Copiar o conteúdo do `prompt.md` e substituir os placeholders `{{nome_variavel}}` pelos valores desejados.

## Adicionando um prompt

Use o slash command [`/catalogar`](./.claude/commands/catalogar.md) passando o texto do prompt como argumento. Ele analisa, propõe organização (categoria, slug, frontmatter) e, após sua aprovação, escreve os arquivos e atualiza os índices — sem commitar. Convenções completas em [`CLAUDE.md`](./CLAUDE.md).

## Categorias

### [Desenvolvimento](./desenvolvimento/)

Escrita, revisão e refatoração de código, design de APIs e arquitetura, debugging, testes e documentação técnica.

_Nenhum prompt cadastrado ainda._

### [DevOps](./devops/)

Pipelines de CI/CD, containers, orquestração, infraestrutura como código, observabilidade, SRE e segurança operacional.

- [analisar-backpressure-barramento](./devops/analisar-backpressure-barramento/) — Recebe um cenário de sobrecarga de barramento de eventos e produz análise comparativa de estratégias de backpressure com recomendação fundamentada em trade-offs.
- [diagnosticar-causa-raiz-incidente](./devops/diagnosticar-causa-raiz-incidente/) — Analisa artefatos heterogêneos de um incidente (config, métricas e logs) e produz diagnóstico de causa-raiz com linha do tempo, cadeia causal, mitigação imediata e correção definitiva.
- [endurecer-networkpolicy-kubernetes](./devops/endurecer-networkpolicy-kubernetes/) — Transforma uma NetworkPolicy permissiva em uma política endurecida com default-deny, liberando apenas fluxos explicitamente legítimos, com verificação iterativa.
- [migrar-pipeline-batch-para-event-driven](./devops/migrar-pipeline-batch-para-event-driven/) — Cadeia de três prompts encadeados para diagnosticar, planejar e executar a migração de um pipeline batch para um modelo event-driven de forma incremental e reversível.
- [nota-de-triagem-alerta](./devops/nota-de-triagem-alerta/) — Transforma um alerta cru em uma nota de triagem padronizada com impacto, hipótese inicial, ação imediata e escalonamento.
- [triagem-de-pods](./devops/triagem-de-pods/) — Analisa um snapshot de cluster Kubernetes e identifica pods problemáticos com causa provável, evidência e próxima ação do plantão.

### [Produtividade](./produtividade/)

Organização pessoal, gestão de tempo e tarefas, rotina, hábitos, foco e decisões sobre fluxo de trabalho individual.

_Nenhum prompt cadastrado ainda._

### [Finanças](./financas/)

Orçamento, investimentos, planejamento financeiro, impostos e apoio a decisões financeiras.

_Nenhum prompt cadastrado ainda._

### [Criação de Conteúdo](./criacao-conteudo/)

Roteiros, artigos, posts para redes sociais, material didático e copy de divulgação.

_Nenhum prompt cadastrado ainda._

<!--
Ao adicionar um prompt, substituir "Nenhum prompt cadastrado ainda" pela lista:

- [nome-do-prompt](./<slug-da-categoria>/<slug-do-prompt>/) — o que o prompt faz, em uma linha.
-->

## Contribuindo

Antes de adicionar ou alterar um prompt, revisar [`CLAUDE.md`](./CLAUDE.md) — a seção **Manutenção da documentação** lista todos os arquivos que precisam ser atualizados junto com a mudança (este índice incluso).
