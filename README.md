
---

<p align="center">
  <a href="https://github.com/poogas/Ax-Shell">
    <img src="assets/cover.png" alt="Ax-Shell Cover Image">
  </a>
</p>

<p align="center">
  <sub><sup><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Telegram-Animated-Emojis/main/Activity/Sparkles.webp" alt="Sparkles" width="25" height="25"/></sup></sub>
  <a href="https://github.com/hyprwm/Hyprland">
    <img src="https://img.shields.io/badge/A%20hackable%20shell%20for-Hyprland-0092CD?style=for-the-badge&logo=linux&color=0092CD&logoColor=D9E0EE&labelColor=000000" alt="A hackable shell for Hyprland">
  </a>
  <a href="https://www.nixos.org">
    <img src="https://img.shields.io/badge/Packaged%20for-NixOS-5277C3?style=for-the-badge&logo=nixos&logoColor=white&labelColor=000000" alt="Packaged for NixOS">
  </a>
  <sub><sup><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Telegram-Animated-Emojis/main/Activity/Sparkles.webp" alt="Sparkles" width="25" height="25"/></sup></sub>
</p>

<p align="center">
  This is a <strong>NixOS Flake</strong> for <a href="https://github.com/Axenide/Ax-Shell">Ax-Shell</a>, providing a seamless and declarative way to integrate this beautiful shell into your NixOS configuration using Home Manager.
</p>

---

## <sub><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Camera%20with%20Flash.png" alt="Camera with Flash" width="25" height="25" /></sub> Screenshots

<table align="center">
  <tr>
    <td colspan="4"><img src="assets/screenshots/1.png"></td>
  </tr>
  <tr>
    <td colspan="1"><img src="assets/screenshots/2.png"></td>
    <td colspan="1"><img src="assets/screenshots/3.png"></td>
    <td colspan="1" align="center"><img src="assets/screenshots/4.png"></td>
    <td colspan="1" align="center"><img src="assets/screenshots/5.png"></td>
  </tr>
</table>

## <sub><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Symbols/Check%20Mark%20Button.png" alt="Check Mark Button" width="25" height="25" /></sub> Features

This flake handles all dependencies and provides a fully declarative setup for Ax-Shell, including:
- **Automatic Dependency Management**: All required system and Python packages are handled by Nix.
- **Declarative Configuration**: Configure every aspect of Ax-Shell directly from your `home.nix` file.
- **Home Manager Module**: A comprehensive module with documented options for easy customization.
- **Seamless Integration**: Automatically generates necessary configurations for Hyprland, `matugen`, and theming.
- **Reproducible Environment**: Get the exact same shell setup on any NixOS machine.

## <sub><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Package.png" alt="Package" width="25" height="25" /></sub> Installation

> [!NOTE]
> A working NixOS setup with Flakes and Home Manager is required.

### 1. Add the Flake to Your Inputs
Add Ax-Shell to your `flake.nix` inputs.

```nix
# flake.nix
{
  inputs = {
    # ... your other inputs
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    home-manager.url = "github:nix-community/home-manager";

    ax-shell = {
      url = "github:poogas/Ax-Shell";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
}
```

### 2. Import the Home Manager Module
In your `home.nix` file, import the provided module.

```nix
# home.nix
{ inputs, ... }: {
  imports = [
    inputs.ax-shell.homeManagerModules.default
  ];
}
```

### 3. Enable Ax-Shell
Enable the shell in your Home Manager configuration.

```nix
# home.nix
{ pkgs, ... }: {
  programs.ax-shell = {
    enable = true;
  };

  # Ax-Shell needs Hyprland to run. See the integration guide below.
  wayland.windowManager.hyprland = {
    enable = true;
    # ... your hyprland settings
  };
}
```

Rebuild your system with `nixos-rebuild switch --flake .#your-host`, and Ax-Shell will be ready to use.

## <sub><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Gear.png" alt="Gear" width="25" height="25" /></sub> Configuration

All settings are managed declaratively under the `programs.ax-shell.settings` option set in your `home.nix`.

Here is an example demonstrating common customizations:
```nix
# home.nix
{ pkgs, ... }: {
  programs.ax-shell = {
    enable = true;
    settings = {
      # --- General ---
      terminalCommand = "alacritty -e";
      wallpapersDir = "/path/to/your/wallpapers";

      # --- Cursor ---
      cursor = {
        package = pkgs.oreo-cursors-plus;
        name = "oreo_black_cursors";
        size = 24;
      };

      # --- Bar & Dock ---
      bar = {
        position = "Top"; # "Top", "Bottom", "Left", "Right"
        theme = "Pills";  # "Pills", "Dense", "Edge"
      };
      dock.enable = false; # Disable the dock
      panel.theme = "Notch"; # "Notch", "Panel"

      # --- Keybindings ---
      keybindings.launcher = { prefix = "SUPER"; suffix = "SPACE"; };
    };
  };
}
```

> [!TIP]
> For a complete list of all available options, please refer to the module file: [`nix/modules/home-manager.nix`](./nix/modules/home-manager.nix).

> [!NOTE]
> For a complete, real-world example of how to integrate Ax-Shell with Hyprland and other desktop components, you can check out this reference configuration:
> **https://github.com/poogas/nix-config**

## <sub><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Travel%20and%20places/Circus%20Tent.png" alt="Circus Tent" width="25" height="25" /></sub> Integrations

<details>
<summary><strong>Core Integration: Hyprland</strong></summary>

