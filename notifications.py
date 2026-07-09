"""
notifications.py (mobile version)
----------------------------------
Same reminder-scheduling logic as the desktop app, but driven by Kivy's
Clock instead of a background Python thread (Kivy already owns the main
loop on Android, so we hook into it instead of spawning our own thread).

IMPORTANT HONEST LIMITATION:
Reminders fire while the app is open/running in the foreground (or while
Android keeps it alive in the background, which varies by device/battery
settings). True "notify me even if the app is fully closed" behavior on
Android requires a native foreground Service or AlarmManager integration
via pyjnius — that is a separate, more advanced project beyond a single
Buildozer/Kivy app. This is the same constraint any simple Kivy/BeeWare
habit-tracker app has out of the box.
"""

from datetime import datetime, timedelta

try:
    from plyer import notification as plyer_notification
except Exception:
    plyer_notification = None

NOTIFY_TITLE = "🏋️ Time for {n} Push-ups!"
NOTIFY_BODY = "Keep going.\nSmall sets build a strong body."

GOAL_REACHED_TITLE = "🎉 Daily Goal Complete!"
GOAL_REACHED_BODY = "Amazing work! You hit today's push-up goal. Rest up, champion."


class NotificationManager:
    def __init__(self, settings, on_fire=None):
        self.settings = settings
        self.on_fire = on_fire
        self._fired_today = set()
        self._extra_reminders = []
        self._last_check_date = datetime.now().date()

    def _todays_schedule(self):
        now = datetime.now()
        times = []
        for t in self.settings.reminder_times:
            try:
                hh, mm = map(int, t.split(":"))
                times.append(now.replace(hour=hh, minute=mm, second=0, microsecond=0))
            except ValueError:
                continue
        times.extend(self._extra_reminders)
        return sorted(times)

    def get_next_reminder(self):
        now = datetime.now()
        upcoming = [t for t in self._todays_schedule() if t > now]
        return upcoming[0] if upcoming else None

    def get_countdown_seconds(self):
        nxt = self.get_next_reminder()
        if nxt is None:
            return None
        return max(0, int((nxt - datetime.now()).total_seconds()))

    def snooze_next(self, minutes=10):
        self._extra_reminders.append(datetime.now() + timedelta(minutes=minutes))

    def send_notification(self, title: str, message: str):
        if plyer_notification is not None:
            try:
                plyer_notification.notify(title=title, message=message, app_name="PushPulse", timeout=8)
            except Exception:
                pass
        if self.settings.sound_enabled:
            self._vibrate_or_beep()

    def _vibrate_or_beep(self):
        try:
            from plyer import vibrator
            vibrator.vibrate(0.3)
        except Exception:
            pass

    def notify_set_reminder(self):
        n = self.settings.set_size
        self.send_notification(NOTIFY_TITLE.format(n=n), NOTIFY_BODY)

    def notify_goal_reached(self):
        self.send_notification(GOAL_REACHED_TITLE, GOAL_REACHED_BODY)

    def check_schedule(self, *_args):
        """Call this periodically (e.g. every 15s via Clock.schedule_interval)."""
        now = datetime.now()
        if now.date() != self._last_check_date:
            self._fired_today.clear()
            self._extra_reminders.clear()
            self._last_check_date = now.date()

        current_key = now.strftime("%H:%M")
        for t in self._todays_schedule():
            key = t.strftime("%H:%M")
            if key == current_key and key not in self._fired_today:
                self._fired_today.add(key)
                self.notify_set_reminder()
                if self.on_fire:
                    try:
                        self.on_fire(key)
                    except Exception:
                        pass
