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
      defaultText = literalExpression "pkgs.ax-shell";
      description = "Пакет Ax-Shell для установки.";
    };
  };

  config = mkIf cfg.enable {
    home.packages = [ cfg.package ];
  };
}
