#!/usr/bin/env python3
"""
check-manifest.py — Conferência mecânica de manifests da Metacortex.
Cobre as regras do padrão que o Trivy não detecta.
Uso: python3 check-manifest.py <arquivo.yaml|diretório> [...]
"""

import sys
import re
import yaml
from pathlib import Path

PASS  = "✓"
FAIL  = "✗"
WARN  = "⚠"

KEBAB        = re.compile(r'^[a-z][a-z0-9-]*$')
NS_FMT       = re.compile(r'^[a-z]+-(?:dev|stg|prod)$')
REGISTRY     = "registry.metacortex.io/"
REQUIRED_LABELS = [
    "app.kubernetes.io/name",
    "app.kubernetes.io/instance",
    "app.kubernetes.io/part-of",
    "app.kubernetes.io/managed-by",
]
SECRET_KEY   = re.compile(r'(?:password|passwd|secret|token|credential|api[_-]?key)', re.I)
CREDS_IN_URL = re.compile(r'[a-z][a-z0-9+.-]*://[^@\s]+:[^@\s]+@')

_results = []

def ok(rule, msg, loc=""):   _results.append((PASS, rule, msg, loc))
def fail(rule, msg, loc=""): _results.append((FAIL, rule, msg, loc))
def warn(rule, msg, loc=""): _results.append((WARN, rule, msg, loc))


