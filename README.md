# 🧠 Mîrza — Intelligent Linux System Assistant

Mîrza is a lightweight, privacy-first system assistant that watches how you use your computer and automatically optimizes resources.

## Features

- Tracks active windows, app usage time, hardware events
- Predicts your next app using Markov chains
- Eco / Normal / Sport modes + custom user presets
- Auto-adjusts CPU governor, brightness, volume per mode
- Battery manager, thermal guard, hardware health
- Mail optimizer, service optimizer
- Audio profile, wallpaper switcher, FPS limiter
- Color tray icon (green/blue/red)
- CLI: reminders, status, logs
- 100% local, zero network
- Plugin system: 10 lines to create one
- 11 official plugins included

## Quick Start

git clone https://github.com/ozgurcekic/mirza ~/mirza
cd ~/mirza && bash install.sh
mirza

## CLI

mirza status
mirza remind "text"
mirza list
mirza --ui
mirza --log 20

## Author

Özgür ÇEKİÇ — GPL-3.0
https://github.com/ozgurcekic/mirza
