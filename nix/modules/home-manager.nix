{ config, pkgs, lib, ... }:

with lib;

let
  cfg = config.programs.ax-shell;
in
{
  options.programs.ax-shell = {
    enable = mkEnableOption "Ax-Shell";
    package = mkOption {
      type = types.package;
      default = pkgs.ax-shell;
      description = "package ax-shell";
    };
  };

  config = mkIf cfg.enable {
    home.packages = [ cfg.package ];

    programs.hyprland.extraConfig = ''
      exec-once = uwsm -- app ax-shell &> ${config.xdg.stateHome}/ax-shell/main.log & disown
    '';
  };
}
