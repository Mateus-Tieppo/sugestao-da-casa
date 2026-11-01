"use client";

import { useCallback, useEffect, useReducer, useRef } from "react";
import { ehCancelamento, FalhaApi, pedirSugestao, type TipoFalha } from "./api";
import { LIMITES, type Criterios, type PedidoSugestao, type PropostaSugerida, type RespostaSugestao } from "./tipos";

export type Fase = "inicio" | "pensando" | "resultado" | "sem_resultado" | "falha";

export interface EstadoSessao {
  fase: Fase;
  /** Última resposta recebida; permanece durante "pensando" e "falha". */
  resposta: RespostaSugestao | null;
  ultimoPedido: PedidoSugestao | null;
  erro: TipoFalha | null;
}

export type AcaoSessao =
  | { tipo: "enviado"; pedido: PedidoSugestao }
  | { tipo: "respondido"; resposta: RespostaSugestao }
  | { tipo: "falhou"; erro: TipoFalha }
  | { tipo: "reiniciou" };

export const estadoInicial: EstadoSessao = {
  fase: "inicio",
  resposta: null,
  ultimoPedido: null,
  erro: null,
};

export function reducerSessao(estado: EstadoSessao, acao: AcaoSessao): EstadoSessao {
  switch (acao.tipo) {
    case "enviado":
      return { ...estado, fase: "pensando", ultimoPedido: acao.pedido, erro: null };
    case "respondido":
      return {
        ...estado,
        fase: acao.resposta.status === "ok" ? "resultado" : "sem_resultado",
        resposta: acao.resposta,
        erro: null,
      };
    case "falhou":
      return { ...estado, fase: "falha", erro: acao.erro };
    case "reiniciou":
      return estadoInicial;
  }
}

/** Devolve novos critérios sem a etiqueta de `chave` (espelha demo/interpretador.remover). */
export function removerCriterio(criterios: Criterios, chave: string): Criterios {
  const c: Criterios = { ...criterios, restricoes: [...criterios.restricoes], alvos: { ...criterios.alvos } };
  const i = chave.indexOf(":");
  const tipo = i < 0 ? chave : chave.slice(0, i);
  const valor = i < 0 ? "" : chave.slice(i + 1);
  switch (tipo) {
    case "restricao":
      c.restricoes = c.restricoes.filter((r) => r !== valor);
      break;
    case "excluir":
      c.ingredientes_excluidos = c.ingredientes_excluidos.filter((x) => x !== valor);
      break;
    case "orcamento":
      c.orcamento_max_centavos = null;
      break;
    case "tempo":
      c.tempo_max_min = null;
      break;
    case "alvo":
      delete c.alvos[valor as keyof Criterios["alvos"]];
      break;
    case "barato":
      c.barato = false;
      break;
    case "rapido":
      c.rapido = false;
      break;
    case "doce":
      c.quer_doce = false;
      break;
  }
  return c;
}

/** Aplica ao critério atual todas as mudanças da proposta (só orçamento e tempo). */
export function aplicarProposta(criterios: Criterios, proposta: PropostaSugerida): Criterios {
  const c: Criterios = { ...criterios };
  for (const m of proposta.mudancas) {
    if (m.campo === "orcamento") c.orcamento_max_centavos = m.valor_sugerido;
    else if (m.campo === "tempo") c.tempo_max_min = m.valor_sugerido;
  }
  return c;
}

export function useSessao() {
  const [estado, dispatch] = useReducer(reducerSessao, estadoInicial);
  const controlador = useRef<AbortController | null>(null);
  const sequencia = useRef(0);
  const respostaAtual = useRef<RespostaSugestao | null>(null);
  const pedidoAtual = useRef<PedidoSugestao | null>(null);
  /** Prato na tela agora: a escolha da casa ou a alternativa que a pessoa promoveu. */
  const pratoAtualId = useRef<string | null>(null);

  const disparar = useCallback((pedido: PedidoSugestao) => {
    controlador.current?.abort();
    const ctl = new AbortController();
    controlador.current = ctl;
    const minha = ++sequencia.current;
    pedidoAtual.current = pedido;
    dispatch({ tipo: "enviado", pedido });

    pedirSugestao(pedido, ctl.signal).then(
      (resposta) => {
        if (minha !== sequencia.current || ctl.signal.aborted) return;
        respostaAtual.current = resposta;
        pratoAtualId.current = resposta.principal?.id ?? null;
        dispatch({ tipo: "respondido", resposta });
      },
      (e: unknown) => {
        if (minha !== sequencia.current || ctl.signal.aborted || ehCancelamento(e)) return;
        dispatch({ tipo: "falhou", erro: e instanceof FalhaApi ? e.tipo : "rede" });
      },
    );
  }, []);

  useEffect(
    () => () => {
      sequencia.current++;
      controlador.current?.abort();
    },
    [],
  );

  const enviar = useCallback(
    (texto: string) => {
      const r = respostaAtual.current;
      const limpo = texto.trim().slice(0, LIMITES.texto).trim();
      if (!limpo && !r) return;
      disparar({
        texto: limpo || null,
        criterios: r?.criterios ?? null,
        prato_atual_id: r ? pratoAtualId.current : null,
      });
    },
    [disparar],
  );

  const removerEtiqueta = useCallback(
    (chave: string) => {
      const r = respostaAtual.current;
      if (!r) return;
      disparar({
        texto: null,
        criterios: removerCriterio(r.criterios, chave),
        prato_atual_id: pratoAtualId.current,
      });
    },
    [disparar],
  );

  const aceitarProposta = useCallback(() => {
    const r = respostaAtual.current;
    if (!r?.proposta) return;
    disparar({
      texto: null,
      criterios: aplicarProposta(r.criterios, r.proposta),
      prato_atual_id: null,
    });
  }, [disparar]);

  /** Promove uma alternativa sem nova chamada: só muda a referência dos próximos ajustes. */
  const escolherPrato = useCallback((id: string) => {
    pratoAtualId.current = id;
  }, []);

  const tentarDeNovo = useCallback(() => {
    if (pedidoAtual.current) disparar(pedidoAtual.current);
  }, [disparar]);

  /** Volta ao início: cancela o que estiver em andamento e esquece a conversa. */
  const reiniciar = useCallback(() => {
    sequencia.current++;
    controlador.current?.abort();
    respostaAtual.current = null;
    pedidoAtual.current = null;
    pratoAtualId.current = null;
    dispatch({ tipo: "reiniciou" });
  }, []);

  return { estado, enviar, removerEtiqueta, aceitarProposta, tentarDeNovo, escolherPrato, reiniciar };
}
