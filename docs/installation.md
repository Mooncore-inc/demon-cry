# Установка

## Из PyPI (пользователям)

```bash
pipx install demon-cry
# или:
uv tool install demon-cry
# или классика:
pip install demon-cry
```

По умолчанию используется SQLite (`database.db` в рабочей директории). Для PostgreSQL-экстры:

```bash
pipx install "demon-cry[postgres]"
# uv:
uv tool install "demon-cry[postgres]"
DC_DB_URL="postgresql+asyncpg://user:pass@localhost/demoncry" demon-cry
```

## Из исходников (разработка)

```bash
git clone https://github.com/Mooncore-inc/demon-cry.git && cd demon-cry
uv sync --locked --group dev
uv run demon-cry migrate upgrade
```

## NixOS

Добавьте flake в inputs:

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

Минимальная конфигурация:

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
  };
}
```

Подробности: [Nix / NixOS](nix.md).
