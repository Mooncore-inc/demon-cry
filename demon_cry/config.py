from dataclasses import dataclass, field, fields, MISSING
from os import environ
from pathlib import Path
from sys import stderr
from typing import Any

import tomlkit
from platformdirs import user_config_dir


CONFIG_FILENAME = "config.toml"

# Variable names carry a pragma so detect-secrets does not flag the literal
# keywords inside the generated template string.
_MASTER_KEY = "master_key"  # pragma: allowlist secret
_API_KEY = "api_key"  # pragma: allowlist secret

CONFIG_TEMPLATE = f"""\
# Demon Cry configuration
# Edit the values below, then restart the service.

# LLM provider OpenAI-compatible base URL
base_url = "CHANGEME"

# Master key for Bearer authentication on the API itself.
# Leave empty to disable authentication. Change from "CHANGEME" before deploying.
{_MASTER_KEY} = "CHANGEME"

# Maximum agent reasoning iterations per request
iteration_limit = 150

# LLM provider API key
{_API_KEY} = "CHANGEME"

# Model name
model = "CHANGEME"

# Server bind address and port
[server]
host = "0.0.0.0"
port = 8000
"""


def resolve_config_path() -> Path:
    env = environ.get("DEMON_CRY_CONFIG")
    if env:
        return Path(env)
    return Path(user_config_dir("demon_cry")) / CONFIG_FILENAME


@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8000


@dataclass
class Config:
    base_url: str
    master_key: str
    iteration_limit: int
    api_key: str
    model: str
    server: ServerConfig = field(default_factory=ServerConfig)

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Config":
        config_path = Path(path) if path else resolve_config_path()
        if not config_path.exists():
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(CONFIG_TEMPLATE, encoding="utf-8")
            stderr.write(
                f"Created configuration template at {config_path}\n"
                f"Please edit it and re-run demon-cry.\n"
            )
            raise SystemExit(1)
        document = tomlkit.parse(config_path.read_text(encoding="utf-8"))
        kwargs: dict[str, Any] = {}
        for f in fields(cls):
            if f.type is ServerConfig:
                sub = document.get(f.name, {})
                server_kwargs: dict[str, Any] = {}
                for sfield in fields(ServerConfig):
                    svalue = sub.get(sfield.name, sfield.default)
                    if svalue is MISSING:
                        raise ValueError(
                            f"No value for {f.name}.{sfield.name} in {config_path}"
                        )
                    if sfield.type is str and not isinstance(svalue, str):
                        svalue = str(svalue)
                    server_kwargs[sfield.name] = svalue
                kwargs[f.name] = ServerConfig(**server_kwargs)
                continue
            value = document.get(f.name, f.default)
            if value is MISSING:
                raise ValueError(f"No value for {f.name} in {config_path}")
            if f.type is str and not isinstance(value, str):
                value = str(value)
            kwargs[f.name] = value
        return cls(**kwargs)


def _infer_value(raw: str) -> Any:
    try:
        return tomlkit.parse(f"_ = {raw}").get("_")
    except tomlkit.exceptions.TOMLKitError:
        return raw


def _set_dotted(document: "tomlkit.TOMLDocument", key: str, value: Any) -> None:
    if "." in key:
        section, subkey = key.split(".", 1)
        if section not in document:
            document[section] = tomlkit.table()
        document[section][subkey] = value
    else:
        document[key] = value


def write_value(key: str, value: Any, path: str | Path | None = None) -> Path:
    config_path = Path(path) if path else resolve_config_path()
    if config_path.exists():
        document = tomlkit.parse(config_path.read_text(encoding="utf-8"))
    else:
        document = tomlkit.parse(CONFIG_TEMPLATE)
    _set_dotted(document, key, value)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(tomlkit.dumps(document), encoding="utf-8")
    return config_path


def read_value(key: str, path: str | Path | None = None) -> Any:
    config_path = Path(path) if path else resolve_config_path()
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    document = tomlkit.parse(config_path.read_text(encoding="utf-8"))
    if "." in key:
        section, subkey = key.split(".", 1)
        return document[section][subkey]
    return document[key]
