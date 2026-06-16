# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import logging
import subprocess

logger = logging.getLogger(__name__)


class DeviceProfiler:
    """Detects device type, OS, and desktop environment."""

    def __init__(self):
        self.device_type = "unknown"
        self.os_name = "unknown"
        self.os_version = "unknown"
        self.desktop = "unknown"
        self.session_type = "unknown"
        self.compositor = "unknown"
        self.cpu_count = 0
        self.ram_total_gb = 0

        self._detect()
        logger.info("Device: %s | OS: %s %s | Desktop: %s | Session: %s",
                    self.device_type, self.os_name, self.os_version,
                    self.desktop, self.session_type)

    def _detect(self):
        """Run all detection methods."""
        self._detect_os()
        self._detect_desktop()
        self._detect_device_type()
        self._detect_hardware()

    def _detect_os(self):
        """Detect OS from /etc/os-release."""
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("ID="):
                        self.os_name = line.split("=")[1].strip().strip('"')
                    elif line.startswith("VERSION_ID="):
                        self.os_version = line.split("=")[1].strip().strip('"')
        except Exception:
            pass

    def _detect_desktop(self):
        """Detect desktop environment and session type."""
        self.desktop = os.environ.get("XDG_CURRENT_DESKTOP", "unknown").lower()
        self.session_type = os.environ.get("XDG_SESSION_TYPE", "unknown").lower()

        # Detect compositor
        try:
            result = subprocess.run(["ps", "-e"], capture_output=True, text=True)
            if "gamescope" in result.stdout:
                self.compositor = "gamescope"
            elif "sway" in result.stdout:
                self.compositor = "wlroots-sway"
            elif "hyprland" in result.stdout:
                self.compositor = "wlroots-hyprland"
            else:
                self.compositor = self.session_type
        except Exception:
            self.compositor = self.session_type

    def _detect_device_type(self):
        """Detect if desktop, laptop, or handheld."""
        # Check for battery = laptop/handheld
        battery_paths = [
            "/sys/class/power_supply/BAT0",
            "/sys/class/power_supply/BAT1",
        ]
        has_battery = any(os.path.exists(p) for p in battery_paths)

        # Check for Steam Deck
        try:
            with open("/sys/class/dmi/id/product_name", "r") as f:
                product = f.read().strip().lower()
                if any(x in product for x in ["steam deck", "rog ally", "legion go", "gpd"]):
                    self.device_type = "handheld"
                    return
        except Exception:
            pass

        if has_battery:
            self.device_type = "laptop"
        else:
            self.device_type = "desktop"

    def _detect_hardware(self):
        """Detect CPU and RAM."""
        import psutil
        self.cpu_count = os.cpu_count() or 0
        self.ram_total_gb = psutil.virtual_memory().total / (1024 ** 3)

    def get_recommended_plugins(self) -> list:
        """Return list of recommended plugins based on device type."""
        plugins = []

        if self.device_type == "handheld":
            plugins.extend([
                "official.steamdeck_tdp",
                "official.steamdeck_fan",
                "official.gamescope_events",
                "official.battery_manager",
            ])
        elif self.device_type == "laptop":
            plugins.extend([
                "official.battery_manager",
                "official.thermal_guard",
            ])
        elif self.device_type == "desktop":
            plugins.extend([
                "official.monitor_profile",
            ])

        plugins.append("official.hardware_health")
        return plugins

    def to_dict(self) -> dict:
        """Return device info as dict."""
        return {
            "device_type": self.device_type,
            "os_name": self.os_name,
            "os_version": self.os_version,
            "desktop": self.desktop,
            "session_type": self.session_type,
            "compositor": self.compositor,
            "cpu_count": self.cpu_count,
            "ram_total_gb": round(self.ram_total_gb, 1),
        }
