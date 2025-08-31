{ config, pkgs, lib, ... }:

with lib;

let
  cfg = config.programs.ax-shell;

  formatKeybindings = keybindings:
    let
      prefixes = mapAttrs' (name: value: nameValuePair "prefix_${name}" value.prefix) keybindings;
      suffixes = mapAttrs' (name: value: nameValuePair "suffix_${name}" value.suffix) keybindings;
    in
    prefixes // suffixes;

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

    # Новые опции
    notif_pos = settings.notifications.position;
    limited_apps_history = settings.notifications.limitedAppsHistory;
    history_ignored_apps = settings.notifications.historyIgnoredApps;

    metrics_visible = settings.metrics.main;
    metrics_small_visible = settings.metrics.small;
  } // (formatKeybindings cfg.settings.keybindings);

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
        limitedAppsHistory = mkOption {
          type = types.listOf types.str;
          default = [ "Spotify" ];
          description = "Apps with limited notification history.";
        };
        historyIgnoredApps = mkOption {
          type = types.listOf types.str;
          default = [ "Hyprshot" ];
          description = "Apps whose notifications are ignored in history.";
        };
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

      keybindings = mkOption {
        type = with types; attrsOf (submodule {
          options = {
            prefix = mkOption { type = types.str; };
            suffix = mkOption { type = types.str; };
          };
        });
        default = {
          restart = { prefix = "SUPER ALT"; suffix = "B"; };
          axmsg = { prefix = "SUPER"; suffix = "A"; };
          dash = { prefix = "SUPER"; suffix = "D"; };
          bluetooth = { prefix = "SUPER"; suffix = "B"; };
          pins = { prefix = "SUPER"; suffix = "Q"; };
          kanban = { prefix = "SUPER"; suffix = "N"; };
          launcher = { prefix = "SUPER"; suffix = "R"; };
          tmux = { prefix = "SUPER"; suffix = "T"; };
          cliphist = { prefix = "SUPER"; suffix = "V"; };
          toolbox = { prefix = "SUPER"; suffix = "S"; };
          overview = { prefix = "SUPER"; suffix = "TAB"; };
          wallpapers = { prefix = "SUPER"; suffix = "COMMA"; };
          randwall = { prefix = "SUPER SHIFT"; suffix = "COMMA"; };
          mixer = { prefix = "SUPER"; suffix = "M"; };
          emoji = { prefix = "SUPER"; suffix = "PERIOD"; };
          power = { prefix = "SUPER"; suffix = "ESCAPE"; };
          caffeine = { prefix = "SUPER SHIFT"; suffix = "M"; };
          toggle = { prefix = "SUPER CTRL"; suffix = "B"; };
          css = { prefix = "SUPER SHIFT"; suffix = "B"; };
          restart_inspector = { prefix = "SUPER CTRL ALT"; suffix = "B"; };
        };
        description = "Keybindings for various Ax-Shell actions.";
      };
    };
    hyprlandBinds = mkOption {
      type = with types; listOf str;
      readOnly = true;
      description = "The list of keybinds that Ax-Shell provides for Hyprland.";
    };
    hyprlandExecOnce = mkOption {
      type = with types; listOf str;
      readOnly = true;
      description = "The list of exec-once commands that Ax-Shell provides for Hyprland.";
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

      kb = cfg.settings.keybindings;

      get_app_and_call = method: "fabric-cli exec ax-shell \"from main import AxShellApp; app = AxShellApp.get_default(); app.${method}\"";

      reloadCmd = "killall ax-shell; ${pkgs.uwsm}/bin/uwsm-app -- ${pkgs.writeShellScriptBin "ax-shell-run" '' exec ${wrappedPackage}/bin/ax-shell &> \"${cfg.autostart.logPath}\"''}/bin/ax-shell-run";

      axShellBinds = [
        "${kb.restart.prefix}, ${kb.restart.suffix}, exec, ${reloadCmd}"
        "${kb.axmsg.prefix}, ${kb.axmsg.suffix}, exec, notify-send 'Axenide' 'FIRE IN THE HOLE‼️🗣️🔥🕳️' -i '${cfg.package}/share/ax-shell/assets/ax.png' -a 'Source Code'"
        "${kb.dash.prefix}, ${kb.dash.suffix}, exec, ${get_app_and_call "notch.open_notch('dashboard')"}"
        "${kb.bluetooth.prefix}, ${kb.bluetooth.suffix}, exec, ${get_app_and_call "notch.open_notch('bluetooth')"}"
        "${kb.pins.prefix}, ${kb.pins.suffix}, exec, ${get_app_and_call "notch.open_notch('pins')"}"
        "${kb.kanban.prefix}, ${kb.kanban.suffix}, exec, ${get_app_and_call "notch.open_notch('kanban')"}"
        "${kb.launcher.prefix}, ${kb.launcher.suffix}, exec, ${get_app_and_call "notch.open_notch('launcher')"}"
        "${kb.tmux.prefix}, ${kb.tmux.suffix}, exec, ${get_app_and_call "notch.open_notch('tmux')"}"
        "${kb.cliphist.prefix}, ${kb.cliphist.suffix}, exec, ${get_app_and_call "notch.open_notch('cliphist')"}"
        "${kb.toolbox.prefix}, ${kb.toolbox.suffix}, exec, ${get_app_and_call "notch.open_notch('tools')"}"
        "${kb.overview.prefix}, ${kb.overview.suffix}, exec, ${get_app_and_call "notch.open_notch('overview')"}"
        "${kb.wallpapers.prefix}, ${kb.wallpapers.suffix}, exec, ${get_app_and_call "notch.open_notch('wallpapers')"}"
        "${kb.mixer.prefix}, ${kb.mixer.suffix}, exec, ${get_app_and_call "notch.open_notch('mixer')"}"
        "${kb.emoji.prefix}, ${kb.emoji.suffix}, exec, ${get_app_and_call "notch.open_notch('emoji')"}"
        "${kb.power.prefix}, ${kb.power.suffix}, exec, ${get_app_and_call "notch.open_notch('power')"}"
        "${kb.css.prefix}, ${kb.css.suffix}, exec, ${get_app_and_call "set_css()"}"
        "${kb.randwall.prefix}, ${kb.randwall.suffix}, exec, ${get_app_and_call "notch.dashboard.wallpapers.set_random_wallpaper(None, external=True)"}"
        "${kb.caffeine.prefix}, ${kb.caffeine.suffix}, exec, ${get_app_and_call "notch.dashboard.widgets.buttons.caffeine_button.toggle_inhibit(external=True)"}"
        "${kb.restart_inspector.prefix}, ${kb.restart_inspector.suffix}, exec, GTK_DEBUG=interactive ${reloadCmd}"
      ];

      axShellExecOnce = if cfg.autostart.enable then
        let
          uwsm-app = "${pkgs.uwsm}/bin/uwsm-app";
          swww-daemon = "swww-daemon";
          ax-shell-runner = pkgs.writeShellScriptBin "ax-shell-run" ''
            #!${pkgs.bash}/bin/bash
            mkdir -p "$(dirname "${cfg.autostart.logPath}")"
            exec ${wrappedPackage}/bin/ax-shell &> "${cfg.autostart.logPath}"
          '';
        in [
          "${swww-daemon}"
          "${uwsm-app} -- ${ax-shell-runner}/bin/ax-shell-run"
        ]
      else [];

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
      programs.ax-shell.hyprlandBinds = axShellBinds;
      programs.ax-shell.hyprlandExecOnce = axShellExecOnce;
    }
  );
}
