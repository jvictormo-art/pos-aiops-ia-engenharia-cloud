"""
Camada de leitura contra a API do Kubernetes.

Invariante estrutural: este módulo só importa e chama métodos list_*/get_*
do cliente oficial. Nenhum create_*/patch_*/delete_*/replace_* aparece aqui.
Isso é verificado por grep em tarefas.md — não é apenas uma promessa em texto.
"""

from __future__ import annotations

import json
import socket
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from kubernetes.config.config_exception import ConfigException
from urllib3.exceptions import MaxRetryError, NewConnectionError, SSLError as Urllib3SSLError


# ──────────────────────────────────────────────────────────────────
#  RESULTADO TIPADO — nunca deixa a exceção subir para a UI crua
# ──────────────────────────────────────────────────────────────────

@dataclass
class Resultado:
    ok: bool
    dados: Any = None
    tipo_erro: Optional[str] = None   # "conexao" | "credencial" | "permissao" | "interno"
    mensagem: Optional[str] = None

    @staticmethod
    def sucesso(dados: Any) -> "Resultado":
        return Resultado(ok=True, dados=dados)

    @staticmethod
    def erro(tipo: str, mensagem: str) -> "Resultado":
        return Resultado(ok=False, tipo_erro=tipo, mensagem=mensagem)


def _classificar_excecao(e: Exception) -> Resultado:
    if isinstance(e, ApiException):
        if e.status == 401:
            return Resultado.erro("credencial", "Credencial expirada ou inválida para este contexto.")
        if e.status == 403:
            return Resultado.erro("permissao", "Sem permissão para listar este recurso no contexto atual (403).")
        if e.status == 404:
            return Resultado.erro("interno", f"Recurso não encontrado: {e.reason}")
        return Resultado.erro("interno", f"Erro da API ({e.status}): {e.reason}")

    # mTLS (certificado cliente): uma credencial inválida/expirada nunca chega a
    # completar o handshake TLS — não existe um 401 HTTP aqui, porque não há uma
    # sessão HTTP autenticada para o apiserver rejeitar. Falha na própria camada
    # TLS. Descoberto testando este cenário contra um cluster kind real (ver
    # curadoria.md) — o spec original assumia 401 para toda credencial inválida,
    # o que só vale para autenticação por token/OIDC, não para certificado cliente.
    causa = getattr(e, "__cause__", None) or getattr(e, "__context__", None)
    if isinstance(e, MaxRetryError) and isinstance(causa, Urllib3SSLError):
        return Resultado.erro("credencial", f"Certificado de cliente inválido ou corrompido: {causa}")
    if isinstance(e, (MaxRetryError, NewConnectionError, socket.timeout, ConnectionRefusedError, OSError)):
        return Resultado.erro("conexao", f"Não foi possível conectar ao cluster: {e}")
    return Resultado.erro("interno", f"Erro inesperado: {e}")


# ──────────────────────────────────────────────────────────────────
#  LEITURA
# ──────────────────────────────────────────────────────────────────

