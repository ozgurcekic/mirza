#!/bin/bash
# ═══════════════════════════════════════════════════════
# MÎRZA - Intelligent System Assistant
# One-command installer for any Linux distribution
# Copyright (C) 2026 Özgür ÇEKİÇ - GPL-3.0
# ═══════════════════════════════════════════════════════

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       MÎRZA  -  Installation             ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
echo ""

# ──────────────────────────────────────────────
# 1. Detect OS and install dependencies
# ──────────────────────────────────────────────
echo -e "${GREEN}[1/6] Installing system dependencies...${NC}"

install_apt() {
    sudo apt update -qq
    sudo apt install -y -qq \
        python3 python3-pip python3-venv python3-dev \
        python3-xlib python3-psutil python3-pyudev \
        python3-gi python3-gi-cairo \
        gir1.2-gtk-3.0 gir1.2-appindicator3-0.1 \
        python3-dbus python3-notify2 python3-yaml \
        dbus-x11 xdotool
}

install_dnf() {
    sudo dnf install -y \
        python3 python3-pip python3-devel \
        python3-xlib python3-psutil python3-pyudev \
        python3-gobject gtk3 libappindicator-gtk3 \
        python3-dbus python3-notify2 python3-pyyaml \
        dbus-x11 xdotool
}

install_pacman() {
    sudo pacman -S --needed --noconfirm \
        python python-pip python-xlib python-psutil python-pyudev \
        python-gobject gtk3 libappindicator-gtk3 \
        python-dbus python-notify2 python-yaml \
        dbus-x11 xdotool
}

if command -v apt &>/dev/null; then
    install_apt
elif command -v dnf &>/dev/null; then
    install_dnf
elif command -v pacman &>/dev/null; then
    install_pacman
else
    echo -e "${RED}Unknown package manager. Install manually:${NC}"
    echo "  python3, python3-xlib, python3-psutil, python3-pyudev, python3-gi,"
    echo "  gir1.2-gtk-3.0, gir1.2-appindicator3-0.1, python3-dbus,"
    echo "  python3-notify2, python3-yaml, xdotool"
fi

# ──────────────────────────────────────────────
# 2. Create directories
# ──────────────────────────────────────────────
echo -e "${GREEN}[2/6] Creating directories...${NC}"
INSTALL_DIR="$HOME/.local/share/mirza"
CONFIG_DIR="$HOME/.config/mirza"
BIN_DIR="$HOME/.local/bin"
SYSTEMD_DIR="$HOME/.config/systemd/user"

mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$BIN_DIR" "$SYSTEMD_DIR"

# ──────────────────────────────────────────────
# 3. Copy Mîrza files
# ──────────────────────────────────────────────
echo -e "${GREEN}[3/6] Copying Mîrza files...${NC}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# If running from a cloned repo, use that. Otherwise use installed location.
if [ -d "$SOURCE_DIR/src" ]; then
    SOURCE_DIR="$SCRIPT_DIR"
else
    SOURCE_DIR="$HOME/.local/share/mirza"
fi
cp -r "$SOURCE_DIR/src" "$INSTALL_DIR/"
cp -r "$SOURCE_DIR/plugins" "$INSTALL_DIR/"
cp -r "$SOURCE_DIR/resources" "$INSTALL_DIR/"

# ──────────────────────────────────────────────
# 4. Create config
# ──────────────────────────────────────────────
echo -e "${GREEN}[4/6] Setting up configuration...${NC}"
if [ ! -f "$CONFIG_DIR/config.yml" ]; then
    cp "$SCRIPT_DIR/resources/default_config.yml" "$CONFIG_DIR/config.yml"
    echo "  Created: $CONFIG_DIR/config.yml"
else
    echo "  Config already exists, skipping"
fi

# ──────────────────────────────────────────────
# 5. Create launcher + helper
# ──────────────────────────────────────────────
echo -e "${GREEN}[5/6] Creating launcher...${NC}"

# Launcher script
cat > "$BIN_DIR/mirza" << 'LAUNCHER'
#!/bin/bash
INSTALL_DIR="$HOME/.local/share/mirza"
cd "$INSTALL_DIR"

# Setup virtual env on first run
if [ ! -d "venv" ]; then
    python3 -m venv venv --system-site-packages
    source venv/bin/activate
    pip install -q pyyaml
fi

source venv/bin/activate 2>/dev/null

# If running from repo, use that path
if [ -d "$HOME/Projects/mirza/src" ]; then
    cd "$HOME/Projects/mirza"
fi

python3 -m src.main "$@" &
LAUNCHER
chmod +x "$BIN_DIR/mirza"

# System symlink
sudo ln -sf "$BIN_DIR/mirza" /usr/local/bin/mirza 2>/dev/null || true

# Polkit helper
sudo tee /usr/local/bin/mirza-helper > /dev/null << 'HELPER'
#!/usr/bin/env python3
import sys
if len(sys.argv) == 4 and sys.argv[1] == "write-sysfs":
    try:
        with open(sys.argv[2], "w") as f:
            f.write(sys.argv[3])
        sys.exit(0)
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)
HELPER
sudo chmod +x /usr/local/bin/mirza-helper

# ──────────────────────────────────────────────
# 6. Systemd service
# ──────────────────────────────────────────────
echo -e "${GREEN}[6/6] Creating systemd service...${NC}"

cat > "$SYSTEMD_DIR/mirza.service" << 'SERVICE'
[Unit]
Description=Mîrza - Intelligent System Assistant
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
ExecStart=%h/.local/bin/mirza
Restart=on-failure
RestartSec=10

[Install]
WantedBy=graphical-session.target
SERVICE

systemctl --user daemon-reload
systemctl --user enable mirza.service 2>/dev/null || true

# ──────────────────────────────────────────────
# Done!
# ──────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Mîrza installed successfully!          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Start now:    ${BLUE}mirza${NC}"
echo -e "  Or service:   ${BLUE}systemctl --user start mirza${NC}"
echo -e "  Settings:     ${BLUE}$CONFIG_DIR/config.yml${NC}"
echo -e "  Logs:         ${BLUE}$INSTALL_DIR/mirza.log${NC}"
echo ""
echo -e "  CLI commands:"
echo -e "    ${BLUE}mirza status${NC}          System overview"
echo -e "    ${BLUE}mirza remind \"text\"${NC}   Add reminder"
echo -e "    ${BLUE}mirza list${NC}            List reminders"
echo -e "    ${BLUE}mirza --ui${NC}            Terminal dashboard"
echo -e "    ${BLUE}mirza --log 20${NC}        Recent logs"
echo ""
