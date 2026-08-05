"""
Schedule definition, validation and next-run calculation.

A schedule is a plain dict stored per source in sources.json:

    "schedule": {
        "enabled": true,
        "trigger": "cron",        # "cron", "usb_mount" or "cron,usb_mount"
        "frequency": "daily",     # hourly | daily | weekly | monthly
        "time": "03:00",          # HH:MM, ignored for hourly
        "minute": 0,              # hourly only
        "weekday": 0,             # weekly only, 0=Monday .. 6=Sunday
        "day": 1,                 # monthly only, 1..28
        "max_duration": 3600
    }

Sources without a schedule fall back to the global default stored in the
settings table under 'schedule.default'.
"""
from calendar import monthrange
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

DEFAULT_SCHEDULE_KEY = 'schedule.default'

FREQUENCIES = ('hourly', 'daily', 'weekly', 'monthly')

# Monthly schedules are capped at 28 so every month has the day.
MAX_MONTH_DAY = 28

BUILTIN_DEFAULT = {
    'enabled': False,
    'trigger': 'cron',
    'frequency': 'daily',
    'time': '03:00',
    'minute': 0,
    'weekday': 0,
    'day': 1,
}


def _coerce_int(value, fallback, minimum, maximum):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return fallback
    if number < minimum or number > maximum:
        return fallback
    return number


def _parse_time(value, fallback='03:00'):
    """Parse 'HH:MM' into (hour, minute), falling back on malformed input."""
    if not isinstance(value, str):
        value = fallback
    parts = value.split(':')
    if len(parts) != 2:
        parts = fallback.split(':')
    hour = _coerce_int(parts[0], 3, 0, 23)
    minute = _coerce_int(parts[1], 0, 0, 59)
    return hour, minute


def normalize_schedule(raw):
    """Return a complete, valid schedule dict from partial/legacy input.

    Legacy configs used {"trigger": "usb_mount", "max_duration": 3600} with no
    time fields at all — those stay usb-only and are not time-scheduled.
    """
    schedule = dict(BUILTIN_DEFAULT)

    if not isinstance(raw, dict):
        return schedule

    trigger = raw.get('trigger', 'cron')
    if not isinstance(trigger, str) or not trigger.strip():
        trigger = 'cron'
    triggers = [t.strip() for t in trigger.split(',') if t.strip()]
    if not triggers:
        triggers = ['cron']
    schedule['trigger'] = ','.join(triggers)

    frequency = raw.get('frequency')
    if frequency in FREQUENCIES:
        schedule['frequency'] = frequency

    hour, minute = _parse_time(raw.get('time'), BUILTIN_DEFAULT['time'])
    schedule['time'] = f'{hour:02d}:{minute:02d}'
    schedule['minute'] = _coerce_int(raw.get('minute'), 0, 0, 59)
    schedule['weekday'] = _coerce_int(raw.get('weekday'), 0, 0, 6)
    schedule['day'] = _coerce_int(raw.get('day'), 1, 1, MAX_MONTH_DAY)

    # A legacy usb_mount-only block has no time scheduling intent.
    has_time_fields = any(
        key in raw for key in ('frequency', 'time', 'minute', 'weekday', 'day')
    )
    if 'enabled' in raw:
        schedule['enabled'] = bool(raw.get('enabled'))
    else:
        schedule['enabled'] = has_time_fields and 'cron' in triggers

    if 'max_duration' in raw:
        schedule['max_duration'] = _coerce_int(raw.get('max_duration'), 3600, 1, 86400)

    return schedule


