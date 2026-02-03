---
name: weather
description: Fetch detailed real-time weather conditions, including temperature, humidity, wind speed, UV index, and visibility for any location. Use when the user asks for comprehensive weather reports or specific metrics like UV levels.
---

# Weather Service

Provides detailed real-time weather updates and forecasts via the `wttr.in` service.

## Capabilities
- Current temperature and "Feels Like" temperature
- Humidity, wind speed, and direction
- UV index and visibility
- Precipitation and barometric pressure

## Procedures

### Get Detailed Weather
To retrieve a comprehensive weather report for a location, execute the `get_weather.py` script.

```bash
python3 skills/weather/scripts/get_weather.py "<location>"
```

### Examples
- User: "What's the weather like in Tokyo?"
  Action: Run `python3 skills/weather/scripts/get_weather.py Tokyo`
- User: "Is it safe to go out in the sun in Miami? Check the UV index."
  Action: Run `python3 skills/weather/scripts/get_weather.py Miami`
