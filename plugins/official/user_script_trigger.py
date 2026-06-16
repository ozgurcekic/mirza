# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import os, subprocess, logging
from plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)

class UserScriptTrigger(BasePlugin):
    """Runs user-defined scripts when specific apps open/close."""
    
    def __init__(self, mirza=None):
        super().__init__(mirza=mirza)
        self._scripts_dir = os.path.expanduser("~/.config/mirza/scripts")
        self._last_app = None

    def activate(self):
        super().activate()
        os.makedirs(self._scripts_dir, exist_ok=True)
        logger.info("UserScriptTrigger active (scripts: %s)", self._scripts_dir)

    def on_focus_change(self, event):
        if not event.process_name or event.process_name == self._last_app:
            return False
        
        old_app = self._last_app
        self._last_app = event.process_name

        # Run close script for old app
        if old_app:
            self._run_script(f"{old_app}.close.sh")
        
        # Run open script for new app
        self._run_script(f"{event.process_name}.open.sh")
        return False

    def _run_script(self, script_name):
        script_path = os.path.join(self._scripts_dir, script_name)
        if os.path.isfile(script_path) and os.access(script_path, os.X_OK):
            try:
                subprocess.Popen([script_path], start_new_session=True)
                logger.info("Script triggered: %s", script_name)
            except Exception as e:
                logger.error("Script failed: %s", e)

    def deactivate(self):
        self._last_app = None
        super().deactivate()
