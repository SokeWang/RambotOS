import subprocess
from mcp_instance import mcp

@mcp.tool()
def close_macos_app(app_name: str) -> str:
    """
    Closes a running macOS application using AppleScript.

    Args:
        app_name (str): The name of the application to close (e.g., 'Spotify', 'Google Chrome', 'Slack').
    """
    # AppleScript command to quit an application gracefully
    script = f'quit app "{app_name}"'
    
    try:
        # Execute the osascript command
        result = subprocess.run(
            ['osascript', '-e', script], 
            check=True, 
            capture_output=True, 
            text=True
        )
        return f"Successfully sent quit command to '{app_name}'."
    except subprocess.CalledProcessError as e:
        # If the app isn't running or doesn't exist, osascript might return an error
        error_msg = e.stderr.strip() if e.stderr else str(e)
        return f"Failed to close '{app_name}'. Error: {error_msg}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"