# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

logger = logging.getLogger(__name__)


class BasePlugin:
    """Base class for all Mîrza plugins.
    
    To create a plugin, inherit from this class and override
    any of the event methods. Place the file in plugins/user/
    and enable it in config.yml.
    
    Example:
        class MyPlugin(BasePlugin):
            def on_focus_change(self, event):
                if "chrome" in event.process_name.lower():
                    self.mirza.send_notification("Chrome opened!")
    """

    def __init__(self, mirza=None):
        self.mirza = mirza
        self.config = {}
        self._active = False

    @property
    def is_active(self):
        return self._active

    def activate(self):
        """Called once when the plugin is activated."""
        self._active = True
        logger.info("Plugin %s activated", self.__class__.__name__)

    def deactivate(self):
        """Called once when the plugin is deactivated."""
        self._active = False
        logger.info("Plugin %s deactivated", self.__class__.__name__)

    def on_focus_change(self, event):
        """Called when active window changes."""
        return False

    def on_device_event(self, event):
        """Called on udev hardware events."""
        return False

    def on_layout_change(self, event):
        """Called when window geometry/state changes."""
        return False

    def on_mode_change(self, old_mode, new_mode):
        """Called when system mode changes."""
        pass

    def on_system_snapshot(self, snapshot):
        """Called periodically with system resource data."""
        return False

    def on_idle_change(self, is_idle):
        """Called when system idle state changes."""
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__} active={self._active}>"
