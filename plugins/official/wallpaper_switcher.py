# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import subprocess, logging, os
from plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)

class WallpaperSwitcher(BasePlugin):
    """Changes wallpaper based on mode (GNOME/KDE/XFCE)."""
    
    WALLPAPERS = {
        "eco": "/usr/share/backgrounds/gnome/blobs-d.svg",
        "normal": "/usr/share/backgrounds/gnome/adwaita-day.jpg",
        "sport": "/usr/share/backgrounds/gnome/adwaita-night.jpg",
    }

    def on_mode_change(self, old_mode, new_mode):
        wp = self.WALLPAPERS.get(new_mode)
        if not wp or not os.path.exists(wp):
            logger.debug("Wallpaper not found: %s", wp)
            return
        
        # GNOME
        try:
            subprocess.run([
                "gsettings", "set", "org.gnome.desktop.background",
                "picture-uri-dark", f"file://{wp}"
            ], timeout=5)
            subprocess.run([
                "gsettings", "set", "org.gnome.desktop.background",
                "picture-uri", f"file://{wp}"
            ], timeout=5)
            logger.info("Wallpaper changed for %s mode: %s", new_mode, wp)
        except Exception as e:
            logger.debug("Wallpaper failed: %s", e)

    def activate(self):
        super().activate()
        logger.info("WallpaperSwitcher active")
