# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import yaml
import shutil
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.config/mirza/config.yml")
RESOURCE_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "resources", "default_config.yml"
)


class ConfigManager:
    def __init__(self, config_path=DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self.data = {}
        self.load()

    def load(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        if not os.path.exists(self.config_path):
            self._copy_default()
        with open(self.config_path, "r") as f:
            self.data = yaml.safe_load(f) or {}
        logger.info("Configuration loaded from %s", self.config_path)

    def _copy_default(self):
        if os.path.exists(RESOURCE_CONFIG_PATH):
            shutil.copy(RESOURCE_CONFIG_PATH, self.config_path)
            logger.info("Default config copied to %s", self.config_path)
        else:
            logger.warning("Default config not found at %s", RESOURCE_CONFIG_PATH)

    def save(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.dump(self.data, f, default_flow_style=False)
        logger.info("Configuration saved to %s", self.config_path)

    def get(self, key_path, default=None):
        keys = key_path.split(".")
        value = self.data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
            if value is None:
                return default
        return value

    def set(self, key_path, value):
        keys = key_path.split(".")
        target = self.data
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        target[keys[-1]] = value

    def __repr__(self):
        return f"ConfigManager(path={self.config_path})"
