import os
from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import Settings

VALID_ENVIRONMENT = {
    "POSTGRES_DB": "test_db",
    "POSTGRES_USER": "test_user",
    "POSTGRES_PASSWORD": "fake-test-password",
    "POSTGRES_HOST": "test-host",
    "POSTGRES_PORT": "5432",
}


@pytest.fixture(autouse=True)
def isolate_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in os.environ:
        if key.upper() in VALID_ENVIRONMENT:
            monkeypatch.delenv(key)


@pytest.fixture
def valid_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in VALID_ENVIRONMENT.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    path = tmp_path / ".env"
    path.write_text(
        "\n".join(f"{key}={value}" for key, value in VALID_ENVIRONMENT.items()),
        encoding="utf-8",
    )
    return path


def test_settings_loads_all_environment_variables(valid_environment: None) -> None:
    settings = Settings(_env_file=None)

    assert settings.postgres_db == "test_db"
    assert settings.postgres_user == "test_user"
    assert settings.postgres_password.get_secret_value() == "fake-test-password"
    assert settings.postgres_host == "test-host"
    assert settings.postgres_port == 5432
    assert isinstance(settings.postgres_port, int)


@pytest.mark.parametrize("variable", VALID_ENVIRONMENT)
def test_settings_requires_each_field(
    valid_environment: None, monkeypatch: pytest.MonkeyPatch, variable: str
) -> None:
    monkeypatch.delenv(variable)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    assert [(error["loc"], error["type"]) for error in exc_info.value.errors()] == [
        ((variable.lower(),), "missing")
    ]


@pytest.mark.parametrize("variable", VALID_ENVIRONMENT)
def test_settings_rejects_empty_field(
    valid_environment: None, monkeypatch: pytest.MonkeyPatch, variable: str
) -> None:
    monkeypatch.setenv(variable, "")

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    assert [error["loc"] for error in exc_info.value.errors()] == [(variable.lower(),)]


@pytest.mark.parametrize("port", ["1", "65535"])
def test_settings_accepts_port_boundaries(
    valid_environment: None, monkeypatch: pytest.MonkeyPatch, port: str
) -> None:
    monkeypatch.setenv("POSTGRES_PORT", port)

    settings = Settings(_env_file=None)

    assert settings.postgres_port == int(port)


@pytest.mark.parametrize("port", ["0", "-1", "65536", "not-a-number"])
def test_settings_rejects_invalid_port(
    valid_environment: None, monkeypatch: pytest.MonkeyPatch, port: str
) -> None:
    monkeypatch.setenv("POSTGRES_PORT", port)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    assert [error["loc"] for error in exc_info.value.errors()] == [("postgres_port",)]


def test_settings_masks_password_when_printed(
    valid_environment: None, capsys: pytest.CaptureFixture[str]
) -> None:
    settings = Settings(_env_file=None)

    assert isinstance(settings.postgres_password, SecretStr)
    assert settings.postgres_password.get_secret_value() == "fake-test-password"

    print(settings)
    print(repr(settings))

    output = capsys.readouterr().out
    assert "fake-test-password" not in output
    assert "**********" in output


def test_settings_reads_temporary_env_file(env_file: Path) -> None:
    settings = Settings(_env_file=env_file)

    assert settings.postgres_db == "test_db"
    assert settings.postgres_user == "test_user"
    assert settings.postgres_password.get_secret_value() == "fake-test-password"
    assert settings.postgres_host == "test-host"
    assert settings.postgres_port == 5432


def test_environment_variables_override_env_file(
    monkeypatch: pytest.MonkeyPatch, env_file: Path
) -> None:
    overrides = {
        "POSTGRES_DB": "environment_db",
        "POSTGRES_USER": "environment_user",
        "POSTGRES_PASSWORD": "fake-environment-password",
        "POSTGRES_HOST": "environment-host",
        "POSTGRES_PORT": "6543",
    }
    for key, value in overrides.items():
        monkeypatch.setenv(key, value)

    settings = Settings(_env_file=env_file)

    assert settings.postgres_db == "environment_db"
    assert settings.postgres_user == "environment_user"
    assert settings.postgres_password.get_secret_value() == "fake-environment-password"
    assert settings.postgres_host == "environment-host"
    assert settings.postgres_port == 6543
