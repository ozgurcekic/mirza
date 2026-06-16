# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import time
import logging
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


class ResourceManager:
    """Manages system resources: CPU governor, services, brightness, volume."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self._dry_run = self.config.get("security.dry_run", False)
        self._helper_path = "/usr/local/bin/mirza-helper"

        # Detect available interfaces
        self._has_cpu_governor = os.path.exists(
            "/sys/devices/system/cpu/cpufreq/policy0/scaling_governor"
        )
        self._has_backlight = os.path.exists("/sys/class/backlight/")
        self._has_battery = os.path.exists("/sys/class/power_supply/BAT0") or \
                           os.path.exists("/sys/class/power_supply/BAT1")

        logger.info("ResourceManager initialized (dry_run=%s, governor=%s, backlight=%s)",
                    self._dry_run, self._has_cpu_governor, self._has_backlight)

    def _run_helper(self, action: str, *args) -> bool:
        """Run a privileged operation via mirza-helper."""
        if self._dry_run:
            logger.info("[DRY-RUN] Would run helper: %s %s", action, args)
            return True

        cmd = [self._helper_path, action] + list(args)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return True
            logger.error("Helper failed for %s: %s", action, result.stderr.strip())
            return False
        except FileNotFoundError:
            logger.warning("mirza-helper not found at %s", self._helper_path)
            return False
        except subprocess.TimeoutExpired:
            logger.error("Helper timeout for %s", action)
            return False

    def _write_sysfs(self, path: str, value: str) -> bool:
        if self._dry_run:
            logger.info("[DRY-RUN] Would write '%s' to %s", value, path)
            return True

        try:
            with open(path, "w") as f:
                f.write(str(value))
            return True
        except PermissionError:
            pass
        except Exception:
            pass

        import subprocess
        try:
            result = subprocess.run(
                ["sudo", "/usr/local/bin/mirza-helper", "write-sysfs", path, str(value)],
                capture_output=True, timeout=5
            )
            if result.returncode == 0:
                return True
        except Exception:
            pass

        return False


    def set_cpu_governor(self, governor: str) -> bool:
        """Set CPU governor for all cores."""
        if not self._has_cpu_governor:
            logger.debug("CPU governor not available")
            return False

        success = True
        policy_dir = "/sys/devices/system/cpu/cpufreq"
        try:
            for policy in os.listdir(policy_dir):
                if policy.startswith("policy"):
                    path = os.path.join(policy_dir, policy, "scaling_governor")
                    if not self._write_sysfs(path, governor):
                        success = False
        except FileNotFoundError:
            return False

        if success:
            logger.info("CPU governor set to '%s'", governor)
        return success

    def set_brightness(self, percent: int) -> bool:
        """Set screen brightness (0-100)."""
        if not self._has_backlight:
            logger.debug("Backlight control not available")
            return False

        percent = max(5, min(100, percent))  # Minimum 5% to avoid black screen
        success = False

        backlight_dir = "/sys/class/backlight"
        try:
            for device in os.listdir(backlight_dir):
                max_path = os.path.join(backlight_dir, device, "max_brightness")
                bright_path = os.path.join(backlight_dir, device, "brightness")

                try:
                    with open(max_path, "r") as f:
                        max_val = int(f.read().strip())
                except Exception:
                    continue

                target = int((percent / 100) * max_val)
                # Ensure target is at least 1% of max to avoid black screen
                target = max(target, int(max_val * 0.01))
                
                if self._write_sysfs(bright_path, str(target)):
                    success = True
                    logger.info("Brightness set to %d%% (%d/%d)", percent, target, max_val)
        except FileNotFoundError:
            pass

        return success

    def set_volume(self, percent: int) -> bool:
        """Set system volume using pactl (0-100)."""
        percent = max(0, min(100, percent))

        try:
            result = subprocess.run(
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{percent}%"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                logger.info("Volume set to %d%%", percent)
                return True
        except FileNotFoundError:
            logger.debug("pactl not available")
        except Exception as e:
            logger.error("Failed to set volume: %s", e)

        return False

    def stop_service(self, service_name: str) -> bool:
        """Stop a systemd user service."""
        if self._dry_run:
            logger.info("[DRY-RUN] Would stop service: %s", service_name)
            return True

        try:
            result = subprocess.run(
                ["systemctl", "--user", "stop", service_name],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                logger.info("Service stopped: %s", service_name)
                return True
            logger.warning("Failed to stop %s: %s", service_name, result.stderr.strip())
            return False
        except Exception as e:
            logger.error("Error stopping %s: %s", service_name, e)
            return False

    def start_service(self, service_name: str) -> bool:
        """Start a systemd user service."""
        if self._dry_run:
            logger.info("[DRY-RUN] Would start service: %s", service_name)
            return True

        try:
            result = subprocess.run(
                ["systemctl", "--user", "start", service_name],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                logger.info("Service started: %s", service_name)
                return True
            return False
        except Exception as e:
            logger.error("Error starting %s: %s", service_name, e)
            return False

    def suspend_process(self, pid: int) -> bool:
        """Suspend a process with SIGSTOP."""
        if self._dry_run:
            logger.info("[DRY-RUN] Would suspend PID %d", pid)
            return True

        try:
            os.kill(pid, 19)  # SIGSTOP
            logger.info("Process suspended: PID %d", pid)
            return True
        except (ProcessLookupError, PermissionError) as e:
            logger.error("Failed to suspend PID %d: %s", pid, e)
            return False

    def resume_process(self, pid: int) -> bool:
        """Resume a process with SIGCONT."""
        if self._dry_run:
            logger.info("[DRY-RUN] Would resume PID %d", pid)
            return True

        try:
            os.kill(pid, 18)  # SIGCONT
            logger.info("Process resumed: PID %d", pid)
            return True
        except (ProcessLookupError, PermissionError) as e:
            logger.error("Failed to resume PID %d: %s", pid, e)
            return False

    def apply_mode_policy(self, mode: str) -> dict:
        """Apply all resource policies for a given mode."""
        # Check standard modes first
        modes_dict = self.config.get("modes", {})
        policies = modes_dict.get(mode, {})
        
        # If not found, check user_modes
        if not policies:
            user_modes = self.config.get("user_modes", [])
            for m in user_modes:
                if m.get("name") == mode:
                    policies = m.get("policies", {})
                    break
        results = {
            "governor": False,
            "brightness": False,
            "volume": False,
        }

        # CPU Governor
        governor = policies.get("cpu_governor")
        if governor:
            results["governor"] = self.set_cpu_governor(governor)

        # Brightness
        brightness = policies.get("brightness_percent")
        if brightness is not None:
            results["brightness"] = self.set_brightness(brightness)

        # Volume
        volume = policies.get("volume_percent")
        if volume is not None:
            results["volume"] = self.set_volume(volume)

        logger.info("Applied %s mode policies: %s", mode, results)
        return results

    def get_current_governor(self) -> str:
        """Get current CPU governor."""
        try:
            path = "/sys/devices/system/cpu/cpufreq/policy0/scaling_governor"
            with open(path, "r") as f:
                return f.read().strip()
        except Exception:
            return "unknown"

    def get_current_brightness(self) -> Optional[int]:
        """Get current brightness as percentage."""
        try:
            backlight_dir = "/sys/class/backlight"
            for device in os.listdir(backlight_dir):
                max_path = os.path.join(backlight_dir, device, "max_brightness")
                bright_path = os.path.join(backlight_dir, device, "brightness")

                with open(max_path, "r") as f:
                    max_val = int(f.read().strip())
                with open(bright_path, "r") as f:
                    current = int(f.read().strip())

                return int((current / max_val) * 100)
        except Exception:
            return None
