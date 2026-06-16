# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import time
import logging
from plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class BatteryManager(BasePlugin):
    """Monitors battery status and auto-switches to Eco mode when low."""

    BATTERY_PATHS = [
        "/sys/class/power_supply/BAT0",
        "/sys/class/power_supply/BAT1",
    ]

    def __init__(self, mirza=None):
        super().__init__(mirza=mirza)
        self._battery_path = self._find_battery()
        self._last_notification = 0
        self._notification_cooldown = 300  # 5 minutes
        self._was_critical = False

    def activate(self):
        super().activate()
        if not self._battery_path:
            logger.warning("No battery found, deactivating")
            self.deactivate()
        else:
            logger.info("BatteryManager active (path: %s)", self._battery_path)

    def _find_battery(self):
        """Find the battery sysfs path."""
        for path in self.BATTERY_PATHS:
            if os.path.exists(path):
                return path
        return None

    def _read_sysfs(self, filename):
        """Read a value from the battery sysfs directory."""
        if not self._battery_path:
            return None
        try:
            with open(os.path.join(self._battery_path, filename), "r") as f:
                return f.read().strip()
        except Exception:
            return None

    def get_capacity(self) -> int:
        """Get battery capacity (0-100)."""
        val = self._read_sysfs("capacity")
        return int(val) if val else 100

    def get_status(self) -> str:
        """Get battery status (Charging/Discharging/Full)."""
        val = self._read_sysfs("status")
        return val or "Unknown"

    def get_health(self) -> str:
        """Get battery health."""
        capacity = self.get_capacity()
        if capacity > 80:
            return "Good"
        elif capacity > 50:
            return "Fair"
        return "Weak"

    def get_remaining_time_estimate(self) -> str:
        """Estimate remaining battery time."""
        try:
            energy_now = self._read_sysfs("energy_now")
            power_now = self._read_sysfs("power_now")
            if energy_now and power_now and int(power_now) > 0:
                hours = int(energy_now) / int(power_now)
                if hours > 1:
                    return f"~{int(hours)}h {int((hours % 1) * 60)}m"
                return f"~{int(hours * 60)}m"
        except Exception:
            pass
        return "Unknown"

    def on_system_snapshot(self, snapshot):
        """Check battery on each system snapshot."""
        if not self._battery_path or not self.mirza:
            return False

        capacity = self.get_capacity()
        status = self.get_status()
        now = time.time()

        # Force Eco mode on critical battery
        if status == "Discharging" and capacity <= self.config.get("battery_critical_threshold", 10):
            if not self._was_critical:
                logger.warning("Battery critical: %d%%", capacity)
                remaining = self.get_remaining_time_estimate()
                self.mirza.send_notification(
                    f"Battery Critical ({capacity}%)",
                    f"Remaining: {remaining}. Switching to Eco mode."
                )
                # Force Eco mode
                if hasattr(self.mirza, 'mode_engine'):
                    from src.core.mode_engine import SystemMode
                    self.mirza.mode_engine.force_mode(SystemMode.ECO)
                self._was_critical = True

        elif capacity > self.config.get("battery_critical_threshold", 10) + 5:
            self._was_critical = False

        # Suggest Eco mode at 20%
        if (status == "Discharging" and capacity <= self.config.get("battery_low_threshold", 20) 
            and now - self._last_notification > self._notification_cooldown):
            remaining = self.get_remaining_time_estimate()
            self.mirza.send_notification(
                f"Battery Low ({capacity}%)",
                f"Remaining: {remaining}. Consider switching to Eco mode."
            )
            self._last_notification = now

        return False
