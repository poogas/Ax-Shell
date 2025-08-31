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

      tabler-icons-font = pkgs.stdenv.mkDerivation {
        pname = "tabler-icons-font";
        version = "local";
        src = self;

        installPhase = ''
          mkdir -p $out/share/fonts/truetype
          cp $src/assets/fonts/tabler-icons/tabler-icons.ttf $out/share/fonts/truetype/
        '';
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
          ps_.dbus-python
          ps_.ijson
          ps_.numpy
          ps_.pillow
          ps_.psutil
          ps_.pywayland
          ps_.requests
          ps_.setproctitle
          ps_.toml
          ps_.watchdog
        ];

      ax-shell-python = pkgs.python312.withPackages ax-shell-python-packages;
      ax-shell-inhibit-pkg = pkgs.stdenv.mkDerivation {
        pname = "ax-shell-inhibit";
        version = "unstable-${self.shortRev or "dirty"}";
        src = self;

        nativeBuildInputs = [ pkgs.makeWrapper ];
        buildInputs = [ ax-shell-python ];

        installPhase = ''
          runHook preInstall;
          
          mkdir -p $out/bin

          makeWrapper ${ax-shell-python}/bin/python $out/bin/ax-inhibit \
            --add-flags "$src/scripts/inhibit.py"
          
          runHook postInstall;
        '';
      };

      runtimeDeps = with pkgs; [
        adwaita-icon-theme
        papirus-icon-theme
        cinnamon-desktop
        gnome-bluetooth
        inputs.fabric-cli.packages.${system}.default
        inputs.gray.packages.${system}.default
        glib
        gobject-introspection
        gtk-layer-shell
        gtk3
        cairo
        gdk-pixbuf
        pango
        power-profiles-daemon
        libdbusmenu-gtk3
        libnotify
        upower
        vte
        webp-pixbuf-loader
        brightnessctl
        cava
        cliphist
        gnome-bluetooth
        gpu-screen-recorder
        grimblast
        hypridle
        hyprlock
        hyprpicker
        hyprshot
        hyprsunset
        imagemagick
        matugen
        networkmanager
        nvtopPackages.full
        playerctl
        procps
        swappy
        swww
        tesseract
        tmux
        unzip
        uwsm
        wl-clipboard
        wlinhibit
        ax-shell-inhibit-pkg
      ];

      ax-shell-pkg = pkgs.callPackage ./default.nix {
          self = self;
          ax-shell-python = ax-shell-python;
          runtimeDeps = runtimeDeps;
          adwaita-icon-theme = pkgs.adwaita-icon-theme;
          tabler-icons-font = tabler-icons-font;
	};

    in {
      packages = {
        default = ax-shell-pkg;
        ax-shell = ax-shell-pkg;
	fabric-cli = inputs.fabric-cli.packages.${system}.default;
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
        fabric-cli = self.packages.${prev.system}.fabric-cli;
      };

      homeManagerModules.default = import ./nix/modules/home-manager.nix;
    };
}
