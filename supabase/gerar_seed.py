#!/usr/bin/env python3
"""Gera supabase/seed.sql a partir de supabase/cardapio.json (só stdlib)."""

import json
from pathlib import Path

# Regra das fotos: foto_url não pode mostrar nenhum ingrediente que contradiga o `atende` do prato.
RAIZ = Path(__file__).resolve().parent


def literal(valor) -> str:
    if valor is None:
        return "null"
    if isinstance(valor, int):
        return str(valor)
    return "'" + str(valor).replace("'", "''") + "'"


def array(itens: list[str]) -> str:
    return "array[" + ", ".join(literal(i) for i in itens) + "]::text[]"


def gerar(dados: dict) -> str:
    saida = [
        "-- Gerado por supabase/gerar_seed.py a partir de cardapio.json. Não edite à mão.",
        "",
    ]
    for r in dados["restaurantes"]:
        saida.append(
            "insert into public.restaurantes "
            "(id, nome, taxa_entrega_centavos, tempo_entrega_min) values "
            f"({literal(r['id'])}, {literal(r['nome'])}, "
            f"{r['taxa_entrega_centavos']}, {r['tempo_entrega_min']});"
        )
    saida.append("")
    for r in dados["restaurantes"]:
        saida.append(f"-- {r['nome']}")
        for p in r["pratos"]:
            valores = [
                literal(p["id"]),
                literal(r["id"]),
                literal(p["nome"]),
                literal(p["descricao"]),
                literal(p["preco_centavos"]),
                literal(p["tempo_preparo_min"]),
                array(p["ingredientes"]),
                array(p["atende"]),
                literal(p["temperatura"]),
                literal(p["peso"]),
                literal(p["picancia"]),
                literal(p["conforto"]),
                literal(p["foto_url"]),
                "true" if p["doce"] else "false",
            ]
            saida.append(
                "insert into public.pratos (id, restaurante_id, nome, descricao, "
                "preco_centavos, tempo_preparo_min, ingredientes, atende, temperatura, "
                "peso, picancia, conforto, foto_url, doce) values ("
                + ", ".join(valores)
                + ");"
            )
        saida.append("")
    return "\n".join(saida)


if __name__ == "__main__":
    dados = json.loads((RAIZ / "cardapio.json").read_text(encoding="utf-8"))
    (RAIZ / "seed.sql").write_text(gerar(dados), encoding="utf-8")
    print("seed.sql atualizado")
