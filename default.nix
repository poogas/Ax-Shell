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

  nativeBuildInputs = [ wrapGAppsHook3 pkg-config makeWrapper gtk3 ];
  buildInputs = [ ax-shell-python tabler-icons-font ] ++ runtimeDeps;
  dontWrapQtApps = true;

  installPhase = ''
    runHook preInstall;

    mkdir -p $out/share/ax-shell
    cp -r ./* $out/share/ax-shell/

    makeWrapper ${ax-shell-python}/bin/python $out/bin/ax-shell \
      --prefix PYTHONPATH : "$out/share/ax-shell" \
      --prefix PATH : "${ax-shell-python}/bin" \
      --add-flags "-m main"

    runHook postInstall;
  '';

  preFixup = ''
    gappsWrapperArgs+=(--set AX_SHELL_WALLPAPERS_DIR_DEFAULT "${placeholder "out"}/share/ax-shell/assets/wallpapers_example");
    gappsWrapperArgs+=(--set FABRIC_CSS_PATH "${placeholder "out"}/share/ax-shell/main.css");
    gappsWrapperArgs+=(--prefix PATH : "${lib.makeBinPath runtimeDeps}");
    gappsWrapperArgs+=(--prefix XDG_DATA_DIRS : "${tabler-icons-font}/share");
    gappsWrapperArgs+=(--prefix XDG_DATA_DIRS : "${adwaita-icon-theme}/share");
  '';

  meta = {
    description = "A custom, flake-based package for Ax-Shell.";
    homepage = "https://github.com/poogas/Ax-Shell";
    license = lib.licenses.mit;
  };
}
