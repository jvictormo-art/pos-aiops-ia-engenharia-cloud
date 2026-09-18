# O que aconteceu com as skills durante este projeto

O ticket pede para registrar o que disparou sozinho, o que foi chamado na mão, o que apareceu onde não devia, e o que precisou ser reexplicado. A resposta mais honesta começa por um fato estrutural que não estava óbvio até eu ir verificar.

---

## Fato estrutural: nenhuma das duas disparou sozinha — e não podia

`metacortex-manifest` (Ticket 01) e `metacortex-triage` (Ticket 02) existem como arquivos `SKILL.md` dentro das pastas de entrega de cada ticket (`ticket-01-padrao-de-manifests/skill/SKILL.md`, `ticket-02-triagem-no-cluster/skill/SKILL.md`). Verifiquei o diretório do projeto (`.claude/`) e não existe nenhum `.claude/skills/<nome>/SKILL.md` — o local que este ambiente de agente escaneia para descobrir skills invocáveis automaticamente. As duas nunca apareceram na lista de skills disponíveis desta sessão, em nenhum dos quatro tickets.

**Consequência prática**: a premissa do ticket ("você entra neste ticket com as duas skills instaladas") descreve a intenção documentada, não o estado real do ambiente. As skills foram *escritas* como se fossem para ser instaladas — mas instalar, no sentido de registrar para disparo automático, é um passo que nunca aconteceu neste repositório. Isso por si só é uma descoberta que vale para a curadoria: documentar o comportamento de uma skill não é o mesmo que publicá-la onde o sistema a reconhece.

---

## O que foi chamado na mão

`metacortex-manifest`, Modo 1 (escrita), foi usado deliberadamente neste ticket para gerar os manifests do `kube-news` (`manifests-kube-news/`). O processo seguiu os passos do próprio `SKILL.md` lido manualmente:

1. "Ler o projeto" — abri a imagem real (`fabricioveronez/kube-news:v1.0.0`) e o código-fonte dentro dela (`server.js`, `models/post.js`, `system-life.js`) para descobrir a porta real (8080), os endpoints de saúde reais (`/health`, `/ready`) e as variáveis de ambiente de banco reais (`DB_HOST`, `DB_USERNAME`, etc.) — o mesmo espírito de "ler o projeto, não adivinhar" do Ticket 01, só que a fonte de leitura foi a imagem Docker em vez de um repositório GitHub
2. Decisões obrigatórias do Passo 2 foram respondidas antes de escrever o YAML (documentado nos comentários do próprio `deployment.yaml`)
3. O template do Passo 3 foi seguido campo a campo
4. O Passo 4 (validação) foi executado exatamente como o `SKILL.md` prescreve: `trivy config` e `check-manifest.py` rodaram contra os manifests gerados, e as duas falhas mecânicas encontradas (`KSV-0125` — registry não confiável, e `3.7` — mesma causa) foram tratadas como exceção documentada, não como bug a esconder (ver `manifests-kube-news/` e a nota no `deployment.yaml`)

Isso foi uma invocação manual completa — abri o arquivo, segui cada passo, não pulei a validação.

---

## O que apareceu onde não devia — o conhecimento vazou, o procedimento não foi chamado

`metacortex-triage` nunca foi aberto nem seguido como procedimento neste ticket. Mas o conteúdo dela apareceu de outro jeito: a tabela de decisão STATUS → camada do Ticket 02 (`OOMKilled` → container, `ImagePullBackOff` → registry, `Running` sem endpoint → roteamento) é exatamente o que determinou **quais campos o dashboard precisava mostrar**. O campo `MOTIVO` na tabela de Pods, a distinção Service/EndpointSlice, a ordem em que os painéis aparecem — tudo isso é a tabela de decisão da triagem, traduzida de "o que o operador deve investigar em qual ordem" para "o que a tela deve mostrar sem que o operador precise perguntar".

Isso não é errado — é o resultado esperado de ter passado pelo Ticket 02 antes deste. Mas é uma linha tênue que vale registrar: o conhecimento de uma skill pode informar o *design* de uma ferramenta nova sem que a skill seja de fato *invocada*. Se alguém perguntasse "a skill de triagem rodou neste ticket?", a resposta correta é não — mas "o que a skill de triagem sabe influenciou o que foi construído?" é sim. São perguntas diferentes e a primeira pode enganar quem está tentando entender o que aconteceu.

---

## O que precisou ser reexplicado — para mim mesmo, não para um agente externo

Como nenhuma skill dispara automaticamente, o invariante "só lê" não veio de graça neste ticket. Nos Tickets 02 e 03, esse invariante já estava documentado e a garantia estrutural (grep por verbos de escrita) já tinha sido inventada. Neste ticket, precisei **recriar** a mesma garantia do zero para o código do dashboard (`ClusterReader` só chama `list_*`/`get_*`, verificado por `grep -E '\.(create|patch|delete|replace)_'`) — não porque uma skill me exigiu isso automaticamente, mas porque eu já sabia, dos tickets anteriores, que essa é a forma certa de garantir a propriedade. O padrão se repetiu por hábito adquirido, não por imposição de uma skill ativa.

**Se as skills estivessem de fato instaladas em `.claude/skills/`**, a expectativa seria: ao pedir "escreva os manifests do kube-news", `metacortex-manifest` dispararia sozinha pela descrição ("Use ao pedir para gerar, escrever, revisar ou validar um manifest"); e ao construir uma ferramenta de leitura de cluster, não haveria disparo de `metacortex-triage` (ela é sobre investigar causa, não sobre desenhar tela) — o que está correto e seria o comportamento esperado pela matriz de roteamento do Ticket 02. A ausência de registro não invalida a matriz — só significa que ela nunca foi posta à prova neste ambiente específico.

---

## Registro para quem for instalar isso de fato

Se este parque quiser que as skills disparem sozinhas em sessões futuras, o próximo passo é mover `ticket-01-padrao-de-manifests/skill/` e `ticket-02-triagem-no-cluster/skill/` (ou cópias deles) para `.claude/skills/metacortex-manifest/` e `.claude/skills/metacortex-triage/` na raiz do repositório onde os operadores realmente trabalham. Documentar o comportamento e publicá-lo para descoberta automática são dois passos diferentes, e só o primeiro foi dado até aqui.
