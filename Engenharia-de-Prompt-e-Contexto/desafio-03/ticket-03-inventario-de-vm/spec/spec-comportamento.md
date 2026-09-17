# Spec de Comportamento — metacortex-inventario

---

## Interface de linha de comando

```
python3 inventario.py \
  --host   <ip_ou_hostname>      # obrigatório
  --user   <usuario_ssh>         # obrigatório
  --key    <caminho_chave_priv>  # obrigatório
  [--baseline baseline.yaml]     # padrão: ./baseline.yaml
  [--format json|md|both]        # padrão: both
  [--porta 22]                   # padrão: 22
```

---

## Saída padrão

Vai para stdout. Quando `--format both`, JSON primeiro, depois `---`, depois Markdown. Mensagens de erro vão para stderr — nunca para stdout. Isso permite que `inventario.py ... | jq` funcione sem filtragem manual.

---

## Os três vereditos

| Veredito | Quando usar | O que NÃO fazer |
|---|---|---|
| `conforme` | O item coletado satisfaz o baseline | Usar quando o dado não pôde ser coletado |
| `desvio` | O item coletado diverge do baseline | Usar quando não há privilégio para coletar |
| `nao_verificado` | Não foi possível coletar o dado para comparar | Usar como substituto de `conforme` |

**`nao_verificado` carrega motivo.** Toda entrada com esse veredito tem campo `motivo` descrevendo por que a verificação não foi possível.

---

## Campos `nao_verificado` esperados

| Regra | Por quê é nao_verificado | Evidência esperada |
|---|---|---|
| `ssh.login_de_root` | `sshd -T` requer privilégio elevado | `login_de_root: null`, `motivo: "exige privilegio que o usuario da coleta nao tem"` |
| Qualquer regra de serviço | systemd não disponível no host | `motivo: "systemd nao disponivel ou nao acessivel"` |
| `ntp.sincronizado` | timedatectl não disponível | `motivo: "timedatectl nao disponivel"` |

---

## Exit codes

| Código | Significado |
|---|---|
| `0` | Host alcançado, sem desvios confirmados (nao_verificados são anotados mas não deflagram saída não-zero) |
| `1` | Host alcançado, há pelo menos um desvio |
| `2` | Falha de conexão: host inalcançável, autenticação recusada, timeout, DNS não resolvido |
| `3` | Erro interno: baseline inválido, argumento obrigatório faltando, erro de parsing |

Exit code 0 não significa "completamente auditado" — pode haver `nao_verificados`. Significa "nenhuma violação confirmada".

---

## Comportamento com host inalcançável

```
$ python3 inventario.py --host 10.0.0.99 --user auditor --key id_ed25519
Erro de conexão: Host inalcançável: 10.0.0.99 — [Errno 110] Connection timed out
```

- Saída vai para **stderr**
- **Nenhuma** linha vai para stdout
- Nenhum stack trace visível ao operador
- A chave privada não aparece na mensagem de erro, nem no nome do arquivo

---

## Invariante de leitura

A ferramenta não altera estado no host remoto. Isso é garantido pelo design:
- Os únicos comandos enviados são listados explicitamente em `spec-decisoes.md`
- Todos são comandos de leitura (`cat`, `uname`, `ss`, `systemctl list-units`, `timedatectl show`, `sshd -T`)
- Nenhum `sudo` é tentado; nenhum arquivo é criado ou modificado
- A consequência direta: execução repetida devolve o mesmo inventário e a mesma conformidade, com o instante de coleta sendo o único campo que muda

---

## Invariante da chave privada

A chave privada é carregada diretamente pela biblioteca SSH e nunca:
- Aparece em stdout ou stderr, nem parcialmente
- É incluída em mensagens de erro (erros de autenticação dizem "chave recusada", não "chave X recusada")
- É logada ou impressa como parte do estado da ferramenta

---

## Schema JSON completo

```json
{
  "host": {
    "endereco": "<string — endereço passado via --host>",
    "hostname": "<string — hostname que o próprio host reporta via hostname(1)>",
    "coletado_em": "<string ISO 8601 UTC — 2026-08-12T09:14:02Z>"
  },
  "inventario": {
    "so":     {"distribuicao": "<string>", "versao": "<string>"},
    "kernel": {"versao": "<string>"},
    "servicos": [
      {"nome": "<nome.tipo>", "tipo": "service|socket", "estado": "active"}
    ],
    "swap":   {"habilitado": "<bool>", "tamanho": "<string|null>"},
    "portas_em_escuta": [
      {"porta": "<int>", "bind": "<string>", "processo": "<string|null>"}
    ],
    "chaves_ssh": [
      {"identificacao": "<string — comentário do campo 3 da linha authorized_keys>"}
    ],
    "ssh":    {"login_de_root": "<bool|null>"},
    "ntp":    {"sincronizado": "<bool|null>", "mecanismo": "<string|null>"}
  },
  "conformidade": [
    {
      "regra": "<string>",
      "esperado": "<any>",
      "encontrado": "<any>",
      "veredito": "conforme|desvio|nao_verificado",
      "severidade": "<string — presente apenas quando veredito=desvio>",
      "motivo": "<string — presente apenas quando veredito=nao_verificado>"
    }
  ],
  "resumo": {
    "conforme": "<int>",
    "desvio": "<int>",
    "nao_verificado": "<int>",
    "por_severidade": {"critico": "<int>", "alto": "<int>", "medio": "<int>"}
  }
}
```

---

## Estrutura Markdown

```
# Inventário — <hostname> (<endereço>)
Coletado em <data hora> UTC · baseline v<versao>

## Desvios
| Severidade | Regra | Esperado | Encontrado |
|---|---|---|---|
| crítico | ... | ... | ... |
| alto    | ... | ... | ... |
| médio   | ... | ... | ... |

## Não verificado
| Regra | Motivo |
|---|---|
| ... | ... |

## Conforme
regra1 · regra2 · regra3

---
**Resumo**: N conforme · N desvio · N não verificado
**Por severidade**: N crítico · N alto · N médio
```

A seção `## Desvios` aparece mesmo quando vazia (`*Nenhum desvio encontrado.*`). A seção `## Não verificado` só aparece se houver itens. `## Conforme` lista regras separadas por ` · `.
