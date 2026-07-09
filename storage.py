"""
storage.py
----------
Handles all persistent data for PushPulse:
- Daily push-up records (completed count, goal, sets, skips)
- The user's program start date (used to compute the current week)
- Reading/writing everything to a local JSON file so the app works offline

This module also contains the training plan logic (weekly goal calculation),
since the goal is intrinsically tied to the stored start date.
"""

import json
import os
from datetime import date, datetime, timedelta

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")

DATE_FMT = "%Y-%m-%d"


def today_str():
    """Return today's date as a string key, e.g. '2026-07-08'."""
    return date.today().strftime(DATE_FMT)


def parse_date(date_str):
    return datetime.strptime(date_str, DATE_FMT).date()


class TrainingPlan:
    """
    Encapsulates the progressive push-up training plan:

    Week 1 -> 80
    Week 2 -> 100
    Week 3 -> 120
    Week 4 -> 140
    Week 5+ -> +20 per week, capped at 200
    """

    BASE_WEEKS = {1: 80, 2: 100, 3: 120, 4: 140}
    MAX_GOAL = 200
    STEP = 20

    @classmethod
    def goal_for_week(cls, week_number: int) -> int:
        if week_number <= 0:
            week_number = 1
        if week_number in cls.BASE_WEEKS:
            return cls.BASE_WEEKS[week_number]
        if week_number < 1:
            return cls.BASE_WEEKS[1]
        # Week 5 onward: start from week 4's goal and add STEP per extra week
        extra_weeks = week_number - 4
        goal = cls.BASE_WEEKS[4] + extra_weeks * cls.STEP
        return min(goal, cls.MAX_GOAL)

    @staticmethod
    def week_number(start: date, today: date) -> int:
        """Week 1 = first 7 days since start_date (inclusive)."""
        delta_days = (today - start).days
        if delta_days < 0:
            delta_days = 0
        return (delta_days // 7) + 1


class Storage:
    """Reads and writes the local data.json file that stores all progress."""

    def __init__(self, filepath: str = DATA_FILE):
        self.filepath = filepath
        self._data = self._load()
        # Make sure a start date exists (first launch = day 1 of the plan)
        if "start_date" not in self._data:
            self._data["start_date"] = today_str()
            self._save()

    # ---------- low level I/O ----------

    def _load(self) -> dict:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {"start_date": today_str(), "history": {}}

    def _save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    # ---------- start date / week / goal ----------

    def get_start_date(self) -> date:
        return parse_date(self._data["start_date"])

    def get_current_week(self) -> int:
        return TrainingPlan.week_number(self.get_start_date(), date.today())

    def get_plan_goal(self) -> int:
        """The goal dictated purely by the training plan (no overrides)."""
        return TrainingPlan.goal_for_week(self.get_current_week())

    # ---------- daily records ----------

    def get_history(self) -> dict:
        return self._data.setdefault("history", {})

    def get_record(self, date_str: str = None, default_goal: int = None) -> dict:
        """Get (or create) today's record. Creates a fresh one if missing."""
        date_str = date_str or today_str()
        history = self.get_history()
        if date_str not in history:
            goal = default_goal if default_goal is not None else self.get_plan_goal()
            history[date_str] = {"completed": 0, "goal": goal, "sets": 0, "skips": 0}
            self._save()
        return history[date_str]

    def ensure_today_record(self, goal: int) -> dict:
        """Ensure today's record exists with the given goal (goal can change via settings)."""
        record = self.get_record(today_str(), default_goal=goal)
        # If the effective goal changed (e.g. user updated it in settings), reflect it
        if record["goal"] != goal:
            record["goal"] = goal
            self._save()
        return record

    def add_pushups(self, count: int, date_str: str = None) -> dict:
        record = self.get_record(date_str)
        record["completed"] = min(record["completed"] + count, max(record["goal"], record["completed"] + count))
        record["sets"] += 1
        self._save()
        return record

    def add_skip(self, date_str: str = None) -> dict:
        record = self.get_record(date_str)
        record["skips"] += 1
        self._save()
        return record

    def reset_day(self, date_str: str = None) -> dict:
        date_str = date_str or today_str()
        history = self.get_history()
        goal = history.get(date_str, {}).get("goal", self.get_plan_goal())
        history[date_str] = {"completed": 0, "goal": goal, "sets": 0, "skips": 0}
        self._save()
        return history[date_str]

    def get_all_records_sorted(self):
        """Return list of (date_obj, record) sorted chronologically."""
        history = self.get_history()
        items = [(parse_date(k), v) for k, v in history.items()]
        items.sort(key=lambda x: x[0])
        return items