def check_doc(doc, source):
    kind      = doc.get("kind", "")
    meta      = doc.get("metadata", {})
    name      = meta.get("name", "")
    namespace = meta.get("namespace", "")
    labels    = meta.get("labels", {})
    annots    = meta.get("annotations", {})
    loc       = f"{source} [{kind}/{name}]"

    # 1.1 — kebab-case
    if name:
        if KEBAB.match(name):
            ok("1.1", f"nome '{name}' em kebab-case", loc)
        else:
            fail("1.1", f"nome '{name}' não é kebab-case (camelCase, underscore ou maiúscula detectados)", loc)

    # 1.2 — namespace <cliente>-<env>
    if namespace:
        if NS_FMT.match(namespace):
            ok("1.2", f"namespace '{namespace}' no formato <cliente>-<env>", loc)
        else:
            fail("1.2", f"namespace '{namespace}' fora do padrão — esperado <cliente>-{{dev|stg|prod}}", loc)

    # 1.3 — rótulos obrigatórios
    missing = [l for l in REQUIRED_LABELS if l not in labels]
    if missing:
        fail("1.3", f"rótulos ausentes: {missing}", loc)
    else:
        ok("1.3", "todos os rótulos obrigatórios presentes", loc)

    # 1.5 — anotação de dono (recomendado)
    if "metacortex.io/owner" not in annots:
        warn("1.5", "metacortex.io/owner ausente (recomendado)", loc)

    if kind != "Deployment":
        return

    spec          = doc.get("spec", {})
    pod_template  = spec.get("template", {})
    pod_meta      = pod_template.get("metadata", {})
    pod_labels    = pod_meta.get("labels", {})
    pod_spec      = pod_template.get("spec", {})
    match_labels  = spec.get("selector", {}).get("matchLabels", {})
    is_prod       = namespace.endswith("-prod")

    # 1.4 — seletor casa com rótulos do pod
    mismatched = {k: v for k, v in match_labels.items() if pod_labels.get(k) != v}
    if mismatched:
        fail("1.4", f"seletor não casa com rótulos do pod: {mismatched}", loc)
    elif match_labels:
        ok("1.4", "seletor e rótulos do pod coincidem", loc)

    # 2.3 — replicas >= 2 em prod
    replicas = spec.get("replicas", 1)
    if is_prod:
        if replicas < 2:
            fail("2.3", f"replicas={replicas} em prod (mínimo 2)", loc)
        else:
            ok("2.3", f"replicas={replicas} em prod", loc)

    # 2.4 — RollingUpdate em prod
    if is_prod:
        strategy = spec.get("strategy", {})
        if strategy.get("type") != "RollingUpdate":
            fail("2.4", f"strategy.type='{strategy.get('type', 'não declarado')}' — esperado RollingUpdate", loc)
        else:
            ru = strategy.get("rollingUpdate", {})
            if ru.get("maxUnavailable") != 0:
                fail("2.4", f"maxUnavailable={ru.get('maxUnavailable', 'não declarado')} — esperado 0", loc)
            elif ru.get("maxSurge") != 1:
                fail("2.4", f"maxSurge={ru.get('maxSurge', 'não declarado')} — esperado 1", loc)
            else:
                ok("2.4", "RollingUpdate com maxUnavailable=0, maxSurge=1", loc)

    # 3.4 — automountServiceAccountToken: false
    amt = pod_spec.get("automountServiceAccountToken")
    if amt is False:
        ok("3.4", "automountServiceAccountToken: false", loc)
    elif amt is None:
        fail("3.4", "automountServiceAccountToken não declarado (default: true)", loc)
    else:
        fail("3.4", "automountServiceAccountToken: true", loc)

    # Checks por container
    all_containers = pod_spec.get("containers", []) + pod_spec.get("initContainers", [])
    for container in pod_spec.get("containers", []):
        c_name = container.get("name", "?")
        c_loc  = f"{source} [{kind}/{name}/container/{c_name}]"
        image  = container.get("image", "")

        # 2.2 — probes
        if "readinessProbe" in container:
            ok("2.2", "readinessProbe declarada — confirme que aponta para endpoint real da aplicação", c_loc)
        else:
            fail("2.2", "readinessProbe ausente", c_loc)

        if "livenessProbe" in container:
            ok("2.2", "livenessProbe declarada — confirme que não depende de banco (risco de reinício em cascata)", c_loc)
        else:
            fail("2.2", "livenessProbe ausente", c_loc)

        # 3.3 — segredo em texto puro
        for e in container.get("env", []):
            if "value" in e:
                key = e.get("name", "")
                val = str(e.get("value", ""))
                if SECRET_KEY.search(key) or CREDS_IN_URL.search(val):
                    fail("3.3", f"possível segredo em texto puro: {key}={val[:40]}...", c_loc)

        # 3.7 — registry interno
        if image and not image.startswith(REGISTRY):
            fail("3.7", f"imagem '{image}' não é do registry interno (registry.metacortex.io/)", c_loc)
        elif image:
            ok("3.7", f"imagem do registry interno", c_loc)


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 check-manifest.py <arquivo.yaml|diretório> [...]")
        sys.exit(1)

    files = []
    for arg in sys.argv[1:]:
        p = Path(arg)
        if p.is_dir():
            files.extend(sorted(p.glob("*.yaml")))
            files.extend(sorted(p.glob("*.yml")))
        elif p.exists():
            files.append(p)
        else:
            print(f"ERRO: {arg} não encontrado", file=sys.stderr)
            sys.exit(1)

    for f in files:
        with open(f) as fh:
            docs = list(yaml.safe_load_all(fh))
        for doc in docs:
            if doc and isinstance(doc, dict):
                check_doc(doc, str(f))

    passes = fails = warns = 0
    for status, rule, msg, loc in _results:
        marker = {"✓": "[OK  ]", "✗": "[FAIL]", "⚠": "[WARN]"}[status]
        print(f"{marker} {rule}  {msg}")
        if loc:
            print(f"         {loc}")
        if status == PASS:  passes += 1
        elif status == FAIL: fails += 1
        else:               warns += 1

    print(f"\n{'─'*60}")
    print(f"Resultado mecânico: {passes} OK · {fails} falhas · {warns} avisos")
    print("Notas:")
    print("  • Regras 3.1, 2.1, 3.2, 3.6 são cobertas pelo Trivy (rode separado).")
    print("  • KSV-0125 do Trivy é falso positivo para registry.metacortex.io — ignore.")
    print("  • 2.2 probe correctness, 2.6 e 3.5 exigem leitura do projeto (ver SKILL.md).")
    print(f"{'─'*60}")

    sys.exit(1 if fails > 0 else 0)


if __name__ == "__main__":
    main()