class ClusterReader:
    """Lê o current-context do kubeconfig. Não escreve nada no cluster."""

    def __init__(self, kubeconfig_path: Optional[str] = None):
        try:
            config.load_kube_config(config_file=kubeconfig_path)
        except ConfigException as e:
            raise RuntimeError(f"Kubeconfig inválido ou ausente: {e}")

        self.contexto_atual = config.list_kube_config_contexts(config_file=kubeconfig_path)[1]["name"]
        self._core = client.CoreV1Api()
        self._apps = client.AppsV1Api()
        self._discovery = client.DiscoveryV1Api()

    def testar_conexao(self) -> Resultado:
        try:
            self._core.list_namespace(limit=1, _request_timeout=5)
            return Resultado.sucesso(True)
        except Exception as e:
            return _classificar_excecao(e)

    def listar_namespaces(self) -> Resultado:
        try:
            resp = self._core.list_namespace(_request_timeout=10)
            nomes = [ns.metadata.name for ns in resp.items]
            return Resultado.sucesso(sorted(nomes))
        except Exception as e:
            return _classificar_excecao(e)

    def listar_pods(self, namespace: str) -> Resultado:
        try:
            resp = self._core.list_namespaced_pod(namespace, _request_timeout=10)
            pods = [self._resumir_pod(p) for p in resp.items]
            return Resultado.sucesso(pods)
        except Exception as e:
            return _classificar_excecao(e)

    def _resumir_pod(self, pod) -> dict:
        status = pod.status
        container_statuses = status.container_statuses or []
        init_statuses = status.init_container_statuses or []

        ready_count = sum(1 for cs in container_statuses if cs.ready)
        total = len(container_statuses)
        restarts = sum(cs.restart_count for cs in container_statuses) if container_statuses else 0
        restarts += sum(cs.restart_count for cs in init_statuses) if init_statuses else 0

        # initContainer pendente/falho é a causa real quando existe — verificar
        # ANTES dos containers principais. Achado real: um pod com o initContainer
        # em ImagePullBackOff reporta o container principal como "PodInitializing"
        # (verdadeiro, mas inútil) — kubectl mostra "Init:ImagePullBackOff" e é
        # esse o motivo que precisa aparecer, não o do container principal.
        # Ver curadoria.md.
        motivo = None
        init_pendente = False
        for cs in init_statuses:
            if cs.state and cs.state.waiting and cs.state.waiting.reason:
                motivo = f"Init:{cs.state.waiting.reason}"
                init_pendente = True
            if cs.state and cs.state.terminated and cs.state.terminated.reason and cs.state.terminated.exit_code != 0:
                motivo = f"Init:{cs.state.terminated.reason}"
                init_pendente = True

        if not init_pendente:
            for cs in container_statuses:
                if cs.state and cs.state.waiting and cs.state.waiting.reason:
                    motivo = cs.state.waiting.reason
                if cs.last_state and cs.last_state.terminated and cs.last_state.terminated.reason:
                    # causa mais específica disponível — substitui o motivo de waiting
                    motivo = cs.last_state.terminated.reason

        return {
            "nome": pod.metadata.name,
            "ready": f"{ready_count}/{total}" if total else "0/0",
            "status": status.phase,
            "restarts": restarts,
            "motivo": motivo,
        }

    def listar_deployments(self, namespace: str) -> Resultado:
        try:
            resp = self._apps.list_namespaced_deployment(namespace, _request_timeout=10)
            deploys = [self._resumir_deployment(d) for d in resp.items]
            return Resultado.sucesso(deploys)
        except Exception as e:
            return _classificar_excecao(e)

    def _resumir_deployment(self, dep) -> dict:
        desejado = dep.spec.replicas if dep.spec.replicas is not None else 0
        # readyReplicas é omitido pela API quando zero réplicas estão prontas —
        # None e 0 são tratados como equivalentes para exibição (ver spec-comportamento.md)
        pronto = dep.status.ready_replicas or 0

        condicao = None
        if dep.status.conditions:
            for c in dep.status.conditions:
                if c.type == "Available":
                    condicao = c.reason or c.type
        return {
            "nome": dep.metadata.name,
            "pronto": pronto,
            "desejado": desejado,
            "condicao": condicao or "(sem condição reportada)",
        }

    def listar_services_com_endpoint(self, namespace: str) -> Resultado:
        try:
            svc_resp = self._core.list_namespaced_service(namespace, _request_timeout=10)
            resultado = []
            for svc in svc_resp.items:
                n_prontos = self._contar_endpoints_prontos(namespace, svc.metadata.name)
                resultado.append({
                    "nome": svc.metadata.name,
                    "endpoint_texto": "sem endpoint" if n_prontos == 0 else f"{n_prontos} endereço(s)",
                })
            return Resultado.sucesso(resultado)
        except Exception as e:
            return _classificar_excecao(e)

    def _contar_endpoints_prontos(self, namespace: str, service_name: str) -> int:
        """Soma endereços prontos através de TODAS as EndpointSlices do Service.
        Um Service pode ter mais de uma fatia (particionamento em blocos de 100).

        Usa leitura crua (_preload_content=False + json.loads) em vez do modelo
        tipado do cliente. Motivo real, encontrado contra o cluster deste ticket:
        quando um EndpointSlice não tem nenhum endpoint, a API retorna
        `"endpoints": null` (não uma lista vazia) — e o modelo gerado pelo
        cliente oficial trata `endpoints` como campo obrigatório não-nulo,
        lançando ValueError ao desserializar. Isso derrubaria a listagem do
        namespace inteiro por causa de UMA fatia vazia. Ver curadoria.md.
        """
        try:
            resp = self._discovery.list_namespaced_endpoint_slice(
                namespace,
                label_selector=f"kubernetes.io/service-name={service_name}",
                _request_timeout=10,
                _preload_content=False,
            )
            bruto = json.loads(resp.data)
        except ApiException:
            return 0

        total = 0
        for sl in bruto.get("items", []):
            for ep in (sl.get("endpoints") or []):
                condicoes = ep.get("conditions") or {}
                if condicoes.get("ready"):
                    total += len(ep.get("addresses") or [])
        return total

    def listar_eventos(self, namespace: str, limite: int = 20) -> Resultado:
        try:
            resp = self._core.list_namespaced_event(namespace, _request_timeout=10)
            eventos = sorted(
                resp.items,
                key=lambda e: e.last_timestamp or e.event_time or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True,
            )[:limite]
            return Resultado.sucesso([self._resumir_evento(e) for e in eventos])
        except Exception as e:
            return _classificar_excecao(e)

    def _resumir_evento(self, ev) -> dict:
        ts = ev.last_timestamp or ev.event_time
        idade = "?"
        if ts:
            delta = datetime.now(timezone.utc) - ts
            minutos = int(delta.total_seconds() // 60)
            idade = f"{minutos}m" if minutos < 60 else f"{minutos // 60}h"
        return {
            "tipo": ev.type,
            "razao": ev.reason,
            "objeto": f"{ev.involved_object.kind}/{ev.involved_object.name}",
            "mensagem": (ev.message or "").strip(),
            "idade": idade,
        }
