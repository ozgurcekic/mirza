#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

"""Terminal UI for Mîrza using rich (fallback: plain text)."""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.storage.config_manager import ConfigManager
from src.storage.database import Database
from src.core.device_profiler import DeviceProfiler


def render_plain():
    """Simple terminal output without rich library."""
    config = ConfigManager()
    db = Database()
    profiler = DeviceProfiler()

    print("╔══════════════════════════════════════════════╗")
    print("║              MÎRZA  -  System Status          ║")
    print("╚══════════════════════════════════════════════╝")
    print()

    # Device info
    info = profiler.to_dict()
    print(f"  Device:    {info['device_type'].upper()} | {info['os_name']} {info['os_version']}")
    print(f"  Desktop:   {info['desktop']} ({info['session_type']})")
    print(f"  Hardware:  {info['cpu_count']} CPUs | {info['ram_total_gb']} GB RAM")
    print()

    # Database stats
    focus_count = db.fetch_one("SELECT COUNT(*) FROM focus_events")[0]
    duration_count = db.fetch_one("SELECT COUNT(*) FROM usage_durations")[0]
    reminders_pending = db.fetch_one(
        "SELECT COUNT(*) FROM reminders WHERE status='pending'"
    )[0]

    print(f"  Events:    {focus_count} focus | {duration_count} durations")
    print(f"  Reminders: {reminders_pending} pending")
    print()

    # Recent focus
    print("  Recent Activity:")
    recent = db.fetch_all(
        "SELECT process_name, window_title, datetime(timestamp, 'unixepoch', 'localtime') "
        "FROM focus_events ORDER BY id DESC LIMIT 10"
    )
    for row in recent:
        print(f"    {row[2]}  |  {row[0]:20s} | {row[1][:40]}")

    db.close()


def render_rich():
    """Rich terminal UI output."""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich.layout import Layout
    except ImportError:
        print("Rich library not installed. Install with: pip install rich")
        render_plain()
        return

    console = Console()
    config = ConfigManager()
    db = Database()
    profiler = DeviceProfiler()

    # Header
    console.print(Panel.fit(
        "[bold cyan]MÎRZA[/bold cyan] - Intelligent System Assistant",
        border_style="cyan"
    ))
    console.print()

    # Device table
    info = profiler.to_dict()
    device_table = Table(title="Device Profile", style="green")
    device_table.add_column("Property", style="dim")
    device_table.add_column("Value")
    device_table.add_row("Type", info['device_type'].upper())
    device_table.add_row("OS", f"{info['os_name']} {info['os_version']}")
    device_table.add_row("Desktop", f"{info['desktop']} ({info['session_type']})")
    device_table.add_row("CPU", f"{info['cpu_count']} cores")
    device_table.add_row("RAM", f"{info['ram_total_gb']} GB")
    console.print(device_table)
    console.print()

    # Stats
    focus_count = db.fetch_one("SELECT COUNT(*) FROM focus_events")[0]
    reminders_pending = db.fetch_one(
        "SELECT COUNT(*) FROM reminders WHERE status='pending'"
    )[0]

    stats_table = Table(title="Statistics", style="blue")
    stats_table.add_column("Metric", style="dim")
    stats_table.add_column("Value")
    stats_table.add_row("Focus Events", str(focus_count))
    stats_table.add_row("Pending Reminders", str(reminders_pending))
    console.print(stats_table)
    console.print()

    # Recent activity
    recent_table = Table(title="Recent Activity", style="yellow")
    recent_table.add_column("Time", style="dim")
    recent_table.add_column("Application")
    recent_table.add_column("Title")
    recent = db.fetch_all(
        "SELECT process_name, window_title, datetime(timestamp, 'unixepoch', 'localtime') "
        "FROM focus_events ORDER BY id DESC LIMIT 10"
    )
    for row in recent:
        recent_table.add_row(row[2], row[0], row[1][:50])

    console.print(recent_table)
    db.close()


def main():
    """Entry point for terminal UI."""
    try:
        render_rich()
    except Exception:
        render_plain()
    return 0


if __name__ == "__main__":
    sys.exit(main())
