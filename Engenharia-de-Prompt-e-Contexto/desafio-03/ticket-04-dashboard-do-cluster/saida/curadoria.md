# Curadoria — metacortex-dashboard

---

## Onde o documento precisou ser corrigido durante a implementação

As cinco correções estão detalhadas em `spec/arquivo-final.md`. Resumo:

1. Versão mínima do Python (3.10 → 3.9, para bater com o ambiente real)
2. O cliente tipado do Kubernetes quebra ao ler `EndpointSlice` com `endpoints: null` — exatamente o dado que o próprio ticket avisou ser traiçoeiro, só que o efeito colateral (derrubar a lista inteira, não só o item afetado) não estava previsto
3. `initContainerStatuses` precisa ser lido antes de `containerStatuses` — o spec só cobria o caso sem initContainer
4. Credencial inválida em cluster com mTLS falha na camada TLS, não como HTTP 401 — o spec assumia autenticação por token
5. Bug estrutural de `DuplicateIds` na primeira versão da tela (correção de código, não de spec)

---

## O que o agente entendeu diferente do que foi escrito

Como esta sessão escreveu o spec e implementou o código na sequência, a divergência não é entre "duas pessoas", mas entre a intenção registrada no momento de escrever o spec e o que só ficou visível no momento de codificar contra dados reais. Três pontos concretos:

### 1. "Distinguir ausência de vazio" foi entendido corretamente na intenção, mas não na mecânica

O `spec-comportamento.md` está certo sobre o **resultado visual** esperado (ausência e vazio colapsam para o mesmo texto na tela). O que a escrita do spec não anticipou é que **produzir esse resultado correto exige desviar do caminho "normal" da biblioteca** — o cliente tipado não deixa o código nem chegar ao ponto de decidir "isso é null, mostro sem endpoint", porque ele já quebra antes, na desserialização. A intenção estava certa; o texto do spec tratava isso como um "if/else" trivial na camada de apresentação, quando na prática exigiu reescrever a própria chamada de rede.

### 2. "Painel independente" foi implementado mais rigidamente do que o texto sugeria

`spec-comportamento.md` diz que "cada painel... trata seu próprio erro de forma independente". Ao implementar, isso significou literalmente quatro chamadas de rede separadas por ciclo de atualização (uma por tipo de objeto), cada uma com seu próprio bloco de tratamento de erro — não uma chamada agregada com pós-processamento. O spec não especificava esse nível de granularidade; o código escolheu o caminho mais simples de raciocinar (uma falha, um efeito, sem lógica de agregação de erros parciais), e isso bateu por acaso com o que o cenário de RBAC parcial exige. Se o spec tivesse pedido uma única chamada agregada (por exemplo, um `list` genérico de múltiplos tipos), o comportamento de degradação parcial exigiria desmontar uma resposta combinada — mais complexo e mais difícil de testar isoladamente.

### 3. O `_meta` interno do Ticket 03 (`inventario.py`) não se repetiu aqui — e isso foi uma escolha consciente, não um esquecimento

O Ticket 03 usa um padrão de campo `_meta` para carregar informação interna (ex: `systemd_disponivel`) sem misturar com os dados de saída. O dashboard não precisou desse padrão porque a informação equivalente (painel restrito por RBAC) já tem seu próprio canal — o campo `tipo_erro` do `Resultado`. Vale registrar que a ausência não é inconsistência entre os dois projetos: é o mesmo princípio (separar dado de metadado de erro) resolvido de forma diferente porque a forma dos dois problemas é diferente.

---

## Justificativa estendida das decisões abertas

As cinco decisões abertas do ticket — linguagem/stack, acesso à API, estratégia de atualização, Endpoints vs. EndpointSlice, e escopo da primeira fatia — estão em `spec/spec-decisoes.md`, cada uma com pelo menos duas alternativas descartadas e o que se ganha e o que se perde em cada caminho. Esse arquivo é o documento de curadoria dessas decisões; não duplico o conteúdo aqui.

O que acrescento nesta curadoria é **o que a implementação confirmou ou contestou** de cada decisão, depois de rodar contra o cluster real:

- **Linguagem/stack (Python + Textual)**: confirmada. A TUI rodou dentro do mesmo terminal sem fricção; o único atrito real foi a versão do Python (item 1 das correções), não a escolha da stack em si.
- **Cliente oficial vs. subprocess/HTTP direto**: a decisão de usar o cliente oficial *quase* foi contestada pelo bug do `EndpointSlice` (item 2) — mas a correção (usar `_preload_content=False` para pegar o JSON bruto numa chamada específica) é possível justamente **porque** é o cliente oficial: ele expõe esse escape hatch de baixo nível quando o modelo tipado falha. Um cliente HTTP feito à mão não teria esse problema de tipagem, mas teria todos os outros (auth, contexto) que a Decisão 2 already descartou. A decisão se mantém, com uma nuance a mais registrada.
- **Polling em vez de watch**: confirmada sem ressalvas — nenhum dos cinco cenários de falha testados exigiu lógica de reconexão de watch, e a simplicidade do polling permitiu isolar e corrigir os cinco problemas reais (lista acima) rápido, um por vez.
- **EndpointSlice em vez de Endpoints**: confirmada, e a durabilidade do argumento apareceu de forma extra: o próprio `kubectl` emitiu o aviso de depreciação durante a coleta de evidência deste ticket, sem eu precisar procurar por ele.
- **Escopo da primeira fatia (sem métricas)**: confirmada — o cluster de evidência não tem `metrics-server` instalado, validando na prática o argumento de que depender dele seria construir algo que quebra no ambiente real disponível.
