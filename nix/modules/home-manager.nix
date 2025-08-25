{ config, pkgs, lib, ... }:

with lib;

let
  # Создаем сокращение для удобства
  cfg = config.programs.ax-shell;
in
{
  # =========================================================================
  #  ЧАСТЬ 1: ОПРЕДЕЛЕНИЕ ОПЦИЙ
  #  Здесь мы описываем, что пользователь сможет настраивать в своем home.nix
  # =========================================================================
  options.programs.ax-shell = {
    enable = mkEnableOption "Ax-Shell";

    # Мы будем использовать тот пакет, который определен в flake
    package = mkOption {
      type = types.package;
      default = pkgs.ax-shell; # Предполагает, что оверлей включен
      description = "Пакет ax-shell для установки.";
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
        description = "Центрировать ли виджеты на панели.";
      };
    };

    dock = {
      enable = mkOption {
        type = types.bool;
        default = true;
        description = "Включить ли док-панель.";
      };
      iconSize = mkOption {
        type = types.int;
        default = 28;
        description = "Размер иконок в доке.";
      };
    };

    terminal = {
      command = mkOption {
        type = types.str;
        default = "${pkgs.kitty}/bin/kitty -e";
        description = "Команда для запуска терминала.";
      };
    };
    
    # Можно добавить любые другие опции по аналогии
    # ...
  };


  # =========================================================================
  #  ЧАСТЬ 2: РЕАЛИЗАЦИЯ КОНФИГУРАЦИИ
  #  Здесь мы берем значения опций и превращаем их в реальные действия
  # =========================================================================
  config = mkIf cfg.enable {
    # Действие 1: Сгенерировать config.json из наших опций
    xdg.configFile."ax-shell/config.json" = {
      # pkgs.writeJson создает файл .json из атрибутов Nix
      source = pkgs.writeJson "ax-shell-config.json" {
        # Мы сопоставляем наши красивые опции с именами ключей,
        # которые ожидает data.py
        bar_position = cfg.bar.position;
        centered_bar = cfg.bar.centered;
        dock_enabled = cfg.dock.enable;
        dock_icon_size = cfg.dock.iconSize;
        terminal_command = cfg.terminal.command;
        # Добавьте здесь остальные опции по мере их реализации
      };
    };
    
    # Действие 2: Установить сам пакет
    home.packages = [ cfg.package ];

    # Действие 3: Передать путь к сгенерированному конфигу через переменную
    # Это "перебьет" значение по умолчанию, которое мы задали в default.nix
    home.sessionVariables.AX_SHELL_CONFIG_FILE =
      "${config.xdg.configHome}/ax-shell/config.json";
  };
}
