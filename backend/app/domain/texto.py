import re
import unicodedata


def normalizar(texto: str) -> str:
    """Minúsculas e sem acentos, para comparações insensíveis a acento e caixa."""
    decomposto = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in decomposto if not unicodedata.combining(c))
    return sem_acento.lower().strip()


def palavras(texto: str) -> list[str]:
    return re.findall(r"\w+", normalizar(texto))
