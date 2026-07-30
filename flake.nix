{
  description = "demon-cry — OSINT agent";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-26.05";
    flake-utils.url = "github:numtide/flake-utils";

    demon-cry-src = {
      url = "github:Mooncore-inc/demon-cry";
      flake = false;
    };
  };

  outputs = { self, nixpkgs, flake-utils, demon-cry-src }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };

        demon-cry = pkgs.callPackage ./package.nix {
          src = demon-cry-src;
        };
      in
      {
        packages.default = demon-cry;

        devShells.default = pkgs.mkShell {
          packages = [
            demon-cry.pythonEnv
            pkgs.poetry
            pkgs.jq
          ];
        };
      }
    ) // {
      nixosModules.default = import ./module.nix self;
    };
}
