import zoneinfo
from zoneinfo import ZoneInfo
from datetime import datetime
import re
from typing import List
import time


class TimeType:
    RELATIVE = 0
    ABSOLUTE = 1

    def __str__(self):
        if self == TimeType.RELATIVE:
            return "RELATIVE"
        elif self == TimeType.ABSOLUTE:
            return "ABSOLUTE"
        else:
            return "UNKNOWN"


class OffsetType:
    SECONDS = 0
    MINUTES = 1
    HOURS = 2
    DAYS = 3
    MONTHS = 4
    YEARS = 5


class Time:
    original_time: str
    unix_time: str
    ttype: TimeType

    def __init__(self, original_time: str, unix_time: str, ttype: TimeType):
        self.original_time = original_time
        self.unix_time = unix_time
        self.ttype = ttype

    def __repr__(self):
        ttype = self.ttype
        ttype_str = ""
        if ttype == TimeType.RELATIVE:
            ttype_str = "RELATIVE"
        elif ttype == TimeType.ABSOLUTE:
            ttype_str = "ABSOLUTE"
        else:
            ttype_str = "UNKNOWN"
        return f"<Time {self.original_time} at {self.unix_time} of type {ttype_str}>"


def get_offset_type(unit: str) -> OffsetType:
    if unit == "seconds" or unit == "secs":
        return OffsetType.SECONDS
    elif unit == "minutes" or unit == "mins":
        return OffsetType.MINUTES
    elif unit == "hours" or unit == "hrs":
        return OffsetType.HOURS
    elif unit == "days":
        return OffsetType.DAYS
    elif unit == "months":
        return OffsetType.MONTHS
    elif unit == "years" or unit == "yrs":
        return OffsetType.YEARS


def parse_relative_group(relative_group: str) -> str:
    offset, unit = relative_group.split(" ")
    offset_type = get_offset_type(unit)
    current_time = int(time.time())
    final_time = 0
    if offset_type == OffsetType.SECONDS:
        final_time = current_time + int(offset)
    elif offset_type == OffsetType.MINUTES:
        final_time = current_time + int(offset) * 60
    elif offset_type == OffsetType.HOURS:
        final_time = current_time + int(offset) * 60 * 60
    elif offset_type == OffsetType.DAYS:
        final_time = current_time + int(offset) * 60 * 60 * 24
    elif offset_type == OffsetType.MONTHS:
        final_time = current_time + int(offset) * 60 * 60 * 24 * 30
    elif offset_type == OffsetType.YEARS:
        final_time = current_time + int(offset) * 60 * 60 * 24 * 365
    return f"<t:{final_time}>"


def parse_absolute_group(absolute_group: str, user_timezone: str) -> str:
    # Expected format: "5:00 PM"
    if user_timezone not in zoneinfo.available_timezones():
        raise ValueError(f"Invalid timezone {user_timezone}")

    tz = ZoneInfo(user_timezone)

    today = datetime.now(tz).date()
    dt = datetime.strptime(f"{today} {absolute_group}", "%Y-%m-%d %I:%M %p")
    dt = dt.replace(tzinfo=tz)

    return f"<t:{int(dt.timestamp())}>"


def parse_message(message: str, user_timezone: str) -> List[Time]:
    groups: List[Time] = []
    relative_groups = re.findall(r"`(\d+ \w+)`", message)
    for relative_group in relative_groups:
        unix_time = parse_relative_group(relative_group)
        timezone = Time(relative_group, unix_time, TimeType.RELATIVE)
        groups.append(timezone)
    absolute_groups = re.findall(r"`(\d?\d:\d\d \w+)`", message)
    for absolute_group in absolute_groups:
        unix_time = parse_absolute_group(absolute_group, user_timezone)
        timezone = Time(absolute_group, unix_time, TimeType.ABSOLUTE)
        groups.append(timezone)

    return groups
