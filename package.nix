{ lib, stdenvNoCC, makeWrapper, python312, src, version ? "0.0.0-dev" }:

let
  # Runtime deps synced with pyproject.toml (requires-python >=3.12,<3.15).
  # ModuleRegistry.discover() swallows ImportError, so pythonEnv must cover
  # every runtime import or modules silently fail to load.
  pythonEnv = python312.withPackages (ps: [
    ps.fastapi
    ps.openai
    ps.httpx
    ps.pydantic
    ps.pydantic-settings
    ps.sqlalchemy
    ps.alembic
    ps.aiosqlite
    ps.uvicorn
    # NOTE: demon-cry-base IS a runtime dep (demon_cry/core/module_registry.py
    # imports BaseModule from it) but is not in nixpkgs — package it as a
    # separate derivation (e.g. buildPythonPackage from PyPI) and add here.
    # NOTE: aiodns/asyncwhois/selectolax removed — no imports found via
    # `rg -n "aiodns|asyncwhois|selectolax" demon_cry/ pyproject.toml`.
    # NOTE: postgres support needs ps.asyncpg — add it here only if the
    # Nix package must talk to postgres (pyproject `postgres` extra).
    # ps.asyncpg
  ] ++ ps.uvicorn.optional-dependencies.standard);
in
stdenvNoCC.mkDerivation {
  pname = "demon-cry";
  inherit version src;

  nativeBuildInputs = [ makeWrapper ];

  dontBuild = true;

  installPhase = ''
    runHook preInstall

    mkdir -p $out/lib/demon-cry $out/bin
    cp -r demon_cry $out/lib/demon-cry/

    makeWrapper ${pythonEnv}/bin/uvicorn $out/bin/demon-cry \
      --prefix PYTHONPATH : $out/lib/demon-cry \
      --set-default PYTHONUNBUFFERED 1 \
      --add-flags "demon_cry.__main__:app"

    runHook postInstall
  '';

  passthru = { inherit pythonEnv; };

  meta = {
    description = "Autonomous LLM-driven OSINT agent (FastAPI + SearXNG)";
    homepage = "https://github.com/Mooncore-inc/demon-cry";
    license = lib.licenses.mpl20;
    mainProgram = "demon-cry";
    platforms = lib.platforms.unix;
  };
}
