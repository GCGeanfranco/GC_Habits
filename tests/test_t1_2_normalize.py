from app.habits.validation import normalize_name


def test_normalize_collapses_multiple_spaces():
    assert normalize_name("Estudiar   Python") == "estudiar_python"


def test_normalize_lowercases():
    assert normalize_name("ESTUDIAR PYTHON") == "estudiar_python"


def test_normalize_strips_accents():
    assert normalize_name("Estúdiar Pýthon") == "estudiar_python"


def test_normalize_preserves_enye():
    assert normalize_name("Baño diario") == "baño_diario"


def test_normalize_trims_leading_and_trailing_spaces():
    assert normalize_name("  Leer  ") == "leer"


def test_normalize_preserves_hyphen_and_dot():
    assert normalize_name("Yoga-Matinal 3.0") == "yoga-matinal_3.0"