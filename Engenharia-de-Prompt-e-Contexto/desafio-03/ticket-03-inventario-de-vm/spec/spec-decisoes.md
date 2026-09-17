# Spec de Decisões Técnicas — metacortex-inventario

Decisões que a ferramenta não carrega sozinha. Registradas antes de abrir o editor de código.

---

## Linguagem: Python 3.10+

**Escolha**: Python 3.  
**Por quê**: paramiko (SSH puro Python, sem dependência de `ssh` no PATH), PyYAML (leitura do baseline), e a stdlib padrão cobrem tudo. Alternativas consideradas:
- Go: binário compilado seria mais portável, mas `golang.org/x/crypto/ssh` é mais verboso para os comandos compostos necessários. Python está presente nas máquinas de operação do parque.
- Shell + `ssh`: execução de comandos remotos seria trivial, mas parsear saídas e comparar versões em shell é frágil e difícil de testar em isolamento.

**Versão mínima**: 3.10 (match/case não é usado, mas walrus operator e f-strings com `=` são convenientes e presentes em 3.10+).

---

## Biblioteca SSH: paramiko

**Escolha**: `paramiko`.  
**Por quê**: implementação pura Python de SSH2; não depende do binário `ssh` do sistema operacional (que pode ter versões diferentes ou flags distintas). A alternativa `subprocess + ssh` dependeria de ter ssh no PATH e de parsear stderr de um binário externo para distinguir erros.

**Política de host key**: `AutoAddPolicy` — a ferramenta não é interativa e não pode esperar input do operador. Em ambiente de produção, a política deveria ser `RejectPolicy` com um known_hosts populado; para o MVP de lab, AutoAddPolicy é aceitável. Decisão registrada aqui para que a mudança seja consciente.

---

## Comando por item coletado

| Item | Comando SSH | Por quê esse comando |
|---|---|---|
| SO distribuição e versão | `. /etc/os-release && echo "$ID $VERSION_ID"` | Padrão LSB, presente em todas as distros modernas; não depende de `lsb_release` instalado |
| Kernel | `uname -r` | Única fonte autoritativa da versão do kernel em execução |
| Serviços ativos (service) | `systemctl list-units --type=service --state=active --no-legend --plain --no-pager 2>/dev/null` | Lista apenas unidades em estado `active`; `--no-legend --plain` facilita parsing; `2>/dev/null` evita erro em containers sem systemd |
| Serviços ativos (socket) | Mesmo comando com `--type=socket` | Baseline proíbe `telnet.socket` e `rpcbind.socket` — sockets são um tipo distinto de unit |
| Swap | `cat /proc/swaps` | Arquivo de kernel, sempre presente; primeira linha é cabeçalho, demais são dispositivos de swap ativos |
| Portas em escuta | `ss -tlnp 2>/dev/null` | `-t` TCP, `-l` LISTEN, `-n` numérico (evita resolução de nomes), `-p` processo; disponível em qualquer Ubuntu via iproute2 |
| Chaves SSH autorizadas | `cat ~/.ssh/authorized_keys 2>/dev/null` | Arquivo padrão de chaves do usuário conectado; `2>/dev/null` trata silenciosamente a ausência do arquivo |
| Configuração efetiva sshd | `sshd -T 2>/dev/null \| grep -i permitrootlogin` | Única forma de obter a config EFETIVA (resolved, com includes). Requer privilégio elevado — sem ele, saída é vazia e o item é marcado como `nao_verificado` |
| Sincronização NTP | `timedatectl show --property=NTPSynchronized,NTPService 2>/dev/null` | Funciona com systemd-timesyncd e chrony (via chrony-wait.service). Fallback: `timedatectl status 2>/dev/null` para parsing da saída em texto |

---

## Definição de "endereço público" para portas

**Endereços considerados públicos** (porta exposta a todas as interfaces):
- `0.0.0.0` (IPv4 wildcard)
- `::` (IPv6 wildcard)
- `*` (wildcard genérico que alguns processos reportam)

**Endereço interno**: qualquer outro endereço (um IP específico como `10.42.7.14` ou `127.0.0.1`).

A regra `portas_em_escuta.somente_rede_interna: [9100]` significa: porta 9100 não deve estar bound em endereço público. Se estiver bound em `10.42.7.14` — conforme. Se estiver bound em `0.0.0.0` — desvio crítico.

A regra `portas_em_escuta.publicas_permitidas: [22]` significa: qualquer porta bound em endereço público (exceto 22) é desvio crítico. Porta 22 em `0.0.0.0` — conforme.

---

## Identificação de chaves SSH "emitidas pela plataforma"

O baseline diz `chaves_ssh.emitidas_por: metacortex-platform`. A identificação de cada chave é o **comentário** (campo 3) da linha do `authorized_keys`. Uma chave "emitida pela plataforma" tem o identificador `metacortex-platform` em algum lugar do comentário (ex: `platform@metacortex-platform`, `deploy@metacortex-platform`).

**Verificação**: `"metacortex-platform" in comentario_da_chave`.

Chaves sem comentário são tratadas como "não reconhecidas" — desvio crítico.

---

## Comparação de versões

Versões são comparadas como tuplas de inteiros extraídas com regex `\d+`. Exemplos:
- `"22.04.4"` → `(22, 4, 4)`
- `"6.5"` → `(6, 5)`
- `"5.15.0-118-generic"` → `(5, 15, 0)` (apenas os primeiros 3 grupos numéricos)

Python compara tuplas elemento a elemento, com tupla mais longa sendo maior quando o prefixo é igual. Isso é correto para versões semânticas.

---

## Proteção da chave privada

O caminho da chave é passado via `--key` e entregue diretamente à função `paramiko.SSHClient.connect(key_filename=...)`. O conteúdo da chave nunca é lido pelo código da ferramenta — apenas pelo paramiko. Mensagens de erro (autenticação recusada, arquivo inválido) são capturadas e reescritas em mensagens limpas sem mencionar o caminho ou conteúdo da chave.

---

## O que acontece quando um dado não pode ser coletado

Cada ponto de coleta tem dois estados de falha:

**Falha "esperada" (sem privilégio)**: o comando retorna exit code diferente de zero ou saída vazia porque o usuário da coleta não tem privilégio. O item é marcado como `nao_verificado` com motivo descritivo. A coleta dos demais itens continua normalmente.

**Falha "inesperada" (erro de runtime)**: qualquer exceção não prevista durante a coleta de um item específico é capturada, o item é marcado como `nao_verificado` com o erro como motivo, e a coleta continua. Isso garante que um item problemático não aborte o inventário inteiro.

**Falha de conexão** (antes de qualquer coleta): a ferramenta termina imediatamente com exit code 2 e mensagem de erro descritiva no stderr. Nenhuma saída vai para stdout.

---

## Geração do `coletado_em`

O instante de coleta é gerado no momento em que `coletar_tudo()` é chamado, em UTC, no formato ISO 8601 (`%Y-%m-%dT%H:%M:%SZ`). É o instante em que a coleta COMEÇA, não quando termina. A consistência entre execuções é garantida porque os comandos remotos são idempotentes — eles leem estado, não alteram.
