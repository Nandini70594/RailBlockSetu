from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import List

from app.models.train import TrainSchedule


@dataclass(frozen=True)
class TrainInterval:
    start_minute: int
    end_minute: int
    section_id: int
    priority_level: int
    train_number: str

    @property
    def is_hard(self) -> bool:
        return self.priority_level <= 2


def build_train_intervals(
    trains: List[TrainSchedule],
    base_time: datetime,
    horizon_minutes: int,
    buffer_minutes: int,
) -> List[TrainInterval]:
    """Convert each daily HH:MM traversal into buffered solver-minute intervals."""
    horizon_end = base_time + timedelta(minutes=horizon_minutes)
    intervals: List[TrainInterval] = []

    for train in trains:
        if train.section_id is None or train.current_status in {"CANCELLED", "DIVERTED"}:
            continue

        entry = time.fromisoformat(train.scheduled_entry_time)
        exit_time = time.fromisoformat(train.scheduled_exit_time)
        entry_offset = entry.hour * 60 + entry.minute
        exit_offset = exit_time.hour * 60 + exit_time.minute
        if exit_offset <= entry_offset:
            exit_offset += 24 * 60

        # Scheduler and timetable datetimes are naive IST wall times throughout.
        first_day = base_time.date() - timedelta(days=1)
        last_day = horizon_end.date()
        train_day = first_day
        while train_day <= last_day:
            train_start = datetime.combine(train_day, time.min) + timedelta(
                minutes=entry_offset - buffer_minutes
            )
            train_end = datetime.combine(train_day, time.min) + timedelta(
                minutes=exit_offset + buffer_minutes
            )
            start_minute = max(
                0, int((train_start - base_time).total_seconds() // 60)
            )
            end_minute = min(
                horizon_minutes,
                int((train_end - base_time).total_seconds() // 60),
            )
            if start_minute < end_minute:
                intervals.append(
                    TrainInterval(
                        start_minute=start_minute,
                        end_minute=end_minute,
                        section_id=train.section_id,
                        priority_level=train.priority_level,
                        train_number=train.train_number,
                    )
                )
            train_day += timedelta(days=1)

    return intervals


def has_train_free_gap(
    earliest_minute: int,
    latest_minute: int,
    duration_minutes: int,
    train_intervals: List[TrainInterval],
) -> bool:
    """Return whether a task fits in the available range outside protected trains."""
    cursor = earliest_minute
    for interval in sorted(train_intervals, key=lambda item: item.start_minute):
        if interval.end_minute <= cursor:
            continue
        if interval.start_minute - cursor >= duration_minutes:
            return True
        cursor = max(cursor, interval.end_minute)
        if cursor + duration_minutes > latest_minute:
            return False
    return cursor + duration_minutes <= latest_minute
