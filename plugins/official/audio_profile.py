# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import subprocess, logging
from plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)

class AudioProfile(BasePlugin):
    """Adjusts volume based on mode."""
    
    def on_mode_change(self, old_mode, new_mode):
        vol = self.config.get(f"modes.{new_mode}.volume_percent", 70) if self.config else 70
        try:
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{vol}%"], timeout=5)
            logger.info("Volume set to %d%% for %s mode", vol, new_mode)
        except Exception as e:
            logger.debug("Volume failed: %s", e)

    def activate(self):
        super().activate()
        logger.info("AudioProfile active")
