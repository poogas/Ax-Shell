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
  xorg,
  gdk-pixbuf,
  glib,
  gsettings-desktop-schemas,
}:
stdenv.mkDerivation {
  pname = "ax-shell";
  version = "unstable-${self.shortRev or "dirty"}";
  src = self;

  nativeBuildInputs = [wrapGAppsHook3 pkg-config makeWrapper gtk3];

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
    gappsWrapperArgs+=(--prefix PATH : "${lib.makeBinPath runtimeDeps}")
    gappsWrapperArgs+=(--prefix XDG_DATA_DIRS : "${gtk3}/share")
    gappsWrapperArgs+=(--prefix XDG_DATA_DIRS : "${adwaita-icon-theme}/share")
    gappsWrapperArgs+=(--prefix XDG_DATA_DIRS : "${xorg.xcursorthemes}/share")
    gappsWrapperArgs+=(--prefix XDG_DATA_DIRS : "${gsettings-desktop-schemas}/share/gsettings-schemas")
    gappsWrapperArgs+=(--set XCURSOR_THEME "Adwaita") # Используем полную тему Adwaita
    gappsWrapperArgs+=(--set XCURSOR_SIZE "24")
    gappsWrapperArgs+=(--prefix XCURSOR_PATH : "${adwaita-icon-theme}/share/icons")
    gappsWrapperArgs+=(--prefix XCURSOR_PATH : "${xorg.xcursorthemes}/share/icons")
    gappsWrapperArgs+=(--set GDK_PIXBUF_MODULE_FILE "${gdk-pixbuf.out}/lib/gdk-pixbuf-2.0/2.10.0/loaders.cache")
    gappsWrapperArgs+=(--prefix GIO_EXTRA_MODULES : "${glib.out}/lib/gio/modules")
  '';


  meta = {
    description = "A custom, flake-based package for Ax-Shell.";
    homepage = "https://github.com/poogas/Ax-Shell";
    license = lib.licenses.mit;
  };
}
