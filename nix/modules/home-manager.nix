{ config, pkgs, lib, ... }:

with lib;

let
  cfg = config.programs.ax-shell;
  hyprlandEnabled = config.wayland.windowManager.hyprland.enable;
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
  };

  config = lib.mkMerge [
    (mkIf cfg.enable {
      home.packages = [ cfg.package ];
    })

    (mkIf (cfg.enable && cfg.autostart.enable && hyprlandEnabled) {
      wayland.windowManager.hyprland.settings.exec-once = [
        "${cfg.package}/bin/ax-shell &> ${cfg.autostart.logPath}"
      ];
    })
  ];
}
