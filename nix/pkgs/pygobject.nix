{
  lib,
  stdenv,
  fetchurl,
  buildPythonPackage,
  pkg-config,
  glib,
  gobject-introspection,
  pycairo,
  cairo,
  meson,
  ninja,
  python,
}:
buildPythonPackage rec {
  pname = "pygobject";
  version = "3.52.3";
  format = "other";

  src = fetchurl {
    url = "mirror://gnome/sources/${pname}/${lib.versions.majorMinor version}/${pname}-${version}.tar.gz";
    sha256 = "sha256-AOQn0pHpV0Yqj61lmp+ci+d2/4Kot2vfQC8eruwIbYI=";
    # sha256 = "";
  };

  nativeBuildInputs = [
    pkg-config
    meson
    ninja
    gobject-introspection
  ];

  buildInputs = [
    cairo
    glib
  ];

  propagatedBuildInputs = [pycairo];
}
