"""
main.py (PushPulse - Mobile / Kivy version)
--------------------------------------------
Same app as the desktop version, rebuilt with Kivy + KivyMD so it can be
packaged into an Android APK with Buildozer. Reuses the pure-Python logic
modules (storage.py, settings_data.py, statistics.py) unchanged, and
replaces the Tkinter UI with Material-style mobile widgets.
"""

import os
import random
import calendar as cal_module
from datetime import date, datetime

from kivy.lang import Builder
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Ellipse

from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout

from storage import Storage, TrainingPlan, today_str
from settings_data import Settings
from statistics import Statistics
from notifications import NotificationManager

ACCENT = (0.22, 0.52, 1, 1)   # #3884FF
GOOD = (0.29, 0.87, 0.5, 1)
BAD = (0.9, 0.28, 0.31, 1)

QUOTES = [
    "Small steps every day create big results.",
    "Consistency beats intensity.",
    "Never miss twice.",
    "Your future self will thank you.",
    "Discipline is choosing what you want most over what you want now.",
    "Every set counts. Every day matters.",
    "Strong body, strong mind.",
    "Progress, not perfection.",
]


def quote_of_the_day():
    seed = int(date.today().strftime("%Y%m%d"))
    return random.Random(seed).choice(QUOTES)


KV = """
MDBottomNavigation:
    panel_color: 0.1, 0.11, 0.14, 1
    text_color_normal: 0.6, 0.63, 0.68, 1
    text_color_active: app.accent_hex

    MDBottomNavigationItem:
        name: "home"
        text: "Home"
        icon: "home"
        ScrollView:
            MDBoxLayout:
                id: home_container
                orientation: "vertical"
                adaptive_height: True
                padding: dp(16)
                spacing: dp(12)

    MDBottomNavigationItem:
        name: "stats"
        text: "Stats"
        icon: "chart-bar"
        ScrollView:
            MDBoxLayout:
                id: stats_container
                orientation: "vertical"
                adaptive_height: True
                padding: dp(16)
                spacing: dp(12)

    MDBottomNavigationItem:
        name: "calendar"
        text: "Calendar"
        icon: "calendar-month"
        ScrollView:
            MDBoxLayout:
                id: calendar_container
                orientation: "vertical"
                adaptive_height: True
                padding: dp(16)
                spacing: dp(12)

    MDBottomNavigationItem:
        name: "settings"
        text: "Settings"
        icon: "cog"
        ScrollView:
            MDBoxLayout:
                id: settings_container
                orientation: "vertical"
                adaptive_height: True
                padding: dp(16)
                spacing: dp(12)
"""


