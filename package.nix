{ lib, stdenvNoCC, makeWrapper, python312, src, version ? "0.5.0" }:

let
  pythonEnv = python312.withPackages (ps: [
    ps.aiodns
    ps.asyncwhois
    ps.fastapi
    ps.openai
    ps.httpx
    ps.pydantic
    ps.selectolax
    ps.uvicorn
  ] ++ ps.uvicorn.optional-dependencies.standard);
in
stdenvNoCC.mkDerivation {
  pname = "demon-cry";
  inherit version src;

  nativeBuildInputs = [ makeWrapper ];

  postPatch = ''
    substituteInPlace core/config.py \
      --replace-fail 'from sys import stderr' 'from os import environ; from sys import stderr' \
      --replace-fail 'Config("config.json")' 'Config(environ.get("DEMON_CRY_CONFIG", "config.json"))'

    substituteInPlace core/__init__.py \
      --replace-fail 'import logging' 'import logging; from os import environ' \
      --replace-fail 'filename="demon-cry.log",' 'filename=environ.get("DEMON_CRY_LOG") or None,'
  '';

  dontBuild = true;

  installPhase = ''
    runHook preInstall

    mkdir -p $out/lib/demon-cry $out/bin
    cp -r core modules $out/lib/demon-cry/

    makeWrapper ${pythonEnv}/bin/uvicorn $out/bin/demon-cry \
      --prefix PYTHONPATH : $out/lib/demon-cry \
      --set-default PYTHONUNBUFFERED 1 \
      --add-flags "core.__main__:app"

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
