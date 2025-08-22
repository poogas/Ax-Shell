{
  stdenv,
  lib,
  self,
  ax-shell-python,
  runtimeDeps,
  devTools,
  wrapGAppsHook3,
  pkg-config,
  makeWrapper,
}:
stdenv.mkDerivation {
  pname = "ax-shell";
  version = "unstable-${self.shortRev or "dirty"}";
  src = self;

  nativeBuildInputs = [wrapGAppsHook3 pkg-config makeWrapper] ++ devTools;
  buildInputs = [ax-shell-python] ++ runtimeDeps;
  dontWrapQtApps = true;

  installPhase = ''
    runHook preInstall
    mkdir -p $out/lib/ax-shell
    cp -r ./* $out/lib/ax-shell/
    makeWrapper ${ax-shell-python}/bin/python $out/bin/ax-shell \
      --add-flags "$out/lib/ax-shell/main.py"
    runHook postInstall
  '';

  preFixup = ''
    gappsWrapperArgs+=(--prefix PYTHONPATH : "$out/lib/ax-shell")
    gappsWrapperArgs+=(--set FABRIC_CSS_PATH "$out/lib/ax-shell/main.css")
  '';

  meta = {
    description = "A custom, flake-based package for Ax-Shell.";
    homepage = "https://github.com/poogas/Ax-Shell";
    license = lib.licenses.mit;
  };
}
