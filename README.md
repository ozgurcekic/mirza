# 🧠 Mîrza — Intelligent Linux System Assistant

**Mîrza** is a lightweight, privacy-first system assistant for Linux. It watches how you use your computer, learns your habits, and automatically optimizes system resources — without you noticing it's there.

---

## ❓ What does Mîrza do?

Mîrza runs quietly in the background. It observes which apps you use, when you use them, and how your system behaves. Then it:

1. **Switches modes automatically** — Eco when idle, Sport when gaming, Normal for daily use
2. **Optimizes resources** — adjusts CPU governor, brightness, volume per mode
3. **Protects your hardware** — monitors battery, temperature, disk health
4. **Saves RAM** — stops unused services, closes mail client when not needed
5. **Learns your routine** — predicts which app you'll open next
6. **Stays out of your way** — color-changing tray icon, optional terminal dashboard

---

## 🎮 How the modes work

| Mode | When | CPU | Brightness | Background services |
|------|------|-----|------------|---------------------|
| 🟢 **Eco** | System idle, on battery | Powersave | 25% | Stopped |
| 🔵 **Normal** | Daily use | Ondemand | 70% | Running |
| 🔴 **Sport** | Gaming, rendering | Performance | 100% | Stopped (all power to app) |
| ⭐ **Custom** | Your preset | Your choice | Your choice | Your choice |

### Each mode has per-mode settings:

- **Dedicate all power to focused app** — kills background tasks
- **Stop background services** — frees RAM
- **Silence notifications** — no distractions
- **Disable Bluetooth** — saves battery
- **Enable Night Light** — eye comfort
- **Screen off timeout** — saves energy

---

## 📦 What's included

### 11 Official Plugins

| Plugin | What it does |
|--------|-------------|
| **Battery Manager** | Auto-switches to Eco on low battery, estimates remaining time |
| **Thermal Guard** | Monitors CPU/GPU temp, forces Eco if overheating |
| **Hardware Health** | Weekly disk SMART check, RAM anomaly detection |
| **Mail Optimizer** | Learns when you check mail, opens client only at those times |
| **Service Optimizer** | Stops unused services (tracker, packagekit, cups...) |
| **Audio Profile** | Adjusts volume per mode |
| **Wallpaper Switcher** | Changes desktop background per mode |
| **FPS Limiter** | Caps FPS in Eco, unlimited in Sport (MangoHud) |
| **Monitor Profile** | Detects external monitor, can switch mode |
| **Shortcut Suggester** | Notices frequent app switches, suggests keybindings |
| **User Script Trigger** | Runs your scripts when specific apps open/close |

---

## 🖥️ User Interface

| Component | Description |
|-----------|-------------|
| **Tray Icon** | Green/Blue/Red circle in system tray. Right-click for mode switch, settings, quit |
| **Settings Window** | GTK3 window with tabs: General, Eco, Normal, Sport, Custom, Features |
| **Terminal Dashboard** | `mirza --ui` — live system stats in terminal |
| **CLI** | Full command-line interface for reminders, status, logs |

---

## 💬 CLI Reference

| Command | Description |
|---------|-------------|
| `mirza` | Start the daemon |
| `mirza status` | Show system overview |
| `mirza remind "buy milk"` | Add a reminder |
| `mirza list` | List all reminders |
| `mirza done 3` | Mark reminder #3 as done |
| `mirza --ui` | Launch terminal dashboard |
| `mirza --log 20` | Show last 20 log lines |
| `mirza --verbose` | Start with debug output |

---

## 🧩 Plugin System

Create a file at `plugins/user/my_plugin.py`:

```python
from plugins.base_plugin import BasePlugin

class MyPlugin(BasePlugin):
    def on_focus_change(self, event):
        if "firefox" in event.process_name:
            self.mirza.send_notification("Firefox!", "Browser opened")
        return False

Enable it in ~/.config/mirza/config.yml:

features:
  my_plugin: true

🛡️ Privacy & Security

    100% local — no network connections, no telemetry, no cloud

    Dry-run mode — test without changing anything

    Rollback — every system change is logged and reversible

    Whitelist — critical services are never touched

    Learning period — first 14 days: observe only, no auto-actions

    Open source — GPL-3.0, anyone can audit the code

📋 Requirements

    Any Linux distribution (Ubuntu, Fedora, Arch, SteamOS, Debian...)

    Python 3.8 or newer

    X11 or Wayland (GNOME, KDE, Sway, Hyprland, Gamescope)

    install.sh installs all dependencies automatically


🚀 Install & Run

git clone https://github.com/ozgurcekic/mirza ~/mirza
cd ~/mirza && bash install.sh
mirza

Auto-start on boot:

systemctl --user enable --now mirza

👤 Author

Özgür ÇEKİÇ

License: GNU General Public License v3.0
