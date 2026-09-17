#!/usr/bin/env python3
"""
metacortex-inventario — audita uma VM contra baseline.yaml via SSH.

Uso:
  python3 inventario.py \\
    --host   <ip_ou_hostname> \\
    --user   <usuario_ssh> \\
    --key    <caminho_chave_privada> \\
    [--baseline baseline.yaml] \\
    [--format json|md|both] \\
    [--porta 22]

Saída: stdout (JSON e/ou Markdown). Erros: stderr.

Códigos de saída:
  0  — host alcançado, sem desvios confirmados
  1  — host alcançado, há desvios
  2  — falha de conexão (host inalcançável, chave recusada, timeout)
  3  — erro interno (baseline inválido, argumento ausente)
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone

try:
    import paramiko
    import yaml
except ImportError as e:
    print(
        f"Erro: dependência ausente — {e}. Execute: pip3 install paramiko pyyaml",
        file=sys.stderr,
    )
    sys.exit(3)


# ──────────────────────────────────────────────────────────────────
#  SSH
# ──────────────────────────────────────────────────────────────────

class SSHConexao:
    """Encapsula a conexão SSH. A chave privada nunca é exposta em logs ou erros."""

    def __init__(self, host: str, usuario: str, chave_path: str, porta: int = 22):
        self.host = host
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self._client.connect(
                hostname=host,
                username=usuario,
                key_filename=chave_path,
                port=porta,
                timeout=10,
                allow_agent=False,
                look_for_keys=False,
            )
        except paramiko.AuthenticationException:
            raise ConnectionError(f"Autenticação recusada em {host}:{porta} — verifique usuário e chave")
        except paramiko.SSHException as e:
            raise ConnectionError(f"Falha SSH em {host}:{porta} — {e}")
        except OSError as e:
            raise ConnectionError(f"Host inalcançável: {host} — {e}")

    def executar(self, cmd: str) -> tuple[str, int]:
        """Executa um comando de leitura no host remoto. Retorna (stdout, exit_code)."""
        _, stdout, _ = self._client.exec_command(cmd, timeout=30)
        saida = stdout.read().decode(errors="replace").strip()
        codigo = stdout.channel.recv_exit_status()
        return saida, codigo

    def fechar(self):
        self._client.close()


# ──────────────────────────────────────────────────────────────────
#  COLETA
# ──────────────────────────────────────────────────────────────────

class Coletor:
    """Coleta dados de inventário via SSH. Apenas leitura — nada é modificado no host."""

    def __init__(self, ssh: SSHConexao):
        self._ssh = ssh

    def _run(self, cmd: str) -> tuple[str, int]:
        return self._ssh.executar(cmd)

    def so(self) -> dict:
        saida, _ = self._run('. /etc/os-release && echo "$ID $VERSION_ID"')
        partes = saida.split(None, 1)
        return {
            "distribuicao": partes[0] if partes else "desconhecido",
            "versao": partes[1].strip() if len(partes) > 1 else "desconhecida",
        }

    def kernel(self) -> dict:
        saida, _ = self._run("uname -r")
        return {"versao": saida or "desconhecida"}

    def servicos(self) -> tuple[list[dict], bool]:
        """Retorna (lista_servicos, systemd_disponivel)."""
        lista = []
        # Verificar se systemd está disponível
        _, codigo = self._run("systemctl is-system-running 2>/dev/null")
        if codigo not in (0, 1, 3, 4):
            # Códigos 0=running, 1=degraded, 3=not-running, 4=unknown são válidos
            # Qualquer outro indica systemd ausente
            _, codigo2 = self._run("systemctl --version 2>/dev/null")
            if codigo2 != 0:
                return [], False

        for tipo in ("service", "socket"):
            saida, _ = self._run(
                f"systemctl list-units --type={tipo} --state=active "
                f"--no-legend --plain --no-pager 2>/dev/null"
            )
            for linha in saida.splitlines():
                partes = linha.split()
                if not partes:
                    continue
                nome = partes[0]
                if nome.endswith(f".{tipo}"):
                    lista.append({"nome": nome, "tipo": tipo, "estado": "active"})
        return lista, True

    def swap(self) -> dict:
        saida, _ = self._run("cat /proc/swaps")
        linhas = [l for l in saida.splitlines() if l and not l.startswith("Filename")]
        if not linhas:
            return {"habilitado": False, "tamanho": None}
        total_kb = 0
        for linha in linhas:
            partes = linha.split()
            if len(partes) >= 3:
                try:
                    total_kb += int(partes[2])
                except ValueError:
                    pass
        gb = total_kb / (1024 * 1024)
        mb = total_kb / 1024
        tamanho = f"{gb:.0f}G" if gb >= 1 else f"{mb:.0f}M"
        return {"habilitado": True, "tamanho": tamanho}

    def portas(self) -> list[dict]:
        saida, _ = self._run("ss -tlnp 2>/dev/null")
        resultado = []
        for linha in saida.splitlines():
            partes = linha.split()
            if not partes or partes[0] != "LISTEN":
                continue
            if len(partes) < 4:
                continue
            endereco_porta = partes[3]
            idx = endereco_porta.rfind(":")
            if idx == -1:
                continue
            try:
                porta = int(endereco_porta[idx + 1:])
            except ValueError:
                continue
            bind = endereco_porta[:idx].strip("[]") or "*"
            processo = None
            m = re.search(r'users:\(\("([^"]+)"', linha)
            if m:
                processo = m.group(1)
            resultado.append({"porta": porta, "bind": bind, "processo": processo})
        return resultado

    def chaves_ssh(self) -> list[dict]:
        saida, _ = self._run("cat ~/.ssh/authorized_keys 2>/dev/null")
        chaves = []
        for linha in saida.splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            partes = linha.split(None, 2)
            if len(partes) >= 3:
                identificacao = partes[2].strip()
            elif len(partes) == 2:
                identificacao = "(sem comentário)"
            else:
                continue
            chaves.append({"identificacao": identificacao})
        return chaves

    def ssh_config(self) -> dict:
        """Tenta ler a configuração efetiva do sshd. Requer privilégio elevado."""
        saida, codigo = self._run("sshd -T 2>/dev/null | grep -i permitrootlogin")
        if codigo != 0 or not saida.strip():
            return {"login_de_root": None, "_nao_verificado": True}
        m = re.search(r'permitrootlogin\s+(\S+)', saida, re.IGNORECASE)
        if not m:
            return {"login_de_root": None, "_nao_verificado": True}
        valor = m.group(1).lower()
        login_permitido = valor in ("yes", "without-password", "prohibit-password")
        return {"login_de_root": login_permitido}

    def ntp(self) -> dict:
        saida, codigo = self._run(
            "timedatectl show --property=NTPSynchronized,NTPService 2>/dev/null"
        )
        sincronizado = None
        mecanismo = None
        if codigo == 0 and saida:
            for linha in saida.splitlines():
                if "=" in linha:
                    k, _, v = linha.partition("=")
                    if k.strip() == "NTPSynchronized":
                        sincronizado = v.strip().lower() == "yes"
                    elif k.strip() == "NTPService":
                        mecanismo = v.strip() or None
        if sincronizado is None:
            # Fallback: timedatectl status
            saida2, _ = self._run("timedatectl status 2>/dev/null")
            for linha in saida2.splitlines():
                linha_l = linha.lower()
                if "synchronized:" in linha_l or "system clock synchronized" in linha_l:
                    sincronizado = "yes" in linha_l
        return {"sincronizado": sincronizado, "mecanismo": mecanismo}

    def coletar_tudo(self, host_address: str) -> dict:
        lista_svc, systemd_ok = self.servicos()
        return {
            "host": {
                "endereco": host_address,
                "hostname": self._run("hostname")[0] or host_address,
                "coletado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            "inventario": {
                "so": self.so(),
                "kernel": self.kernel(),
                "servicos": lista_svc,
                "swap": self.swap(),
                "portas_em_escuta": self.portas(),
                "chaves_ssh": self.chaves_ssh(),
                "ssh": self.ssh_config(),
                "ntp": self.ntp(),
            },
            "_meta": {"systemd_disponivel": systemd_ok},
        }


# ──────────────────────────────────────────────────────────────────
#  AUDITORIA
# ──────────────────────────────────────────────────────────────────

def _versao_tuple(v: str) -> tuple:
    """'5.15.0-118-generic' → (5, 15, 0). '22.04' → (22, 4)."""
    partes = re.findall(r'\d+', str(v))
    return tuple(int(x) for x in partes[:3]) if partes else (0,)


def auditar(baseline: dict, dados: dict) -> list[dict]:
    """Compara inventário com baseline. Retorna lista de entradas de conformidade."""
    esperado = baseline.get("esperado", {})
    severidades = baseline.get("severidade", {})
    inv = dados["inventario"]
    systemd_ok = dados.get("_meta", {}).get("systemd_disponivel", True)

    def sev(regra: str) -> str:
        for nivel, regras in severidades.items():
            if regra in regras:
                return nivel
        return "info"

    def ok(regra, esp, enc):
        return {"regra": regra, "esperado": esp, "encontrado": enc, "veredito": "conforme"}

    def desvio(regra, esp, enc):
        return {"regra": regra, "esperado": esp, "encontrado": enc, "veredito": "desvio", "severidade": sev(regra)}

    def nv(regra, esp, motivo):
        return {"regra": regra, "esperado": esp, "encontrado": None, "veredito": "nao_verificado", "motivo": motivo}

    resultado = []

    # ── so.distribuicao ──
    dist_esp = esperado.get("so", {}).get("distribuicao")
    dist_enc = inv["so"]["distribuicao"]
    resultado.append(ok("so.distribuicao", dist_esp, dist_enc)
                     if dist_enc == dist_esp
                     else desvio("so.distribuicao", dist_esp, dist_enc))

    # ── so.versao_minima ──
    versao_min = esperado.get("so", {}).get("versao_minima")
    versao_enc = inv["so"]["versao"]
    conforme_v = _versao_tuple(versao_enc) >= _versao_tuple(versao_min)
    resultado.append(ok("so.versao_minima", versao_min, versao_enc)
                     if conforme_v
                     else desvio("so.versao_minima", versao_min, versao_enc))

    # ── kernel.versao_minima ──
    kernel_min = esperado.get("kernel", {}).get("versao_minima")
    kernel_enc = inv["kernel"]["versao"]
    conforme_k = _versao_tuple(kernel_enc) >= _versao_tuple(kernel_min)
    resultado.append(ok("kernel.versao_minima", kernel_min, kernel_enc)
                     if conforme_k
                     else desvio("kernel.versao_minima", kernel_min, kernel_enc))

    # ── servicos.ativos ──
    servicos_enc = {s["nome"] for s in inv["servicos"]}
    for svc in esperado.get("servicos", {}).get("ativos", []):
        if not systemd_ok:
            resultado.append(nv("servicos.ativos", f"{svc} ativo", "systemd nao disponivel ou nao acessivel"))
            continue
        nome_full = svc if "." in svc else f"{svc}.service"
        presente = nome_full in servicos_enc or svc in servicos_enc
        resultado.append(ok("servicos.ativos", f"{svc} ativo", "presente")
                         if presente
                         else desvio("servicos.ativos", f"{svc} ativo", "ausente"))

    # ── servicos.proibidos ──
    for svc in esperado.get("servicos", {}).get("proibidos", []):
        if not systemd_ok:
            resultado.append(nv("servicos.proibidos", f"{svc} inativo", "systemd nao disponivel ou nao acessivel"))
            continue
        nome_full = svc if "." in svc else f"{svc}.socket"
        presente = nome_full in servicos_enc or svc in servicos_enc
        resultado.append(desvio("servicos.proibidos", f"{svc} inativo", "presente")
                         if presente
                         else ok("servicos.proibidos", f"{svc} inativo", "ausente"))

    # ── swap.habilitado ──
    swap_esp = esperado.get("swap", {}).get("habilitado")
    swap_enc = inv["swap"]["habilitado"]
    tamanho = inv["swap"].get("tamanho")
    enc_str = f"true ({tamanho})" if swap_enc and tamanho else swap_enc
    resultado.append(ok("swap.habilitado", swap_esp, swap_enc)
                     if swap_enc == swap_esp
                     else desvio("swap.habilitado", swap_esp, enc_str))

    # ── portas_em_escuta.publicas_permitidas ──
    publicas_perm = set(esperado.get("portas_em_escuta", {}).get("publicas_permitidas", []))
    WILDCARDS = {"0.0.0.0", "::", "*", ""}
    portas_pub = [p for p in inv["portas_em_escuta"] if p["bind"] in WILDCARDS]
    nao_perm = [p for p in portas_pub if p["porta"] not in publicas_perm]
    if nao_perm:
        enc = ", ".join(f"{p['porta']} em {p['bind']}" for p in nao_perm)
        resultado.append(desvio(
            "portas_em_escuta.publicas_permitidas",
            f"apenas {sorted(publicas_perm)} públicas",
            f"não permitidas expostas: {enc}",
        ))
    else:
        resultado.append(ok(
            "portas_em_escuta.publicas_permitidas",
            f"apenas {sorted(publicas_perm)} públicas",
            "nenhuma porta não autorizada em endereço público",
        ))

    # ── portas_em_escuta.somente_rede_interna ──
    somente_int = set(esperado.get("portas_em_escuta", {}).get("somente_rede_interna", []))
    for porta in somente_int:
        enc_lista = [p for p in inv["portas_em_escuta"] if p["porta"] == porta]
        vazadas = [p for p in enc_lista if p["bind"] in WILDCARDS]
        if vazadas:
            resultado.append(desvio(
                "portas_em_escuta.somente_rede_interna",
                f"{porta} somente rede interna",
                f"{porta} exposta em {vazadas[0]['bind']}",
            ))
        elif enc_lista:
            resultado.append(ok(
                "portas_em_escuta.somente_rede_interna",
                f"{porta} somente rede interna",
                f"{porta} em {enc_lista[0]['bind']}",
            ))
        else:
            resultado.append(ok(
                "portas_em_escuta.somente_rede_interna",
                f"{porta} somente rede interna",
                f"{porta} não encontrada em escuta",
            ))

    # ── chaves_ssh.emitidas_por ──
    emitidas_por = esperado.get("chaves_ssh", {}).get("emitidas_por", "")
    chaves = inv["chaves_ssh"]
    if not chaves:
        resultado.append(desvio(
            "chaves_ssh.emitidas_por",
            f"todas emitidas por {emitidas_por}",
            "nenhuma chave em authorized_keys",
        ))
    else:
        estranhas = [c for c in chaves if emitidas_por not in c["identificacao"]]
        if estranhas:
            ids = [c["identificacao"] for c in estranhas]
            resultado.append(desvio(
                "chaves_ssh.emitidas_por",
                f"todas emitidas por {emitidas_por}",
                f"{len(estranhas)} chave(s) não reconhecida(s): {ids}",
            ))
        else:
            resultado.append(ok(
                "chaves_ssh.emitidas_por",
                f"todas emitidas por {emitidas_por}",
                f"{len(chaves)} chave(s), todas com identificação correta",
            ))

    # ── ssh.login_de_root ──
    ssh_cfg = inv["ssh"]
    if ssh_cfg.get("_nao_verificado"):
        resultado.append(nv(
            "ssh.login_de_root", False,
            "exige privilegio que o usuario da coleta nao tem",
        ))
    else:
        login_root = ssh_cfg.get("login_de_root")
        resultado.append(ok("ssh.login_de_root", False, login_root)
                         if login_root is False
                         else desvio("ssh.login_de_root", False, login_root))

    # ── ntp.sincronizado ──
    ntp_esp = esperado.get("ntp", {}).get("sincronizado")
    ntp_enc = inv["ntp"]["sincronizado"]
    if ntp_enc is None:
        resultado.append(nv("ntp.sincronizado", ntp_esp, "timedatectl nao disponivel"))
    else:
        resultado.append(ok("ntp.sincronizado", ntp_esp, ntp_enc)
                         if ntp_enc == ntp_esp
                         else desvio("ntp.sincronizado", ntp_esp, ntp_enc))

    return resultado


def resumir(conformidade: list[dict]) -> dict:
    conforme = sum(1 for c in conformidade if c["veredito"] == "conforme")
    n_desvio = sum(1 for c in conformidade if c["veredito"] == "desvio")
    nao_v = sum(1 for c in conformidade if c["veredito"] == "nao_verificado")
    por_sev: dict = {}
    for c in conformidade:
        if c["veredito"] == "desvio":
            s = c.get("severidade", "info")
            por_sev[s] = por_sev.get(s, 0) + 1
    return {"conforme": conforme, "desvio": n_desvio, "nao_verificado": nao_v, "por_severidade": por_sev}


# ──────────────────────────────────────────────────────────────────
#  RENDERIZAÇÃO
# ──────────────────────────────────────────────────────────────────

def _limpar_meta(obj):
    """Remove campos internos com prefixo '_' recursivamente."""
    if isinstance(obj, dict):
        return {k: _limpar_meta(v) for k, v in obj.items() if not k.startswith("_")}
    if isinstance(obj, list):
        return [_limpar_meta(i) for i in obj]
    return obj


def renderizar_json(dados: dict, conformidade: list[dict]) -> str:
    saida = _limpar_meta(dados)
    saida.pop("_meta", None)
    saida["conformidade"] = conformidade
    saida["resumo"] = resumir(conformidade)
    return json.dumps(saida, ensure_ascii=False, indent=2)


def _fmt(v) -> str:
    """Formata um valor para exibição em Markdown: bool → true/false, None → null."""
    if v is True:
        return "true"
    if v is False:
        return "false"
    if v is None:
        return "null"
    return str(v)


def renderizar_markdown(dados: dict, conformidade: list[dict]) -> str:
    host = dados["host"]
    resumo = resumir(conformidade)
    ts = host["coletado_em"].replace("T", " ").replace("Z", " UTC")

    desvios = [c for c in conformidade if c["veredito"] == "desvio"]
    nao_vs = [c for c in conformidade if c["veredito"] == "nao_verificado"]
    conformes = [c for c in conformidade if c["veredito"] == "conforme"]

    linhas = [
        f"# Inventário — {host['hostname']} ({host['endereco']})",
        f"Coletado em {ts} · baseline v{dados.get('_baseline_versao', 1)}",
        "",
    ]

    linhas += ["## Desvios", ""]
    if desvios:
        _sev_ord = {"critico": 0, "alto": 1, "medio": 2, "info": 3}
        desvios_s = sorted(desvios, key=lambda c: _sev_ord.get(c.get("severidade", "info"), 99))
        _sev_pt = {"critico": "crítico", "alto": "alto", "medio": "médio", "info": "info"}
        linhas += ["| Severidade | Regra | Esperado | Encontrado |", "|---|---|---|---|"]
        for c in desvios_s:
            s = _sev_pt.get(c.get("severidade", "info"), c.get("severidade", ""))
            linhas.append(f"| {s} | {c['regra']} | {_fmt(c['esperado'])} | {_fmt(c['encontrado'])} |")
    else:
        linhas.append("*Nenhum desvio encontrado.*")
    linhas.append("")

    if nao_vs:
        linhas += ["## Não verificado", ""]
        linhas += ["| Regra | Motivo |", "|---|---|"]
        for c in nao_vs:
            linhas.append(f"| {c['regra']} | {c.get('motivo', '')} |")
        linhas.append("")

    if conformes:
        linhas += ["## Conforme", ""]
        # Deduplicate rule names while preserving order
        seen: set = set()
        nomes_uniq = []
        for c in conformes:
            if c["regra"] not in seen:
                seen.add(c["regra"])
                nomes_uniq.append(c["regra"])
        linhas.append(" · ".join(nomes_uniq))
        linhas.append("")

    linhas += [
        "---",
        f"**Resumo**: {resumo['conforme']} conforme · {resumo['desvio']} desvio · {resumo['nao_verificado']} não verificado",
    ]
    if resumo.get("por_severidade"):
        _pt = {"critico": "crítico", "alto": "alto", "medio": "médio"}
        partes = [f"{v} {_pt.get(k, k)}" for k, v in resumo["por_severidade"].items()]
        linhas.append(f"**Por severidade**: {' · '.join(partes)}")

    return "\n".join(linhas)


# ──────────────────────────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Audita uma VM contra baseline.yaml via SSH. Apenas leitura.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--host", required=True, help="Endereço IP ou hostname da VM")
    parser.add_argument("--user", required=True, help="Usuário SSH")
    parser.add_argument("--key", required=True, help="Caminho para a chave privada SSH")
    parser.add_argument("--baseline", default="baseline.yaml",
                        help="Arquivo baseline YAML (padrão: baseline.yaml)")
    parser.add_argument("--format", choices=["json", "md", "both"], default="both", dest="fmt")
    parser.add_argument("--porta", type=int, default=22, help="Porta SSH (padrão: 22)")
    args = parser.parse_args()

    # Carregar baseline
    try:
        with open(args.baseline) as f:
            baseline = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Erro: baseline não encontrado: {args.baseline}", file=sys.stderr)
        sys.exit(3)
    except yaml.YAMLError as e:
        print(f"Erro: baseline inválido — {e}", file=sys.stderr)
        sys.exit(3)

    # Conectar
    ssh = None
    try:
        ssh = SSHConexao(args.host, args.user, args.key, args.porta)
    except ConnectionError as e:
        print(f"Erro de conexão: {e}", file=sys.stderr)
        sys.exit(2)

    # Coletar
    try:
        coletor = Coletor(ssh)
        dados = coletor.coletar_tudo(args.host)
        dados["_baseline_versao"] = baseline.get("versao", 1)
    except Exception as e:
        print(f"Erro durante coleta: {e}", file=sys.stderr)
        sys.exit(3)
    finally:
        if ssh:
            ssh.fechar()

    # Auditar
    try:
        conformidade = auditar(baseline, dados)
    except Exception as e:
        print(f"Erro durante auditoria: {e}", file=sys.stderr)
        sys.exit(3)

    # Renderizar
    if args.fmt in ("json", "both"):
        print(renderizar_json(dados, conformidade))
    if args.fmt == "both":
        print("\n---\n")
    if args.fmt in ("md", "both"):
        print(renderizar_markdown(dados, conformidade))

    # Exit code
    sys.exit(1 if resumir(conformidade)["desvio"] > 0 else 0)


if __name__ == "__main__":
    main()
