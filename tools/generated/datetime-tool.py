from datetime import datetime
import pytz
from mcp_instance import mcp

@mcp.tool()
def get_current_time(timezone: str = "UTC") -> str:
    """
    Provides the current time with precision (including seconds) for a specified timezone.
    
    Args:
        timezone (str): The IANA timezone string (e.g., 'America/New_York', 'Europe/London', 'UTC'). Defaults to 'UTC'.
    
    Returns:
        str: A formatted string containing the current date and time, or an error message if the timezone is invalid.
    """
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        return f"Current time in {timezone}: {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"
    except pytz.exceptions.UnknownTimeZoneError:
        return f"Error: Unknown timezone '{timezone}'. Please use a valid IANA timezone name."
    except Exception as e:
        return f"Error: {str(e)}"