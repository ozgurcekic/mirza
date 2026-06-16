import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from src.core.mode_engine import ModeEngine, SystemMode
from src.storage.config_manager import ConfigManager

def test_mode_engine():
    config = ConfigManager()
    engine = ModeEngine(config=config.data)
    assert engine.current_mode is not None
    print("  OK ModeEngine")

def test_config_manager():
    config = ConfigManager()
    assert config.data is not None
    print("  OK ConfigManager")

if __name__ == "__main__":
    test_mode_engine()
    test_config_manager()
    print("All smoke tests passed!")
