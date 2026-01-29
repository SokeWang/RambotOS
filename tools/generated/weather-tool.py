import httpx
from mcp_instance import mcp

async def _fetch_weather_data(location: str):
    """Helper to fetch JSON data from wttr.in"""
    url = f"https://wttr.in/{location}?format=j1"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def get_current_weather(location: str):
    """
    Get current weather information for a specific location using wttr.in.
    
    Args:
        location (str): The city or location name (e.g., 'London', 'Tokyo', 'New York').
    """
    try:
        data = await _fetch_weather_data(location)
        
        area = data['nearest_area'][0]['areaName'][0]['value']
        country = data['nearest_area'][0]['country'][0]['value']
        current = data['current_condition'][0]
        
        temp_c = current['temp_C']
        temp_f = current['temp_F']
        desc = current['weatherDesc'][0]['value']
        humidity = current['humidity']
        wind = current['windspeedKmph']
        
        return (
            f"Current weather for {area}, {country}:\n"
            f"- Condition: {desc}\n"
            f"- Temperature: {temp_c} C ({temp_f} F)\n"
            f"- Humidity: {humidity}%\n"
            f"- Wind Speed: {wind} km/h"
        )
    except httpx.HTTPStatusError as e:
        return f"Error: Could not find weather for '{location}'. (Status: {e.response.status_code})"
    except Exception as e:
        return f"Error fetching weather data: {str(e)}"

@mcp.tool()
async def get_forecast(location: str, days: int = 5, include_morning: bool = True):
    """
    Get a multi-day weather forecast for a specific location.
    
    Args:
        location (str): The city or location name.
        days (int): Number of forecast days to return (default 5, wttr.in typically provides up to 3).
        include_morning (bool): Whether to include morning-specific forecast details.
    """
    try:
        data = await _fetch_weather_data(location)
        
        area = data['nearest_area'][0]['areaName'][0]['value']
        country = data['nearest_area'][0]['country'][0]['value']
        
        available_days = data.get('weather', [])
        requested_days = min(days, len(available_days))
        
        forecast_str = f"Weather forecast for {area}, {country} ({requested_days} days available):\n"
        
        for i in range(requested_days):
            day_data = available_days[i]
            date = day_data['date']
            max_c = day_data['maxtempC']
            min_c = day_data['mintempC']
            
            hourly = day_data.get('hourly', [])
            # Hourly mapping for j1: 0=00, 1=03, 2=06, 3=09, 4=12, 5=15, 6=18, 7=21
            mid_day = hourly[4] if len(hourly) > 4 else (hourly[0] if hourly else {})
            
            cond = mid_day.get('weatherDesc', [{}])[0].get('value', 'N/A')
            hum = mid_day.get('humidity', 'N/A')
            
            day_str = (
                f"\n[{date}]\n"
                f"  Condition: {cond}\n"
                f"  Temp Range: {min_c} C to {max_c} C\n"
                f"  Humidity: {hum}% (mid-day)"
            )
            
            if include_morning and len(hourly) > 3:
                morning = hourly[3] # 09:00 slot
                m_cond = morning.get('weatherDesc', [{}])[0].get('value', 'N/A')
                m_temp = morning.get('tempC', 'N/A')
                day_str += f"\n  Morning (09:00): {m_cond}, {m_temp} C"
                
            forecast_str += day_str
        
        return forecast_str
                
    except httpx.HTTPStatusError as e:
        return f"Error: Could not find forecast for '{location}'. (Status: {e.response.status_code})"
    except Exception as e:
        return f"Error fetching forecast data: {str(e)}"

@mcp.tool()
async def get_weather(location: str, days: int = 0, forecast: bool = False, date: str = None):
    """
    Unified weather tool: get current weather or forecast.
    
    Args:
        location (str): The city or location name.
        days (int): Number of days for forecast (if using multi-day).
        forecast (bool): If True, returns forecast data even if days is not specified.
        date (str): Specific date for forecast (YYYY-MM-DD format).
    """
    if not forecast and days <= 0 and not date:
        return await get_current_weather(location)
    
    # Fetch forecast data
    try:
        if date:
            data = await _fetch_weather_data(location)
            available_days = data.get('weather', [])
            target_day = next((d for d in available_days if d['date'] == date), None)
            if target_day:
                # Repackage into a string format similar to get_forecast for consistency
                area = data['nearest_area'][0]['areaName'][0]['value']
                country = data['nearest_area'][0]['country'][0]['value']
                hourly = target_day.get('hourly', [])
                mid_day = hourly[4] if len(hourly) > 4 else (hourly[0] if hourly else {})
                morning = hourly[3] if len(hourly) > 3 else mid_day
                
                return (
                    f"Weather for {area}, {country} on {date}:\n"
                    f"- Condition: {mid_day.get('weatherDesc', [{}])[0].get('value', 'N/A')}\n"
                    f"- Temp Range: {target_day['mintempC']} C to {target_day['maxtempC']} C\n"
                    f"- Morning (09:00): {morning.get('weatherDesc', [{}])[0].get('value', 'N/A')}, {morning.get('tempC', 'N/A')} C"
                )
            else:
                return f"Forecast for {date} is not available. Please try a date within the next 3 days."
        
        # Fallback to multi-day forecast
        return await get_forecast(location, days=max(days, 1))
    except Exception as e:
        return f"Error fetching weather/forecast data: {str(e)}"