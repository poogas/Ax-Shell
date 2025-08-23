{
  stdenv,
  lib,
  self,
  ax-shell-python,
  runtimeDeps,
  wrapGAppsHook3,
  pkg-config,
  makeWrapper,
  gtk3,
  adwaita-icon-theme,
  tabler-icons-font,
}:
stdenv.mkDerivation {
  pname = "ax-shell";
  version = "unstable-${self.shortRev or "dirty"}";
  src = self;

  nativeBuildInputs = [wrapGAppsHook3 pkg-config makeWrapper gtk3];

  buildInputs = [ax-shell-python tabler-icons-font] ++ runtimeDeps;
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
    gappsWrapperArgs+=(--prefix PATH : "${lib.makeBinPath runtimeDeps}")
    gappsWrapperArgs+=(--set XCURSOR_THEME "Adwaita")
    gappsWrapperArgs+=(--set XCURSOR_SIZE "24")
    gappsWrapperArgs+=(--prefix XCURSOR_PATH : "${adwaita-icon-theme}/share/icons")
    gappsWrapperArgs+=(--prefix XDG_DATA_DIRS : "${tabler-icons-font}/share")
  '';


  meta = {
    description = "A custom, flake-based package for Ax-Shell.";
    homepage = "https://github.com/poogas/Ax-Shell";
    license = lib.licenses.mit;
  };
}
