"""
settings.py
-----------
Manages user-configurable preferences for PushPulse and persists them
to a local settings.json file so choices survive app restarts.
"""

import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

DEFAULT_REMINDER_TIMES = [
    "07:30", "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00",
    "17:30", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00",
]

DEFAULTS = {
    "dark_mode": True,
    "sound_enabled": True,
    "daily_goal_override": None,   # None = use training plan automatically
    "reminder_times": DEFAULT_REMINDER_TIMES,
    "set_size": 10,                # push-ups per reminder/set
    "reminder_interval_minutes": 30,
}


class Settings:
    """Simple key/value settings store backed by JSON."""

    def __init__(self, filepath: str = SETTINGS_FILE):
        self.filepath = filepath
        self._data = self._load()

    def _load(self) -> dict:
        data = dict(DEFAULTS)
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                data.update(saved)
            except (json.JSONDecodeError, OSError):
                pass
        return data

    def save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    # ---------- generic accessors ----------

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        self.save()

    # ---------- convenience properties ----------

    @property
    def dark_mode(self) -> bool:
        return self._data.get("dark_mode", True)

    @dark_mode.setter
    def dark_mode(self, value: bool):
        self.set("dark_mode", value)

    @property
    def sound_enabled(self) -> bool:
        return self._data.get("sound_enabled", True)

    @sound_enabled.setter
    def sound_enabled(self, value: bool):
        self.set("sound_enabled", value)

    @property
    def daily_goal_override(self):
        return self._data.get("daily_goal_override")

    @daily_goal_override.setter
    def daily_goal_override(self, value):
        self.set("daily_goal_override", value)

    @property
    def reminder_times(self):
        return list(self._data.get("reminder_times", DEFAULT_REMINDER_TIMES))

    @reminder_times.setter
    def reminder_times(self, value):
        self.set("reminder_times", list(value))

    @property
    def set_size(self) -> int:
        return self._data.get("set_size", 10)

    @set_size.setter
    def set_size(self, value: int):
        self.set("set_size", value)
