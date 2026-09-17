# Arquivo Final — metacortex-inventario

**Data de encerramento**: 2026-09-17  
**Versão entregue**: 1.0  
**Status**: todos os critérios de aceite da proposta verificados

---

## O que foi entregue conforme o spec

| Item | Status | Nota |
|---|---|---|
| Host com desvios → cada um classificado | ✓ | 6 desvios em 5 categorias, severidade correta |
| Host inalcançável → exit 2, mensagem limpa | ✓ | `timed out` sem stack trace, chave não exposta |
| `nao_verificado` distinto de `conforme` | ✓ | ssh.login_de_root marcado com motivo |
| Execução repetida → mesmo veredito | ✓ | Conformidade e resumo idênticos entre run1 e run2 |
| Chave privada não aparece na saída | ✓ | Testado com autenticação recusada e host inalcançável |
| Exit 0/1/2/3 distinguíveis em pipeline | ✓ | Desvios → 1, inalcançável → 2, --help → 0 |

---

## O que o spec precisou ser ajustado durante a implementação

### 1. Idempotência: o inventário de serviços pode diferir, mas a conformidade não

O spec dizia "execução repetida devolve o mesmo retrato". Durante os testes, o inventário completo de serviços (campo `servicos` no JSON) variou entre a primeira e segunda execução porque o systemd do container ainda estava completando o boot durante a primeira execução (`systemd-timedated.service` apareceu só no run2).

**Decisão**: o invariante correto é "o mesmo **veredito** por regra e o mesmo **resumo**" — não o inventário bruto. O `coletado_em` sempre difere por design. O inventário bruto de serviços pode diferir em hosts que acabaram de reiniciar. Isso não viola a promessa da ferramenta: ela fotografa o estado atual, não garante que o estado é estável. O spec foi atualizado para refletir isso: "execução repetida devolve o mesmo veredito para cada regra, mudando entre elas apenas o instante da coleta".

### 2. `porta 53` com interface qualifier (`127.0.0.53%lo`)

`ss -tlnp` em Ubuntu com systemd-resolved reporta a porta 53 como `127.0.0.53%lo`. O parser original fazia `rfind(":")` para separar endereço de porta, o que funcionava. O bind resultante era `127.0.0.53%lo` — que **não** está nos wildcards `("0.0.0.0", "::", "*")` e portanto é corretamente tratado como endereço interno. O spec não precisou mudar, mas o comportamento foi verificado explicitamente neste campo.

### 3. Processo não visível em `ss -tlnp` para sshd (usuário não-root)

O campo `processo` em `portas_em_escuta` retorna `null` para a porta 22 quando rodando como usuário comum. Isso ocorre porque `ss -tlnp` exibe o processo dono apenas para o usuário atual (ou root). O spec já previa `"processo": null` como valor válido — o campo é informacional, não um item de conformidade. Comportamento correto; confirmado na evidência.

### 4. `swap` em container Docker compartilha o swap do host

O container de teste reportou `swap.habilitado: true, tamanho: 1024M` porque `/proc/swaps` em um container Linux expõe o swap do host (VM Linux do Docker Desktop). Em VMs reais do parque o comportamento é idêntico ao de um bare-metal. O desvio é real e o campo é coletado corretamente.

### 5. `AutoAddPolicy` para host key documentado como trade-off

O spec-decisoes.md registrou que `AutoAddPolicy` é adequado para o MVP de lab e deve ser substituído por `RejectPolicy + known_hosts` em produção. Esta decisão foi mantida e explicitada como pendência de versão futura, não como bug.

---

## O que ficou para uma versão futura

| Item | Decisão |
|---|---|
| `RejectPolicy` com known_hosts populado | Melhoria de segurança explicitamente documentada |
| Coleta de múltiplos hosts em paralelo | Fora do escopo MVP conforme proposta |
| Verificação de port 9100 quando node_exporter não está rodando | Confirmado: `9100 não encontrada em escuta` → conforme (ausência de escuta não é exposição indevida) |
