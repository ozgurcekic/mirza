# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import os, logging
from plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)

class FPSLimiter(BasePlugin):
    """Suggests FPS limits per mode. Requires MangoHud for actual limiting."""
    
    FPS_LIMITS = {"eco": 30, "normal": 60, "sport": 0}  # 0 = unlimited

    def on_mode_change(self, old_mode, new_mode):
        fps = self.FPS_LIMITS.get(new_mode, 60)
        config_path = os.path.expanduser("~/.config/MangoHud/MangoHud.conf")
        
        if os.path.exists(os.path.dirname(config_path)):
            try:
                with open(config_path, "w") as f:
                    f.write(f"fps_limit={fps}\n" if fps > 0 else "fps_limit=0\n")
                logger.info("FPS limit set to %s for %s mode", fps or "unlimited", new_mode)
            except Exception as e:
                logger.debug("FPS limit failed: %s", e)
        else:
            self.mirza.send_notification(
                "Mîrza FPS Limiter",
                "Install MangoHud for FPS limiting: sudo apt install mangohud"
            )

    def activate(self):
        super().activate()
        logger.info("FPSLimiter active")
