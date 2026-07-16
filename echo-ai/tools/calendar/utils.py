from datetime import datetime, timedelta
from typing import List, Tuple

def validate_iso_format(time_str: str) -> bool:
    """Verifies if the string is a valid ISO-8601 datetime format."""
    try:
        # Accepts 'YYYY-MM-DDTHH:MM:SS' or with offset Z/tz
        time_str = time_str.rstrip('Z')
        if '.' in time_str:
            time_str = time_str.split('.')[0]
        datetime.fromisoformat(time_str)
        return True
    except ValueError:
        return False

def find_free_slots(
    busy_ranges: List[Tuple[datetime, datetime]], 
    start: datetime, 
    end: datetime, 
    duration: timedelta
) -> List[Tuple[datetime, datetime]]:
    """
    Finds open time slots of the specified duration between start and end datetimes,
    excluding any intervals listed in busy_ranges.
    """
    free_slots = []
    # Sort busy ranges by their start time
    sorted_busy = sorted(busy_ranges, key=lambda x: x[0])
    
    current_start = start
    for busy_start, busy_end in sorted_busy:
        if busy_start > current_start:
            # Check slot size
            if busy_start - current_start >= duration:
                free_slots.append((current_start, busy_start))
        current_start = max(current_start, busy_end)
        
    if end - current_start >= duration:
        free_slots.append((current_start, end))
        
    return free_slots
