"""Interpretador por palavras-chave: rede de segurança quando o LLM falha."""

import re

from pydantic import BaseModel

from app.domain.ajustes import Ajuste
from app.domain.modelos import Criterios, Eixo, Restricao
from app.domain.texto import normalizar


class Interpretacao(BaseModel):
    criterios: Criterios
    ajuste: Ajuste | None = None


# Frases de ajuste relativo (já sem acento). Removidas do texto antes de tudo.
_AJUSTES: list[tuple[str, Ajuste]] = [
    (r"mais barat[oa]", Ajuste.mais_barato),
    (r"mais rapid[oa]", Ajuste.mais_rapido),
    (r"mais leve", Ajuste.mais_leve),
    (r"menos gordur\w+", Ajuste.mais_leve),
    (r"mais quente", Ajuste.mais_quente),
    (r"mais fres[cq]\w+", Ajuste.mais_fresco),
    (r"menos picante", Ajuste.menos_picante),
    (r"mais picante", Ajuste.mais_picante),
]

_RESTRICOES: list[tuple[str, Restricao]] = [
    (r"sem lactose", Restricao.sem_lactose),
    (r"sem gluten", Restricao.sem_gluten),
    (r"vegetarian[oa]", Restricao.vegetariano),
    (r"vegan[oa]", Restricao.vegano),
    (r"sem amendoim", Restricao.sem_amendoim),
    (r"sem frutos do mar|sem camarao", Restricao.sem_frutos_do_mar),
    (r"sem ovo", Restricao.sem_ovo),
]

# (padrão, eixo, valor). A ordem importa: negações antes dos positivos.
_ALVOS_NEGADOS: list[tuple[str, Eixo, int]] = [
    (r"nao muito pesad\w*|nao pesad\w*", Eixo.peso, 25),
    (r"sem pimenta|nao picante", Eixo.picancia, 15),
]
_ALVOS: list[tuple[str, Eixo, int]] = [
    (r"leve no calor", Eixo.temperatura, 20),
    (r"quent|caldo|sopa", Eixo.temperatura, 85),
    (r"fresc|fresq|gelad", Eixo.temperatura, 20),
    (r"\bleve\b", Eixo.peso, 25),
    (r"pesad|caprichad|matar a fome", Eixo.peso, 80),
    (r"picant|apimentad", Eixo.picancia, 75),
    (r"reconfort|aconcheg|abraco", Eixo.conforto, 85),
]

_TEMPO = re.compile(r"(?:(?:ate|max(?:imo)?|em) )?\b(\d+) ?min\w*")
_ORCAMENTO = re.compile(
    r"(?:ate|max(?:imo)?) ?(?:r ?\$|reais)? ?(\d+)(?:[.,](\d{1,2}))?"
)
_SEM_INGREDIENTE = re.compile(r"\bsem (\w+)")


def _consumir(padrao: str | re.Pattern[str], texto: str) -> tuple[bool, str]:
    """Remove as ocorrências do padrão; diz se achou alguma."""
    novo, n = re.subn(padrao, " ", texto)
    return n > 0, novo


