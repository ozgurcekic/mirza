# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import os, subprocess, logging, gi, time
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)

class SystemDashboard(BasePlugin):
    def __init__(self, mirza=None):
        super().__init__(mirza=mirza)
        self._window = None
    def activate(self):
        super().activate()
        logger.info("SystemDashboard active")
    def open_dashboard(self):
        if self._window:
            try: self._window.destroy()
            except: pass
        self._window = DashboardWindow(mirza=self.mirza)
        self._window.show_all()
    def deactivate(self):
        if self._window:
            try: self._window.destroy()
            except: pass
        super().deactivate()

class DashboardWindow(Gtk.Window):
    def __init__(self, mirza=None):
        super().__init__(title="Mirza - System Dashboard")
        self.mirza = mirza
        self.set_default_size(750, 550)
        self.set_position(Gtk.WindowPosition.CENTER)
        main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(main)
        h = Gtk.Box(spacing=10, margin=15)
        t = Gtk.Label()
        t.set_markup("<b><big>System Dashboard</big></b>")
        h.pack_start(t, True, True, 0)
        main.pack_start(h, False, False, 0)
        main.pack_start(Gtk.Separator(), False, False, 0)
        self.notebook = Gtk.Notebook()
        self.notebook.set_margin_start(10); self.notebook.set_margin_end(10); self.notebook.set_margin_top(10)
        self._tab_device()
        self._tab_cleanup()
        self._tab_recommendations()
        main.pack_start(self.notebook, True, True, 0)
        main.pack_start(Gtk.Separator(), False, False, 0)
        btn = Gtk.Box(spacing=10, margin=15); btn.set_halign(Gtk.Align.END)
        b = Gtk.Button(label="  Close  "); b.set_size_request(100, 35)
        b.connect("clicked", lambda w: self.destroy())
        btn.pack_start(b, False, False, 0)
        main.pack_start(btn, False, False, 0)

    def _sec(self, g, t, r):
        l = Gtk.Label(); l.set_markup(f"<b>{t}</b>"); l.set_halign(Gtk.Align.START)
        l.set_margin_top(10); g.attach(l, 0, r, 2, 1)

    def _pkg_ok(self, pkg):
        try:
            r = subprocess.run(["dpkg", "-s", pkg], capture_output=True, text=True)
            return r.returncode == 0 and "install ok installed" in r.stdout
        except: return False

    # ===== DEVICE INFO =====
    def _tab_device(self):
        s = Gtk.ScrolledWindow()
        g = Gtk.Grid(column_spacing=15, row_spacing=8, margin=15); r = 0
        self._sec(g, "System", r); r += 1
        for k, v in self._sys_info().items():
            l = Gtk.Label(label=k); l.set_halign(Gtk.Align.START); l.set_margin_start(15)
            g.attach(l, 0, r, 1, 1)
            l2 = Gtk.Label(label=str(v)); l2.set_halign(Gtk.Align.START); l2.set_selectable(True)
            g.attach(l2, 1, r, 1, 1); r += 1
        r += 1
        self._sec(g, "Drivers", r); r += 1
        for name, st in self._drivers().items():
            l = Gtk.Label(label=name); l.set_halign(Gtk.Align.START); l.set_margin_start(15)
            g.attach(l, 0, r, 1, 1)
            box = Gtk.Box(spacing=10)
            if st["installed"]:
                l = Gtk.Label(); l.set_markup("<span foreground='green'>✅ Installed</span>")
                box.pack_start(l, False, False, 0)
            else:
                l = Gtk.Label(); l.set_markup("<span foreground='orange'>⚠️ Not installed</span>")
                box.pack_start(l, False, False, 0)
                b = Gtk.Button(label="Install"); b.set_size_request(80, 25)
                b.connect("clicked", self._install, st.get("package", name))
                box.pack_start(b, False, False, 0)
            g.attach(box, 1, r, 1, 1); r += 1
        s.add(g)
        self.notebook.append_page(s, Gtk.Label(label="  Device Info  "))

    def _sys_info(self):
        i = {}
        try:
            with open("/etc/os-release") as f:
                for l in f:
                    if l.startswith("PRETTY_NAME="): i["OS"] = l.split("=")[1].strip().strip('"')
        except: i["OS"] = "?"
        try:
            r = subprocess.run(["uname", "-r"], capture_output=True, text=True)
            i["Kernel"] = r.stdout.strip()
        except: i["Kernel"] = "?"
        try:
            with open("/proc/cpuinfo") as f:
                for l in f:
                    if "model name" in l: i["CPU"] = l.split(":")[1].strip(); break
        except: i["CPU"] = "?"
        try:
            import psutil
            i["RAM"] = f"{psutil.virtual_memory().total / (1024**3):.1f} GB"
        except: i["RAM"] = "?"
        try:
            r = subprocess.run(["lspci"], capture_output=True, text=True)
            for l in r.stdout.split("\n"):
                if "VGA" in l or "3D" in l: i["GPU"] = l.split(":")[-1].strip(); break
        except: i["GPU"] = "?"
        i["Session"] = os.environ.get("XDG_SESSION_TYPE", "?")
        i["Desktop"] = os.environ.get("XDG_CURRENT_DESKTOP", "?")
        try:
            import psutil
            i["Disk Free"] = f"{psutil.disk_usage('/').free / (1024**3):.1f} GB"
        except: pass
        return i

    def _drivers(self):
        return {
            "NVIDIA Driver": {"installed": os.path.exists("/usr/bin/nvidia-smi"), "available": True, "package": "nvidia-driver-550"},
            "Intel VA-API": {"installed": self._pkg_ok("intel-media-va-driver"), "available": True, "package": "intel-media-va-driver"},
            "CUPS (Printing)": {"installed": self._pkg_ok("cups"), "available": True, "package": "cups"},
            "OpenSSH Server": {"installed": self._pkg_ok("openssh-server"), "available": True, "package": "openssh-server"},
            "GStreamer": {"installed": self._pkg_ok("gstreamer1.0-libav"), "available": True, "package": "gstreamer1.0-libav"},
            "Flatpak": {"installed": os.path.exists("/usr/bin/flatpak"), "available": True, "package": "flatpak"},
        }

    # ===== CLEANUP =====
    def _tab_cleanup(self):
        s = Gtk.ScrolledWindow()
        g = Gtk.Grid(column_spacing=15, row_spacing=10, margin=15); r = 0
        self._sec(g, "Cleanup", r); r += 1
        items = [
            ("APT Cache", "apt clean", "Cleans downloaded package files"),
            ("Journal Logs (7d)", "journalctl --vacuum-time=7d", "Removes old system logs"),
            ("Thumbnail Cache", "rm -rf ~/.cache/thumbnails/*", "Deletes cached thumbnails"),
            ("Trash", "rm -rf ~/.local/share/Trash/*", "Empties the trash"),
            ("pip Cache", "pip cache purge 2>/dev/null", "Cleans Python package cache"),
            ("npm Cache", "npm cache clean --force 2>/dev/null", "Cleans Node.js cache"),
            ("Docker (unused)", "docker system prune -f 2>/dev/null", "Removes unused Docker data"),
        ]
        for name, cmd, desc in items:
            box = Gtk.Box(spacing=10, margin_start=15)
            l = Gtk.Label(label=f"{name}:"); l.set_size_request(180, 25); l.set_halign(Gtk.Align.START)
            box.pack_start(l, False, False, 0)
            d = Gtk.Label(label=desc); d.set_halign(Gtk.Align.START)
            box.pack_start(d, True, True, 0)
            b = Gtk.Button(label="Clean"); b.set_size_request(80, 25)
            b.connect("clicked", lambda w, c=cmd, n=name: self._clean(c, n))
            box.pack_start(b, False, False, 0)
            g.attach(box, 0, r, 2, 1); r += 1
        r += 1
        b = Gtk.Button(label="  Clean All  "); b.set_size_request(150, 40)
        b.connect("clicked", lambda w: self._clean("apt clean; journalctl --vacuum-time=7d; rm -rf ~/.cache/thumbnails/*; rm -rf ~/.local/share/Trash/*; pip cache purge 2>/dev/null; npm cache clean --force 2>/dev/null; docker system prune -f 2>/dev/null", "all tasks"))
        g.attach(b, 0, r, 2, 1)
        s.add(g)
        self.notebook.append_page(s, Gtk.Label(label="  Cleanup  "))

    def _clean(self, cmd, name):
        d = Gtk.MessageDialog(self, 0, Gtk.MessageType.QUESTION, Gtk.ButtonsType.OK_CANCEL, f"Run {name}?")
        if d.run() == Gtk.ResponseType.OK:
            subprocess.Popen(["pkexec", "bash", "-c", cmd])
        d.destroy()

    # ===== RECOMMENDATIONS =====
    def _tab_recommendations(self):
        s = Gtk.ScrolledWindow()
        self._rec_content(s)
        self.notebook.append_page(s, Gtk.Label(label="  Recommendations  "))

    def _rec_content(self, s):
        g = Gtk.Grid(column_spacing=15, row_spacing=8, margin=15); r = 0
        self._sec(g, "Recommended Software", r); r += 1
        for cat, apps in [("Graphics and Design", [("GIMP","gimp"),("Inkscape","inkscape"),("Krita","krita"),("Blender","blender")]),("Office and Productivity", [("LibreOffice","libreoffice"),("Thunderbird","thunderbird")]),("Development", [("Git","git"),("Node.js","nodejs")]),("Gaming", [("Steam","steam-installer"),("Lutris","lutris")])]:
            cl = Gtk.Label(); cl.set_markup(f"<b>{cat}</b>"); cl.set_halign(Gtk.Align.START); cl.set_margin_top(10); g.attach(cl, 0, r, 2, 1); r += 1
            for name, pkg in apps:
                box = Gtk.Box(spacing=10, margin_start=15)
                if self._pkg_ok(pkg):
                    l = Gtk.Label(); l.set_markup(f"✅ <b>{name}</b> <span foreground='green'>(Installed)</span>"); box.pack_start(l, False, False, 0)
                else:
                    box.pack_start(Gtk.Label(label=f"⬜ {name}"), False, False, 0)
                    b = Gtk.Button(label="Install"); b.set_size_request(70, 25); b.connect("clicked", self._install, pkg); box.pack_start(b, False, False, 0)
                g.attach(box, 0, r, 2, 1); r += 1
        for child in s.get_children(): s.remove(child)
        s.add(g); s.show_all()
    def _refresh_rec(self):
        # Find recommendations tab and rebuild
        for i in range(self.notebook.get_n_pages()):
            page = self.notebook.get_nth_page(i)
            label = self.notebook.get_tab_label(page)
            if label and "Recommendations" in label.get_text():
                self._rec_content(page)
                return

    # ===== INSTALL =====
    def _install(self, widget, pkg):
        if os.path.exists("/usr/bin/apt"):
            cmd = ["pkexec", "apt", "install", "-y", pkg]
        elif os.path.exists("/usr/bin/dnf"):
            cmd = ["pkexec", "dnf", "install", "-y", pkg]
        elif os.path.exists("/usr/bin/pacman"):
            cmd = ["pkexec", "pacman", "-S", "--noconfirm", pkg]
        else:
            self._show_info("No supported package manager found.")
            return
        
        win = Gtk.Window(title=f"Installing {pkg}...")
        win.set_default_size(500, 300); win.set_position(Gtk.WindowPosition.CENTER)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5, margin=10)
        box.pack_start(Gtk.Label(label=f"Installing {pkg}..."), False, False, 0)
        scr = Gtk.ScrolledWindow()
        buf = Gtk.TextBuffer(); tv = Gtk.TextView(buffer=buf)
        tv.set_editable(False); scr.add(tv); box.pack_start(scr, True, True, 0)
        sp = Gtk.Spinner(); sp.start(); box.pack_start(sp, False, False, 0)
        win.add(box); win.show_all()
        
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        def check():
            if proc.poll() is not None:
                try:
                    rest = proc.stdout.read()
                    if rest: buf.insert(buf.get_end_iter(), rest)
                except: pass
                sp.stop()
                buf.insert(buf.get_end_iter(), "\nDone!\n" if proc.returncode == 0 else "\nFailed.\n")
                self._refresh_rec()
                cb = Gtk.Button(label="Close"); cb.connect("clicked", lambda w: win.destroy())
                box.pack_start(cb, False, False, 0); cb.show_all()
                return False
            return True
        def read(fd, cond):
            line = proc.stdout.readline()
            if line:
                buf.insert(buf.get_end_iter(), line)
                tv.scroll_to_iter(buf.get_end_iter(), 0, False, 0, 0)
            return True
        GLib.io_add_watch(proc.stdout, GLib.IO_IN, read)
        GLib.timeout_add(2000, check)
    def _show_info(self, msg, auto_close=0):
        d = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, msg)
        if auto_close > 0:
            GLib.timeout_add(auto_close, d.destroy)
        d.run()
        try: d.destroy()
        except: pass
