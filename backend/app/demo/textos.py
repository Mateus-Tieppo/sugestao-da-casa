"""Textos prontos, no tom de um garçom que conhece a casa."""

from app.demo.interpretador import rotulos
from app.domain.afrouxar import PropostaAfrouxar
from app.domain.modelos import Criterios, Eixo, Prato
from app.domain.texto import normalizar

_FEMININOS = {
    "sopa", "salada", "moqueca", "lasanha", "torta", "pizza",
    "tapioca", "panqueca", "omelete", "quiche",
}  # fmt: skip

LIMITE_EXPLICACAO = 160
_MINIMO_DIFERENCA = 15  # pontos de eixo ou % de preço/tempo


def frase_decisao(prato: Prato) -> str:
    primeira = normalizar(prato.nome).split(" ")[0] if prato.nome.strip() else ""
    artigo = "uma" if primeira in _FEMININOS else "um"
    return f"Hoje pede {artigo} {prato.nome}."


def explicar(prato: Prato, criterios: Criterios) -> str:
    # alvos primeiro: são o que mais pesa no gosto; depois o resto
    alvos = [r for k, r in rotulos(criterios) if k.startswith("alvo:")]
    resto = [r for k, r in rotulos(criterios) if not k.startswith("alvo:")]
    motivos = (alvos + resto)[:2]
    if not motivos:
        texto = (
            f"A cozinha do {prato.restaurante_nome} acerta a mão nesse, vale a escolha."
        )
    else:
        texto = f"Vem {' e '.join(motivos)}, do jeito que você pediu."
    if len(texto) > LIMITE_EXPLICACAO:
        texto = "Vem do jeito que você pediu."
    return texto


def _reais(centavos: int) -> str:
    inteiro, resto = divmod(centavos, 100)
    valor = f"{inteiro}" if resto == 0 else f"{inteiro},{resto:02d}"
    return f"R$\u00a0{valor}"  # espaço não separável: "R$ 19" nunca quebra linha


def mensagem_afrouxar(proposta: PropostaAfrouxar) -> str:
    partes = []
    for m in proposta.mudancas:
        if m.campo == "orcamento":
            partes.append(f"subir para {_reais(m.valor_sugerido)}")
        else:
            partes.append(f"der para esperar {m.valor_sugerido} min")
    return (
        f"Com tudo isso junto não achei nada, mas se {' e '.join(partes)} "
        f"tem {proposta.prato.nome}."
    )


_EIXO_FRASES: dict[Eixo, tuple[str, str | None]] = {
    # eixo: (frase se a alternativa tem mais, frase se tem menos)
    Eixo.peso: ("mais caprichado", "mais leve"),
    Eixo.temperatura: ("mais quentinho", "mais fresco"),
    Eixo.picancia: ("um toque de picância", "mais suave"),
    Eixo.conforto: ("mais reconfortante", None),
}


def diferenca(alternativa: Prato, principal: Prato) -> str:
    """Frase curta (até 40 caracteres) da maior diferença da alternativa para o prato principal."""
    candidatos: list[tuple[float, str]] = []
    for eixo, (mais, menos) in _EIXO_FRASES.items():
        if eixo not in alternativa.eixos or eixo not in principal.eixos:
            continue
        delta = alternativa.eixos[eixo] - principal.eixos[eixo]
        frase = mais if delta > 0 else menos
        if frase:
            candidatos.append((abs(delta), frase))
    if principal.total_centavos > 0:
        queda = (principal.total_centavos - alternativa.total_centavos) * 100
        candidatos.append((queda / principal.total_centavos, "mais em conta"))
    if principal.tempo_min > 0:
        queda = (principal.tempo_min - alternativa.tempo_min) * 100
        candidatos.append((queda / principal.tempo_min, "chega mais rápido"))
    if not candidatos:
        return "outra boa opção"
    forca, frase = max(candidatos, key=lambda c: c[0])
    return frase if forca >= _MINIMO_DIFERENCA else "outra boa opção"
