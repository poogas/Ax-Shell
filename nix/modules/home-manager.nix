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

    bar_button_apps_visible = settings.bar.components.button_apps;
    bar_systray_visible = settings.bar.components.systray;
    bar_control_visible = settings.bar.components.control;
    bar_network_visible = settings.bar.components.network;
    bar_button_tools_visible = settings.bar.components.button_tools;
    bar_sysprofiles_visible = settings.bar.components.sysprofiles;
    bar_button_overview_visible = settings.bar.components.button_overview;
    bar_ws_container_visible = settings.bar.components.ws_container;
    bar_weather_visible = settings.bar.components.weather;
    bar_battery_visible = settings.bar.components.battery;
    bar_metrics_visible = settings.bar.components.metrics;
    bar_language_visible = settings.bar.components.language;
    bar_date_time_visible = settings.bar.components.date_time;
    bar_button_power_visible = settings.bar.components.button_power;

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
      description = "The Ax-Shell package to use.";
    };

    autostart = {
      enable = mkEnableOption "autostart Ax-Shell with Hyprland" // {
        default = true;
      };
      logPath = mkOption {
        type = types.str;
        default = "${config.xdg.stateHome}/ax-shell/main.log";
        description = "Path to the log file for Ax-Shell.";
      };
    };

    settings = {
      wallpapersDir = mkOption {
        type = types.str;
        default = "${cfg.package}/share/ax-shell/assets/wallpapers_example";
        description = "Path to the wallpapers directory.";
      };
      defaultWallpaper = mkOption {
        type = types.path;
        default = "${cfg.package}/share/ax-shell/assets/wallpapers_example/example-1.jpg";
        description = "Path to the image to be used as the default wallpaper.";
      };
      terminalCommand = mkOption {
        type = types.str;
        default = "kitty -e";
        description = "The command to launch the terminal.";
      };
      datetime12hFormat = mkOption {
        type = types.bool;
        default = false;
        description = "Whether to use the 12-hour time format.";
      };
      bar = {
        position = mkOption {
          type = types.enum [ "Top" "Bottom" "Left" "Right" ];
          default = "Top";
          description = "The position of the main bar.";
        };
        centered = mkOption {
          type = types.bool;
          default = false;
          description = "Whether to center the components on the bar.";
        };
        theme = mkOption {
          type = types.str;
          default = "Pills";
          description = "The theme for the bar.";
        };
        workspace = {
          showNumber = mkOption { type = types.bool; default = false; description = "Show workspace number."; };
          useChineseNumerals = mkOption { type = types.bool; default = false; description = "Use Chinese numerals for workspace numbers."; };
          hideSpecial = mkOption { type = types.bool; default = true; description = "Hide special workspaces (e.g., scratchpads)."; };
        };
        metrics = {
          disks = mkOption {
            type = types.listOf types.str;
            default = [ "/" ];
            description = "List of disks to display in the metrics widget.";
          };
        };
        components = mkEnableOption "visibility of components on the bar" // {
          default = mapAttrs (_: _: true) (import ./component-types.nix);
          type = with types; attrsOf bool;
        };
      };
      dock = {
        enable = mkOption { type = types.bool; default = true; description = "Enable the dock."; };
        alwaysOccluded = mkOption { type = types.bool; default = false; description = "Keep the dock below windows at all times."; };
        iconSize = mkOption { type = types.int; default = 28; description = "The size of the icons in the dock."; };
        theme = mkOption { type = types.str; default = "Pills"; description = "The theme for the dock."; };
      };
      panel = {
        theme = mkOption { type = types.str; default = "Notch"; description = "The theme for the main panel (dashboard)."; };
        position = mkOption { type = types.str; default = "Center"; description = "The position of the main panel."; };
      };
      notifications = {
        position = mkOption { type = types.enum [ "Top" "Bottom" ]; default = "Top"; description = "The position of notifications."; };
      };
      metrics = {
        main = mkOption {
          type = with types; attrsOf bool;
          default = { cpu = true; ram = true; disk = true; gpu = true; };
          description = "Metrics to show in the main dashboard view.";
        };
        small = mkOption {
          type = with types; attrsOf bool;
          default = { cpu = true; ram = true; disk = true; gpu = true; };
          description = "Metrics to show in the small bar widget.";
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
        pkgs.swww
        pkgs.matugen
	pkgs.fabric-cli
      ];

      home.file."${config.xdg.configHome}/ax-shell/current.wall" = {
        source = cfg.settings.defaultWallpaper;
        force = true;
      };

      wayland.windowManager.hyprland.settings = mkIf (hyprlandEnabled) (
        let
          uwsm-app = "${pkgs.uwsm}/bin/uwsm-app";
          swww-daemon = "swww-daemon";
          ax-shell = pkgs.writeShellScriptBin "ax-shell-run" ''
	    #!${pkgs.bash}/bin/bash
            mkdir -p "$(dirname "${cfg.autostart.logPath}")"
            exec ${wrappedPackage}/bin/ax-shell &> "${cfg.autostart.logPath}"
          '';
        in
        {
          exec-once = mkIf cfg.autostart.enable [
            "${swww-daemon}"
            "${uwsm-app} -- ${ax-shell}/bin/ax-shell-run"
          ];
        }
      );
    }
  );
}
