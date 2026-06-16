# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import time
import logging
from dataclasses import dataclass
from typing import Optional, Callable

import psutil

logger = logging.getLogger(__name__)


@dataclass
class FocusEvent:
    timestamp: float
    process_name: str
    window_title: str
    window_id: int
    workspace: int = 0
    geometry: tuple = (0, 0, 0, 0)


@dataclass
class DeviceEvent:
    timestamp: float
    subsystem: str
    action: str
    device_path: str


class EventEngine:
    """Collects system events for Mîrza."""

    # System processes to exclude
    SYSTEM_PROCESSES = {
        'gnome-shell', 'gnome-session', 'gsd-', 'gjs', 'ibus-',
        'pipewire', 'pulseaudio', 'wireplumber', 'dbus-', 'systemd',
        'polkit', 'upower', 'udisks', 'rtkit', 'switcheroo',
        'xdg-', 'evolution-source', 'evolution-alarm',
        'gnome-keyring', 'goa-', 'tracker-', 'snapd', 'python3', 'ptyxis-agent',
    }

    # Known GUI applications to always include
    GUI_APPS = {
        'firefox', 'firefox-bin', 'chrome', 'chromium', 'brave', 'edge',
        'nautilus', 'gnome-terminal', 'kgx', 'ptyxis', 'console', 'konsole',
        'alacritty', 'kitty', 'terminator', 'ptyxis', 'tilix', 'xfce4-terminal',
        'gedit', 'gnome-text-editor', 'kate', 'mousepad',
        'gnome-control-center', 'gnome-software', 'snap-store',
        'code', 'code-oss', 'thunderbird', 'evolution',
        'gimp', 'inkscape', 'blender', 'vlc', 'eog', 'evince',
    }

    def __init__(self, database=None):
        self.db = database
        self._listeners: list[Callable] = []
        self._last_process: str = ""
        self._process_stability_count: int = 0
        self._stability_threshold: int = 2  # Reduced for faster response
        self._own_pid = os.getpid()

        self._session_type = os.environ.get("XDG_SESSION_TYPE", "x11").lower()
        self._desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()

        # udev monitor
        self._udev_monitor = None
        try:
            import pyudev
            self._udev_context = pyudev.Context()
            self._udev_monitor = pyudev.Monitor.from_netlink(self._udev_context)
            self._udev_monitor.filter_by(subsystem='drm')
            self._udev_monitor.filter_by(subsystem='sound')
            self._udev_monitor.filter_by(subsystem='input')
            self._udev_monitor.filter_by(subsystem='usb')
            self._udev_monitor.start()
            logger.info("udev monitor initialized")
        except Exception as e:
            logger.warning("udev not available: %s", e)

        logger.info("EventEngine initialized (session: %s, desktop: %s)",
                    self._session_type, self._desktop)

    def add_listener(self, callback: Callable):
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _is_system_process(self, name: str) -> bool:
        """Check if process is a system/background process."""
        name_lower = name.lower()
        for sys_p in self.SYSTEM_PROCESSES:
            if sys_p in name_lower:
                return True
        return False

    def _is_known_gui(self, name: str) -> bool:
        """Check if process name matches known GUI applications."""
        name_lower = name.lower()
        for gui in self.GUI_APPS:
            if gui in name_lower:
                return True
        return False

    def get_current_focus(self) -> Optional[FocusEvent]:
        """Get currently focused application."""
        
        candidates = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                pid = proc.info['pid']
                name = proc.info['name'] or ""

                # Skip our own process
                if pid == self._own_pid:
                    continue

                # Skip system processes
                if self._is_system_process(name):
                    continue

                # Must be a known GUI app
                if not self._is_known_gui(name):
                    continue

                cpu = proc.info['cpu_percent'] or 0
                candidates.append((cpu, name))

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if not candidates:
            return None

        # Sort by CPU usage (most active first)
        candidates.sort(reverse=True)
        process_name = candidates[0][1]

        # Stability check
        if process_name == self._last_process:
            self._process_stability_count += 1
        else:
            self._last_process = process_name
            self._process_stability_count = 1

        if self._process_stability_count < self._stability_threshold:
            return None

        # Geometry: GNOME Wayland doesn't expose real coordinates
        # Use placeholder values; layout tracking works on X11
        geometry = (0, 0, 0, 0)

        return FocusEvent(
            timestamp=time.time(),
            process_name=process_name,
            window_title=process_name,
            window_id=hash(process_name) % 1000000,
            geometry=geometry,
        )

    def poll_udev_events(self):
        """Check for pending udev events."""
        events = []
        if not self._udev_monitor:
            return events

        try:
            import select
            fd = self._udev_monitor.fileno()
            while select.select([fd], [], [], 0)[0]:
                device = self._udev_monitor.poll(timeout=0)
                if device:
                    events.append(DeviceEvent(
                        timestamp=time.time(),
                        subsystem=device.subsystem,
                        action=device.action,
                        device_path=device.device_path
                    ))
        except Exception as e:
            logger.debug("udev poll error: %s", e)

        return events

    def get_system_snapshot(self) -> dict:
        """Collect current system resource usage."""
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory().percent
        except Exception:
            cpu, ram = 0.0, 0.0

        return {
            "timestamp": time.time(),
            "cpu_percent": cpu,
            "ram_percent": ram,
            "disk_mb_total": 0,
            "net_mb_total": 0
        }

    def stop(self):
        """Clean shutdown."""
        logger.info("EventEngine stopped")