def validate_schedule(raw):
    """Validate user-supplied schedule input.

    Returns (schedule, error). Unlike normalize_schedule this rejects bad
    values instead of silently substituting defaults, so the UI can show a
    real message rather than saving something the user did not intend.
    """
    if raw is None:
        return None, None
    if not isinstance(raw, dict):
        return None, 'Schedule must be an object'

    frequency = raw.get('frequency', 'daily')
    if frequency not in FREQUENCIES:
        return None, f"Invalid frequency. Use one of: {', '.join(FREQUENCIES)}"

    time_value = raw.get('time', '03:00')
    if frequency != 'hourly':
        if not isinstance(time_value, str) or ':' not in time_value:
            return None, 'Time must be in HH:MM format'
        parts = time_value.split(':')
        try:
            hour = int(parts[0])
            minute = int(parts[1])
        except (ValueError, IndexError):
            return None, 'Time must be in HH:MM format'
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return None, 'Time must be between 00:00 and 23:59'

    if frequency == 'hourly':
        minute = raw.get('minute', 0)
        try:
            minute = int(minute)
        except (TypeError, ValueError):
            return None, 'Minute must be a number'
        if not 0 <= minute <= 59:
            return None, 'Minute must be between 0 and 59'

    if frequency == 'weekly':
        weekday = raw.get('weekday', 0)
        try:
            weekday = int(weekday)
        except (TypeError, ValueError):
            return None, 'Weekday must be a number'
        if not 0 <= weekday <= 6:
            return None, 'Weekday must be between 0 (Monday) and 6 (Sunday)'

    if frequency == 'monthly':
        day = raw.get('day', 1)
        try:
            day = int(day)
        except (TypeError, ValueError):
            return None, 'Day must be a number'
        if not 1 <= day <= MAX_MONTH_DAY:
            return None, f'Day must be between 1 and {MAX_MONTH_DAY}'

    return normalize_schedule(raw), None


def next_run_after(schedule, after):
    """Return the next datetime this schedule should fire, strictly after `after`.

    Returns None if the schedule is disabled or has no time-based trigger.
    """
    schedule = normalize_schedule(schedule)

    if not schedule.get('enabled'):
        return None
    if 'cron' not in schedule.get('trigger', ''):
        return None

    frequency = schedule['frequency']
    hour, minute = _parse_time(schedule['time'])

    if frequency == 'hourly':
        target_minute = schedule['minute']
        candidate = after.replace(minute=target_minute, second=0, microsecond=0)
        if candidate <= after:
            candidate += timedelta(hours=1)
        return candidate

    if frequency == 'daily':
        candidate = after.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= after:
            candidate += timedelta(days=1)
        return candidate

    if frequency == 'weekly':
        target_weekday = schedule['weekday']
        candidate = after.replace(hour=hour, minute=minute, second=0, microsecond=0)
        days_ahead = (target_weekday - candidate.weekday()) % 7
        candidate += timedelta(days=days_ahead)
        if candidate <= after:
            candidate += timedelta(days=7)
        return candidate

    if frequency == 'monthly':
        target_day = min(schedule['day'], MAX_MONTH_DAY)
        candidate = after.replace(
            day=target_day, hour=hour, minute=minute, second=0, microsecond=0
        )
        if candidate <= after:
            # Roll into the following month without overshooting short months.
            year = candidate.year + (1 if candidate.month == 12 else 0)
            month = 1 if candidate.month == 12 else candidate.month + 1
            day = min(target_day, monthrange(year, month)[1])
            candidate = candidate.replace(year=year, month=month, day=day)
        return candidate

    return None


def describe_schedule(schedule):
    """Short human-readable summary, used for logging."""
    schedule = normalize_schedule(schedule)
    if not schedule.get('enabled'):
        return 'disabled'

    frequency = schedule['frequency']
    if frequency == 'hourly':
        return f"hourly at :{schedule['minute']:02d}"
    if frequency == 'daily':
        return f"daily at {schedule['time']}"
    if frequency == 'weekly':
        names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        return f"weekly on {names[schedule['weekday']]} at {schedule['time']}"
    if frequency == 'monthly':
        return f"monthly on day {schedule['day']} at {schedule['time']}"
    return frequency


def get_default_schedule():
    """Read the global default schedule from the settings table."""
    from app.models.backup import Setting

    raw = Setting.get(DEFAULT_SCHEDULE_KEY)
    if not raw:
        return dict(BUILTIN_DEFAULT)
    try:
        return normalize_schedule(json.loads(raw))
    except (ValueError, TypeError):
        logger.warning('Invalid default schedule in settings, using built-in default')
        return dict(BUILTIN_DEFAULT)


def set_default_schedule(schedule):
    """Persist the global default schedule."""
    from app.models.backup import Setting

    normalized = normalize_schedule(schedule)
    Setting.set(DEFAULT_SCHEDULE_KEY, json.dumps(normalized))
    return normalized


def resolve_schedule(source, default_schedule=None):
    """Return the effective schedule for a source.

    A source without its own schedule inherits the global default.
    """
    raw = source.get('schedule')
    if raw is None:
        if default_schedule is None:
            default_schedule = get_default_schedule()
        return normalize_schedule(default_schedule)
    return normalize_schedule(raw)
