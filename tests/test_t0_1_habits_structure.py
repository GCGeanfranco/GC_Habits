from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HABITS_DIR = ROOT / "app" / "habits"

EXPECTED_FILES = ("__init__.py", "validation.py", "streak.py", "management.py")


def test_habits_package_directory_exists():
    assert HABITS_DIR.is_dir(), "Falta el directorio app/habits/ (Constitución §3)"


def test_habits_package_has_expected_files():
    for filename in EXPECTED_FILES:
        assert (HABITS_DIR / filename).is_file(), f"Falta {filename} en app/habits/"


def test_habits_package_imports():
    import app.habits  # noqa: F401


def test_habits_modules_do_not_import_flask():
    for filename in EXPECTED_FILES:
        content = (HABITS_DIR / filename).read_text(encoding="utf-8")
        assert "flask" not in content, (
            f"{filename} no debe importar flask (Constitución §3)"
        )