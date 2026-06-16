# Mîrza - Intelligent Linux System Assistant

Mîrza is a lightweight, privacy-first system assistant for Linux.
It watches how you use your computer, learns your habits,
and automatically optimizes system resources.

## Quick Start

git clone https://github.com/ozgurcekic/mirza ~/mirza
cd ~/mirza && bash install.sh

mirza

## What does Mîrza do?

- Switches modes automatically: Eco when idle, Sport when gaming, Normal for daily use
- Adjusts CPU governor, brightness, volume per mode
- Monitors battery, temperature, disk health
- Stops unused background services, saves RAM
- Learns your routine, predicts your next app
- 11 plugins included, write your own in 10 lines
- Color-changing tray icon, terminal dashboard, CLI
- 100% local, zero network, no telemetry

## Modes

Eco
- When: system idle, on battery
- CPU: powersave, Brightness: low, Background services: stopped

Normal
- When: daily use
- CPU: ondemand, Brightness: medium, Background services: running

Sport
- When: gaming, rendering, compiling
- CPU: performance, Brightness: max, Background services: stopped

Custom
- Your own preset with per-mode settings

## Per-mode power settings

Each mode can be fine-tuned in Settings:

- Dedicate all power to focused app
- Stop background services
- Silence notifications
- Disable Bluetooth
- Enable Night Light
- Screen off timeout

## 11 Official Plugins

    Battery Manager - Auto Eco on low battery
    Thermal Guard - Forces Eco if overheating
    Hardware Health - Disk SMART checks, RAM anomaly
    Mail Optimizer - Opens mail only when needed
    Service Optimizer - Stops unused background services
    Audio Profile - Volume per mode
    Wallpaper Switcher - Background per mode
    FPS Limiter - Caps FPS in Eco, unlimited in Sport
    Monitor Profile - External display detection
    Shortcut Suggester - Keybindings for frequent switches
    User Script Trigger - Your scripts on app open/close

## Plugin System

Create plugins/user/my_plugin.py:

    from plugins.base_plugin import BasePlugin

    class MyPlugin(BasePlugin):
        def on_focus_change(self, event):
            if "firefox" in event.process_name:
                self.mirza.send_notification("Firefox!", "Browser opened")
            return False

Enable in config.yml under features: 

    my_plugin: true

## CLI Commands

    mirza                  Start the daemon
    mirza status           System overview
    mirza remind "text"    Add a reminder
    mirza list             List all reminders
    mirza done 3           Mark reminder 3 as done
    mirza --ui             Terminal dashboard
    mirza --log 20         Show last 20 log lines 

## Privacy and Security

- 100% local, no network, no telemetry, no cloud
- Dry-run mode for testing without system changes
- Rollback for every change
- Whitelist for critical services
- Learning period: first 14 days observe only
- Open source GPL-3.0


## Requirements

- Any Linux distribution
- Python 3.8 or newer
- X11 or Wayland
- install.sh handles all dependencies

## Author

Ozgur CEKIC - GPL-3.0
