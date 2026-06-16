# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk

logger = logging.getLogger(__name__)


class SettingsWindow(Gtk.Window):
    """GTK3 settings window for Mîrza configuration."""

    def __init__(self, config_manager=None, mirza_daemon=None):
        super().__init__(title="Mîrza Settings")
        self.config = config_manager
        self.mirza = mirza_daemon
        self._widgets = {}

        self.set_default_size(650, 550)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(True)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_box)

        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header.set_margin_start(15)
        header.set_margin_end(15)
        header.set_margin_top(15)
        header.set_margin_bottom(10)
        title = Gtk.Label()
        title.set_markup("<b><big>Mîrza Settings</big></b>")
        title.set_halign(Gtk.Align.START)
        header.pack_start(title, True, True, 0)
        main_box.pack_start(header, False, False, 0)
        main_box.pack_start(Gtk.Separator(), False, False, 0)

        # Notebook
        notebook = Gtk.Notebook()
        notebook.set_margin_start(10)
        notebook.set_margin_end(10)
        notebook.set_margin_top(10)

        notebook.append_page(self._build_general_tab(), Gtk.Label(label="  General  "))
        notebook.append_page(self._build_mode_tab("eco", "Eco"), Gtk.Label(label="  Eco  "))
        notebook.append_page(self._build_mode_tab("normal", "Normal"), Gtk.Label(label="  Normal  "))
        notebook.append_page(self._build_mode_tab("sport", "Sport"), Gtk.Label(label="  Sport  "))
        notebook.append_page(self._build_custom_modes_tab(), Gtk.Label(label="  Custom  "))
        notebook.append_page(self._build_features_tab(), Gtk.Label(label="  Features  "))

        main_box.pack_start(notebook, True, True, 0)
        main_box.pack_start(Gtk.Separator(), False, False, 0)

        # Buttons
        btn_box = Gtk.Box(spacing=10)
        btn_box.set_margin_start(15)
        btn_box.set_margin_end(15)
        btn_box.set_margin_top(10)
        btn_box.set_margin_bottom(15)
        btn_box.set_halign(Gtk.Align.END)

        save_btn = Gtk.Button(label="  Save  ")
        save_btn.set_size_request(100, 35)
        save_btn.connect("clicked", self._on_save)
        btn_box.pack_start(save_btn, False, False, 0)

        close_btn = Gtk.Button(label="  Close  ")
        close_btn.set_size_request(100, 35)
        close_btn.connect("clicked", self._on_close)
        btn_box.pack_start(close_btn, False, False, 0)

        main_box.pack_start(btn_box, False, False, 0)
        logger.info("Settings window created")

    def _make_section(self, text):
        label = Gtk.Label()
        label.set_markup(f"<b>{text}</b>")
        label.set_halign(Gtk.Align.START)
        label.set_margin_top(12)
        label.set_margin_bottom(4)
        return label

    def _make_switch(self, config_key, label_text, grid, row, indent=True):
        label = Gtk.Label(label=label_text)
        label.set_halign(Gtk.Align.START)
        if indent:
            label.set_margin_start(15)
        grid.attach(label, 0, row, 1, 1)
        switch = Gtk.Switch()
        switch.set_active(self.config.get(config_key, False))
        switch.set_halign(Gtk.Align.START)
        self._widgets[config_key] = switch
        grid.attach(switch, 1, row, 1, 1)

    def _make_slider(self, config_key, label_text, min_val, max_val, step, grid, row, default=50):
        label = Gtk.Label(label=label_text)
        label.set_halign(Gtk.Align.START)
        label.set_margin_start(15)
        grid.attach(label, 0, row, 1, 1)
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, min_val, max_val, step)
        slider.set_value(self.config.get(config_key, default))
        slider.set_size_request(180, 30)
        slider.set_draw_value(True)
        slider.set_value_pos(Gtk.PositionType.RIGHT)
        box.pack_start(slider, True, True, 0)
        self._widgets[config_key] = slider
        grid.attach(box, 1, row, 1, 1)

    def _make_combo(self, config_key, label_text, options, default, grid, row):
        label = Gtk.Label(label=label_text)
        label.set_halign(Gtk.Align.START)
        label.set_margin_start(15)
        grid.attach(label, 0, row, 1, 1)
        combo = Gtk.ComboBoxText()
        for opt in options:
            combo.append_text(opt)
        current = self.config.get(config_key, default)
        for i, opt in enumerate(options):
            if opt == current:
                combo.set_active(i)
                break
        combo.set_size_request(180, 30)
        self._widgets[config_key] = combo
        grid.attach(combo, 1, row, 1, 1)

    def _make_entry(self, config_key, label_text, default, grid, row):
        label = Gtk.Label(label=label_text)
        label.set_halign(Gtk.Align.START)
        label.set_margin_start(15)
        grid.attach(label, 0, row, 1, 1)
        entry = Gtk.Entry()
        entry.set_text(str(self.config.get(config_key, default)))
        entry.set_size_request(180, 30)
        self._widgets[config_key] = entry
        grid.attach(entry, 1, row, 1, 1)

    # ==================== GENERAL TAB ====================
    def _build_general_tab(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        grid = Gtk.Grid(column_spacing=15, row_spacing=6, margin=10)
        row = 0

        grid.attach(self._make_section("Assistant"), 0, row, 2, 1); row += 1
        self._make_entry("general.assistant_name", "Name:", "Mîrza", grid, row); row += 1
        self._make_combo("general.language", "Language:", ["en", "tr", "de"], "en", grid, row); row += 1

        grid.attach(self._make_section("Display"), 0, row, 2, 1); row += 1
        self._make_combo("general.widget_mode", "Widget mode:", ["tray", "desktop", "off"], "tray", grid, row); row += 1

        grid.attach(self._make_section("System"), 0, row, 2, 1); row += 1
        self._make_switch("prediction.enabled", "Enable Predictions", grid, row); row += 1
        self._make_switch("security.dry_run", "Dry Run Mode (no changes)", grid, row); row += 1

        scroll.add(grid)
        return scroll

    # ==================== MODE TAB ====================
    def _build_mode_tab(self, mode_name, mode_label):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        grid = Gtk.Grid(column_spacing=15, row_spacing=6, margin=10)
        row = 0
        prefix = f"modes.{mode_name}"

        # Display
        grid.attach(self._make_section("Display"), 0, row, 2, 1); row += 1
        self._make_slider(f"{prefix}.brightness_percent", "Brightness %", 10, 100, 5, grid, row, 
                         default={"eco": 25, "normal": 70, "sport": 100}.get(mode_name, 70)); row += 1

        # Audio
        grid.attach(self._make_section("Audio"), 0, row, 2, 1); row += 1
        self._make_slider(f"{prefix}.volume_percent", "Volume %", 0, 100, 5, grid, row,
                         default={"eco": 50, "normal": 70, "sport": 85}.get(mode_name, 70)); row += 1

        # Performance
        grid.attach(self._make_section("Performance"), 0, row, 2, 1); row += 1
        self._make_combo(f"{prefix}.cpu_governor", "CPU Governor:", 
                        ["powersave", "ondemand", "performance", "schedutil"],
                        {"eco": "powersave", "normal": "ondemand", "sport": "performance"}.get(mode_name, "ondemand"),
                        grid, row); row += 1

        # Power user: Dedicate resources to one app
        grid.attach(self._make_section("Power User"), 0, row, 2, 1); row += 1
        self._make_switch(f"{prefix}.dedicate_to_focused", "Dedicate all power to focused app", grid, row); row += 1
        self._make_switch(f"{prefix}.stop_background_services", "Stop background services", grid, row); row += 1
        self._make_switch(f"{prefix}.stop_network_sync", "Stop network sync", grid, row); row += 1
        self._make_switch(f"{prefix}.silence_notifications", "Silence notifications", grid, row); row += 1
        self._make_switch(f"{prefix}.disable_bluetooth", "Disable Bluetooth", grid, row); row += 1
        self._make_switch(f"{prefix}.enable_night_light", "Enable Night Light", grid, row); row += 1

        # Idle
        grid.attach(self._make_section("Idle"), 0, row, 2, 1); row += 1
        self._make_slider(f"{prefix}.app_idle_timeout_minutes", "Close apps after idle (min, 0=never)", 0, 60, 1, grid, row,
                         default={"eco": 10, "normal": 30, "sport": 0}.get(mode_name, 30)); row += 1
        self._make_slider(f"{prefix}.screen_off_minutes", "Turn screen off after (min, 0=never)", 0, 60, 1, grid, row,
                         default={"eco": 5, "normal": 15, "sport": 0}.get(mode_name, 15)); row += 1

        scroll.add(grid)
        return scroll

    # ==================== CUSTOM MODES TAB ====================
    def _build_custom_modes_tab(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        grid = Gtk.Grid(column_spacing=15, row_spacing=6, margin=10)
        row = 0

        info = Gtk.Label()
        info.set_markup("<i>Custom modes create your own presets. Define them in ~/.config/mirza/config.yml</i>")
        info.set_halign(Gtk.Align.START)
        info.set_line_wrap(True)
        info.set_margin_bottom(10)
        grid.attach(info, 0, row, 2, 1); row += 1

        user_modes = self.config.get("user_modes", [])
        
        for mode_def in user_modes:
            name = mode_def.get("name", "unnamed")
            policies = mode_def.get("policies", {})
            prefix = f"custom.{name}"

            grid.attach(self._make_section(f"⭐ {name.title()} Mode"), 0, row, 2, 1); row += 1

            self._make_slider(f"{prefix}.brightness_percent", "Brightness %", 10, 100, 5, grid, row,
                             default=policies.get("brightness_percent", 70)); row += 1
            self._make_slider(f"{prefix}.volume_percent", "Volume %", 0, 100, 5, grid, row,
                             default=policies.get("volume_percent", 70)); row += 1
            self._make_combo(f"{prefix}.cpu_governor", "CPU Governor:",
                            ["powersave", "ondemand", "performance", "schedutil"],
                            policies.get("cpu_governor", "ondemand"), grid, row); row += 1

            grid.attach(self._make_section("Power User"), 0, row, 2, 1); row += 1
            self._make_switch(f"{prefix}.dedicate_to_focused", "Dedicate all power to focused app", grid, row); row += 1
            self._make_switch(f"{prefix}.stop_background_services", "Stop background services", grid, row); row += 1
            self._make_switch(f"{prefix}.stop_network_sync", "Stop network sync", grid, row); row += 1
            self._make_switch(f"{prefix}.silence_notifications", "Silence notifications", grid, row); row += 1
            self._make_switch(f"{prefix}.disable_bluetooth", "Disable Bluetooth", grid, row); row += 1
            self._make_switch(f"{prefix}.enable_night_light", "Enable Night Light", grid, row); row += 1

        if not user_modes:
            no_modes = Gtk.Label()
            no_modes.set_markup("<i>No custom modes defined yet.</i>")
            no_modes.set_halign(Gtk.Align.START)
            no_modes.set_margin_top(20)
            grid.attach(no_modes, 0, row, 2, 1)

        scroll.add(grid)
        return scroll

    # ==================== FEATURES TAB ====================
    def _build_features_tab(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        grid = Gtk.Grid(column_spacing=15, row_spacing=4, margin=10)
        row = 0

        grid.attach(self._make_section("Enabled Plugins"), 0, row, 2, 1); row += 1

        plugins = [
            ("features.battery_manager", "Battery Manager"),
            ("features.thermal_guard", "Thermal Guard"),
            ("features.hardware_health", "Hardware Health"),
            ("features.service_optimizer", "Service Optimizer"),
            ("features.mail_optimizer", "Mail Optimizer"),
            ("features.audio_profile", "Audio Profile"),
            ("features.wallpaper_switcher", "Wallpaper Switcher"),
            ("features.monitor_profile", "Monitor Profile"),
            ("features.shortcut_suggester", "Shortcut Suggester"),
            ("features.user_script_trigger", "User Script Trigger"),
            ("features.fps_limiter", "FPS Limiter"),
        ]

        for key, name in plugins:
            self._make_switch(key, name, grid, row, indent=False); row += 1

        scroll.add(grid)
        return scroll

    # ==================== SAVE ====================
    def _on_save(self, widget):
        for key_path, widget in self._widgets.items():
            value = None
            if isinstance(widget, Gtk.Entry):
                value = widget.get_text()
            elif isinstance(widget, Gtk.ComboBoxText):
                value = widget.get_active_text()
            elif isinstance(widget, Gtk.Switch):
                value = widget.get_active()
            elif isinstance(widget, Gtk.Scale):
                value = int(widget.get_value())

            if value is not None:
                if key_path.startswith("custom."):
                    parts = key_path.split(".")
                    mode_name = parts[1]
                    setting = parts[2]
                    user_modes = self.config.get("user_modes", [])
                    for m in user_modes:
                        if m.get("name") == mode_name:
                            m.setdefault("policies", {})[setting] = value
                            break
                    self.config.set("user_modes", user_modes)
                else:
                    self.config.set(key_path, value)

        self.config.save()
        logger.info("Settings saved")
        self._show_info("Settings saved successfully.")

    def _on_close(self, widget):
        self.destroy()

    def _show_info(self, message):
        dialog = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, message)
        dialog.run()
        dialog.destroy()
