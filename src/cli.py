#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import sys
import time
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.storage.config_manager import ConfigManager
from src.storage.database import Database


def cmd_remind(args):
    """Add a reminder: mirza remind "text" [--tag=tagname]"""
    if not args:
        print("Usage: mirza remind \"text\" [--tag=tagname]")
        return 1

    text = args[0]
    tag = None
    for arg in args[1:]:
        if arg.startswith("--tag="):
            tag = arg.split("=", 1)[1]

    db = Database()
    db.execute(
        "INSERT INTO reminders (text, created_at, status, tags) VALUES (?, ?, 'pending', ?)",
        (text, time.time(), tag)
    )
    db.close()
    print(f"Reminder added: \"{text}\"")
    return 0


def cmd_list(args):
    """List all reminders: mirza list [--all] [--pending] [--done]"""
    db = Database()
    status_filter = "pending"
    if "--all" in args:
        status_filter = None
    elif "--done" in args:
        status_filter = "done"

    if status_filter:
        rows = db.fetch_all(
            "SELECT id, text, created_at, tags FROM reminders WHERE status=? ORDER BY created_at DESC",
            (status_filter,)
        )
    else:
        rows = db.fetch_all(
            "SELECT id, text, created_at, status, tags FROM reminders ORDER BY created_at DESC"
        )

    if not rows:
        print("No reminders found.")
    else:
        print(f"{'ID':<4} {'Status':<10} {'Text':<50} {'Tag':<15}")
        print("-" * 80)
        for row in rows:
            status = row[2] if len(row) > 3 else status_filter
            tag = row[-1] if row[-1] else ""
            text = row[1][:48] + ".." if len(row[1]) > 50 else row[1]
            print(f"{row[0]:<4} {status:<10} {text:<50} {tag:<15}")

    db.close()
    return 0


def cmd_done(args):
    """Mark reminder as done: mirza done <id>"""
    if not args:
        print("Usage: mirza done <id>")
        return 1

    reminder_id = args[0]
    db = Database()
    db.execute("UPDATE reminders SET status='done' WHERE id=?", (reminder_id,))
    db.close()
    print(f"Reminder #{reminder_id} marked as done.")
    return 0


def cmd_status(args):
    """Show system status: mirza status"""
    config = ConfigManager()
    db = Database()

    print("=== Mîrza System Status ===")
    print(f"Assistant: {config.get('general.assistant_name')}")
    print(f"Language: {config.get('general.language')}")

    # Count events
    focus_count = db.fetch_one("SELECT COUNT(*) FROM focus_events")[0]
    duration_count = db.fetch_one("SELECT COUNT(*) FROM usage_durations")[0]
    print(f"Focus events: {focus_count}")
    print(f"Duration records: {duration_count}")

    db.close()
    return 0


def cmd_ui(args):
    """Launch terminal UI: mirza --ui"""
    try:
        subprocess.run([sys.executable, "-m", "src.ui.terminal_ui"] + args)
    except Exception as e:
        print(f"Terminal UI not available yet: {e}")
    return 0


def cmd_log(args):
    """Show recent logs: mirza --log [lines]"""
    lines = 20
    if args:
        try:
            lines = int(args[0])
        except ValueError:
            pass

    log_path = os.path.expanduser("~/.local/share/mirza/mirza.log")
    if not os.path.exists(log_path):
        print("No log file found.")
        return 1

    with open(log_path, "r") as f:
        all_lines = f.readlines()
        for line in all_lines[-lines:]:
            print(line.rstrip())
    return 0


def main():
    if len(sys.argv) < 2:
        print("Mîrza - Intelligent System Assistant")
        print("Usage: mirza <command> [args]")
        print()
        print("Commands:")
        print("  remind <text>     Add a reminder")
        print("  list              List pending reminders")
        print("  done <id>         Mark reminder as done")
        print("  status            Show system status")
        print("  --ui              Launch terminal UI")
        print("  --log [lines]     Show recent logs")
        print("  --help            Show this help")
        return 0

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "remind": cmd_remind,
        "list": cmd_list,
        "done": cmd_done,
        "status": cmd_status,
        "--ui": cmd_ui,
        "--log": cmd_log,
        "--help": lambda _: main(),
    }

    if command in commands:
        return commands[command](args)
    else:
        print(f"Unknown command: {command}")
        print("Run 'mirza --help' for usage.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