Ax-Shell is not a standalone window manager; it is a comprehensive shell environment designed to run on top of **Hyprland**.

To make integration seamless, the NixOS module automatically generates the necessary Hyprland `bind` and `exec-once` directives. You can easily merge them with your personal configuration using the `++` operator.

```nix
# In your home.nix
{ config, ... }: {
  wayland.windowManager.hyprland = {
    enable = true;

    settings = {
      # ... your other Hyprland settings (monitors, animations, etc.)

      # --- Ax-Shell Integration ---
      # Use the '++' operator to merge Ax-Shell's binds with your own.
      bind = config.programs.ax-shell.hyprlandBinds ++ [
        # Add your custom keybinds here
        "SUPER, return, exec, alacritty"
        "SUPER, C, killactive,"
      ];

      # Merge Ax-Shell's startup commands with your own.
      exec-once = config.programs.ax-shell.hyprlandExecOnce ++ [
        # Your other startup apps
      ];
    };
  };
}
```
> For a practical example, see this **[hyprland.nix module](https://github.com/poogas/nix-config/blob/master/home/modules/desktop/hyprland.nix)**.

</details>

<details>
<summary><strong>Screen Locking & Idle Management (hyprlock, hypridle)</strong></summary>

Ax-Shell provides keybindings and UI elements for screen locking, but you need to configure the underlying tools. This setup integrates seamlessly with the theme generated by Ax-Shell.

```nix
# In your home.nix
{ config, ... }: {
  # Hyprland idle daemon
  services.hypridle = {
    enable = true;
    # ... your settings
  };

  # Hyprland screen locker
  programs.hyprlock = {
    enable = true;
    settings = {
      # This links hyprlock's theme to Ax-Shell's dynamic colors
      source = config.programs.ax-shell.hyprlandColorsConfPath;

      background = {
        path = config.programs.ax-shell.currentWallpaperPath;
        # ...
      };
    };
  };
}
```
> See a working example for **[hypridle.nix](https://github.com/poogas/nix-config/blob/master/home/modules/desktop/hypridle.nix)** and **[hyprlock.nix](https://github.com/poogas/nix-config/blob/master/home/modules/desktop/hyprlock.nix)**.
</details>

<details>
<summary><strong>Launching Terminal Applications (xdg.terminal-exec)</strong></summary>

To allow the Ax-Shell launcher to open terminal-based applications (like `btop` or `neovim`), you need to specify a default terminal emulator.

```nix
# In your configuration.nix or home.nix
{ pkgs, ... }: {
  xdg.terminal-exec = {
    enable = true;
    settings.default = [ "alacritty.desktop" ];
  };
}
```
> You can see an example implementation in this **[terminal-exec.nix module](https://github.com/poogas/nix-config/blob/master/system/desktop/terminal-exec.nix)**.
</details>

<details>
<summary><strong>SDDM Dynamic Theme</strong></summary>

To sync your login screen wallpaper with your Ax-Shell wallpaper, use `sddm-dynamic-theme`.

1.  **Add the input** to your `flake.nix`.
2.  **Enable it** in your system configuration (`configuration.nix`).
    ```nix
    # configuration.nix
    { inputs, config, ... }: {
      imports = [ inputs.sddm-dynamic-theme.nixosModules.default ];

      services.sddm-dynamic-theme = {
        enable = true;
        username = "your-username";
        avatar.sourcePath = config.home-manager.users.your-username.programs.ax-shell.settings.defaultFaceIcon;
      };
    }
    ```
> For an example of this setup, see this **[sddm.nix file](https://github.com/poogas/nix-config/blob/master/system/desktop/sddm.nix)**.
</details>

<details>
<summary><strong>NVIDIA Brightness Control</strong></summary>

For brightness control to work correctly on NVIDIA desktop GPUs, you need `nixos-ddcci-nvidia`.

1.  **Add the input** to your `flake.nix`.
2.  **Import the module** in your system configuration (`configuration.nix`).
    ```nix
    # configuration.nix
    { inputs, ... }: {
      imports = [ inputs.nixos-ddcci-nvidia.nixosModules.default ];
      hardware.ddcci.enable = true;
    }
    ```
> An example of this module can be found in this **[ddcci.nix configuration](https://github.com/poogas/nix-config/blob/master/system/hardware/ddcci.nix)**.
</details>

## ✨ Included Features

- [x] App Launcher
- [x] Bluetooth Manager
- [x] Calculator
- [x] Calendar
- [x] Clipboard Manager
- [x] Color Picker
- [x] Customizable UI
- [x] Dashboard
- [x] Dock
- [x] Emoji Picker
- [x] Kanban Board
- [x] Network Manager
- [x] Notifications
- [x] OCR
- [x] Pins
- [x] Power Manager
- [x] Power Menu
- [x] Screen Recorder
- [x] Screenshot
- [x] Settings
- [x] System Tray
- [x] Terminal
- [x] Tmux Session Manager
- [x] Update checker
- [x] Vertical Layout
- [x] Wallpaper Selector
- [x] Workspaces Overview

## <sub><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Hand%20gestures/Flexed%20Biceps.png" alt="Flexed Biceps" width="25" height="25" /></sub> Acknowledgements

A huge thank you to **[Axenide](https://github.com/Axenide)** for creating the original [Ax-Shell](https://github.com/Axenide/Ax-Shell). This project is a NixOS-focused packaging and declarative integration of their amazing work.
