# Curadoria — metacortex-inventario

---

## Onde o documento precisou ser corrigido durante a implementação

### Idempotência tem granularidade errada no spec original

O spec dizia "execução repetida devolve o mesmo retrato". Durante o teste, o inventário de serviços variou entre duas execuções com 11 segundos de intervalo — o systemd do container ainda estava completando o boot na primeira execução.

**O que eu escrevi**: "execução repetida devolve o mesmo retrato"  
**O que deveria dizer**: "execução repetida devolve o mesmo veredito para cada regra — o inventário bruto pode refletir o estado no instante exato da coleta, que pode mudar em hosts recém-reiniciados"

A conformidade e o resumo foram idênticos entre os dois runs. O invariante real da ferramenta é sobre o **veredito**, não sobre o inventário bruto. O arquivo-final registra isso.

---

## O que o agente entendeu diferente do que eu escrevi

### 1. `somente_rede_interna` quando a porta não está escutando

O ticket diz que a ferramenta deve checar portas em escuta. Quando `node_exporter` não está instalado, a porta 9100 simplesmente não aparece em `ss -tlnp`. O spec não especificava o comportamento para esta situação.

**O que o agente fez**: interpretou "9100 não encontrada em escuta" como `conforme`, com a lógica de que uma porta que não está aberta não pode estar exposta indevidamente.

**Por que faz sentido**: o desvio seria a porta estar exposta publicamente. Não estar escutando não é uma violação da regra `somente_rede_interna` — é simplesmente o processo que deveria estar na porta que está faltando (coberto por `servicos.ativos`). As duas regras são ortogonais.

**Pendência**: o spec deveria ter explicado este caso explicitamente. Foi adicionado ao arquivo-final.

### 2. Conformidade de `servicos.ativos` quando o serviço existe mas não está `active`

chrony estava em estado `activating` (iniciando) durante os testes. O systemctl `list-units --state=active` não inclui unidades em `activating`. Resultado: chrony aparece como "ausente" → desvio (alto).

**O que o agente fez**: marcou como desvio — correto. Um serviço que está iniciando não está `active` e o baseline exige `active`.

**Nuance que o spec não cobriu**: em um host recém-reiniciado, serviços transitoriamente em `activating` podem gerar falsos positivos temporários. Para auditoria contínua, a ferramenta deveria ser rodada em hosts estáveis. O spec não especificou isso.

### 3. Chave SSH com `(sem comentário)` vs desvio crítico

O spec dizia que chaves sem comentário deveriam ser tratadas como "não reconhecidas". O código implementou isso como desvio crítico (comentário vazio não contém "metacortex-platform"). 

**Por que é correto**: chave sem comentário é chave cuja origem não pode ser verificada — é exatamente o problema que o Roster quer detectar. Chave de origem desconhecida é tão problemática quanto chave de origem errada.

### 4. O que o agente corrigiu sem ser pedido

**Formatação de booleanos no Markdown**: o Python renderiza `False` com F maiúsculo em f-strings. O código inicial produzia `| false | True (1024M) |` com inconsistência de capitalização. Corrigido adicionando `_fmt()` que normaliza booleans para `true`/`false` e `None` para `null` — consistente com JSON e com o exemplo do ticket.

**Deduplicação da seção `## Conforme`**: sem deduplicação, `servicos.proibidos` aparecia duas vezes na seção Conforme (uma por cada socket proibido ausente). O código foi corrigido para listar nomes de regras únicos, consistente com o exemplo do ticket.

---

## O que o método fixou (e o que ficou para o agente decidir)

**O spec fixou:**
- Quais dados coletar e qual comando para cada um (especificidade: sem improviso em prod)
- O que é `nao_verificado` vs `desvio` (não depende da interpretação do agente)
- Exit codes para uso em pipeline
- A garantia de que a chave nunca aparece em saída

**Ficou para o agente:**
- Como lidar com portas que não estão em escuta (9100 ausente → conforme, não desvio)
- Comportamento de serviços em `activating` vs `active`
- Como normalizar a formatação de booleanos no Markdown

Esses três pontos geraram as três divergências documentadas acima. Todos foram resolvidos de forma defensiva (a ferramenta escolheu o comportamento mais seguro em cada caso), mas o spec de produção deveria cobrir cada um explicitamente para eliminar a margem de interpretação.
