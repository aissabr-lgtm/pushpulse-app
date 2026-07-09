"""
statistics.py
-------------
Computes analytics from stored push-up history: totals, streaks, averages,
completion rate, and weekly/monthly breakdowns. Also supports CSV export.
"""

import csv
from datetime import date, timedelta
from collections import defaultdict


class Statistics:
    """Reads records from a Storage instance and derives statistics."""

    def __init__(self, storage):
        self.storage = storage

    # ---------- core numbers ----------

    def total_pushups(self) -> int:
        return sum(r["completed"] for _, r in self.storage.get_all_records_sorted())

    def total_training_days(self) -> int:
        """Days where at least one push-up was logged."""
        return sum(1 for _, r in self.storage.get_all_records_sorted() if r["completed"] > 0)

    def average_daily(self) -> float:
        records = self.storage.get_all_records_sorted()
        if not records:
            return 0.0
        total = sum(r["completed"] for _, r in records)
        return round(total / len(records), 1)

    def completion_rate(self) -> float:
        """Percentage of tracked days where the daily goal was fully met."""
        records = self.storage.get_all_records_sorted()
        if not records:
            return 0.0
        met = sum(1 for _, r in records if r["goal"] > 0 and r["completed"] >= r["goal"])
        return round(100 * met / len(records), 1)

    def current_streak(self) -> int:
        """Consecutive days (ending today or yesterday) where the goal was met."""
        history = self.storage.get_history()
        streak = 0
        day = date.today()
        # Allow today to still be "in progress" without breaking the streak count
        if history.get(day.strftime("%Y-%m-%d"), {}).get("completed", 0) < \
           history.get(day.strftime("%Y-%m-%d"), {}).get("goal", 1):
            day = day - timedelta(days=1)
        while True:
            key = day.strftime("%Y-%m-%d")
            rec = history.get(key)
            if rec and rec["goal"] > 0 and rec["completed"] >= rec["goal"]:
                streak += 1
                day -= timedelta(days=1)
            else:
                break
        return streak

    def longest_streak(self) -> int:
        records = self.storage.get_all_records_sorted()
        longest = 0
        current = 0
        prev_date = None
        for d, r in records:
            met = r["goal"] > 0 and r["completed"] >= r["goal"]
            if prev_date is not None and (d - prev_date).days == 1 and met:
                current += 1
            elif met:
                current = 1
            else:
                current = 0
            longest = max(longest, current)
            prev_date = d
        return longest

    # ---------- grouped breakdowns ----------

    def weekly_stats(self):
        """Return dict {week_start_date_str: total_pushups} for the last 8 weeks."""
        records = self.storage.get_all_records_sorted()
        weekly = defaultdict(int)
        for d, r in records:
            week_start = d - timedelta(days=d.weekday())  # Monday start
            weekly[week_start] += r["completed"]
        return dict(sorted(weekly.items()))

    def monthly_stats(self):
        """Return dict {'YYYY-MM': total_pushups}."""
        records = self.storage.get_all_records_sorted()
        monthly = defaultdict(int)
        for d, r in records:
            key = d.strftime("%Y-%m")
            monthly[key] += r["completed"]
        return dict(sorted(monthly.items()))

    # ---------- export ----------

    def export_csv(self, filepath: str):
        records = self.storage.get_all_records_sorted()
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Completed", "Goal", "Sets", "Skips", "Goal Met"])
            for d, r in records:
                met = "Yes" if r["completed"] >= r["goal"] else "No"
                writer.writerow([d.strftime("%Y-%m-%d"), r["completed"], r["goal"], r["sets"], r["skips"], met])
        return filepath
