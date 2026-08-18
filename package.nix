{ lib, stdenvNoCC, makeWrapper, python312, src, version ? "0.7.0" }:

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

  dontBuild = true;

  installPhase = ''
    runHook preInstall

    mkdir -p $out/lib/demon-cry $out/bin
    cp -r demon_cry modules $out/lib/demon-cry/

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
