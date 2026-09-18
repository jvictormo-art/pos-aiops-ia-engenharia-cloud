"""
metacortex-dashboard — TUI de leitura contra o current-context do kubeconfig.

Uso: python3 app.py [--kubeconfig CAMINHO] [--namespace NOME]

Só lê. Ver spec/spec-decisoes.md — "Como a garantia de leitura fica visível
no projeto" — para a garantia estrutural de que nenhum verbo de escrita é
chamado por este código.
"""

from __future__ import annotations

import argparse
import sys

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Footer, Header, Input, Select, Static

from k8s_reader import ClusterReader, Resultado

POLL_INTERVAL_SEGUNDOS = 5


class PainelErro(Static):
    """Mensagem de erro central — usada para falhas fatais (conexão/credencial)."""


class MetacortexDashboard(App):
    CSS = """
    Screen { layout: vertical; }
    #controles { height: 3; padding: 0 1; }
    #controles Select { width: 30; margin-right: 2; }
    #controles Input { width: 40; }
    .painel-titulo { text-style: bold; background: $primary-darken-2; padding: 0 1; }
    .painel-erro-recurso { color: $warning; padding: 0 1; }
    .painel-vazio { color: $text-muted; padding: 0 1; }
    #rodape-status { height: 1; padding: 0 1; color: $text-muted; }
    """

    BINDINGS = [("q", "quit", "Sair")]

    def __init__(self, kubeconfig: str | None, namespace_inicial: str | None):
        super().__init__()
        self._kubeconfig = kubeconfig
        self._namespace_inicial = namespace_inicial
        self._reader: ClusterReader | None = None
        self._namespace_atual: str | None = None
        self._busca_atual: str = ""
        self._paineis_restritos = 0

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="controles"):
            yield Select([], id="select-namespace", prompt="Namespace")
            yield Input(placeholder="Buscar por nome...", id="input-busca")
        yield PainelErro("Conectando ao cluster...", id="painel-erro")
        with Vertical(id="area-dados"):
            yield Static("PODS", classes="painel-titulo")
            yield DataTable(id="tabela-pods")
            yield Static("DEPLOYMENTS", classes="painel-titulo")
            yield DataTable(id="tabela-deployments")
            yield Static("SERVICES", classes="painel-titulo")
            yield DataTable(id="tabela-services")
            yield Static("EVENTOS RECENTES", classes="painel-titulo")
            yield DataTable(id="tabela-eventos")
        yield Static("", id="rodape-status")
        yield Footer()

    def on_mount(self) -> None:
        self._preparar_colunas_tabelas()
        self.query_one("#area-dados", Vertical).display = False
        self._conectar_e_iniciar()

    def _conectar_e_iniciar(self) -> None:
        try:
            self._reader = ClusterReader(self._kubeconfig)
        except RuntimeError as e:
            self._mostrar_erro_fatal(str(e))
            return

        teste = self._reader.testar_conexao()
        if not teste.ok:
            self._mostrar_erro_fatal(self._formatar_erro_fatal(teste))
            return

        self.title = "metacortex-dashboard"
        self.sub_title = f"contexto: {self._reader.contexto_atual}"

        ns_result = self._reader.listar_namespaces()
        if not ns_result.ok:
            self._mostrar_erro_fatal(self._formatar_erro_fatal(ns_result))
            return

        self._esconder_erro_mostrar_dados()
        select = self.query_one("#select-namespace", Select)
        select.set_options([(ns, ns) for ns in ns_result.dados])
        escolhido = self._namespace_inicial if self._namespace_inicial in ns_result.dados else ns_result.dados[0]
        select.value = escolhido
        self._namespace_atual = escolhido

        self.set_interval(POLL_INTERVAL_SEGUNDOS, self._atualizar_paineis)
        self._atualizar_paineis()

    def _formatar_erro_fatal(self, resultado: Resultado) -> str:
        contexto = self._reader.contexto_atual if self._reader else "(desconhecido)"
        if resultado.tipo_erro == "conexao":
            return (
                f'Não foi possível conectar ao cluster do contexto "{contexto}".\n'
                f"{resultado.mensagem}\n"
                'Verifique se o cluster está no ar ou troque o contexto com "kubectl config use-context".'
            )
        if resultado.tipo_erro == "credencial":
            return (
                f'Credencial expirada ou inválida para o contexto "{contexto}".\n'
                "Renove a credencial e reabra a aplicação."
            )
        return f"Erro ao inicializar: {resultado.mensagem}"

    def _mostrar_erro_fatal(self, mensagem: str) -> None:
        painel = self.query_one("#painel-erro", PainelErro)
        painel.update(mensagem)
        painel.display = True
        self.query_one("#area-dados", Vertical).display = False

    def _esconder_erro_mostrar_dados(self) -> None:
        self.query_one("#painel-erro", PainelErro).display = False
        self.query_one("#area-dados", Vertical).display = True

    def _preparar_colunas_tabelas(self) -> None:
        self.query_one("#tabela-pods", DataTable).add_columns("NOME", "READY", "STATUS", "RESTARTS", "MOTIVO")
        self.query_one("#tabela-deployments", DataTable).add_columns("NOME", "PRONTOS/DESEJADOS", "CONDIÇÃO")
        self.query_one("#tabela-services", DataTable).add_columns("NOME", "ENDPOINT")
        self.query_one("#tabela-eventos", DataTable).add_columns("TIPO", "RAZÃO", "OBJETO", "MENSAGEM", "IDADE")

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "select-namespace" and event.value is not None:
            self._namespace_atual = str(event.value)
            self._atualizar_paineis()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "input-busca":
            self._busca_atual = event.value.lower()
            self._atualizar_paineis()

    def _filtrar(self, linhas: list[dict], campo: str) -> list[dict]:
        if not self._busca_atual:
            return linhas
        return [l for l in linhas if self._busca_atual in str(l.get(campo, "")).lower()]

    def _atualizar_paineis(self) -> None:
        if not self._reader or not self._namespace_atual:
            return

        restritos = 0
        restritos += self._preencher_tabela(
            "tabela-pods", self._reader.listar_pods(self._namespace_atual),
            campo_busca="nome",
            colunas=lambda p: (p["nome"], p["ready"], p["status"], str(p["restarts"]), p["motivo"] or "(aguardando)"),
            vazio_msg="Nenhum Pod neste namespace",
        )
        restritos += self._preencher_tabela(
            "tabela-deployments", self._reader.listar_deployments(self._namespace_atual),
            campo_busca="nome",
            colunas=lambda d: (d["nome"], f'{d["pronto"]}/{d["desejado"]}', d["condicao"]),
            vazio_msg="Nenhum Deployment neste namespace",
        )
        restritos += self._preencher_tabela(
            "tabela-services", self._reader.listar_services_com_endpoint(self._namespace_atual),
            campo_busca="nome",
            colunas=lambda s: (s["nome"], s["endpoint_texto"]),
            vazio_msg="Nenhum Service neste namespace",
        )
        restritos += self._preencher_tabela(
            "tabela-eventos", self._reader.listar_eventos(self._namespace_atual),
            campo_busca="objeto",
            colunas=lambda e: (e["tipo"], e["razao"], e["objeto"], e["mensagem"][:60], e["idade"]),
            vazio_msg="Nenhum evento recente neste namespace",
        )

        self._paineis_restritos = restritos
        rodape = self.query_one("#rodape-status", Static)
        if restritos:
            rodape.update(f"⚠ {restritos} painel(is) com acesso restrito neste contexto")
        else:
            rodape.update("")

    def _preencher_tabela(self, table_id: str, resultado: Resultado, campo_busca: str, colunas, vazio_msg: str) -> int:
        tabela = self.query_one(f"#{table_id}", DataTable)
        tabela.clear()
        n_colunas = len(tabela.columns)

        def linha_unica(texto: str) -> tuple:
            return (texto,) + ("",) * (n_colunas - 1)

        if not resultado.ok:
            if resultado.tipo_erro == "permissao":
                tabela.add_row(*linha_unica("[Sem permissão para listar este recurso (403)]"))
                return 1
            tabela.add_row(*linha_unica(f"[Erro: {resultado.mensagem}]"))
            return 0

        linhas = self._filtrar(resultado.dados, campo_busca)
        if not linhas:
            tabela.add_row(*linha_unica(vazio_msg))
            return 0

        for item in linhas:
            tabela.add_row(*colunas(item))
        return 0


def main():
    parser = argparse.ArgumentParser(description="metacortex-dashboard — leitura do cluster do current-context")
    parser.add_argument("--kubeconfig", default=None, help="Caminho do kubeconfig (padrão: ~/.kube/config)")
    parser.add_argument("--namespace", default=None, help="Namespace inicial (padrão: primeiro em ordem alfabética)")
    args = parser.parse_args()

    app = MetacortexDashboard(kubeconfig=args.kubeconfig, namespace_inicial=args.namespace)
    app.run()


if __name__ == "__main__":
    main()
