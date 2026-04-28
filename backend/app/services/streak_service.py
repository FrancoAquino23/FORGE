# ==================================================================
# STREAK SERVICE 
# ==================================================================

from dataclasses import dataclass
from datetime import date, timedelta

# Model StreakUpdate (Data)
@dataclass(frozen=True)
class StreakUpdate:
    new_streak: int
    new_max: int
    was_broken: bool
    missed_days: int
    already_logged_today: bool

# Model StreakService (Streak Logic)
class StreakService:
   
    MAX_BRIDGEABLE_DAYS = 1
    # Computes the new streak state based on last activity date and current streak info
    @staticmethod
    def compute(
        last_date: date | None,
        current_streak: int,
        current_max: int,
        today: date,
    ) -> StreakUpdate:
        # No previous activity -> start new streak
        if last_date is None:
            new_streak = 1
            return StreakUpdate(
                new_streak=new_streak,
                new_max=max(new_streak, current_max),
                was_broken=False,
                missed_days=0,
                already_logged_today=False,
            )
        # Same day -> no change
        if last_date == today:
            return StreakUpdate(
                new_streak=current_streak,
                new_max=current_max,
                was_broken=False,
                missed_days=0,
                already_logged_today=True,
            )

        missed = (today - last_date).days - 1
        # Missed 0 days -> streak continues
        if missed == 0:
            new_streak = current_streak + 1
            return StreakUpdate(
                new_streak=new_streak,
                new_max=max(new_streak, current_max),
                was_broken=False,
                missed_days=0,
                already_logged_today=False,
            )

        # Streak broken
        return StreakUpdate(
            new_streak=1,
            new_max=current_max,
            was_broken=True,
            missed_days=missed,
            already_logged_today=False,
        )

    # Determines if a Stability Potion can protect the streak based on missed days
    @staticmethod
    def can_shield_protect(missed_days: int) -> bool:
        return 0 < missed_days <= StreakService.MAX_BRIDGEABLE_DAYS

    # Applies the effect of a Stability Potion, incrementing the streak as if the break didn't happen
    @staticmethod
    def apply_shield(
        current_streak: int,
        current_max: int,
    ) -> StreakUpdate:
        new_streak = current_streak + 1
        return StreakUpdate(
            new_streak=new_streak,
            new_max=max(new_streak, current_max),
            was_broken=False,
            missed_days=0,
            already_logged_today=False,
        )
