# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
from plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)

class MonitorProfile(BasePlugin):
    """Detects external monitor connection and switches mode."""
    
    def __init__(self, mirza=None):
        super().__init__(mirza=mirza)
        self._external_connected = False

    def activate(self):
        super().activate()
        logger.info("MonitorProfile active")

    def on_device_event(self, event):
        if event.subsystem == "drm" and event.action == "change":
            logger.info("Display configuration changed")
            if self.mirza and hasattr(self.mirza, 'mode_engine'):
                # Switch to Sport when external monitor connected (presentation mode)
                if not self._external_connected:
                    self._external_connected = True
                    from src.core.mode_engine import SystemMode
                    self.mirza.mode_engine.force_mode(SystemMode.SPORT)
        return False

    def deactivate(self):
        super().deactivate()
