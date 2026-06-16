# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import time
import logging
from collections import defaultdict
from plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class MailOptimizer(BasePlugin):
    """Learns mail checking habits and optimizes mail client lifecycle.
    
    Instead of keeping the mail client open 24/7, this plugin:
    - Learns when the user checks mail (e.g., 09:15, 14:00, 17:45)
    - Opens the mail client 2 minutes before expected check time
    - Closes it after 10 minutes of inactivity
    - Saves RAM and CPU by not running mail client when not needed
    """

    # Known mail clients
    MAIL_CLIENTS = {
        "thunderbird", "evolution", "geary", "kmail", "mailspring",
        "betterbird", "claws-mail", "sylpheed",
    }

    def __init__(self, mirza=None):
        super().__init__(mirza=mirza)
        self._check_times: dict[int, int] = defaultdict(int)  # hour -> count
        self._mail_client_name = None
        self._mail_client_pid = None
        self._last_mail_open = 0
        self._last_mail_close = 0
        self._is_managed = False
        self._min_occurrences = 3  # Min observations before suggesting
        self._open_before_minutes = 2  # Open 2 min before expected time
        self._close_after_idle_minutes = 10  # Close after 10 min idle

    def activate(self):
        super().activate()
        self._load_history()
        logger.info("MailOptimizer active (observations: %d)", 
                    sum(self._check_times.values()))

    def _load_history(self):
        """Load mail check history from database."""
        if not self.mirza or not hasattr(self.mirza, 'db'):
            return

        try:
            rows = self.mirza.db.fetch_all(
                """SELECT process_name, datetime(timestamp, 'unixepoch', 'localtime') as dt
                   FROM focus_events
                   WHERE process_name IN ({})
                   ORDER BY timestamp DESC
                   LIMIT 500""".format(','.join('?' * len(self.MAIL_CLIENTS))),
                tuple(self.MAIL_CLIENTS)
            )
            for proc_name, dt in rows:
                hour = int(dt.split()[1].split(':')[0])
                self._check_times[hour] += 1
                if not self._mail_client_name:
                    self._mail_client_name = proc_name
        except Exception as e:
            logger.debug("History load failed: %s", e)

    def on_focus_change(self, event):
        """Track when user opens mail client."""
        if not event.process_name:
            return False

        name_lower = event.process_name.lower()
        
        # Check if it's a mail client
        for client in self.MAIL_CLIENTS:
            if client in name_lower:
                now = time.time()
                hour = time.localtime(now).tm_hour
                
                self._check_times[hour] += 1
                self._mail_client_name = event.process_name
                self._last_mail_open = now
                
                logger.info("Mail check detected: %s at %02d:00", 
                           event.process_name, hour)
                
                # Save to DB
                if self.mirza and hasattr(self.mirza, 'db'):
                    try:
                        self.mirza.db.execute(
                            "INSERT INTO focus_events (timestamp, process_name, window_title) VALUES (?, ?, ?)",
                            (now, event.process_name, "mail_check")
                        )
                    except Exception:
                        pass
                
                return True

        return False

    def on_system_snapshot(self, snapshot):
        """Check if mail client should be opened or closed."""
        if not self._mail_client_name:
            return False

        now = time.time()
        current_hour = time.localtime(now).tm_hour
        current_minute = time.localtime(now).tm_min

        # Check if we should open mail client (2 min before expected time)
        predicted_times = self._get_predicted_times()
        for predicted_hour in predicted_times:
            if (current_hour == predicted_hour and 
                current_minute >= (60 - self._open_before_minutes) and
                not self._is_mail_running()):
                
                self._open_mail_client()
                self._is_managed = True
                logger.info("Auto-opened mail client at %02d:%02d", 
                           current_hour, current_minute)
                return True

        # Check if we should close mail client (idle for too long)
        if self._is_managed and self._is_mail_running():
            idle_time = now - self._last_mail_open
            if idle_time > self._close_after_idle_minutes * 60:
                self._close_mail_client()
                self._is_managed = False
                logger.info("Auto-closed mail client after %d min idle", 
                           int(idle_time / 60))

        return False

    def _get_predicted_times(self) -> list[int]:
        """Return list of hours where user usually checks mail."""
        if not self._check_times:
            return []

        max_count = max(self._check_times.values())
        if max_count < self._min_occurrences:
            return []

        threshold = max_count * 0.5
        return sorted([
            hour for hour, count in self._check_times.items()
            if count >= threshold
        ])

    def _is_mail_running(self):
        """Check if mail client is currently running."""
        import psutil
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name'] or ''
                if self._mail_client_name and self._mail_client_name.lower() in name.lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False

    def _open_mail_client(self):
        """Open the mail client."""
        try:
            import subprocess
            subprocess.Popen(
                ["gtk-launch", self._mail_client_name] if self._mail_client_name 
                else ["thunderbird"],
                start_new_session=True
            )
            self._last_mail_open = time.time()
        except Exception as e:
            logger.error("Failed to open mail client: %s", e)

    def _close_mail_client(self):
        """Close the mail client gracefully."""
        try:
            import subprocess
            subprocess.run(
                ["pkill", "-f", self._mail_client_name],
                timeout=5
            )
            self._last_mail_close = time.time()
        except Exception as e:
            logger.error("Failed to close mail client: %s", e)

    def get_stats(self) -> dict:
        """Return optimization statistics."""
        return {
            "mail_client": self._mail_client_name or "unknown",
            "predicted_times": [f"{h:02d}:00" for h in self._get_predicted_times()],
            "total_observations": sum(self._check_times.values()),
            "is_managed": self._is_managed,
        }

    def deactivate(self):
        super().deactivate()
        logger.info("MailOptimizer deactivated (stats: %s)", self.get_stats())
