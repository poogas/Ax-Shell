{
  description = "A clean, elegant, and working flake for Ax-Shell";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    fabric.url = "github:Fabric-Development/fabric";
    gray.url = "github:Fabric-Development/gray";
    fabric-cli.url = "github:poogas/fabric-cli"; # Ваш рабочий форк
  };

  # Гарантируем, что все флейки используют одну и ту же версию nixpkgs
  inputs.fabric.inputs.nixpkgs.follows = "nixpkgs";
  inputs.gray.inputs.nixpkgs.follows = "nixpkgs";
  inputs.fabric-cli.inputs.nixpkgs.follows = "nixpkgs";

  outputs = { self, nixpkgs, flake-utils, ... }@inputs:
    let
      # Определяем поддерживаемые системы. `gray` работает только на x86_64-linux.
      supportedSystems = [ "x86_64-linux" ];
    in
    flake-utils.lib.eachSystem supportedSystems (system:
      let
        # --- ШАГ 1: Создаем кастомный набор пакетов `pkgs` ---
        
        # Оверлей, который "учит" nixpkgs о существовании нашего внешнего пакета `fabric`.
        # Это единственный правильный способ добавить внешний Python-пакет.
        ax-shell-overlay = final: prev: {
          pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
            (python-final: python-prev: {
              # Мы превращаем "сырой" пакет из флейка fabric в "настоящий"
              # Python-пакет, который nixpkgs сможет понять.
              ax-shell-fabric = python-prev.toPythonModule (inputs.fabric.packages.${system}.default);
            })
          ];
        };

        # Создаем `pkgs`, применяя наш оверлей.
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
          overlays = [ ax-shell-overlay ];
        };

        # --- ШАГ 2: Группируем зависимости для лучшей читаемости ---
        
        pythonDeps = with pkgs.python3Packages; [
          # Наш кастомный пакет `fabric`, добавленный через оверлей
          ax-shell-fabric
          # Стандартные Python-зависимости
          ijson numpy pillow psutil pygobject3
          requests setproctitle toml watchdog
        ];

        systemDeps = with pkgs; [
          # Зависимости из других флейков
          inputs.fabric-cli.packages.${system}.default
          inputs.gray.packages.${system}.default
          # Системные библиотеки для GObject (критически важно для `wrapGAppsHook`)
          glib gobject-introspection gtk-layer-shell
          # Все остальные системные утилиты
          brightnessctl cava cliphist gnome-bluetooth gpu-screen-recorder
          grimblast hypridle hyprlock hyprpicker
          hyprshot hyprsunset imagemagick libdbusmenu-gtk3 libnotify matugen
          networkmanager noto-fonts-emoji nvtopPackages.full playerctl
          swappy swww tesseract tmux uwsm
          webp-pixbuf-loader wl-clipboard wlinhibit
        ];

      in
      {
        # --- ШАГ 3: Определяем наш финальный пакет ---
        packages = {
          default = pkgs.stdenv.mkDerivation {
            pname = "ax-shell";
            version = "unstable-${self.shortRev or "dirty"}";
            src = self;

            # `wrapGAppsHook3` - наш главный инструмент для GObject-приложений.
            nativeBuildInputs = [ pkgs.wrapGAppsHook3 ];

            # Передаем все зависимости. `wrapGAppsHook3` сам разберется,
            # что положить в PYTHONPATH, GI_TYPELIB_PATH и т.д.
            buildInputs = [ pkgs.python3 ] ++ pythonDeps ++ systemDeps;

            # Простая и чистая фаза установки.
            installPhase = ''
              runHook preInstall
  
              # Копируем ВСЕ файлы из исходного кода в библиотечную директорию,
              # чтобы main.py мог найти все свои модули, виджеты и ассеты.
              mkdir -p $out/lib/ax-shell
              cp -r ./* $out/lib/ax-shell/

              # Создаем исполняемый файл-запускальщик в /bin
              mkdir -p $out/bin
              cp $out/lib/ax-shell/main.py $out/bin/ax-shell
              chmod +x $out/bin/ax-shell
  
              runHook postInstall
            '';

            preFixup = ''
              # `wrapGAppsHook3` автоматически создаст PYTHONPATH со всеми зависимостями.
              # Нам нужно просто ДОБАВИТЬ к этому пути путь к нашим собственным исходникам.
              # `--prefix PYTHONPATH : "$out/lib/ax-shell"` делает именно это.
              # : в начале означает "добавить в начало существующей переменной".
              gappsWrapperArgs+=(--prefix PYTHONPATH : "$out/lib/ax-shell")
              
              # Мы все еще можем добавить FABRIC_CSS_PATH, если он понадобится
              gappsWrapperArgs+=(--set FABRIC_CSS_PATH "$out/lib/ax-shell/main.css")
            '';

            # `preFixup` больше не нужен, так как мы убрали FABRIC_CSS_PATH.
            # `wrapGAppsHook3` сделает всю работу по созданию обертки.
          };
          
          # Удобный алиас для пакета
          ax-shell = self.packages.${system}.default;
        };

        # --- ШАГ 4: Определяем приложение и оверлей ---
        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/ax-shell";
          
          # --- ИСПРАВЛЕНИЕ: Добавляем метаданные, чтобы убрать предупреждение ---
          meta = {
            description = "A hackable shell for Hyprland, packaged as a flake.";
            license = pkgs.lib.licenses.mit; # Предполагаемая лицензия, можно уточнить
          };
        };
      }
    )
    # Стандартный паттерн для экспорта оверлея из флейка
    // {
      overlays.default = final: prev: {
        ax-shell = self.packages.${prev.system}.ax-shell;
      };
    };
}
