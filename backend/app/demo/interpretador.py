"""Interpretador por palavras-chave: rede de segurança quando o LLM falha."""

import re

from pydantic import BaseModel

from app.domain.ajustes import Ajuste
from app.domain.modelos import Criterios, Eixo, Restricao
from app.domain.texto import normalizar


class Interpretacao(BaseModel):
    criterios: Criterios
    ajuste: Ajuste | None = None
    nega_doce: bool = False  # o texto disse "sem doce" e afins


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

# Formas de dizer "não pode ter": "sem", "nada de", "não como", "sou alérgico a"...
_NEGA = r"\b(?:sem|nada de|nao (?:como|posso comer|pode ter|quero)|alergic[oa] a|alergia a)"

_RESTRICOES: list[tuple[str, Restricao]] = [
    (rf"{_NEGA} carnes?\b", Restricao.vegetariano),
    (rf"{_NEGA} (?:lactose|leite)\b", Restricao.sem_lactose),
    (rf"{_NEGA} (?:gluten|trigo)\b", Restricao.sem_gluten),
    (r"vegetarian[oa]", Restricao.vegetariano),
    (r"vegan[oa]", Restricao.vegano),
    (rf"{_NEGA} amendoim\b", Restricao.sem_amendoim),
    (rf"{_NEGA} (?:frutos do mar|camarao)\b", Restricao.sem_frutos_do_mar),
    (rf"{_NEGA} ovos?\b", Restricao.sem_ovo),
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

# "batata doce" não é sobremesa; negações desligam o pedido de doce.
_BATATA_DOCE = r"batata[- ]doces?\b"
_SEM_DOCE = r"\bsem (?:doces?|sobremesas?)\b|\bnada doces?\b|\bnao (?:quero|quer|queria|precisa)(?: nenhum| nenhuma)? (?:doces?|sobremesas?)\b"
_DOCE = r"\bdoces?\b|sobremesa|chocolate|brigadeiro|acucar|docinho|sorvete|brownie"

_TEMPO = re.compile(r"(?:(?:ate|max(?:imo)?|em) )?\b(\d+) ?min\w*")
_ORCAMENTO = re.compile(
    r"\b(?:ate|max(?:imo)?)\b ?(?P<moeda>r ?\$|reais)? ?(?P<int>\d+)"
    r"(?:[.,](?P<dec>\d{1,2}))?(?P<fim> ?(?:reais|real|contos?)\b)?"
)
# Número solto seguido de outra unidade não é dinheiro ("até 2 pessoas", "70%").
_NAO_DINHEIRO = re.compile(
    r" ?(?:pessoas?\b|min\w*|unidades?\b|un\b|pecas?\b|%|graus?\b|porcoes\b|porcao\b)"
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
    barato, rapido, quer_doce = base.barato, base.rapido, base.quer_doce

    # 1. ajustes: o primeiro por posição vence; todos saem do texto
    achados = [
        (m.start(), ajuste)
        for padrao, ajuste in _AJUSTES
        for m in re.finditer(padrao, t)
    ]
    ajuste = min(achados, key=lambda a: a[0])[1] if achados else None
    for padrao, _ in _AJUSTES:
        _, t = _consumir(padrao, t)

    # 1b. batata doce não conta; "sem doce" desliga o pedido
    _, t = _consumir(_BATATA_DOCE, t)
    nega_doce, t = _consumir(_SEM_DOCE, t)
    if nega_doce:
        quer_doce = False

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
    for m in _ORCAMENTO.finditer(t):
        tem_moeda = bool(m.group("moeda") or m.group("fim"))
        if not tem_moeda and _NAO_DINHEIRO.match(t, m.end()):
            continue
        centavos = int(m.group("int")) * 100
        if m.group("dec"):
            centavos += int(m.group("dec").ljust(2, "0"))
        orcamento = centavos
        t = t[: m.start()] + " " + t[m.end() :]
        break

    # 4. negações antes dos positivos ("sem pimenta" também tira o ingrediente)
    if re.search(r"\bsem pimenta\b", t):
        excluidos.add("pimenta")
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
    if re.search(_DOCE, t):
        quer_doce = True

    criterios = Criterios(
        restricoes=restricoes,
        ingredientes_excluidos=excluidos,
        orcamento_max_centavos=orcamento,
        tempo_max_min=tempo,
        alvos=alvos,
        barato=barato,
        rapido=rapido,
        quer_doce=quer_doce,
    )
    return Interpretacao(criterios=criterios, ajuste=ajuste, nega_doce=nega_doce)


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
        saida.append(("orcamento", f"até R$\u00a0{criterios.orcamento_max_centavos // 100}"))
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
    if criterios.quer_doce:
        saida.append(("doce", "algo doce"))
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
    elif tipo == "doce":
        c.quer_doce = False
    return c
