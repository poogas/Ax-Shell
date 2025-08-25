# ~/.config/Ax-Shell/nix/modules/home-manager.nix

{ config, pkgs, lib, ... }:

with lib;

let
  cfg = config.programs.ax-shell;
  hyprlandEnabled = config.wayland.windowManager.hyprland.enable;

  # --- Генератор JSON ---
  # Эта функция берет настройки из Nix и преобразует их в формат,
  # который ожидает Python-скрипт (например, bar.centered -> centered_bar).
  formatJson = settings: {
    wallpapers_dir = settings.wallpapersDir;
    terminal_command = settings.terminalCommand;
    datetime_12h_format = settings.datetime12hFormat;

    # Секция "bar"
    bar_position = settings.bar.position;
    centered_bar = settings.bar.centered;
    bar_theme = settings.bar.theme;
    bar_workspace_show_number = settings.bar.workspace.showNumber;
    bar_workspace_use_chinese_numerals = settings.bar.workspace.useChineseNumerals;
    bar_hide_special_workspace = settings.bar.workspace.hideSpecial;
    bar_metrics_disks = settings.bar.metrics.disks;

    # Видимость компонентов бара
    bar_button_apps_visible = settings.bar.components.appsButton;
    bar_systray_visible = settings.bar.components.systray;
    bar_control_visible = settings.bar.components.control;
    bar_network_visible = settings.bar.components.network;
    bar_button_tools_visible = settings.bar.components.toolsButton;
    bar_sysprofiles_visible = settings.bar.components.systemProfiles;
    bar_button_overview_visible = settings.bar.components.overviewButton;
    bar_ws_container_visible = settings.bar.components.workspaces;
    bar_weather_visible = settings.bar.components.weather;
    bar_battery_visible = settings.bar.components.battery;
    bar_metrics_visible = settings.bar.components.metrics;
    bar_language_visible = settings.bar.components.language;
    bar_date_time_visible = settings.bar.components.dateTime;
    bar_button_power_visible = settings.bar.components.powerButton;

    # Секция "dock"
    dock_enabled = settings.dock.enable;
    dock_always_occluded = settings.dock.alwaysOccluded;
    dock_icon_size = settings.dock.iconSize;
    dock_theme = settings.dock.theme;

    # Секция "panel"
    panel_theme = settings.panel.theme;
    panel_position = settings.panel.position;

    # Остальные настройки
    notif_pos = settings.notifications.position;
    metrics_visible = settings.metrics.main;
    metrics_small_visible = settings.metrics.small;
  };

in {
  # --- Опции, которые пользователь сможет настраивать ---
  options.programs.ax-shell = {
    enable = mkEnableOption "Ax-Shell";

    package = mkOption {
      type = types.package;
      default = pkgs.ax-shell;
      defaultText = literalExpression "pkgs.ax-shell";
      description = "Какой пакет Ax-Shell использовать.";
    };

    autostart = {
      enable = mkEnableOption "автозапуск Ax-Shell вместе с Hyprland" // {
        default = true;
      };
      logPath = mkOption {
        type = types.str;
        default = "${config.xdg.stateHome}/ax-shell/main.log";
        description = "Путь к файлу для логирования Ax-Shell.";
      };
    };

    # --- НОВАЯ СЕКЦИЯ: Декларативная конфигурация Ax-Shell ---
    settings = {
      wallpapersDir = mkOption {
        type = types.str;
        default = "${cfg.package}/share/ax-shell/assets/wallpapers_example";
        description = "Путь к директории с обоями.";
      };

      terminalCommand = mkOption {
        type = types.str;
        default = "kitty -e";
        description = "Команда для запуска терминала.";
      };
      
      datetime12hFormat = mkOption {
        type = types.bool;
        default = false;
        description = "Использовать 12-часовой формат времени.";
      };

      bar = {
        position = mkOption {
          type = types.enum [ "Top" "Bottom" "Left" "Right" ];
          default = "Top";
          description = "Позиция основной панели.";
        };

        centered = mkOption {
          type = types.bool;
          default = false;
          description = "Центрировать ли компоненты на панели.";
        };

        theme = mkOption {
          type = types.str; # Можно будет сделать enum
          default = "Pills";
          description = "Тема оформления панели.";
        };
        
        workspace = {
            showNumber = mkOption { type = types.bool; default = false; };
            useChineseNumerals = mkOption { type = types.bool; default = false; };
            hideSpecial = mkOption { type = types.bool; default = true; };
        };

        metrics = {
          disks = mkOption {
            type = types.listOf types.str;
            default = [ "/" ];
            description = "Список дисков для отображения в виджете метрик.";
          };
        };

        components = mkEnableOption "видимость компонентов на панели" // {
          # Используем `mkOptionDefault` для установки всех значений по умолчанию в `true`
          default = mapAttrs (_: _: true) (import ./component-types.nix);
          # Тип - это атрибут-сет булевых значений
          type = with types; attrsOf bool;
        };
      };

      dock = {
        enable = mkOption { type = types.bool; default = true; };
        alwaysOccluded = mkOption { type = types.bool; default = false; };
        iconSize = mkOption { type = types.int; default = 28; };
        theme = mkOption { type = types.str; default = "Pills"; };
      };

      panel = {
        theme = mkOption { type = types.str; default = "Notch"; };
        position = mkOption { type = types.str; default = "Center"; };
      };
      
      notifications = {
          position = mkOption { type = types.enum [ "Top" "Bottom" ]; default = "Top"; };
      };

      metrics = {
        main = mkOption {
          type = with types; attrsOf bool;
          default = { cpu = true; ram = true; disk = true; gpu = true; };
        };
        small = mkOption {
          type = with types; attrsOf bool;
          default = { cpu = true; ram = true; disk = true; gpu = true; };
        };
      };
    };
  };

  # --- Конфигурация, которая будет применяться ---
  config = mkIf cfg.enable (let
    # 1. Генерируем JSON из настроек пользователя
    jsonConfigFile = pkgs.writeText "ax-shell-config.json" (builtins.toJSON (formatJson cfg.settings));

    # 2. Создаем "обернутый" пакет, который знает о нашем конфиге
    wrappedPackage = pkgs.symlinkJoin {
      name = "ax-shell-with-declarative-config";
      paths = [ cfg.package ]; # Берем оригинальный пакет
      nativeBuildInputs = [ pkgs.makeWrapper ];
      postBuild = ''
        # "Оборачиваем" бинарник, добавляя переменную окружения
        wrapProgram $out/bin/ax-shell \
          --set AX_SHELL_CONFIG_FILE "${jsonConfigFile}"
      '';
    };
  in {
    home.packages = [ wrappedPackage ];

    wayland.windowManager.hyprland.settings = mkIf (cfg.autostart.enable && hyprlandEnabled) {
      exec-once = [
        "${wrappedPackage}/bin/ax-shell &> ${cfg.autostart.logPath}"
      ];
    };
  });
}
