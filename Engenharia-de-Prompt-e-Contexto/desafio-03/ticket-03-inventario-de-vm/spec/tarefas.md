# Tarefas — metacortex-inventario

---

## T1 — Spec de comportamento e decisões técnicas

**Entrega**: `spec-comportamento.md` + `spec-decisoes.md`  
**Critério**: todas as decisões listadas em proposta.md documentadas antes de abrir o editor

---

## T2 — Baseline e estrutura da ferramenta

**Entrega**: `ferramenta/baseline.yaml` + esqueleto de `inventario.py` com argparse e exit codes  
**Critério**: `python3 inventario.py --help` funciona; `python3 inventario.py --host x.x.x.x --user u --key k` falha com exit 2 e mensagem limpa (sem host real)

---

## T3 — Módulo de coleta SSH

**Entrega**: classe `Coletor` com todos os métodos de coleta implementados  
**Critério**: `coletar_tudo()` retorna dict com todos os campos do inventário; chave privada nunca aparece em stderr mesmo com host inválido

---

## T4 — Módulo de auditoria

**Entrega**: função `auditar()` comparando inventário com baseline  
**Critério**: cada regra do baseline tem pelo menos um caso de teste mental documentado; `nao_verificado` nunca confundido com `conforme`

---

## T5 — Renderização JSON e Markdown

**Entrega**: `renderizar_json()` e `renderizar_markdown()` correspondendo ao schema do ticket  
**Critério**: saída JSON válida; Markdown renderiza tabelas sem formatação quebrada

---

## T6 — Ambiente de teste e execução real

**Entrega**: `Dockerfile.test-vm` + instruções de como subir e conectar  
**Critério**: `python3 inventario.py` executado contra host Docker real; saída capturada nos dois formatos

---

## T7 — Evidência e validação dos critérios de aceite

**Entrega**: arquivos em `saida/evidencia/`  
**Critério**: cobre todos os 5 critérios de aceite da proposta: host com desvios, host inalcançável, segunda execução, exit codes, ausência da chave na saída

---

## T8 — Arquivo final e curadoria

**Entrega**: `spec/arquivo-final.md` + `saida/curadoria.md`  
**Critério**: onde o spec precisou ser corrigido durante a implementação está documentado com a decisão tomada

---

## Sequência de dependências

```
T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8
```

T1 e T2 podem ser executadas em paralelo (T1 não bloqueia T2 no início, mas T3 depende de T1 estar concluída).
