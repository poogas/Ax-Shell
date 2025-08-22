{
  description = "A clean, elegant, and working flake for Ax-Shell";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    fabric-gtk.url = "github:poogas/fabric";
    fabric-cli.url = "github:poogas/fabric-cli";
    gray.url = "github:Fabric-Development/gray";
  };

  inputs.fabric-gtk.inputs.nixpkgs.follows = "nixpkgs";
  inputs.fabric-cli.inputs.nixpkgs.follows = "nixpkgs";
  inputs.gray.inputs.nixpkgs.follows = "nixpkgs";

  outputs = {self, nixpkgs, flake-utils, ...}@inputs:
    let
      supportedSystems = ["x86_64-linux"];
    in
    flake-utils.lib.eachSystem supportedSystems (system: let
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true;
      };

      ax-shell-python-packages = ps:
        let
          ps_ = ps.override {
            overrides = self: super: {
              pygobject3 = pkgs.callPackage ./nix/pkgs/pygobject.nix {
                python = pkgs.python312;
                buildPythonPackage = pkgs.python312Packages.buildPythonPackage;
                pycairo = pkgs.python312Packages.pycairo;
              };
            };
          };
        in
        [
          (ps_.buildPythonPackage {
            pname = "fabric-gtk";
            version = "unstable-${self.shortRev or "dirty"}";
            src = inputs.fabric-gtk;
            format = "pyproject";
            # postPatch больше не нужен
            nativeBuildInputs =
              [ps_.setuptools ps_.wheel]
              ++ (with pkgs; [cairo gobject-introspection glib pkg-config]);
            propagatedBuildInputs = [
              ps_.click
              ps_.loguru
              ps_.pycairo
              ps_.pygobject3
            ];
          })
          # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
          # Добавляем недостающий пакет dbus-python
          ps_.dbus-python

          ps_.ijson
          ps_.numpy
          ps_.pillow
          ps_.psutil
          ps_.requests
          ps_.setproctitle
          ps_.toml
          ps_.watchdog
        ];

      ax-shell-python = pkgs.python312.withPackages ax-shell-python-packages;

      # ... (остальная часть flake.nix остается без изменений)
      runtimeDeps = with pkgs; [
        adwaita-icon-theme
        cinnamon-desktop
        networkmanager
        playerctl
        gnome-bluetooth
        inputs.gray.packages.${system}.default
        glib
        gobject-introspection
        gtk-layer-shell
        gtk3
        cairo
        gdk-pixbuf
        pango
        libdbusmenu-gtk3
	vte
      ];

      devTools = with pkgs; [
        inputs.fabric-cli.packages.${system}.default
        brightnessctl
        cava
        cliphist
        gpu-screen-recorder
        grimblast
        hypridle
        hyprlock
        hyprpicker
        hyprshot
        hyprsunset
        imagemagick
        matugen
        noto-fonts-emoji
        nvtopPackages.full
        swappy
        swww
        tesseract
        tmux
        uwsm
        webp-pixbuf-loader
        wl-clipboard
        wlinhibit
      ];

      ax-shell-pkg = pkgs.callPackage ./default.nix {
        inherit
          self
          ax-shell-python
          runtimeDeps
          devTools;
      };

    in {
      packages = {
        default = ax-shell-pkg;
        ax-shell = ax-shell-pkg;
      };

      apps.default = {
        type = "app";
        program = "${ax-shell-pkg}/bin/ax-shell";
        meta.description = "A custom launcher for the Ax-Shell.";
      };
    })
    // {
      overlays.default = final: prev: {
        ax-shell = self.packages.${prev.system}.ax-shell;
      };
    };
}