def interpretar(texto: str, atuais: Criterios | None) -> Interpretacao:
    t = normalizar(texto)
    base = atuais or Criterios()
    restricoes = set(base.restricoes)
    excluidos = set(base.ingredientes_excluidos)
    orcamento = base.orcamento_max_centavos
    tempo = base.tempo_max_min
    alvos = dict(base.alvos)
    barato, rapido = base.barato, base.rapido

    # 1. ajustes: o primeiro por posição vence; todos saem do texto
    achados = [
        (m.start(), ajuste)
        for padrao, ajuste in _AJUSTES
        for m in re.finditer(padrao, t)
    ]
    ajuste = min(achados, key=lambda a: a[0])[1] if achados else None
    for padrao, _ in _AJUSTES:
        _, t = _consumir(padrao, t)

    # 2. restrições (nunca viram ingrediente excluído)
    for padrao, restricao in _RESTRICOES:
        achou, t = _consumir(padrao, t)
        if achou:
            restricoes.add(restricao)

    # 3. tempo e orçamento (tempo primeiro: "até 30 min" não é dinheiro)
    m = _TEMPO.search(t)
    if m:
        tempo = int(m.group(1))
        t = _TEMPO.sub(" ", t)
    m = _ORCAMENTO.search(t)
    if m:
        centavos = int(m.group(1)) * 100
        if m.group(2):
            centavos += int(m.group(2).ljust(2, "0"))
        orcamento = centavos
        t = _ORCAMENTO.sub(" ", t)

    # 4. negações antes dos positivos
    for padrao, eixo, valor in _ALVOS_NEGADOS:
        achou, t = _consumir(padrao, t)
        if achou:
            alvos[eixo] = valor

    # 5. ingredientes excluídos
    for m in _SEM_INGREDIENTE.finditer(t):
        excluidos.add(m.group(1))
    t = _SEM_INGREDIENTE.sub(" ", t)

    # 6. positivos
    for padrao, eixo, valor in _ALVOS:
        achou, t = _consumir(padrao, t)
        if achou:
            alvos[eixo] = valor
    if re.search(r"barat|economic", t):
        barato = True
    if re.search(r"rapid|\blogo\b|pressa", t):
        rapido = True

    criterios = Criterios(
        restricoes=restricoes,
        ingredientes_excluidos=excluidos,
        orcamento_max_centavos=orcamento,
        tempo_max_min=tempo,
        alvos=alvos,
        barato=barato,
        rapido=rapido,
    )
    return Interpretacao(criterios=criterios, ajuste=ajuste)


_ROTULO_RESTRICAO = {
    Restricao.sem_lactose: "sem lactose",
    Restricao.sem_gluten: "sem glúten",
    Restricao.vegetariano: "vegetariano",
    Restricao.vegano: "vegano",
    Restricao.sem_amendoim: "sem amendoim",
    Restricao.sem_frutos_do_mar: "sem frutos do mar",
    Restricao.sem_ovo: "sem ovo",
}


def _rotulo_alvo(eixo: Eixo, valor: int) -> str:
    if eixo is Eixo.temperatura:
        return "quentinho" if valor >= 50 else "fresco"
    if eixo is Eixo.peso:
        return "leve" if valor < 50 else "caprichado"
    if eixo is Eixo.picancia:
        return "picante" if valor >= 50 else "sem picância"
    return "reconfortante"


def rotulos(criterios: Criterios) -> list[tuple[str, str]]:
    """Pares (chave, rótulo) das etiquetas "o que eu entendi", em ordem fixa."""
    saida: list[tuple[str, str]] = []
    for r in Restricao:  # ordem do enum, determinística
        if r in criterios.restricoes:
            saida.append((f"restricao:{r.value}", _ROTULO_RESTRICAO[r]))
    for ing in sorted(criterios.ingredientes_excluidos):
        saida.append((f"excluir:{ing}", f"sem {ing}"))
    if criterios.orcamento_max_centavos is not None:
        saida.append(("orcamento", f"até R$ {criterios.orcamento_max_centavos // 100}"))
    if criterios.tempo_max_min is not None:
        saida.append(("tempo", f"até {criterios.tempo_max_min} min"))
    for eixo in Eixo:
        if eixo in criterios.alvos:
            saida.append(
                (f"alvo:{eixo.value}", _rotulo_alvo(eixo, criterios.alvos[eixo]))
            )
    if criterios.barato:
        saida.append(("barato", "barato"))
    if criterios.rapido:
        saida.append(("rapido", "rápido"))
    return saida


def remover(criterios: Criterios, chave: str) -> Criterios:
    """Devolve novos critérios sem a etiqueta indicada; chave desconhecida não muda nada."""
    c = criterios.model_copy(deep=True)
    tipo, _, valor = chave.partition(":")
    if tipo == "restricao":
        c.restricoes = {r for r in c.restricoes if r.value != valor}
    elif tipo == "excluir":
        c.ingredientes_excluidos = c.ingredientes_excluidos - {valor}
    elif tipo == "orcamento":
        c.orcamento_max_centavos = None
    elif tipo == "tempo":
        c.tempo_max_min = None
    elif tipo == "alvo":
        c.alvos = {e: v for e, v in c.alvos.items() if e.value != valor}
    elif tipo == "barato":
        c.barato = False
    elif tipo == "rapido":
        c.rapido = False
    return c
