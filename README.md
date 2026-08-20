# Demon Cry 🔍

Demon Cry — это автономный OSINT-агент, который использует LLM для проведения расследований в открытых источниках. Агент сам строит гипотезы, выбирает инструменты и анализирует данные.

[![License: MPL2](https://img.shields.io/badge/License-MPL2-red.svg)](https://www.mozilla.org/en-US/MPL/2.0/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-red.svg)](https://www.python.org/downloads/)
[![Docker Release](https://github.com/Mooncore-inc/demon-cry/actions/workflows/docker-release.yml/badge.svg)](https://github.com/Mooncore-inc/demon-cry/actions/workflows/docker-release.yml)

## Быстрый старт (Рекомендуется)

```bash
bash <(curl -Ls https://raw.githubusercontent.com/Mooncore-inc/demon-cry/main/install.sh)
```

## Ручная настройка
<details>
<summary>Нажмите, чтобы открыть</summary>

### Pip (альтернатива Docker)

```bash
pip install demon-cry

cp example_config.toml ~/.config/demon_cry/config.toml  # настроить base_url, api_key, model
demon-cry
```

Swagger доступен по `http://localhost:8000/docs`. Конфигурация ищется в `config.toml` (см. `demon-cry config path`, переопределяется через `DEMON_CRY_CONFIG`). Адрес и порт задаются в секции `[server]`.

Создайте `docker-compose.yml`:

```yaml
services:
  app:
    image: fazzyt/demon-cry
    ports:
      - "8000:8000"
    volumes:
      - ./config.json:/app/config.json:ro,z
    restart: unless-stopped

  searxng:
    image: searxng/searxng:latest
    ports:
      - "8080:8080"
    volumes:
      - ./searxng:/etc/searxng:z
    environment:
      - SEARXNG_BASE_URL=http://localhost:8080/
    restart: unless-stopped

networks:
  demon-cry-net:
    name: demon-cry-net
```

Создайте `config.json`:

```json
{
    "base_url": "https://api.openai.com/v1",
    "master_key": "secret", # pragma: allowlist secret
    "api_key": "sk-...", # pragma: allowlist secret
    "model": "gpt-4o",
    "searxng_url": "http://searxng:8080"
}
```

Создайте папку `searxng` с файлом `settings.yml`:

```yml
use_default_settings: true

server:
  secret_key: "сюда ключ придумай"
  limiter: false
  bind_address: "0.0.0.0"
  port: 8080

search:
  formats:
    - html
    - json
  cache:
    enable: true
    expiration_time: 3600

engines:
  - name: startpage
    disabled: true

  - name: duckduckgo
    disabled: false
    weight: 1.5

  - name: google
    disabled: false
    weight: 1.5

  - name: bing
    disabled: false
    weight: 1.5

  - name: qwant
    disabled: false
    weight: 1.2

  - name: yandex
    disabled: false
    weight: 1.0

  - name: wikipedia
    disabled: false
    weight: 0.8
```

Запуск:

```bash
docker compose up -d
```

</details>

## NixOS (flake)
<details>
<summary>Нажмите, чтобы открыть</summary>

Разовый запуск (нужен `config.toml` по пути из `demon-cry config path`):

```bash
nix run github:Mooncore-inc/demon-cry
```

Как NixOS-модуль — добавьте flake в inputs:

```nix
{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-26.05";
    demon-cry.url = "github:Mooncore-inc/demon-cry";
  };

  outputs = { nixpkgs, demon-cry, ... }: {
    nixosConfigurations.myhost = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        demon-cry.nixosModules.default
        ./configuration.nix
      ];
    };
  };
}
```

И включите сервис в конфигурации хоста:

```nix
{
  services.demon-cry = {
    enable = true;

    settings = {
      base_url = "https://api.openai.com/v1";
      model = "gpt-4o";
    };

    apiKeyFile = "/run/secrets/demon-cry-api-key";
    masterKeyFile = "/run/secrets/demon-cry-master-key";

    searx.enable = true;  # поднимет локальный SearXNG и укажет на него агента
  };

  # файл вида: SEARXNG_SECRET=<openssl rand -hex 32>
  services.searx.environmentFile = "/run/secrets/searx-env";
}
```

Ключи не попадают в nix store: сервис получает их через systemd `LoadCredential` и подставляет в `config.json` при старте.

Полный список опций, работа с sops-nix/agenix и dev-shell — в [Nix / NixOS](docs/nix.md).

</details>

## Использование

Swagger: http://localhost:8000/docs

**Пример:**

```bash
curl -X 'POST' \
  'http://localhost:8000/api/investigate' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer secret' \
  -H 'Content-Type: application/json' \
  -d '{"target": "кто такой fazzyt"}'
```

## Документация

- [Конфигурация](docs/configuration.md) — настройка `config.json`, провайдеры
- [Docker](docs/docker.md) — Docker Compose, сборка, запуск
- [Nix / NixOS](docs/nix.md) — flake, NixOS-модуль, секреты, dev-shell
- [SearXNG](docs/searxng.md) — метапоисковик, настройка
- [Разработка](docs/development.md) — локальный запуск, добавление модулей

## Контрибьюторы

Спасибо нашим контрибьюторам! ❤️

<a href="https://github.com/Mooncore-inc/demon-cry/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Mooncore-inc/demon-cry&columns=25&max=500" />
</a>

## Лицензия

Mozilla Public License 2.0
