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
        
        if 'weather' in data:
            print(f"\n3-Day Forecast for {location}:")
            for day in data['weather']:
                date = day.get('date', '')
                maxtemp = day.get('maxtempC', '')
                mintemp = day.get('mintempC', '')
                condition = "Unknown"
                if 'hourly' in day and len(day['hourly']) > 4:
                     condition = day['hourly'][4]['weatherDesc'][0]['value']
                print(f" - Date: {date}, Condition: {condition}, High: {maxtemp}°C, Low: {mintemp}°C")
                
    except Exception as e:
        print(f"Error fetching weather: {e}")

def get_ip_location():
    try:
        response = requests.get("http://ip-api.com/json/")
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "success":
                return data["city"]
    except Exception as e:
        pass
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        loc = get_ip_location()
        if loc:
            get_weather(loc)
        else:
            print("Usage: python get_weather.py <location>")
    else:
        get_weather(" ".join(sys.argv[1:]))
