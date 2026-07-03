# ==================================================================
# BACKEND - SHARED UTILITIES
# ==================================================================

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Return current datetime player's local timezone
def local_now(tz_name: str) -> datetime:
    try:
        tz = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, KeyError):
        tz = timezone.utc
    return datetime.now(tz)
