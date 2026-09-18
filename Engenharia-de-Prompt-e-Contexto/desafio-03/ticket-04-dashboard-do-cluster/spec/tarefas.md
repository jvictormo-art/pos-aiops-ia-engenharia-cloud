# Tarefas — metacortex-dashboard

---

## T1 — Evidência prévia: subir workload real

**Entrega**: dois projetos (kube-news, fake-shop) implantados via `metacortex-manifest`, mais os três labs do Ticket 02 mantidos no mesmo cluster.
**Critério**: `kubectl get pods -A` mostra pelo menos um Deployment saudável, um `ImagePullBackOff`, um `CrashLoopBackOff` e um Service sem endpoint.

## T2 — `ClusterReader`: camada de leitura

**Entrega**: `dashboard/k8s_reader.py` com métodos `listar_namespaces`, `listar_pods`, `listar_deployments`, `listar_services_com_endpoint`, `listar_eventos` — todos usando apenas verbos `list_*`/`get_*` do cliente oficial.
**Critério**: nenhuma chamada de escrita no arquivo; grep por `\.(create|patch|delete|replace)_` não encontra nada fora de comentários.

## T3 — Tratamento de erro por painel

**Entrega**: cada método de `ClusterReader` captura `ApiException` e conexão recusada, retornando um resultado tipado (`Ok(dados)` ou `Erro(tipo, mensagem)`) em vez de deixar a exceção subir.
**Critério**: os quatro cenários de falha do `spec-comportamento.md` cobertos por teste manual contra o cluster real.

## T4 — Renderização (TUI com Textual)

**Entrega**: `dashboard/app.py` — layout dos 5 painéis, seletor de namespace, campo de busca, rodapé com contexto e contador de painéis restritos.
**Critério**: layout corresponde ao `spec-comportamento.md`; ausência de campo nunca aparece como `None` na tela.

## T5 — Polling

**Entrega**: laço de atualização a cada 5s usando o worker assíncrono do Textual, sem bloquear a interface.
**Critério**: falha de uma consulta não trava as demais; próximo ciclo tenta de novo.

## T6 — Evidência contra cluster real

**Entrega**: capturas de tela/texto do dashboard rodando contra `kind-metacortex-lab`, cobrindo: caminho feliz (kube-news saudável), workload com falhas reais (labs do Ticket 02 + fake-shop `ErrImagePull`), cluster inalcançável (contexto apontando para endereço morto), RBAC restrito (contexto `platform-ro`-like, simulado com uma ServiceAccount de permissão parcial).
**Critério**: todos os 4 cenários de falha do spec, evidenciados com output real, não hipotético.

## T7 — Registro das skills

**Entrega**: `saida/skills-neste-projeto.md`.
**Critério**: cobre o que disparou sozinho, o que foi chamado manualmente, o que apareceu fora de contexto, o que precisou ser reexplicado.

## T8 — Arquivamento

**Entrega**: `spec/arquivo-final.md` — o que foi entregue, onde o spec precisou de correção durante a implementação.
**Critério**: cada divergência entre o spec e o código final tem uma linha explicando o motivo.

---

## Sequência

```
T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8
```

T1 é pré-requisito de tudo — sem workload real, não há o que desenhar na tela nem o que investigar nos cenários de falha.
