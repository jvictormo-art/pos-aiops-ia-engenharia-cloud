# Spec de Decisões Técnicas — metacortex-dashboard

Cinco decisões abertas. Nenhuma tem resposta única — cada uma é registrada com pelo menos duas alternativas descartadas e o que se ganha e o que se perde em cada caminho.

---

## Decisão 1 — Linguagem e stack

**Escolhido**: Python 3.10+ com [Textual](https://textual.textualize.io/) (TUI — interface de terminal).

**Por quê**: quem mantém isso é um time de infraestrutura que, ao longo deste mesmo desafio, já demonstrou fluência em Python (a skill `metacortex-manifest`, o `check-manifest.py`, a ferramenta `inventario.py` do Ticket 03 são todos Python). Uma TUI abre instantaneamente no mesmo terminal onde o operador já roda `kubectl` — sem trocar de janela, sem esperar um servidor subir, sem abrir navegador. Isso combina diretamente com o objetivo do ticket: encurtar os primeiros dez minutos de reconhecimento, não adicionar uma etapa.

### Alternativa descartada A — Go + client-go + TUI (bubbletea/tview)

**O que se ganha**: binário único, estático, sem dependência de interpretador ou pacotes instalados na estação do operador — `go build` e distribui um arquivo. Performance superior e tipagem mais forte contra a API do Kubernetes. `client-go` é a mesma biblioteca que o próprio `kubectl` usa internamente, o que dá confiança de que o comportamento de autenticação/contexto está alinhado com a ferramenta que todos já usam.

**O que se perde**: o time que mantém isso hoje não escreve Go — mantém Python em todos os outros artefatos deste desafio. Trocar de stack aqui significa um segundo conjunto de convenções, um segundo pipeline de build, uma segunda curva de aprendizado para quem for dar manutenção. Para uma ferramenta interna de baixo tráfego (um operador por vez, algumas centenas de objetos), o ganho de performance do Go não paga o custo de fragmentar a stack do time.

### Alternativa descartada B — aplicação web (backend Python + frontend HTML/JS, aberta no navegador local)

**O que se ganha**: mais liberdade visual (tabelas ricas, cores, potencial de adicionar links e drill-down mais tarde), paradigma mais familiar para desenvolvedores web, caminho natural se algum dia o dashboard precisar ser compartilhado entre múltiplos operadores.

**O que se perde**: o ticket descreve a ferramenta como algo que "roda na máquina de quem opera" — uma aplicação web precisa de um processo servidor rodando e um navegador aberto apontando para `localhost`, dois processos coordenados em vez de um. Isso adiciona uma etapa (abrir o navegador, confiar que a porta local não está em conflito) exatamente onde o ticket pede menos etapas. Backend e frontend como projetos separados também dobra a superfície de manutenção para um time que hoje escreve scripts e ferramentas de linha de comando, não aplicações full-stack.

---

## Decisão 2 — Como falar com a API do Kubernetes

**Escolhido**: biblioteca cliente oficial Python (`kubernetes` no PyPI, gerada a partir da OpenAPI spec do projeto).

**Por quê**: ela resolve autenticação, contexto e tipagem do jeito que o ticket pede que seja resolvido — uma vez, corretamente, sem reimplementar. `kubernetes.config.load_kube_config()` lê o `current-context` do kubeconfig e lida nativamente com certificado-cliente, token, e plugins `exec` (usados por autenticação de nuvem) sem código adicional. Erros vêm como `ApiException` com `status` HTTP inspecionável — essencial para diferenciar programaticamente "cluster fora do ar" (erro de conexão) de "permissão negada" (403) de "recurso não encontrado" (404), que é exatamente o comportamento que os critérios de aceite exigem.

### Alternativa descartada A — `kubectl` como subprocesso, lendo a saída em JSON

**O que se ganha**: zero dependência nova — todo operador já tem `kubectl` instalado, e a saída `-o json` é um contrato estável e testado pela própria comunidade Kubernetes. Não exige aprender a API gerada (que é grande e, em partes, verbosa).

**O que se perde**: cada chamada gasta o custo de um processo novo (mais lento que uma chamada de biblioteca em memória). Mais importante: o erro de `kubectl` chega como texto em stderr mais um código de saída — para diferenciar "cluster inalcançável" de "403 Forbidden neste recurso" seria necessário fazer *string matching* na mensagem de erro do kubectl, que muda de formato entre versões e é exatamente o tipo de acoplamento frágil que o Ticket 02 já identificou como antipadrão de triagem (ler texto de erro para decidir causa, em vez de ler o dado estruturado). E se a decisão de atualização evoluir para watch/informer no futuro, subprocess não tem caminho — teria que reimplementar do zero.

### Alternativa descartada B — HTTP direto ao apiserver

**O que se ganha**: controle total sobre a requisição, nenhuma dependência do `kubectl` nem do cliente gerado, superfície mínima.

**O que se perde**: seria necessário reimplementar manualmente a leitura do kubeconfig para os múltiplos tipos de autenticação que ele pode conter — certificado cliente, token estático, e plugins `exec` (comuns em provedores de nuvem, que executam um binário externo para obter um token temporário). Isso é precisamente o trabalho que o ticket cita como caro e específico ("como ela conversa com o host remoto... é decisão sua, com consequência") — e reimplementá-lo mal significa um bug de autenticação sutil e recorrente, exatamente o tipo de manutenção cara que a proposta busca evitar ao delegar essa responsabilidade a uma biblioteca mantida pelo próprio projeto Kubernetes.

---

## Decisão 3 — Estratégia de atualização da tela

**Escolhido**: consulta em intervalo fixo (polling, a cada 5 segundos) na primeira fatia.

**Por quê**: é o ponto de equilíbrio entre "a tela precisa estar razoavelmente atual" e "o código precisa ser simples o suficiente para validar rápido contra um cluster real". Um poll que falha simplesmente tenta de novo no próximo ciclo — não há estado de conexão para recuperar.

### Alternativa descartada A — consulta sob demanda (só busca quando o operador pede)

**O que se ganha**: carga mínima possível sobre o apiserver — só uma requisição por ação explícita do operador. Implementação mais simples ainda que o polling.

**O que se perde**: isso contraria a própria motivação do ticket. Se o operador precisa apertar "atualizar" para ver cada mudança, a ferramenta não é mais rápida que rodar os mesmos 6-10 `kubectl get` um por um — só troca o lugar onde os comandos são digitados. O valor de "assistir o estado se assentar" (por exemplo, ver os pods saindo de `CrashLoopBackOff` depois de uma correção) se perde.

### Alternativa descartada B — watch/informer (observar mudanças e receber eventos conforme acontecem)

**O que se ganha**: atualização quase em tempo real, menor volume total de dados trafegados ao longo do tempo (só deltas, não o estado completo repetido), e é a arquitetura "correta" para ferramentas de observação de longa duração — é o que `k9s` e o próprio `kubectl get -w` fazem.

**O que se perde**: é, de longe, a peça de maior complexidade e maior risco da primeira fatia. Um watch exige rastrear `resourceVersion` por tipo de recurso, tratar o erro `410 Gone` (quando a versão observada expirou e é preciso re-sincronizar do zero), reconectar com backoff quando a conexão cai, e multiplexar cinco streams independentes (pods, deployments, services, endpointslices, eventos) simultaneamente. Um loop de reconexão de watch malfeito, rodando contra um apiserver de produção, é uma versão auto-inflingida do próprio problema que o ticket quer resolver — silenciosamente parar de atualizar e ninguém notar. Fica registrado como a evolução natural da segunda fatia, depois que a versão com polling for validada em uso real.

---

## Decisão 4 — Endpoints (`v1`) ou EndpointSlice (`discovery.k8s.io/v1`)

**Escolhido**: `EndpointSlice`.

**Por quê**: `v1/Endpoints` está em rota de aposentadoria — a evidência disso apareceu sem ser buscada: `kubectl get endpoints -n nyx-dev` durante a coleta de evidência deste próprio ticket imprimiu `Warning: v1 Endpoints is deprecated in v1.33+; use discovery.k8s.io/v1 EndpointSlice`. Construir uma ferramenta nova sobre uma API que o próprio Kubernetes já avisa para não usar é comprar dívida técnica no primeiro dia.

### Alternativa descartada A — manter `v1/Endpoints`

**O que se ganha**: um objeto por Service (mapeamento 1:1 simples), API mais antiga e mais estável em termos de forma (não sofreu mudanças de schema recentes), e é o objeto que o próprio exemplo do ticket usa para ilustrar o problema do Chamado 3.

**O que se perde**: durabilidade. `Endpoints` já está marcado como deprecated a partir do Kubernetes v1.33 nos avisos do próprio `kubectl`; construir a leitura do dashboard sobre ele significa que a próxima major version pode remover o suporte, obrigando uma reescrita não planejada.

### Alternativa descartada B — consultar ambos e escolher o que responder primeiro

**O que se ganha**: comportamento correto em clusters antigos (sem EndpointSlice habilitado) e novos ao mesmo tempo.

**O que se perde**: complexidade dobrada para um cenário que não existe no parque da Metacortex — `EndpointSlice` é GA desde o Kubernetes 1.21 e está habilitado por padrão em qualquer cluster suportado hoje. Cobrir os dois formatos é engenharia para um problema hipotético, não para o cluster real. `EndpointSlice` sozinho basta.

**Nuance registrada**: um Service pode ter múltiplos objetos `EndpointSlice` (o Kubernetes particiona endereços em fatias de até 100 por padrão). O dashboard soma os endereços prontos (`endpoints[].conditions.ready`) através de todas as fatias do mesmo Service antes de decidir "tem endpoint" ou "não tem" — não basta olhar a primeira fatia.

---

## Decisão 5 — Quanto do escopo entra na primeira fatia

**Escolhido**: exatamente os 5 objetos citados como mínimo no ticket (namespaces, pods, deployments, services+endpoints, eventos), com filtro por namespace e busca por nome. Nada de métricas de CPU/memória, nada de PodDisruptionBudget, nada de ação a partir da tela.

### Alternativa descartada A — fatia mais fina ainda: só pods

**O que se ganha**: caminho mais rápido para validar "conecta no contexto corrente e desenha algo real na tela" antes de investir nos outros quatro tipos de objeto.

**O que se perde**: um dashboard só de pods não consegue mostrar o cenário do Chamado 3 (Service sem endpoint por seletor divergente) nem o do `orion-web` (Deployment com `unavailableReplicas` e `readyReplicas` ausente) — que são os próprios exemplos que o ticket usa para justificar a ferramenta. Entregar só pods falharia os critérios de aceite, que listam os 5 objetos como "no mínimo", não como aspiração.

### Alternativa descartada B — fatia mais larga: incluir métricas (CPU/memória via metrics-server) e PDB

**O que se ganha**: resposta mais completa, inclusive um começo de resposta para a pergunta da Niobe sobre quanto o parque custa a mais por estar fora do padrão.

**O que se perde**: `metrics-server` é um componente opcional do cluster, não garantido — e de fato **não está instalado** no cluster `kind-metacortex-lab` usado como evidência deste ticket. Construir uma feature que quebra silenciosamente quando metrics-server está ausente contradiz o próprio requisito de "comportar-se quando o ambiente não colabora" — e o jeito mais simples de não violar esse requisito é não depender de um componente que pode não existir. Fica registrado como escopo futuro, não como promessa desta versão.

---

## Como a garantia de leitura fica visível no projeto

O mesmo princípio do Ticket 02: a garantia não pode depender de "o agente decidiu não escrever" — precisa ser estrutural.

**No código**: a classe `ClusterReader` (`dashboard/k8s_reader.py`) só importa e chama métodos `list_*` e `get_*` da API do Kubernetes. Nenhum método `create_*`, `patch_*`, `delete_*`, `replace_*` aparece em nenhum lugar do código-fonte — não porque foram evitados por convenção, mas porque a única classe que fala com a API do cluster não os referencia.

**Verificável automaticamente**: `spec/tarefas.md` inclui uma tarefa de validação que faz `grep` no código-fonte por padrões de método de escrita (`\.create_`, `\.patch_`, `\.delete_`, `\.replace_`) e falha o build se encontrar qualquer ocorrência fora de comentários/docstrings. Isso transforma "a ferramenta só lê" de promessa em algo que um pipeline de CI recusa a violar silenciosamente.
