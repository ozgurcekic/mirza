# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import logging
from collections import deque
from plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class ThermalGuard(BasePlugin):
    """Monitors system temperature and protects against overheating."""

    THERMAL_PATHS = [
        "/sys/class/thermal/thermal_zone0/temp",
        "/sys/class/thermal/thermal_zone1/temp",
        "/sys/class/hwmon/",
    ]

    def __init__(self, mirza=None):
        super().__init__(mirza=mirza)
        self._sensors = []
        self._temp_history = deque(maxlen=30)
        self._high_temp_count = 0
        self._was_emergency = False

    def activate(self):
        super().activate()
        self._find_sensors()
        logger.info("ThermalGuard active (found %d sensors)", len(self._sensors))

    def _find_sensors(self):
        """Discover available thermal sensors."""
        for path in self.THERMAL_PATHS:
            if os.path.exists(path):
                if path.endswith("temp"):
                    self._sensors.append(path)
                elif os.path.isdir(path):
                    for item in os.listdir(path):
                        if item.endswith("_input") and "temp" in item:
                            self._sensors.append(os.path.join(path, item))

    def _read_temp(self, sensor_path):
        """Read temperature from a sensor in millidegrees Celsius."""
        try:
            with open(sensor_path, "r") as f:
                return int(f.read().strip()) / 1000  # Convert to Celsius
        except Exception:
            return None

    def get_max_temp(self) -> float:
        """Get the highest temperature across all sensors."""
        max_temp = 0
        for sensor in self._sensors:
            temp = self._read_temp(sensor)
            if temp and temp > max_temp:
                max_temp = temp
        return max_temp

    def on_system_snapshot(self, snapshot):
        """Check temperature on each snapshot."""
        if not self._sensors or not self.mirza:
            return False

        current_temp = self.get_max_temp()
        if current_temp == 0:
            return False

        self._temp_history.append(current_temp)

        # Calculate trend (simple moving average)
        if len(self._temp_history) >= 5:
            avg = sum(list(self._temp_history)[-5:]) / 5

            # Emergency: > 90°C
            if avg > self.config.get("temp_emergency", 90):
                if not self._was_emergency:
                    logger.warning("Temperature emergency: %.1f°C", avg)
                    self.mirza.send_notification(
                        f"High Temperature ({avg:.0f}°C)",
                        "System is overheating. Switching to Eco mode for safety."
                    )
                    if hasattr(self.mirza, 'mode_engine'):
                        from src.core.mode_engine import SystemMode
                        self.mirza.mode_engine.force_mode(SystemMode.ECO)
                    self._was_emergency = True

            elif avg < self.config.get("temp_safe", 75):
                self._was_emergency = False

            # Warning: > 80°C
            if avg > self.config.get("temp_warning", 80) and not self._was_emergency:
                self._high_temp_count += 1
                if self._high_temp_count >= 5:
                    logger.warning("Temperature high: %.1f°C", avg)
                    self.mirza.send_notification(
                        f"Elevated Temperature ({avg:.0f}°C)",
                        "Consider reducing system load."
                    )
                    self._high_temp_count = 0

        return False