class StatCard(MDCard):
    def __init__(self, title, value, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(14)
        self.size_hint_y = None
        self.height = dp(90)
        self.radius = [18, 18, 18, 18]
        self.md_bg_color = (0.11, 0.12, 0.14, 1)
        self.add_widget(MDLabel(text=title, font_style="Caption", theme_text_color="Secondary",
                                 size_hint_y=None, height=dp(18)))
        self.value_label = MDLabel(text=str(value), font_style="H5", bold=True,
                                    size_hint_y=None, height=dp(36))
        self.add_widget(self.value_label)


class PushPulseApp(MDApp):
    accent_hex = ACCENT

    def build(self):
        self.title = "PushPulse"
        data_dir = self.user_data_dir  # guaranteed writable on Android + desktop
        self.storage = Storage(os.path.join(data_dir, "data.json"))
        self.settings_data = Settings(os.path.join(data_dir, "settings.json"))
        self.stats = Statistics(self.storage)
        self.notifier = NotificationManager(self.settings_data, on_fire=self._on_reminder_fired)

        self.theme_cls.theme_style = "Dark" if self.settings_data.dark_mode else "Light"
        self.theme_cls.primary_palette = "Blue"

        self.root_widget = Builder.load_string(KV)

        Clock.schedule_interval(self.notifier.check_schedule, 15)
        Clock.schedule_interval(self._tick_countdown, 1)

        self.build_home()
        self.build_statistics()
        self.build_calendar()
        self.build_settings()
        return self.root_widget

    # ------------------------------------------------------------------
    # HOME
    # ------------------------------------------------------------------

    def _effective_goal(self):
        override = self.settings_data.daily_goal_override
        return override if override else self.storage.get_plan_goal()

    def build_home(self):
        container = self.root_widget.ids.home_container
        container.clear_widgets()

        goal = self._effective_goal()
        record = self.storage.ensure_today_record(goal)
        remaining = max(0, record["goal"] - record["completed"])

        container.add_widget(MDLabel(text="Today's Push-up Goal", font_style="H5", bold=True,
                                      size_hint_y=None, height=dp(36)))
        container.add_widget(MDLabel(text=f'"{quote_of_the_day()}"', font_style="Caption",
                                      theme_text_color="Secondary", italic=True,
                                      size_hint_y=None, height=dp(20)))

        stat_row = MDBoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(90))
        stat_row.add_widget(StatCard("Completed", record["completed"]))
        stat_row.add_widget(StatCard("Remaining", remaining))
        stat_row.add_widget(StatCard("Current Week", f"Wk {self.storage.get_current_week()}"))
        container.add_widget(stat_row)

        # Progress card
        progress_card = MDCard(orientation="vertical", padding=dp(16), spacing=dp(8),
                                size_hint_y=None, height=dp(90), radius=[18, 18, 18, 18],
                                md_bg_color=(0.11, 0.12, 0.14, 1))
        progress_card.add_widget(MDLabel(text=f"Daily Progress · {record['completed']}/{record['goal']}",
                                          bold=True, size_hint_y=None, height=dp(24)))
        self.progress_bar = MDProgressBar(value=0, max=100, size_hint_y=None, height=dp(14))
        progress_card.add_widget(self.progress_bar)
        container.add_widget(progress_card)
        pct = 0 if record["goal"] == 0 else min(100, 100 * record["completed"] / record["goal"])
        Animation(value=pct, duration=0.6, t="out_cubic").start(self.progress_bar)

        # Countdown card
        countdown_card = MDCard(orientation="vertical", padding=dp(14), size_hint_y=None,
                                 height=dp(74), radius=[18, 18, 18, 18], md_bg_color=(0.11, 0.12, 0.14, 1))
        countdown_card.add_widget(MDLabel(text="Next Reminder", font_style="Caption",
                                           theme_text_color="Secondary", size_hint_y=None, height=dp(18)))
        self.countdown_label = MDLabel(text="--:--:--", font_style="H6", bold=True,
                                        size_hint_y=None, height=dp(30))
        countdown_card.add_widget(self.countdown_label)
        container.add_widget(countdown_card)

        # Schedule chips
        sched_card = MDCard(orientation="vertical", padding=dp(14), size_hint_y=None,
                             height=dp(110), radius=[18, 18, 18, 18], md_bg_color=(0.11, 0.12, 0.14, 1))
        sched_card.add_widget(MDLabel(text="Today's Schedule", font_style="Caption",
                                       theme_text_color="Secondary", size_hint_y=None, height=dp(18)))
        grid = GridLayout(cols=4, spacing=dp(4), size_hint_y=None, height=dp(80))
        now_str = datetime.now().strftime("%H:%M")
        for t in self.settings_data.reminder_times:
            passed = t <= now_str
            lbl = MDLabel(text=t, font_style="Caption", halign="center",
                          theme_text_color="Secondary" if passed else "Primary")
            grid.add_widget(lbl)
        sched_card.add_widget(grid)
        container.add_widget(sched_card)

        # Action buttons
        btn_row = MDBoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(48))
        complete_btn = MDRaisedButton(text=f"Complete Set (+{self.settings_data.set_size})",
                                       md_bg_color=ACCENT, size_hint_x=1)
        complete_btn.bind(on_release=lambda *_: self.complete_set())
        skip_btn = MDFlatButton(text="Skip", size_hint_x=0.5)
        skip_btn.bind(on_release=lambda *_: self.skip_reminder())
        reset_btn = MDFlatButton(text="Reset", size_hint_x=0.5, theme_text_color="Custom",
                                  text_color=BAD)
        reset_btn.bind(on_release=lambda *_: self.reset_today())
        btn_row.add_widget(complete_btn)
        btn_row.add_widget(skip_btn)
        btn_row.add_widget(reset_btn)
        container.add_widget(btn_row)

        container.add_widget(MDLabel(text=f"Current streak: {self.stats.current_streak()} days",
                                      font_style="Caption", theme_text_color="Secondary",
                                      size_hint_y=None, height=dp(20)))

    def complete_set(self):
        goal = self._effective_goal()
        record = self.storage.ensure_today_record(goal)
        already_done = record["completed"] >= record["goal"]
        self.storage.add_pushups(self.settings_data.set_size)
        self.stats = Statistics(self.storage)

        updated = self.storage.get_record()
        if not already_done and updated["completed"] >= updated["goal"]:
            self.notifier.notify_goal_reached()
            self._show_confetti()
            self._show_dialog("Goal Complete! 🎉",
                               "Amazing work! You hit today's push-up goal.\nRest up, champion.")
        self.build_home()

    def skip_reminder(self):
        self.storage.add_skip()
        self.notifier.snooze_next(10)
        self._show_dialog("Reminder Postponed", "No problem — next reminder pushed back by 10 minutes.")
        self.build_home()

    def reset_today(self):
        self.storage.reset_day()
        self.build_home()

    def _on_reminder_fired(self, time_str):
        pass

    def _tick_countdown(self, *_args):
        if hasattr(self, "countdown_label"):
            seconds = self.notifier.get_countdown_seconds()
            if seconds is None:
                self.countdown_label.text = "No more today"
            else:
                h, rem = divmod(seconds, 3600)
                m, s = divmod(rem, 60)
                self.countdown_label.text = f"{h:02d}:{m:02d}:{s:02d}"

    def _show_dialog(self, title, text):
        dialog = MDDialog(title=title, text=text,
                           buttons=[MDFlatButton(text="OK", on_release=lambda *a: dialog.dismiss())])
        dialog.open()

    def _show_confetti(self):
        overlay = FloatLayout()
        colors = [(0.22, 0.52, 1, 1), (1, 0.77, 0.24, 1), (1, 0.36, 0.48, 1),
                  (0.29, 0.87, 0.5, 1), (0.69, 0.52, 0.96, 1)]
        particles = []
        for _ in range(40):
            x = random.uniform(0, 1)
            y = random.uniform(0.6, 1.0)
            size = random.uniform(dp(6), dp(12))
            color_val = random.choice(colors)
            with overlay.canvas:
                Color(*color_val)
                ellipse = Ellipse(pos=(x * overlay.width, y * overlay.height), size=(size, size))
            particles.append(ellipse)
        self.root_widget.add_widget(overlay)

        def fall(dt):
            still_falling = False
            for ellipse in particles:
                px, py = ellipse.pos
                new_y = py - dp(6)
                if new_y > -dp(20):
                    still_falling = True
                ellipse.pos = (px + random.uniform(-2, 2), new_y)
            if not still_falling:
                self.root_widget.remove_widget(overlay)
                return False

        Clock.schedule_interval(fall, 1 / 30)
        Clock.schedule_once(lambda dt: self.root_widget.remove_widget(overlay)
                             if overlay.parent else None, 3)

    # ------------------------------------------------------------------
    # STATISTICS
    # ------------------------------------------------------------------

    def build_statistics(self):
        container = self.root_widget.ids.stats_container
        container.clear_widgets()
        self.stats = Statistics(self.storage)

        container.add_widget(MDLabel(text="Statistics", font_style="H5", bold=True,
                                      size_hint_y=None, height=dp(36)))

        data = [
            ("Total Push-ups", self.stats.total_pushups()),
            ("Total Training Days", self.stats.total_training_days()),
            ("Current Streak", f"{self.stats.current_streak()} d"),
            ("Longest Streak", f"{self.stats.longest_streak()} d"),
            ("Average Daily", self.stats.average_daily()),
            ("Completion Rate", f"{self.stats.completion_rate()}%"),
        ]
        for i in range(0, len(data), 2):
            row = MDBoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(90))
            for title, value in data[i:i + 2]:
                row.add_widget(StatCard(title, value))
            container.add_widget(row)

        export_btn = MDRaisedButton(text="Export Statistics to CSV", md_bg_color=ACCENT,
                                     size_hint_y=None, height=dp(48))
        export_btn.bind(on_release=lambda *_: self._export_csv())
        container.add_widget(export_btn)

    def _export_csv(self):
        export_dir = os.path.join(self.user_data_dir, "exports")
        os.makedirs(export_dir, exist_ok=True)
        filepath = os.path.join(export_dir, f"pushpulse_stats_{today_str()}.csv")
        self.stats.export_csv(filepath)
        self._show_dialog("Export Complete", f"Saved to:\n{filepath}")

    # ------------------------------------------------------------------
    # CALENDAR
    # ------------------------------------------------------------------

    def build_calendar(self):
        container = self.root_widget.ids.calendar_container
        container.clear_widgets()
        today = date.today()

        container.add_widget(MDLabel(text=today.strftime("%B %Y"), font_style="H5", bold=True,
                                      size_hint_y=None, height=dp(36)))

        grid = GridLayout(cols=7, spacing=dp(4), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        for day_name in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            grid.add_widget(MDLabel(text=day_name, font_style="Caption", halign="center",
                                     theme_text_color="Secondary", size_hint_y=None, height=dp(20)))

        history = self.storage.get_history()
        month_days = cal_module.monthcalendar(today.year, today.month)
        for week in month_days:
            for day_num in week:
                if day_num == 0:
                    grid.add_widget(MDBoxLayout(size_hint_y=None, height=dp(56)))
                    continue
                d = date(today.year, today.month, day_num)
                key = d.strftime("%Y-%m-%d")
                rec = history.get(key)
                if rec and rec["goal"] > 0 and rec["completed"] >= rec["goal"]:
                    bg = ACCENT
                elif rec and rec["completed"] > 0:
                    bg = (0.16, 0.2, 0.32, 1)
                else:
                    bg = (0.13, 0.14, 0.16, 1)
                cell = MDCard(orientation="vertical", size_hint_y=None, height=dp(56),
                              radius=[10, 10, 10, 10], md_bg_color=bg, padding=dp(4))
                cell.add_widget(MDLabel(text=str(day_num), font_style="Caption", bold=True,
                                         halign="center", size_hint_y=None, height=dp(18)))
                if rec:
                    cell.add_widget(MDLabel(text=f"{rec['completed']}/{rec['goal']}",
                                             font_style="Caption", halign="center",
                                             size_hint_y=None, height=dp(14)))
                grid.add_widget(cell)
        container.add_widget(grid)

    # ------------------------------------------------------------------
    # SETTINGS
    # ------------------------------------------------------------------

    def build_settings(self):
        container = self.root_widget.ids.settings_container
        container.clear_widgets()

        container.add_widget(MDLabel(text="Settings", font_style="H5", bold=True,
                                      size_hint_y=None, height=dp(36)))

        # Dark mode switch
        row1 = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(48))
        row1.add_widget(MDLabel(text="Dark Mode"))
        dark_switch = MDSwitch(size_hint_x=None, width=dp(60))
        dark_switch.bind(active=lambda inst, val: self._toggle_dark_mode(val))
        row1.add_widget(dark_switch)
        container.add_widget(row1)
        Clock.schedule_once(lambda dt: setattr(dark_switch, "active", self.settings_data.dark_mode))

        # Sound switch
        row2 = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(48))
        row2.add_widget(MDLabel(text="Notification Sound / Vibration"))
        sound_switch = MDSwitch(size_hint_x=None, width=dp(60))
        sound_switch.bind(active=lambda inst, val: self._toggle_sound(val))
        row2.add_widget(sound_switch)
        container.add_widget(row2)
        Clock.schedule_once(lambda dt: setattr(sound_switch, "active", self.settings_data.sound_enabled))

        # Daily goal override
        goal_field = MDTextField(hint_text="Custom Daily Goal (blank = auto plan)",
                                  text=str(self.settings_data.daily_goal_override or ""),
                                  input_filter="int", size_hint_y=None, height=dp(48))
        goal_field.bind(on_text_validate=lambda inst: self._save_goal_override(inst.text))
        goal_field.bind(focus=lambda inst, focused: None if focused else self._save_goal_override(inst.text))
        container.add_widget(goal_field)

        # Set size
        set_field = MDTextField(hint_text="Push-ups per Set",
                                 text=str(self.settings_data.set_size),
                                 input_filter="int", size_hint_y=None, height=dp(48))
        set_field.bind(focus=lambda inst, focused: None if focused else self._save_set_size(inst.text))
        container.add_widget(set_field)

        # Reminder times
        times_field = MDTextField(hint_text="Reminder Times (comma-separated, HH:MM)",
                                   text=", ".join(self.settings_data.reminder_times),
                                   multiline=True, size_hint_y=None, height=dp(90))
        container.add_widget(times_field)

        save_btn = MDRaisedButton(text="Save Reminder Times", md_bg_color=ACCENT,
                                   size_hint_y=None, height=dp(48))
        save_btn.bind(on_release=lambda *_: self._save_reminder_times(times_field.text))
        container.add_widget(save_btn)

    def _toggle_dark_mode(self, value):
        self.settings_data.dark_mode = bool(value)
        self.theme_cls.theme_style = "Dark" if value else "Light"

    def _toggle_sound(self, value):
        self.settings_data.sound_enabled = bool(value)

    def _save_goal_override(self, value):
        value = (value or "").strip()
        if value == "":
            self.settings_data.daily_goal_override = None
        elif value.isdigit():
            self.settings_data.daily_goal_override = int(value)
        self.build_home()

    def _save_set_size(self, value):
        value = (value or "").strip()
        if value.isdigit() and int(value) > 0:
            self.settings_data.set_size = int(value)
        self.build_home()

    def _save_reminder_times(self, raw_text):
        parts = [p.strip() for p in raw_text.replace("\n", ",").split(",") if p.strip()]
        valid = []
        for p in parts:
            try:
                hh, mm = map(int, p.split(":"))
                if 0 <= hh <= 23 and 0 <= mm <= 59:
                    valid.append(f"{hh:02d}:{mm:02d}")
            except ValueError:
                continue
        if valid:
            self.settings_data.reminder_times = sorted(set(valid))
            self._show_dialog("Saved", "Reminder times updated.")
            self.build_home()


if __name__ == "__main__":
    PushPulseApp().run()
