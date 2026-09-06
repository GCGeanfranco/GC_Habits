import re
import unicodedata

NAME_REGEX = re.compile(r"^[\w _\-.]{1,100}\Z")
NAME_MAX_CHARS = 100
NAME_MAX_WORDS = 8


def validate_name(name: str) -> None:
    if name is None or name.strip() == "":
        raise ValueError("El nombre no puede estar vacío.")
    if len(name) > NAME_MAX_CHARS:
        raise ValueError(f"El nombre no puede superar los {NAME_MAX_CHARS} caracteres.")
    if not NAME_REGEX.match(name):
        raise ValueError(
            "El nombre solo puede contener letras, números, espacios, "
            "guiones, guiones bajos y puntos."
        )
    if len(name.split()) > NAME_MAX_WORDS:
        raise ValueError(f"El nombre no puede tener más de {NAME_MAX_WORDS} palabras.")


def normalize_name(name: str) -> str:
    decomposed = unicodedata.normalize("NFKD", name)
    kept = []
    for ch in decomposed:
        if unicodedata.combining(ch):
            if kept and kept[-1].lower() == "n" and ch == "\u0303":
                kept.append(ch)
            continue
        kept.append(ch)
    text = unicodedata.normalize("NFC", "".join(kept)).lower()
    return re.sub(r"\s+", "_", text.strip())