from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class StreakUpdate:
    new_streak: int
    new_max: int
    was_broken: bool
    missed_days: int
    already_logged_today: bool


class StreakService:
    """
    Pure logic layer — no I/O, no DB.
    Stability Potion can bridge exactly 1 missed day.
    """

    MAX_BRIDGEABLE_DAYS = 1

    @staticmethod
    def compute(
        last_date: date | None,
        current_streak: int,
        current_max: int,
        today: date,
    ) -> StreakUpdate:
        if last_date is None:
            new_streak = 1
            return StreakUpdate(
                new_streak=new_streak,
                new_max=max(new_streak, current_max),
                was_broken=False,
                missed_days=0,
                already_logged_today=False,
            )

        if last_date == today:
            return StreakUpdate(
                new_streak=current_streak,
                new_max=current_max,
                was_broken=False,
                missed_days=0,
                already_logged_today=True,
            )

        missed = (today - last_date).days - 1

        if missed == 0:
            new_streak = current_streak + 1
            return StreakUpdate(
                new_streak=new_streak,
                new_max=max(new_streak, current_max),
                was_broken=False,
                missed_days=0,
                already_logged_today=False,
            )

        # Gap detected
        return StreakUpdate(
            new_streak=1,
            new_max=current_max,
            was_broken=True,
            missed_days=missed,
            already_logged_today=False,
        )

    @staticmethod
    def can_shield_protect(missed_days: int) -> bool:
        """A Stability Potion bridges at most MAX_BRIDGEABLE_DAYS of inactivity."""
        return 0 < missed_days <= StreakService.MAX_BRIDGEABLE_DAYS

    @staticmethod
    def apply_shield(
        current_streak: int,
        current_max: int,
    ) -> StreakUpdate:
        """Computes result when a Stability Potion absorbs the broken streak."""
        new_streak = current_streak + 1
        return StreakUpdate(
            new_streak=new_streak,
            new_max=max(new_streak, current_max),
            was_broken=False,
            missed_days=0,
            already_logged_today=False,
        )
