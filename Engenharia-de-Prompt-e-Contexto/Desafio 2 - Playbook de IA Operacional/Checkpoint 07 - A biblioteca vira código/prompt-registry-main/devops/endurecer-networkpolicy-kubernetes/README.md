---
nome: Endurecimento de NetworkPolicy Kubernetes
descricao: Transforma uma NetworkPolicy permissiva em uma política endurecida com default-deny, liberando apenas fluxos explicitamente legítimos, com verificação iterativa.
versao: 1.0.0
tags: [kubernetes, segurança, networkpolicy, hardening, devops]
inputs:
  - nome: MANIFESTO_PERMISSIVO
    descricao: YAML da NetworkPolicy permissiva a ser corrigida
  - nome: REGRAS_DO_PADRAO
    descricao: Fluxos de ingress/egress permitidos e requisitos de conformidade da organização
  - nome: MAPA_DE_SERVICOS
    descricao: Identificação de cada serviço no cluster — namespace, labels e portas
---

# Endurecimento de NetworkPolicy Kubernetes

## Objetivo

Recebe um manifesto de NetworkPolicy permissivo e o transforma em uma política endurecida que segue o princípio default-deny: diagnostica cada regra aberta, mapeia os fluxos legítimos contra o padrão e o mapa de serviços, emite a política corrigida com comentário por regra e conduz ao menos duas rodadas de verificação iterativa (v1 → revisão de segurança → v2/v3), documentando cada correção.

## Quando usar

- Ao revisar manifestos de NetworkPolicy criados sem restrições de segurança (allow-all ou seletores vazios) antes de aplicar em produção.
- Para adequar políticas de rede a um padrão de conformidade organizacional específico.
- Quando um revisor de segurança precisa de um diagnóstico estruturado + YAML aplicável diretamente via `kubectl apply`.
- Em auditorias de cluster onde políticas permissivas precisam ser substituídas por políticas segmentadas e auditáveis.

## Exemplo de uso

_A preencher_ (depende do manifesto real fornecido em `{{MANIFESTO_PERMISSIVO}}`, das regras em `{{REGRAS_DO_PADRAO}}` e do inventário em `{{MAPA_DE_SERVICOS}}`).

## Limitações conhecidas

- Se `{{REGRAS_DO_PADRAO}}` exigir um fluxo cujo serviço não consta em `{{MAPA_DE_SERVICOS}}`, o modelo sinaliza a lacuna em vez de inventar labels ou portas.
- Se `{{MAPA_DE_SERVICOS}}` omitir a porta de um egress exigido, o modelo marca como pendência na verificação em vez de assumir uma porta arbitrária.
- O YAML produzido é válido conforme as regras do prompt, mas deve ser validado em ambiente de staging antes de aplicar em produção — o modelo opera sobre o snapshot fornecido, não sobre o cluster ao vivo.
