# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
from collections import defaultdict
from plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)

class ShortcutSuggester(BasePlugin):
    """Detects repeated window switches and suggests shortcuts."""
    
    def __init__(self, mirza=None):
        super().__init__(mirza=mirza)
        self._transitions = defaultdict(int)
        self._threshold = 50

    def activate(self):
        super().activate()
        logger.info("ShortcutSuggester active")

    def on_focus_change(self, event):
        if not event.process_name:
            return False
        
        # Count transitions between the same two apps
        current = event.process_name
        if hasattr(self, '_last'):
            pair = tuple(sorted([self._last, current]))
            self._transitions[pair] += 1
            if self._transitions[pair] == self._threshold:
                self.mirza.send_notification(
                    "Shortcut Suggestion",
                    f"You frequently switch between {pair[0]} and {pair[1]}. Consider binding a shortcut!"
                )
        self._last = current
        return False

    def deactivate(self):
        super().deactivate()
