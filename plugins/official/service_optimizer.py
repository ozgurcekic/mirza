# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import subprocess
import logging
from plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class ServiceOptimizer(BasePlugin):
    """Detects and stops unused background services."""

    # Services safe to stop when not in use
    OPTIMIZABLE_SERVICES = [
        "tracker-miner-fs-3.service",
        "tracker-extract-3.service",
        "packagekit.service",
        "cups-browsed.service",
        "bluetooth.service",
    ]

    # Services that should NEVER be stopped
    NEVER_STOP = [
        "dbus", "systemd", "polkit", "pipewire", "pulseaudio",
        "gnome-shell", "gdm", "sddm", "NetworkManager",
    ]

    def __init__(self, mirza=None):
        super().__init__(mirza=mirza)
        self._stopped_services = []
        self._cooldown = 0

    def activate(self):
        super().activate()
        logger.info("ServiceOptimizer active")

    def _stop_service(self, service_name):
        """Stop a systemd user service."""
        try:
            result = subprocess.run(
                ["systemctl", "--user", "stop", service_name],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                self._stopped_services.append(service_name)
                logger.info("Stopped service: %s", service_name)
                return True
        except Exception as e:
            logger.debug("Failed to stop %s: %s", service_name, e)
        return False

    def _start_service(self, service_name):
        """Restart a stopped service."""
        try:
            subprocess.run(
                ["systemctl", "--user", "start", service_name],
                capture_output=True, text=True, timeout=10
            )
            if service_name in self._stopped_services:
                self._stopped_services.remove(service_name)
            logger.info("Restarted service: %s", service_name)
        except Exception:
            pass

    def _is_service_running(self, service_name):
        """Check if a service is currently active."""
        try:
            result = subprocess.run(
                ["systemctl", "--user", "is-active", service_name],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() == "active"
        except Exception:
            return False

    def on_mode_change(self, old_mode, new_mode):
        """Stop services in Eco mode, restore in Normal/Sport."""
        if new_mode == "eco":
            for service in self.OPTIMIZABLE_SERVICES:
                if self._is_service_running(service):
                    self._stop_service(service)
        elif old_mode == "eco":
            for service in self._stopped_services[:]:
                self._start_service(service)

    def on_system_snapshot(self, snapshot):
        """Periodic check for optimization opportunities."""
        self._cooldown += 1
        if self._cooldown < 30:  # Check every 30 snapshots (~5 min)
            return False

        self._cooldown = 0

        # Check for services that were restarted manually
        for service in self._stopped_services[:]:
            if self._is_service_running(service):
                self._stopped_services.remove(service)

        return False

    def deactivate(self):
        """Restore all stopped services on deactivation."""
        for service in self._stopped_services[:]:
            self._start_service(service)
        super().deactivate()
