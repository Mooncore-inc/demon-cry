# Установка

## pip (рекомендуется)

```bash
pip install demon-cry
```

По умолчанию используется SQLite (`database.db` в рабочей директории). Для PostgreSQL:

```bash
pip install demon-cry[postgres]
DC_DB_URL="postgresql+asyncpg://user:pass@localhost/demoncry" demon-cry
```

## Из исходников

```bash
git clone https://github.com/Mooncore-inc/demon-cry.git && cd demon-cry
pip install poetry
poetry install
demon-cry migrate upgrade
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
