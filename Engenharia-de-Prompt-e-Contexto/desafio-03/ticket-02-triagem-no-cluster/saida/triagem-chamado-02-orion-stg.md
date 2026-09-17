# Triagem — Chamado 2: orion-stg, loja parou após publicação do Loom

**Sintoma declarado**: loja do fake-shop parou depois de uma publicação de release. Tag foi anunciada, deploy foi aplicado, mas o pod nunca trocou.

---

## Passo 1 — Estado dos pods

```
kubectl get pods -n orion-stg
```

```
NAME                              READY   STATUS         RESTARTS   AGE
orion-postgres-6775c9f896-8f7w2   1/1     Running        0          50s
orion-web-67cd86ffd5-54v6l        0/1     ErrImagePull   0          50s
orion-web-67cd86ffd5-ls7zv        0/1     ErrImagePull   0          50s
orion-web-67cd86ffd5-tg7cb        0/1     ErrImagePull   0          50s
```

STATUS `ErrImagePull` em todas as 3 réplicas → camada Registry. Banco sobe normal.

## Passo 2b — Eventos do namespace

```
kubectl get events -n orion-stg --sort-by='.lastTimestamp'
```

Eventos relevantes:
```
Warning  Failed  pod/orion-web-67cd86ffd5-ls7zv
  Failed to pull image "fabricioveronez/fake-shop:v1.14.2":
  rpc error: code = NotFound
  desc = failed to pull and unpack image "docker.io/fabricioveronez/fake-shop:v1.14.2":
  failed to resolve reference "docker.io/fabricioveronez/fake-shop:v1.14.2":
  docker.io/fabricioveronez/fake-shop:v1.14.2: not found
```

Mensagem `not found` — a tag `v1.14.2` não existe no Docker Hub para a imagem `fabricioveronez/fake-shop`. O Loom anunciou a tag antes de publicá-la (ou a publicação falhou silenciosamente).

---

## Resultado

```
CAUSA:     A tag de imagem declarada no Deployment não existe no registry
EVIDÊNCIA: Evento ErrImagePull em orion-web — image=fabricioveronez/fake-shop:v1.14.2
           Mensagem: "docker.io/fabricioveronez/fake-shop:v1.14.2: not found"
CAMADA:    registry
O QUE ESTÁ OK: orion-postgres sobe normalmente; o problema é exclusivo do Deployment orion-web
AÇÃO SUGERIDA: verificar se o Loom completou a publicação da tag v1.14.2 no registry;
               se não, aguardar a publicação ou reverter o deploy para a tag anterior
```

**Triagem encerrada.** Causa identificada no Passo 2b sem precisar de describe ou logs.
