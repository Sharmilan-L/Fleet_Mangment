from pathlib import Path

import pytest
from alembic.config import Config


@pytest.fixture
def alembic_config_path() -> Path:
    """
    Returns Path to backend/alembic.ini.
    """
    backend_dir = Path(__file__).resolve().parents[2]
    return backend_dir / "alembic.ini"


def test_alembic_config_loading(alembic_config_path: Path) -> None:
    """
    Verifies Alembic Config loads backend/alembic.ini and script_location is correct.
    """
    assert alembic_config_path.exists(), "alembic.ini must exist in backend directory"
    config = Config(str(alembic_config_path))

    script_location = config.get_main_option("script_location")
    assert script_location is not None
    assert script_location.replace("\\", "/").endswith("migrations")

    prepend_sys_path = config.get_main_option("prepend_sys_path")
    assert prepend_sys_path == "."

    path_separator = config.get_main_option("path_separator")
    assert path_separator == "os"


def test_alembic_ini_no_hardcoded_credentials(alembic_config_path: Path) -> None:
    """
    Verifies sqlalchemy.url is empty or not populated with hardcoded credentials in alembic.ini.
    """
    config = Config(str(alembic_config_path))
    db_url = config.get_main_option("sqlalchemy.url")
    assert not db_url or db_url.strip() == "", (
        "sqlalchemy.url must be blank in alembic.ini to enforce dynamic Settings configuration"
    )


def test_alembic_framework_files_exist() -> None:
    """
    Verifies that all expected Alembic migration framework files exist.
    """
    backend_dir = Path(__file__).resolve().parents[2]

    alembic_ini = backend_dir / "alembic.ini"
    env_py = backend_dir / "migrations" / "env.py"
    script_mako = backend_dir / "migrations" / "script.py.mako"
    versions_gitkeep = backend_dir / "migrations" / "versions" / ".gitkeep"

    assert alembic_ini.is_file(), "alembic.ini file missing"
    assert env_py.is_file(), "migrations/env.py file missing"
    assert script_mako.is_file(), "migrations/script.py.mako file missing"
    assert versions_gitkeep.is_file(), "migrations/versions/.gitkeep file missing"


def test_versions_directory_has_revisions() -> None:
    """
    Verifies that migrations/versions directory contains Alembic revision files.
    """
    backend_dir = Path(__file__).resolve().parents[2]
    versions_dir = backend_dir / "migrations" / "versions"

    assert versions_dir.is_dir(), "migrations/versions directory missing"

    py_revisions = list(versions_dir.glob("*.py"))
    assert len(py_revisions) > 0, "migrations/versions directory must contain revision files"
