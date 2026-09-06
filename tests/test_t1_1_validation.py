import pytest

from app.habits.validation import (
    NAME_MAX_CHARS,
    NAME_MAX_WORDS,
    NAME_REGEX,
    validate_name,
)


def test_constants_values():
    assert NAME_MAX_CHARS == 100
    assert NAME_MAX_WORDS == 8
    assert NAME_REGEX is not None
    assert NAME_REGEX.match("Estudiar Python") is not None


def test_validate_name_rejects_empty():
    with pytest.raises(ValueError, match="vacío"):
        validate_name("")


def test_validate_name_rejects_whitespace_only():
    with pytest.raises(ValueError, match="vacío"):
        validate_name("   ")


def test_validate_name_rejects_character_outside_charset():
    with pytest.raises(ValueError, match="solo puede contener"):
        validate_name("Estudiar@Python")


def test_validate_name_rejects_more_than_100_chars():
    with pytest.raises(ValueError, match="100"):
        validate_name("a" * (NAME_MAX_CHARS + 1))


def test_validate_name_rejects_more_than_8_words():
    with pytest.raises(ValueError, match="8"):
        validate_name(" ".join(["a"] * (NAME_MAX_WORDS + 1)))


def test_validate_name_accepts_simple_valid_name():
    validate_name("Estudiar Python")
    validate_name("Estudiar_Python-3.0")


def test_validate_name_accepts_unicode_letters():
    validate_name("Estúdiar Ñoños")


def test_validate_name_accepts_limit_case():
    words = ["a" * 12] * 7 + ["b" * 9]
    name = " ".join(words)
    assert len(name) == NAME_MAX_CHARS
    assert len(name.split()) == NAME_MAX_WORDS
    validate_name(name)