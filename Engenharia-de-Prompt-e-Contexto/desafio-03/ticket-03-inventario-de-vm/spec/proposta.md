# Proposta — metacortex-inventario

**Versão**: 1.0  
**Data**: 2026-09-17  
**Status**: aprovada

---

## Problema

O Roster manual do Mouse acumula drift silencioso: host que mudou de papel e não teve o registro atualizado, chave SSH inserida durante incidente e nunca catalogada, serviço proibido que sobreviveu a uma migração. Quando o Seraph pergunta quantas VMs estão fora do padrão, a resposta honesta é "não sei".

O parque não tem agente instalado nas VMs. O que existe em toda VM é acesso por chave SSH — e é com ele que a ferramenta trabalha.

---

## O que estamos construindo

Uma ferramenta de linha de comando que:
1. Recebe o endereço de uma VM, o usuário e a chave privada
2. Conecta por SSH
3. Coleta o retrato real do host (SO, kernel, serviços, swap, portas, chaves SSH autorizadas, config SSH, NTP)
4. Compara o retrato com o `baseline.yaml` versionado do parque
5. Produz saída em JSON (para o Roster consumir) e Markdown (para o plantão ler às 3h)

A ferramenta não instala, não corrige, não escreve nada no host remoto. Duas execuções seguidas devem produzir o mesmo veredito — mudando apenas o instante da coleta.

---

## O que está fora do escopo desta versão

| Item | Motivo |
|---|---|
| Coleta de múltiplos hosts em paralelo | Complexidade de UI/output fora do MVP |
| Integração direta com o Roster | O Roster ainda não existe; o JSON é o contrato de interface |
| Remediação automática de desvios | Invariante da ferramenta: só lê |
| Verificação de conformidade de rede/firewall | Requer acesso externo ao host, não só SSH interno |
| Coleta via usuário root | Operação padrão com usuário comum; root não é requisito |

---

## Critérios de aceite

- Host conforme sai sem desvio (exit 0)
- Host com desvios sai com cada um classificado pela severidade do baseline (exit 1)
- Regra não verificável por falta de privilégio aparece como `nao_verificado`, distinta de `conforme`
- Host inalcançável falha com mensagem descritiva sem stack trace cru (exit 2)
- Execução repetida devolve o mesmo retrato (idempotência)
- Chave privada não aparece em nenhuma saída, log ou mensagem de erro

---

## Decisões fechadas antes da implementação

As decisões técnicas (linguagem, biblioteca SSH, comandos por item coletado, o que determina "público" vs "interno" para portas) estão em `spec-decisoes.md`. Nenhuma escolha silenciosa no meio do código.
