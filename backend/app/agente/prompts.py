"""Prompts e esquema da ferramenta do agente."""

from app.domain.ajustes import Ajuste
from app.domain.modelos import Eixo, Restricao

SISTEMA = """Você é "o garçom da casa": uma pessoa com vontade vaga de comer chega e você decide por ela, com confiança.
Responda sempre em português do Brasil, sem emoji.

Passo 1: entender o pedido. Chame a ferramenta buscar_pratos UMA vez com os critérios que a pessoa expressou.
- Valores de dinheiro vão em centavos (R$ 40 = 4000).
- Restrições ditas pela pessoa (sem lactose, vegano etc.) são sempre duras: inclua em restricoes e mantenha as que já estavam nos critérios atuais.
- Palavras vagas (leve, quentinho, reconfortante, picante, barato, rápido) viram alvos (0 a 100), barato ou rapido. Nunca invente limites numéricos que a pessoa não disse.
- Pedidos relativos ao prato atual ("mais barato", "mais leve") vão no campo ajuste.

Passo 2: com os candidatos devolvidos, escolha o prato que melhor responde ao pedido.
- Nunca invente prato fora dos candidatos; use apenas ids da lista.
- Explicações de 1 a 2 frases, até 160 caracteres, ligando o prato às palavras da pessoa.
- Escolha no máximo 2 alternativas, cada uma com uma diferença curta (até 40 caracteres) em relação ao principal."""

PEDIDO_ESCRITA = (
    "Agora escolha entre os candidatos acima e responda SOMENTE um objeto JSON no formato "
    '{"principal_id": "id", "alternativas": [{"id": "id", "diferenca": "frase curta"}], '
    '"frase_decisao": "Hoje pede ...", "explicacoes": {"id": "texto"}}. '
    "Inclua explicações para o principal e para as alternativas. Use só ids dos candidatos."
)

_INTEIRO_OU_NULO = {"type": ["integer", "null"]}

FERRAMENTA_BUSCAR_PRATOS: dict = {
    "type": "function",
    "function": {
        "name": "buscar_pratos",
        "description": (
            "Busca no cardápio os pratos que respeitam os critérios. "
            "Dinheiro em centavos (R$ 40 = 4000)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "restricoes": {
                    "type": "array",
                    "items": {"type": "string", "enum": [r.value for r in Restricao]},
                    "description": "Restrições duras, incluindo as já ativas.",
                },
                "ingredientes_excluidos": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Ingredientes a evitar, minúsculas e sem acento.",
                },
                "orcamento_max_centavos": {
                    **_INTEIRO_OU_NULO,
                    "description": "Orçamento máximo em centavos, só se a pessoa disse um valor.",
                },
                "tempo_max_min": {
                    **_INTEIRO_OU_NULO,
                    "description": "Tempo máximo em minutos, só se a pessoa disse um valor.",
                },
                "alvos": {
                    "type": "object",
                    "properties": {
                        e.value: {"type": "integer", "minimum": 0, "maximum": 100}
                        for e in Eixo
                    },
                    "description": (
                        "Eixos de 0 a 100. temperatura: 0 fresco, 100 quentinho. "
                        "peso: 0 leve, 100 pesado. picancia. conforto."
                    ),
                },
                "barato": {"type": "boolean"},
                "rapido": {"type": "boolean"},
                "ajuste": {
                    "type": ["string", "null"],
                    "enum": [*(a.value for a in Ajuste), None],
                    "description": "Pedido relativo ao prato atual, se houver.",
                },
            },
            "required": [],
        },
    },
}
