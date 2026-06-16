# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import subprocess
import logging
import psutil
from datetime import datetime
from plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class HardwareHealth(BasePlugin):
    """Periodic hardware health checks: disk SMART, RAM anomalies."""

    def __init__(self, mirza=None):
        super().__init__(mirza=mirza)
        self._last_check = None
        self._check_interval_hours = 24
        self._ram_baseline = None

    def activate(self):
        super().activate()
        # Establish RAM baseline
        self._ram_baseline = psutil.virtual_memory().percent
        logger.info("HardwareHealth active (RAM baseline: %.1f%%)", self._ram_baseline)

    def _check_disk_health(self):
        """Check disk health using smartctl."""
        try:
            result = subprocess.run(
                ["smartctl", "-H", "/dev/sda"],
                capture_output=True, text=True, timeout=30
            )
            if "PASSED" in result.stdout:
                return {"status": "OK", "detail": "SMART status: PASSED"}
            elif "FAILED" in result.stdout:
                return {"status": "FAIL", "detail": "SMART status: FAILED - Backup recommended!"}
            return {"status": "UNKNOWN", "detail": "smartctl not available"}
        except FileNotFoundError:
            return {"status": "SKIP", "detail": "smartctl not installed"}
        except Exception as e:
            return {"status": "ERROR", "detail": str(e)}

    def _check_ram_anomaly(self):
        """Check for abnormal RAM usage."""
        current = psutil.virtual_memory().percent
        if self._ram_baseline and current > self._ram_baseline + 30:
            return {
                "anomaly": True,
                "current": current,
                "baseline": self._ram_baseline,
                "detail": f"RAM usage is unusually high ({current:.1f}% vs baseline {self._ram_baseline:.1f}%)"
            }
        return {"anomaly": False, "current": current}

    def on_system_snapshot(self, snapshot):
        """Run periodic health checks."""
        now = datetime.now()

        if self._last_check:
            hours_since = (now - self._last_check).total_seconds() / 3600
            if hours_since < self._check_interval_hours:
                return False

        self._last_check = now
        logger.info("Running hardware health checks...")

        # Disk check
        disk = self._check_disk_health()
        if disk["status"] in ["FAIL", "ERROR"]:
            self.mirza.send_notification(
                "Disk Health Warning",
                disk["detail"]
            )

        # RAM check
        ram = self._check_ram_anomaly()
        if ram["anomaly"]:
            self.mirza.send_notification(
                "RAM Anomaly Detected",
                ram["detail"]
            )

        # Log summary
        logger.info("Health check: Disk=%s, RAM=%.1f%%", disk["status"], ram["current"])

        return False

    def deactivate(self):
        super().deactivate()
        logger.info("HardwareHealth deactivated")
