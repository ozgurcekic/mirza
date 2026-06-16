# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import time
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class SystemMode(Enum):
    ECO = "eco"
    NORMAL = "normal"
    SPORT = "sport"


class ModeEngine:
    """Decides system mode based on activity and resource usage."""

    SPORT_APPS = {
        "steam", "blender", "kdenlive", "obs", "gimp",
        "inkscape", "godot", "unity", "handbrake", "krita"
    }

    def __init__(self, config: dict = None):
        self.config = config or {}
        self._current_mode = SystemMode.NORMAL
        self._last_change = 0.0
        self._cooldown = self.config.get("mode_change_cooldown_minutes", 2) * 60
        self._last_input_time = time.time()
        self._idle_threshold = 300
        self._cpu_high = 70.0
        self._cpu_low = 20.0
        self._ram_high = 90.0
        self._cpu_emergency = self.config.get("cpu_emergency_threshold", 90)
        self._ram_emergency = self.config.get("ram_emergency_threshold", 95)
        self._temp_emergency = self.config.get("temp_emergency_threshold", 90)

        # Load custom user modes
        self._custom_modes: dict[str, dict] = {}
        self._load_custom_modes()

        logger.info("ModeEngine initialized in %s mode", self._current_mode.value)

    def _load_custom_modes(self):
        """Load user-defined custom modes from config."""
        user_modes = self.config.get("user_modes", [])
        for mode_def in user_modes:
            name = mode_def.get("name", "").lower()
            if name and name not in ["eco", "normal", "sport"]:
                self._custom_modes[name] = mode_def.get("policies", {})
                logger.info("Custom mode loaded: %s", name)

    @property
    def current_mode(self) -> SystemMode:
        return self._current_mode

    @property
    def current_mode_name(self) -> str:
        """Return mode name including custom modes."""
        return self._current_mode.value

    @property
    def can_change(self) -> bool:
        return (time.time() - self._last_change) >= self._cooldown

    def get_custom_modes(self) -> list[str]:
        """Return list of custom mode names."""
        return list(self._custom_modes.keys())

    def get_custom_mode_policies(self, mode_name: str) -> dict:
        """Return policies for a custom mode."""
        return self._custom_modes.get(mode_name, {})

    def set_mode(self, mode, force=False):
        if not force and not self.can_change:
            return False
        old = self._current_mode
        self._current_mode = mode
        self._last_change = time.time()
        logger.info("Mode changed: %s -> %s", old.value, mode.value)
        return True

    def force_mode(self, mode, apply_policies=True):
        """Override with a user-selected mode."""
        return self.set_mode(mode, force=True)

    def user_input_detected(self):
        self._last_input_time = time.time()

    def _is_system_idle(self, snapshot):
        input_idle = (time.time() - self._last_input_time) > self._idle_threshold
        cpu_idle = snapshot.get("cpu_percent", 100) < self._cpu_low
        ram_ok = snapshot.get("ram_percent", 100) < self._ram_high
        return all([input_idle, cpu_idle, ram_ok])

    def _is_heavy_load(self, snapshot):
        return snapshot.get("cpu_percent", 0) > self._cpu_high

    def evaluate(self, active_app, snapshot):
        app_lower = active_app.lower() if active_app else ""

        # Emergency checks
        if snapshot.get("cpu_percent", 0) > self._cpu_emergency:
            return SystemMode.NORMAL
        if snapshot.get("ram_percent", 0) > self._ram_emergency:
            return SystemMode.NORMAL

        # Sport mode
        if any(sport in app_lower for sport in self.SPORT_APPS):
            return SystemMode.SPORT
        if self._is_heavy_load(snapshot):
            return SystemMode.SPORT

        # Eco mode
        if self._is_system_idle(snapshot):
            return SystemMode.ECO

        return SystemMode.NORMAL

    def get_mode_policies(self, mode=None):
        """Get policies for a mode (supports custom modes)."""
        if mode is None:
            mode = self._current_mode

        mode_key = mode.value if isinstance(mode, SystemMode) else str(mode)

        # Check custom modes first
        if mode_key in self._custom_modes:
            return self._custom_modes[mode_key]
        
        # Check user_modes list in config
        user_modes = self.config.get("user_modes", [])
        for m in user_modes:
            if m.get("name") == mode_key:
                return m.get("policies", {})

        # Standard modes
        return self.config.get(f"modes.{mode_key}", {})

    def add_custom_mode(self, name, policies):
        """Add a new custom mode at runtime."""
        name = name.lower()
        if name in ["eco", "normal", "sport"]:
            return False
        self._custom_modes[name] = policies
        return True

    def remove_custom_mode(self, name):
        """Remove a custom mode."""
        if name in self._custom_modes:
            del self._custom_modes[name]
            return True
        return False
