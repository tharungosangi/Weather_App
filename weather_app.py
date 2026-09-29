"""A small command-line weather app powered by Open-Meteo."""

from __future__ import annotations

import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT = 10

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def get_coordinates(city: str) -> dict:
    """Look up a city and return its geocoding result."""
    response = requests.get(
        GEOCODING_URL,
        params={"name": city, "count": 1, "language": "en", "format": "json"},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    results = response.json().get("results", [])
    if not results:
        raise ValueError(f"No location found for '{city}'. Check the spelling and try again.")
    return results[0]


def get_current_weather(latitude: float, longitude: float) -> dict:
    """Fetch current weather measurements for a coordinate pair."""
    response = requests.get(
        WEATHER_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,relative_humidity_2m,apparent_temperature,"
                "weather_code,wind_speed_10m"
            ),
            "timezone": "auto",
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def describe_weather(code: int) -> str:
    """Translate a WMO weather code to a short description."""
    return WEATHER_CODES.get(code, "Unknown conditions")


def format_weather(location: dict, weather: dict) -> str:
    """Format the location and measurements into readable terminal output."""
    current = weather["current"]
    units = weather.get("current_units", {})
    place = location.get("name", "Unknown location")
    country = location.get("country")
    if country:
        place = f"{place}, {country}"

    temperature_unit = units.get("temperature_2m", "°C")
    wind_unit = units.get("wind_speed_10m", "km/h")
    return (
        f"\nWeather for {place}\n"
        f"{'-' * (12 + len(place))}\n"
        f"Conditions: {describe_weather(current['weather_code'])}\n"
        f"Temperature: {current['temperature_2m']}{temperature_unit}\n"
        f"Feels like: {current['apparent_temperature']}{temperature_unit}\n"
        f"Humidity: {current['relative_humidity_2m']}%\n"
        f"Wind: {current['wind_speed_10m']} {wind_unit}\n"
        f"Updated: {current.get('time', 'unknown')}\n"
    )


def main() -> None:
    """Prompt for a city and print its current weather."""
    city = input("Enter a city: ").strip()
    if not city:
        print("Please enter a city name.")
        return

    try:
        location = get_coordinates(city)
        weather = get_current_weather(location["latitude"], location["longitude"])
        print(format_weather(location, weather))
    except ValueError as error:
        print(error)
    except requests.RequestException as error:
        print(f"Could not retrieve weather. Check your internet connection and try again. ({error})")
    except (KeyError, TypeError) as error:
        print(f"The weather service returned an unexpected response. ({error})")


if __name__ == "__main__":
    main()
