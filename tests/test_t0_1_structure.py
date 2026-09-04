from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ALLOWED_DEPENDENCIES = {
    "flask",
    "google-auth",
    "python-dotenv",
    "flask-wtf",
    "flask-limiter",
    "flask-talisman",
}


def _strip_version(name: str) -> str:
    for sep in ("==", ">=", "<=", "~=", "<", ">"):
        if sep in name:
            return name.split(sep)[0].strip()
    return name.strip()


def test_requirements_txt_only_lists_allowed_dependencies():
    req = ROOT / "requirements.txt"
    assert req.is_file(), "requirements.txt no existe"
    deps = {
        _strip_version(line)
        for line in req.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    assert deps, "requirements.txt está vacío"
    not_allowed = deps - ALLOWED_DEPENDENCIES
    assert not not_allowed, f"Dependencias no permitidas (Constitución §1): {not_allowed}"
    assert "flask" in deps, "flask debe estar listado en requirements.txt"


def test_gitignore_excludes_env():
    gitignore = ROOT / ".gitignore"
    assert gitignore.is_file(), ".gitignore no existe"
    assert ".env" in gitignore.read_text(encoding="utf-8"), ".gitignore debe excluir .env"


def test_env_example_has_required_keys():
    env_example = ROOT / ".env.example"
    assert env_example.is_file(), ".env.example no existe"
    content = env_example.read_text(encoding="utf-8")
    for key in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "FLASK_SECRET_KEY"):
        assert key in content, f"Falta {key} en .env.example"


def test_package_directories_exist():
    for rel in ("app", "app/auth", "app/storage", "app/web", "tests"):
        assert (ROOT / rel).is_dir(), f"Falta el directorio {rel}/"


def test_app_package_imports():
    import app  # noqa: F401
