def format_duration(seconds: float) -> str:
    """Format a duration in seconds into a human-readable string.

    This function takes a duration in seconds and converts it into a formatted string
    showing days, hours, minutes, and seconds as appropriate. The function will omit
    larger units if they are zero (e.g., won't show days if the duration is less than
    24 hours).

    Args:
        seconds (float): The duration in seconds to format.

    Returns:
        str: A formatted string representation of the duration in the format:
            "{d} Days, {h} Hours, {m} Minutes, {s} Seconds" where larger units
            are omitted if zero.

    Examples:
        >>> format_duration(3665)
        '1 Hours, 1 Minutes, 5 Seconds'
        >>> format_duration(45)
        '45 Seconds'
        >>> format_duration(90000)
        '1 Days, 1 Hours, 0 Minutes, 0 Seconds'
    """
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
