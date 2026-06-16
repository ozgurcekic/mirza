# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import logging
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, GLib, AppIndicator3

logger = logging.getLogger(__name__)

from src.ui.settings_window import SettingsWindow


class TrayIcon:
    """System tray icon with mode-colored indicator and menu."""

    # Path to icon files
    ICON_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "resources", "icons"
    )

    MODE_ICONS = {
        "eco": os.path.join(ICON_DIR, "mode_eco.png"),
        "normal": os.path.join(ICON_DIR, "mode_normal.png"),
        "sport": os.path.join(ICON_DIR, "mode_sport.png"),
    }

    MODE_COLORS = {
        "eco": "#33cc55",
        "normal": "#3388ee",
        "sport": "#ee3333",
    }

    def __init__(self, mirza_daemon=None):
        self.mirza = mirza_daemon
        self._current_mode = "normal"

        # Use custom icon if exists, fallback to system icon
        icon_path = self.MODE_ICONS.get("normal", "emblem-system")
        if os.path.exists(icon_path):
            self.indicator = AppIndicator3.Indicator.new(
                "mirza", icon_path, AppIndicator3.IndicatorCategory.APPLICATION_STATUS
            )
        else:
            self.indicator = AppIndicator3.Indicator.new(
                "mirza", "emblem-system", AppIndicator3.IndicatorCategory.APPLICATION_STATUS
            )

        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self._build_menu()
        logger.info("TrayIcon initialized")

    def _build_menu(self):
        """Build the tray menu."""
        menu = Gtk.Menu()

        # Mode indicator with color emoji
        color_dot = {"eco": "🟢", "normal": "🔵", "sport": "🔴"}
        dot = color_dot.get(self._current_mode, "⚪")
        mode_label = f"{dot}  Mode: {self._current_mode.upper()}"
        mode_item = Gtk.MenuItem(label=mode_label)
        mode_item.set_sensitive(False)
        menu.append(mode_item)
        menu.append(Gtk.SeparatorMenuItem())

        # Mode selection with checkmarks
        modes = [
            ("eco", "🟢  Eco"),
            ("normal", "🔵  Normal"),
            ("sport", "🔴  Sport"),
        ]
        for mode_name, mode_label in modes:
            prefix = "✓ " if mode_name == self._current_mode else "    "
            item = Gtk.MenuItem(label=f"{prefix}{mode_label}")
            item.connect("activate", self._on_mode_selected, mode_name)
            menu.append(item)

        # Custom modes
        custom_modes = self._get_custom_modes()
        if custom_modes:
            menu.append(Gtk.SeparatorMenuItem())
            for mode_name, mode_label in custom_modes:
                prefix = "✓ " if mode_name == self._current_mode else "    "
                item = Gtk.MenuItem(label=f"{prefix}⭐  {mode_label}")
                item.connect("activate", self._on_mode_selected, mode_name)
                menu.append(item)

        menu.append(Gtk.SeparatorMenuItem())

        # Settings
        settings_item = Gtk.MenuItem(label="⚙  Settings")
        settings_item.connect("activate", self._on_settings)
        menu.append(settings_item)

        # Quit
        quit_item = Gtk.MenuItem(label="✕  Quit")
        quit_item.connect("activate", self._on_quit)
        menu.append(quit_item)

        menu.show_all()
        self.indicator.set_menu(menu)

    def _on_mode_selected(self, widget, mode_name):
        """Handle mode selection from menu."""
        logger.info("User selected mode: %s", mode_name)
        if self.mirza and hasattr(self.mirza, 'mode_engine'):
            from src.core.mode_engine import SystemMode
            # Standard modes
            mode_map = {
                "eco": SystemMode.ECO,
                "normal": SystemMode.NORMAL,
                "sport": SystemMode.SPORT,
            }
            
            if mode_name in mode_map:
                if self.mirza.mode_engine.force_mode(mode_map[mode_name]):
                    self.mirza.mode_engine._current_mode_name = mode_name
                    self.mirza.resource_manager.apply_mode_policy(mode_name)
            else:
                # Custom mode: just apply policies and update UI
                self.mirza.mode_engine._current_mode_name = mode_name
                self.mirza.resource_manager.apply_mode_policy(mode_name)
            self.set_mode(mode_name)

    def _on_settings(self, widget):
        """Open settings window."""
        logger.info("Opening settings window")
        if self.mirza and hasattr(self.mirza, "config"):
            win = SettingsWindow(config_manager=self.mirza.config, mirza_daemon=self.mirza)
            win.show_all()

    def _get_custom_modes(self):
        """Get list of custom user modes from config."""
        if not self.mirza or not hasattr(self.mirza, 'config'):
            return []
        user_modes = self.mirza.config.get("user_modes", [])
        return [(m.get("name", ""), m.get("name", "").title()) for m in user_modes if m.get("name")]

    def _on_quit(self, widget):
        """Quit the application."""
        logger.info("Quit requested")
        if self.mirza:
            self.mirza.stop()

    def set_mode(self, mode_name: str):
        """Update the tray icon and menu for the given mode."""
        if mode_name == self._current_mode:
            return

        self._current_mode = mode_name
        logger.info("Tray mode updated to: %s", mode_name)

        # Update icon (custom modes use normal icon with a star emoji in menu)
        icon_path = self.MODE_ICONS.get(mode_name)
        if icon_path and os.path.exists(icon_path):
            self.indicator.set_icon_full(icon_path, f"mîrza-{mode_name}")
        elif mode_name not in ["eco", "normal", "sport"]:
            # Custom mode: use normal icon
            icon_path = self.MODE_ICONS.get("normal")
            if icon_path and os.path.exists(icon_path):
                self.indicator.set_icon_full(icon_path, f"mîrza-custom")

        # Rebuild menu
        self._build_menu()

    def stop(self):
        """Stop the tray icon."""
        logger.info("Stopping tray icon")
