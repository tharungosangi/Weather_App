# Simple Weather App

A beginner-friendly Python weather app with both a command-line version and a desktop interface. Enter a city to see current conditions, temperature, feels-like temperature, humidity, and wind speed. It uses Open-Meteo's geocoding and forecast services and does not require an API key.

## Requirements

- Python 3.9 or newer
- An internet connection

## Setup

Create and activate a virtual environment, then install the dependency:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS/Linux, activate the environment with `source .venv/bin/activate` instead.

## Run the desktop app

```powershell
python weather_gui.py
```

The desktop interface runs weather searches in the background so the window stays responsive.

## Run the command-line app

```powershell
python weather_app.py
```

Enter a city name when prompted. The app prints the current conditions or a helpful message if the city cannot be found or the service is unavailable.

## Tests

The unit tests mock HTTP requests and do not need an internet connection:

```powershell
python -m unittest -v
```
