"""Avalia um provedor LLM nas frases de evals/frases.jsonl.

Uso:
    uv run python -m evals.rodar --base-url URL --modelo NOME [--api-key KEY]
        [--saida evals/resultados/<nome>.json]
"""

import argparse
import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any

from app.agente.agente import AgenteFalhou, _apelidos, _resolver, rodar_agente
from app.cardapio.repositorio import RepositorioArquivo
from app.config import Settings
from app.domain.filtro import passa_restricoes
from app.domain.modelos import Prato
from app.llm.cliente import ClienteLLM, ClienteOpenAICompativel, RespostaLLM
from evals.metricas import criterios_cobrem, resumir

FRASES = Path(__file__).parent / "frases.jsonl"
TIMEOUT_S = 60.0


class _Observador:
    """Repassa as chamadas ao LLM e guarda o que o passo 2 respondeu."""

    def __init__(self, llm: ClienteLLM) -> None:
        self._llm = llm
        self.respostas_ok = 0
        self.escrita: str | None = None

    async def conversar(
        self,
        mensagens: list[dict],
        ferramentas: list[dict] | None = None,
        json: bool = False,
    ) -> RespostaLLM:
        resposta = await self._llm.conversar(mensagens, ferramentas, json)
        self.respostas_ok += 1
        if json:
            self.escrita = resposta.conteudo
        return resposta


def _principal_do_modelo(escrita: str | None) -> Any:
    try:
        dados = json.loads(escrita or "")
    except ValueError:
        return None
    return dados.get("principal_id") if isinstance(dados, dict) else None


async def avaliar_frase(
    frase: dict[str, Any], pratos: list[Prato], llm: ClienteLLM
) -> dict[str, Any]:
    obs = _Observador(llm)
    linha: dict[str, Any] = {
        "texto": frase["texto"],
        "ok_passo1": False,
        "restricoes_corretas": False,
        "guarda_ok": None,
        "escolha_modelo": None,
        "erro": None,
        "criterios": None,
        "principal": None,
    }
    inicio = time.perf_counter()
    try:
        resultado = await rodar_agente(frase["texto"], None, None, pratos, obs)
    except Exception as e:  # noqa: BLE001 - registrar e seguir para a próxima frase
        linha["erro"] = f"{type(e).__name__}: {e}"
        # exceção depois da resposta do passo 1 (ex.: timeout ao redigir) não é falha do passo 1
        linha["ok_passo1"] = obs.respostas_ok >= 1 and not isinstance(e, AgenteFalhou)
    else:
        linha["ok_passo1"] = True
        c = resultado.criterios
        linha["criterios"] = c.model_dump(mode="json")
        linha["restricoes_corretas"] = criterios_cobrem(frase, c)
        e = resultado.escolha
        entregues = [p for p in [e.principal, *e.alternativas] if p is not None]
        linha["guarda_ok"] = all(passa_restricoes(p, c) for p in entregues)
        if e.principal is not None:
            linha["principal"] = e.principal.nome
            # a guarda aceitou o principal do modelo se o id dele resolve entre os candidatos
            aceito = _resolver(_principal_do_modelo(obs.escrita), _apelidos(e))
            linha["escolha_modelo"] = aceito is not None
    linha["latencia_s"] = round(time.perf_counter() - inicio, 3)
    return linha


def carregar_frases(caminho: Path = FRASES) -> list[dict[str, Any]]:
    return [
        json.loads(l)
        for l in caminho.read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]


def _fmt(valor: float | None, sufixo: str = "") -> str:
    return "n/d" if valor is None else f"{valor:.1f}{sufixo}"


def tabela_markdown(nome: str, r: dict[str, Any]) -> str:
    cabecalho = (
        "| Provedor / modelo | Sucesso passo 1 | Restrições corretas | Guarda 100% "
        "| Escolha do modelo usada | Latência p50 | Latência p95 |"
    )
    celulas = [
        nome,
        _fmt(r["sucesso_passo1_pct"], "%"),
        _fmt(r["restricoes_corretas_pct"], "%"),
        "sim" if r["guarda_100"] else "NÃO",
        _fmt(r["escolha_modelo_pct"], "%"),
        _fmt(r["latencia_p50_s"], " s"),
        _fmt(r["latencia_p95_s"], " s"),
    ]
    return "\n".join(
        [cabecalho, "|---|---|---|---|---|---|---|", f"| {' | '.join(celulas)} |"]
    )


async def avaliar(
    base_url: str, modelo: str, api_key: str, intervalo_s: float = 0.0
) -> list[dict[str, Any]]:
    settings = Settings(
        llm_base_url=base_url,
        llm_model=modelo,
        llm_api_key=api_key,
        llm_timeout_s=TIMEOUT_S,
    )
    llm = ClienteOpenAICompativel(settings)
    pratos = await RepositorioArquivo().pratos()
    linhas = []
    for i, frase in enumerate(carregar_frases(), start=1):
        if i > 1 and intervalo_s:
            # cotas gratuitas limitam tokens por minuto; a pausa não entra na latência
            await asyncio.sleep(intervalo_s)
        linha = await avaliar_frase(frase, pratos, llm)
        marca = "ok" if linha["ok_passo1"] and linha["restricoes_corretas"] else "falha"
        print(
            f"[{i:02d}] {marca} {linha['latencia_s']:.1f}s  {frase['texto']}",
            flush=True,
        )
        linhas.append(linha)
    return linhas


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--modelo", required=True)
    # Padrão: a chave vem de LLM_API_KEY no ambiente, para não aparecer na linha de comando.
    ap.add_argument("--api-key", default=os.environ.get("LLM_API_KEY", "sem-chave"))
    ap.add_argument("--intervalo", type=float, default=0.0, help="segundos entre frases")
    ap.add_argument("--saida", type=Path)
    args = ap.parse_args()

    linhas = asyncio.run(avaliar(args.base_url, args.modelo, args.api_key, args.intervalo))
    resumo = resumir(linhas)
    print()
    print(tabela_markdown(args.modelo, resumo))
    if args.saida:
        args.saida.parent.mkdir(parents=True, exist_ok=True)
        args.saida.write_text(
            json.dumps(
                {
                    "base_url": args.base_url,
                    "modelo": args.modelo,
                    "resumo": resumo,
                    "frases": linhas,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"\nResultados por frase em {args.saida}")


if __name__ == "__main__":
    main()
