from typing import Any

from app.domain.modelos import Prato


def prato(**sobrescritas: Any) -> Prato:
    base: dict[str, Any] = {
        "id": "p1",
        "nome": "Prato de teste",
        "descricao": "Descrição de teste",
        "restaurante_id": "r1",
        "restaurante_nome": "Restaurante Teste",
        "preco_centavos": 3000,
        "taxa_entrega_centavos": 500,
        "tempo_min": 30,
        "ingredientes": ["arroz", "feijão"],
        "atende": set(),
        "eixos": {},
        "foto_url": None,
    }
    base.update(sobrescritas)
    return Prato(**base)
