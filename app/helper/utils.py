def format_duration(seconds: float) -> str:
    """Format seconds into human readable duration."""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    if days == 0:
        if hours == 0:
            if minutes == 0:
                return f"{int(seconds)} Seconds"
            return f"{int(minutes)} Minutes, {int(seconds)} Seconds"
        return f"{int(hours)} Hours, {int(minutes)} Minutes, {int(seconds)} Seconds"
    return f"{int(days)} Days, {int(hours)} Hours, {int(minutes)} Minutes, {int(seconds)} Seconds"
