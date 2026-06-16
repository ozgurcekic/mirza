#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import os, sys, gc, time, signal, logging, logging.handlers, importlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, GLib

from src.storage.config_manager import ConfigManager
from src.storage.database import Database
from src.core.event_engine import EventEngine
from src.core.prediction_engine import PredictionEngine
from src.core.mode_engine import ModeEngine, SystemMode
from src.core.resource_manager import ResourceManager
from src.core.device_profiler import DeviceProfiler
from src.ui.tray_icon import TrayIcon
from plugins.base_plugin import BasePlugin

LOG_DIR = os.path.expanduser("~/.local/share/mirza")
LOG_FILE = os.path.join(LOG_DIR, "mirza.log")
ERROR_LOG = os.path.join(LOG_DIR, "error.log")


def setup_logging(config):
    os.makedirs(LOG_DIR, exist_ok=True)
    level = getattr(logging, config.get("logging.level", "INFO"), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    fh = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=3)
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
    root_logger.addHandler(fh)

    eh = logging.handlers.RotatingFileHandler(ERROR_LOG, maxBytes=10*1024*1024, backupCount=3)
    eh.setLevel(logging.WARNING)
    eh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
    root_logger.addHandler(eh)

    if config.get("logging.terminal_output", False) or "--verbose" in sys.argv:
        console = logging.StreamHandler(sys.stderr)
        console.setLevel(logging.DEBUG)
        console.setFormatter(logging.Formatter('[%(levelname)s] %(name)s: %(message)s'))
        root_logger.addHandler(console)

    return root_logger


