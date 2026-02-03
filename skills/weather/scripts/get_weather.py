import requests
import sys
import json

def get_weather(location):
    url = f"https://wttr.in/{location}?format=j1"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        current = data['current_condition'][0]
        temp_C = current['temp_C']
        feels_like = current['FeelsLikeC']
        desc = current['weatherDesc'][0]['value']
        humidity = current['humidity']
        wind = current['windspeedKmph']
        uv_index = current['uvIndex']
        visibility = current['visibility']
        pressure = current['pressure']
        precip = current['precipMM']
        
        print(f"Detailed Weather in {location}:")
        print(f"Temperature: {temp_C}°C (Feels like: {feels_like}°C)")
        print(f"Condition: {desc}")
        print(f"Humidity: {humidity}%")
        print(f"Wind Speed: {wind} km/h")
        print(f"UV Index: {uv_index}")
        print(f"Visibility: {visibility} km")
        print(f"Pressure: {pressure} hPa")
        print(f"Precipitation: {precip} mm")
        
    except Exception as e:
        print(f"Error fetching weather: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python get_weather.py <location>")
    else:
        get_weather(" ".join(sys.argv[1:]))
