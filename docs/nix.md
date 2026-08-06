# Nix / NixOS

Репозиторий содержит flake с пакетом, dev-shell и NixOS-модулем.

| Выход flake | Что это |
|-------------|---------|
| `packages.<system>.default` | Пакет `demon-cry` (обёртка над `uvicorn`) |
| `devShells.<system>.default` | Окружение для разработки (Python с зависимостями, `poetry`, `jq`) |
| `nixosModules.default` | Systemd-сервис `services.demon-cry` |

Поддерживаются системы, которые даёт `flake-utils.lib.eachDefaultSystem` (linux/darwin, x86_64/aarch64). Сам NixOS-модуль, разумеется, только для NixOS.

## Быстрый запуск без установки

```bash
# нужен config.json в текущей директории
nix run github:Mooncore-inc/demon-cry -- --host 0.0.0.0 --port 8000
```

Всё, что идёт после `--`, передаётся напрямую в `uvicorn`.

Путь к конфигу можно переопределить переменной окружения:

```bash
DEMON_CRY_CONFIG=/etc/demon-cry/config.json nix run github:Mooncore-inc/demon-cry
```

## NixOS-модуль

### Подключение flake

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

### nixpkgs и `follows`

Флейк пинит `nixpkgs` на `nixos-26.05`. Этот пин влияет только на `packages.default`, `devShells.default` и на дефолтное значение `services.demon-cry.package` — то есть на Python-окружение агента. К SearXNG он отношения не имеет: модуль лишь выставляет опции `services.searx.*`, а сам пакет `searxng` резолвится из nixpkgs вашей системы.

Если ваша система на другой ветке nixpkgs, добавьте `follows` — иначе в eval попадёт второй nixpkgs, а Python-окружение соберётся отдельным, вместо переиспользования системного:

```nix
inputs = {
  nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

  demon-cry = {
    url = "github:Mooncore-inc/demon-cry";
    inputs.nixpkgs.follows = "nixpkgs";
  };
};
```

Агент работает и на релизной ветке, и на unstable — жёстких требований к версиям Python-зависимостей у него нет, так что `follows` безопасен.

Разово переопределить вход, ничего не меняя в конфигурации:

```bash
nix build github:Mooncore-inc/demon-cry --override-input nixpkgs github:nixos/nixpkgs/nixos-unstable
```

### Минимальная конфигурация

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

    searx.enable = true;
  };

  # файл вида: SEARXNG_SECRET=<openssl rand -hex 32>
  services.searx.environmentFile = "/run/secrets/searx-env";
}
```

### Опции

| Опция | Тип | По умолчанию | Описание |
|-------|-----|--------------|----------|
| `services.demon-cry.enable` | bool | `false` | Включить сервис |
| `services.demon-cry.package` | package | пакет из этого flake | Какой пакет запускать |
| `services.demon-cry.host` | str | `"127.0.0.1"` | Адрес, который слушает API |
| `services.demon-cry.port` | port | `8000` | Порт API |
| `services.demon-cry.openFirewall` | bool | `false` | Открыть `port` в firewall |
| `services.demon-cry.apiKeyFile` | path | — (обязательно) | Файл с ключом LLM-провайдера |
| `services.demon-cry.masterKeyFile` | path | — (обязательно) | Файл с master-ключом для Bearer-авторизации API |
| `services.demon-cry.settings` | attrs (JSON) | `{ }` | Несекретная часть `config.json` |
| `services.demon-cry.searx.enable` | bool | `false` | Поднять локальный SearXNG и указать на него агента |
| `services.demon-cry.searx.port` | port | `8888` | Порт локального SearXNG |

`settings` — это ровно те же поля, что и в `config.json` (см. [Конфигурация](configuration.md)), кроме `api_key` и `master_key`. Модуль требует как минимум `base_url` и `model`, иначе сборка конфигурации падает с assertion.

### Секреты

`apiKeyFile` и `masterKeyFile` **не попадают в nix store**. Юнит получает их через systemd `LoadCredential`, а в `preStart` они вклеиваются через `jq` в `config.json`, который лежит в `/run/demon-cry/` (`RuntimeDirectoryMode = 0700`, `DynamicUser`). Завершающие переводы строки обрезаются, так что `echo 'sk-...' > file` безопасен.

С [sops-nix](https://github.com/Mic92/sops-nix):

```nix
{
  sops.secrets.demon-cry-api-key = { };
  sops.secrets.demon-cry-master-key = { };

  services.demon-cry = {
    enable = true;
    apiKeyFile = config.sops.secrets.demon-cry-api-key.path;
    masterKeyFile = config.sops.secrets.demon-cry-master-key.path;
    # ...
  };
}
```

С [agenix](https://github.com/ryantm/agenix) — то же самое через `config.age.secrets.<name>.path`.

> Пустой `masterKeyFile` полностью отключает авторизацию на API. Не делайте так, если порт доступен извне.

### SearXNG

`searx.enable = true` поднимает `services.searx` (пакет `searxng`) на `127.0.0.1:<searx.port>`, включает JSON-формат выдачи и проставляет `settings.searxng_url` в `http://127.0.0.1:<searx.port>`. Значение ставится через `mkDefault`, так что явно заданный `searxng_url` его переопределит.

Требуется `services.searx.environmentFile` с `SEARXNG_SECRET` — модуль проверяет это assertion'ом. Если хочется использовать внешний SearXNG, оставьте `searx.enable = false` и укажите URL руками:

```nix
services.demon-cry.settings.searxng_url = "https://searx.example.org";
```

### Проверка

```bash
systemctl status demon-cry
journalctl -u demon-cry -f          # приложение логирует в journal, не в файл

curl http://127.0.0.1:8000/api/health
```

## Разработка

```bash
git clone https://github.com/Mooncore-inc/demon-cry.git && cd demon-cry
nix develop

cp example_config.json config.json
uvicorn core.__main__:app --reload
```

Dev-shell даёт Python 3.12 со всеми рантайм-зависимостями, `poetry` и `jq`.

Локальная сборка рабочего дерева:

```bash
nix build .#default
./result/bin/demon-cry --host 127.0.0.1 --port 8000
```

Прогнать NixOS-модуль на локальном чекауте можно через `.url = "path:/path/to/demon-cry"` в inputs.

## Как устроен пакет

- Зависимости берутся из nixpkgs (`python312.withPackages`), не из `poetry.lock`. **При добавлении зависимости в `pyproject.toml` её нужно добавить и в `package.nix`** — иначе модуль просто не зарегистрируется: `ModuleRegistry.discover()` глушит ошибки импорта в лог.
- `postPatch` заменяет два захардкоженных пути на переменные окружения:
  - `DEMON_CRY_CONFIG` — путь к `config.json` (по умолчанию `config.json` в рабочей директории);
  - `DEMON_CRY_LOG` — файл лога; если не задан, логи идут в stderr (в journal).
- Бинарь `demon-cry` — это `makeWrapper` вокруг `uvicorn core.__main__:app`, поэтому ему можно передавать любые флаги uvicorn.
- Версия пакета задана аргументом `version` в `package.nix` и должна совпадать с версией в `core/__main__.py`.