class MirzaDaemon:
    def __init__(self):
        gc.disable()
        self.config = ConfigManager()
        self.logger = setup_logging(self.config)
        self.logger.info("Mîrza daemon starting...")

        self.db = Database()
        self.events = EventEngine(database=self.db)
        self.predictor = PredictionEngine(database=self.db, config=self.config.data.get("prediction", {}))
        self.mode_engine = ModeEngine(config=self.config.data)
        self.resource_manager = ResourceManager(config=self.config.data)
        self.device_profiler = DeviceProfiler()
        self.tray = None
        self.plugins = []

        self._running = False
        self._current_app = ""
        self._last_focus_time = None
        self._last_window_id = None
        self._poll_interval_ms = self.config.get("polling.interval_ms", 1000)
        self._snapshot_interval = 10
        self._poll_count = 0
        self._gc_counter = 0
        self._gc_interval = 1000

        self._load_plugins()

                # Load user plugins from plugins/user/
        user_dir = os.path.join(os.path.dirname(__file__), "..", "plugins", "user")
        if os.path.exists(user_dir):
            for fname in os.listdir(user_dir):
                if fname.endswith(".py") and not fname.startswith("_"):
                    mod_name = f"plugins.user.{fname[:-3]}"
                    try:
                        mod = importlib.import_module(mod_name)
                        for name, cls in inspect.getmembers(mod, inspect.isclass):
                            if issubclass(cls, BasePlugin) and cls != BasePlugin:
                                p = cls(mirza=self)
                                p.activate()
                                self.plugins.append(p)
                                self.logger.info("User plugin loaded: %s", name)
                    except Exception as e:
                        self.logger.error("User plugin %s failed: %s", fname, e)

        self.logger.info("Device profile: %s", self.device_profiler.to_dict())

    def _load_plugins(self):
        enabled = self.config.get("features", {})
        plugin_map = {
            "battery_manager": ("plugins.official.battery_manager", "BatteryManager"),
            "thermal_guard": ("plugins.official.thermal_guard", "ThermalGuard"),
            "hardware_health": ("plugins.official.hardware_health", "HardwareHealth"),
            "service_optimizer": ("plugins.official.service_optimizer", "ServiceOptimizer"),
            "mail_optimizer": ("plugins.official.mail_optimizer", "MailOptimizer"),
            "user_script_trigger": ("plugins.official.user_script_trigger", "UserScriptTrigger"),
            "monitor_profile": ("plugins.official.monitor_profile", "MonitorProfile"),
            "shortcut_suggester": ("plugins.official.shortcut_suggester", "ShortcutSuggester"),
            "audio_profile": ("plugins.official.audio_profile", "AudioProfile"),
            "wallpaper_switcher": ("plugins.official.wallpaper_switcher", "WallpaperSwitcher"),
            "fps_limiter": ("plugins.official.fps_limiter", "FPSLimiter"),
        }
        for key, (mod_path, class_name) in plugin_map.items():
            if enabled.get(key, False):
                try:
                    mod = importlib.import_module(mod_path)
                    cls = getattr(mod, class_name)
                    plugin = cls(mirza=self)
                    plugin.activate()
                    self.plugins.append(plugin)
                    self.logger.info("Plugin loaded: %s", class_name)
                except Exception as e:
                    self.logger.error("Plugin %s failed: %s", key, e)

    def _poll_cycle(self):
        if not self._running:
            return False
        try:
            current = self.events.get_current_focus()
            if current and current.process_name:
                if self._last_window_id != current.window_id:
                    self._last_window_id = current.window_id
                    self._on_focus_event(current)
            for dev_event in self.events.poll_udev_events():
                for plugin in self.plugins:
                    try:
                        plugin.on_device_event(dev_event)
                    except Exception as e:
                        self.logger.error("Plugin %s on_device_event error: %s", plugin.__class__.__name__, e)
            self._poll_count += 1
            if self._poll_count >= self._snapshot_interval:
                self._evaluate_mode()
                self._poll_count = 0
        except Exception as e:
            self.logger.error("Poll error: %s", e)
        return True

    def _on_focus_event(self, event):
        self._gc_counter += 1
        if self._current_app and event.process_name and self._current_app != event.process_name:
            self.predictor.record_transition(self._current_app, event.process_name)
        self._current_app = event.process_name
        if self.db:
            try:
                self.db.execute(
                    "INSERT INTO focus_events (timestamp, process_name, window_title, window_geometry) VALUES (?, ?, ?, ?)",
                    (event.timestamp, event.process_name, event.window_title, str(event.geometry))
                )
            except Exception as e:
                self.logger.error("DB error: %s", e)
        # Record duration of previous app
        if self._current_app and self._last_focus_time:
            duration = event.timestamp - self._last_focus_time
            if duration > 0.5 and duration < 3600:  # Sanity check
                try:
                    self.db.execute(
                        "INSERT INTO usage_durations (process_name, duration_seconds, start_time, end_time) VALUES (?, ?, ?, ?)",
                        (self._current_app, duration, self._last_focus_time, event.timestamp)
                    )
                except Exception:
                    pass
        self._last_focus_time = event.timestamp

        self.logger.info("Focus: %s - %s", event.process_name, event.window_title)
        for plugin in self.plugins:
            try:
                plugin.on_focus_change(event)
            except Exception as e:
                self.logger.error("DB error: %s", e)
        if self._gc_counter >= self._gc_interval:
            gc.collect()
            self._gc_counter = 0

    def _evaluate_mode(self):
        snapshot = self.events.get_system_snapshot()
        if not snapshot:
            return
        old_mode = self.mode_engine.current_mode
        new_mode = self.mode_engine.evaluate(self._current_app, snapshot)
        if new_mode != old_mode:
            self.logger.info("Mode: %s -> %s", old_mode.value, new_mode.value)
            self.resource_manager.apply_mode_policy(new_mode.value)
            if self.tray:
                self.tray.set_mode(new_mode.value)
        for plugin in self.plugins:
            try:
                plugin.on_system_snapshot(snapshot)
            except Exception as e:
                self.logger.error("DB error: %s", e)
        if self._current_app:
            predicted = self.predictor.predict_next(self._current_app)
            accuracy = self.predictor.get_accuracy()
            if predicted and accuracy >= 0.70:
                self.logger.info("Predicted: %s (%.1f%%)", predicted, accuracy * 100)

    def send_notification(self, title, message):
        try:
            import notify2
            notify2.init("Mîrza")
            n = notify2.Notification(title, message)
            n.set_timeout(5000)
            n.show()
        except Exception:
            pass

    def start(self):
        self._running = True
        self.logger.info("Mîrza daemon started")
        self.tray = TrayIcon(mirza_daemon=self)
        self.tray.set_mode(self.mode_engine.current_mode.value)
        GLib.timeout_add(self._poll_interval_ms, self._poll_cycle)
        try:
            Gtk.main()
        except KeyboardInterrupt:
            self.logger.info("Interrupted")
        finally:
            self.stop()

    def stop(self):
        self._running = False
        self.logger.info("Shutting down...")
        for plugin in self.plugins:
            try:
                plugin.deactivate()
            except Exception as e:
                self.logger.error("DB error: %s", e)
        self.events.stop()
        self.db.close()
        gc.collect()
        self.logger.info("Goodbye!")


def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Mîrza - Intelligent System Assistant")
        print("Usage: mirza [--verbose] [--help]")
        return 0
    MirzaDaemon().start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
