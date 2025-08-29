{ config, pkgs, lib, ... }:

with lib;

let
  cfg = config.programs.ax-shell;
  hyprlandEnabled = config.wayland.windowManager.hyprland.enable;

  formatJson = settings: {
    wallpapers_dir = settings.wallpapersDir;
    terminal_command = settings.terminalCommand;
    datetime_12h_format = settings.datetime12hFormat;
    bar_position = settings.bar.position;
    centered_bar = settings.bar.centered;
    bar_theme = settings.bar.theme;
    bar_workspace_show_number = settings.bar.workspace.showNumber;
    bar_workspace_use_chinese_numerals = settings.bar.workspace.useChineseNumerals;
    bar_hide_special_workspace = settings.bar.workspace.hideSpecial;
    bar_metrics_disks = settings.bar.metrics.disks;
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
    dock_enabled = settings.dock.enable;
    dock_always_occluded = settings.dock.alwaysOccluded;
    dock_icon_size = settings.dock.iconSize;
    dock_theme = settings.dock.theme;
    panel_theme = settings.panel.theme;
    panel_position = settings.panel.position;
    notif_pos = settings.notifications.position;
    metrics_visible = settings.metrics.main;
    metrics_small_visible = settings.metrics.small;
  };

in
{
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

    settings = {
      wallpapersDir = mkOption {
        type = types.str;
        default = "${cfg.package}/share/ax-shell/assets/wallpapers_example";
        description = "Путь к директории с обоями.";
      };
      defaultWallpaper = mkOption {
        type = types.path;
        default = "${cfg.package}/share/ax-shell/assets/wallpapers_example/example-1.jpg";
        description = "Путь к изображению, которое будет использоваться как обои по умолчанию.";
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
          type = types.str;
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
          default = mapAttrs (_: _: true) (import ./component-types.nix);
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

  config = mkIf cfg.enable (
    let
      wrappedPackage = pkgs.symlinkJoin {
        name = "ax-shell-with-declarative-config";
        paths = [ cfg.package ];
        nativeBuildInputs = [ pkgs.makeWrapper ];
        postBuild = ''
          wrapProgram $out/bin/ax-shell \
            --set AX_SHELL_CONFIG_FILE "${jsonConfigFile}"
        '';
      };

      jsonConfigFile = pkgs.writeText "ax-shell-config.json" (builtins.toJSON (formatJson cfg.settings));

    in
    {
      home.packages = [
        wrappedPackage
        pkgs.uwsm
        pkgs.swww
        pkgs.matugen
      ];

      home.file."${config.xdg.configHome}/ax-shell/current.wall" = {
        source = cfg.settings.defaultWallpaper;
        force = true;
      };

      wayland.windowManager.hyprland.settings = mkIf (hyprlandEnabled) (
        let
          uwsm-app = "${pkgs.uwsm}/bin/uwsm-app";
          swww-daemon = "${pkgs.swww}/bin/swww-daemon";
          ax-shell-run = ''
            ${pkgs.bash}/bin/bash -c "${wrappedPackage}/bin/ax-shell &> ${cfg.autostart.logPath}"
          '';
        in
        {
          exec-once = mkIf cfg.autostart.enable [
            "${uwsm-app} -- ${swww-daemon}"
            "${uwsm-app} -- ${ax-shell-run}"
          ];
        }
      );
    }
  );
}
