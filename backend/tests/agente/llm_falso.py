import copy

from app.llm.cliente import RespostaLLM


class LLMRoteirizado:
    """LLM de teste: devolve as respostas na ordem e registra o que recebeu."""

    def __init__(self, respostas: list[RespostaLLM | Exception]) -> None:
        self._respostas = list(respostas)
        self.mensagens_recebidas: list[list[dict]] = []
        self.ferramentas_recebidas: list[list[dict] | None] = []
        self.json_recebido: list[bool] = []

    async def conversar(
        self,
        mensagens: list[dict],
        ferramentas: list[dict] | None = None,
        json: bool = False,
    ) -> RespostaLLM:
        self.mensagens_recebidas.append(copy.deepcopy(mensagens))
        self.ferramentas_recebidas.append(ferramentas)
        self.json_recebido.append(json)
        resposta = self._respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta
