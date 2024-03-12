# developer: Taoshidev
# Copyright © 2023 Taoshi Inc
import time
from datetime import datetime, timedelta, timezone
from typing import List, Tuple


class TimeUtil:

    @staticmethod
    def generate_start_timestamp(days: int) -> datetime:
        return datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=days)

    @staticmethod
    def convert_range_timestamps_to_millis(timestamps: List[Tuple[datetime, datetime]]) -> List[Tuple[int, int]]:
        return [(int(row[0].timestamp() * 1000), int(row[1].timestamp() * 1000)) for row in timestamps]

    @staticmethod
    def now_in_millis() -> int:
        return int(datetime.utcnow().replace(tzinfo=timezone.utc).timestamp() * 1000)

    @staticmethod
    def timestamp_to_millis(dt) -> int:
        return int(dt.timestamp() * 1000)

    @staticmethod
    def seconds_to_timestamp(seconds: int) -> datetime:
        return datetime.utcfromtimestamp(seconds).replace(tzinfo=timezone.utc)

    @staticmethod
    def millis_to_timestamp(millis: int) -> datetime:
        return datetime.utcfromtimestamp(millis / 1000).replace(tzinfo=timezone.utc)

    @staticmethod
    def minute_in_millis(minutes: int) -> int:
        return minutes * 60000

    @staticmethod
    def hours_in_millis(hours: int = 24) -> int:
        # standard is 1 day
        return 60000 * 60 * hours * 1 * 1

    @staticmethod
    def sleeper(sleeper_time, subject, logger):
        logger.debug(f"sleeper called for [{subject}]...")
        time.sleep(sleeper_time)
        logger.debug(f"sleeper done for [{subject}].")
