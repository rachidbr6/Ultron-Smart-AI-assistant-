"""Weather lookups via Open-Meteo (free, no API key required)."""

from __future__ import annotations

import os

import requests

_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
_IP_LOCATE_URL = "http://ip-api.com/json/"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather interpretation codes -> plain-language description.
_WEATHER_CODES = {
    0: "clear sky",
    1: "mostly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "foggy",
    48: "foggy with frost",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    56: "freezing drizzle",
    57: "dense freezing drizzle",
    61: "light rain",
    63: "moderate rain",
    65: "heavy rain",
    66: "freezing rain",
    67: "heavy freezing rain",
    71: "light snow",
    73: "moderate snow",
    75: "heavy snow",
    77: "snow grains",
    80: "light rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "light snow showers",
    86: "heavy snow showers",
    95: "a thunderstorm",
    96: "a thunderstorm with light hail",
    99: "a thunderstorm with heavy hail",
}


def weather_condition(code: int) -> str:
    return _WEATHER_CODES.get(code, "unusual conditions")


def _configured_city() -> str:
    return os.getenv("JARVIS_WEATHER_CITY", "").strip()


def _geocode_city(city: str) -> tuple[float, float, str] | None:
    try:
        response = requests.get(_GEOCODE_URL, params={"name": city, "count": 1}, timeout=6)
        response.raise_for_status()
        results = response.json().get("results") or []
    except (requests.RequestException, ValueError):
        return None
    if not results:
        return None
    place = results[0]
    label = place.get("name", city)
    country = place.get("country")
    if country:
        label = f"{label}, {country}"
    return place["latitude"], place["longitude"], label


def _locate_by_ip() -> tuple[float, float, str] | None:
    try:
        response = requests.get(_IP_LOCATE_URL, timeout=6)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return None
    if data.get("status") != "success":
        return None
    return data["lat"], data["lon"], data.get("city", "your location")


def resolve_location() -> tuple[float, float, str] | None:
    """Resolve (lat, lon, label) from JARVIS_WEATHER_CITY, else IP geolocation."""

    city = _configured_city()
    if city:
        geocoded = _geocode_city(city)
        if geocoded is not None:
            return geocoded
    return _locate_by_ip()


def fetch_current_weather() -> dict | None:
    """Return current conditions + today's high/low, or None on failure."""

    location = resolve_location()
    if location is None:
        return None
    lat, lon, label = location

    try:
        response = requests.get(
            _FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
                "daily": "temperature_2m_max,temperature_2m_min",
                "timezone": "auto",
                "forecast_days": 1,
            },
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return None

    current = data.get("current") or {}
    daily = data.get("daily") or {}
    try:
        return {
            "location": label,
            "temperature": round(current["temperature_2m"]),
            "feels_like": round(current["apparent_temperature"]),
            "condition": weather_condition(current["weather_code"]),
            "wind_kph": round(current["wind_speed_10m"]),
            "high": round(daily["temperature_2m_max"][0]),
            "low": round(daily["temperature_2m_min"][0]),
        }
    except (KeyError, IndexError, TypeError):
        return None


def build_weather_summary() -> str | None:
    """Return a spoken weather summary, or None if lookup failed."""

    weather = fetch_current_weather()
    if weather is None:
        return None
    return (
        f"It's {weather['temperature']} degrees in {weather['location']} with {weather['condition']}, "
        f"feels like {weather['feels_like']}. Today's high is {weather['high']}, low is {weather['low']}, "
        f"with wind around {weather['wind_kph']} kilometers per hour."
    )


__all__ = [
    "build_weather_summary",
    "fetch_current_weather",
    "resolve_location",
    "weather_condition",
]
