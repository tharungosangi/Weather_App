"""A polished desktop interface for the Open-Meteo weather app."""

from __future__ import annotations

import queue
import threading
import tkinter as tk

import requests

import weather_app


COLORS = {
    "background": "#0B1220",
    "surface": "#111D32",
    "card": "#172742",
    "card_light": "#1D3150",
    "accent": "#65E6D2",
    "accent_hover": "#8AF2E2",
    "text": "#F4F7FC",
    "muted": "#A5B4C9",
    "subtle": "#71839E",
    "error": "#FF8A8A",
}

WEATHER_ICONS = {
    0: "☀",
    1: "🌤",
    2: "⛅",
    3: "☁",
    45: "🌫",
    48: "🌫",
    51: "🌦",
    53: "🌧",
    55: "🌧",
    56: "🌧",
    57: "🌧",
    61: "🌦",
    63: "🌧",
    65: "🌧",
    66: "🌧",
    67: "🌧",
    71: "🌨",
    73: "❄",
    75: "❄",
    77: "❄",
    80: "🌦",
    81: "🌧",
    82: "⛈",
    85: "🌨",
    86: "❄",
    95: "⛈",
    96: "⛈",
    99: "⛈",
}


class WeatherWindow:
    """Build and manage the weather application's desktop window."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Skycast — Weather")
        self.root.geometry("900x720")
        self.root.minsize(700, 620)
        self.root.configure(bg=COLORS["background"])

        self.results: queue.Queue[tuple[str, object]] = queue.Queue()
        self.loading = False
        self._build_interface()
        self.root.after(100, self._check_results)

    def _build_interface(self) -> None:
        """Create the header, search box, weather panel, and detail cards."""
        page = tk.Frame(self.root, bg=COLORS["background"], padx=52, pady=34)
        page.pack(fill="both", expand=True)
        page.grid_columnconfigure(0, weight=1)

        header = tk.Frame(page, bg=COLORS["background"])
        header.grid(row=0, column=0, sticky="ew", pady=(0, 30))
        header.grid_columnconfigure(0, weight=1)

        brand = tk.Frame(header, bg=COLORS["background"])
        brand.grid(row=0, column=0, sticky="w")
        tk.Label(
            brand,
            text="☁",
            font=("Segoe UI Symbol", 25),
            fg=COLORS["accent"],
            bg=COLORS["background"],
        ).pack(side="left", padx=(0, 10))
        tk.Label(
            brand,
            text="SKYCAST",
            font=("Segoe UI", 16, "bold"),
            fg=COLORS["text"],
            bg=COLORS["background"],
        ).pack(side="left")
        tk.Label(
            header,
            text="CURRENT WEATHER  ·  OPEN-METEO",
            font=("Segoe UI", 9, "bold"),
            fg=COLORS["muted"],
            bg=COLORS["background"],
        ).grid(row=0, column=1, sticky="e")

        tk.Label(
            page,
            text="Weather, at a glance.",
            font=("Segoe UI", 28, "bold"),
            fg=COLORS["text"],
            bg=COLORS["background"],
        ).grid(row=1, column=0, sticky="w")
        tk.Label(
            page,
            text="Find current conditions for any city around the world.",
            font=("Segoe UI", 11),
            fg=COLORS["muted"],
            bg=COLORS["background"],
        ).grid(row=2, column=0, sticky="w", pady=(5, 22))

        search = tk.Frame(page, bg=COLORS["surface"], padx=7, pady=7)
        search.grid(row=3, column=0, sticky="ew", pady=(0, 22))
        search.grid_columnconfigure(0, weight=1)
        self.city_entry = tk.Entry(
            search,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 12),
        )
        self.city_entry.insert(0, "Search a city, e.g. Tokyo")
        self.city_entry.config(fg=COLORS["subtle"])
        self.city_entry.bind("<FocusIn>", self._clear_placeholder)
        self.city_entry.bind("<Return>", lambda _event: self.search())
        self.city_entry.grid(row=0, column=0, sticky="ew", ipady=11, padx=(12, 8))

        self.search_button = tk.Button(
            search,
            text="Get weather  →",
            command=self.search,
            bg=COLORS["accent"],
            fg=COLORS["background"],
            activebackground=COLORS["accent_hover"],
            activeforeground=COLORS["background"],
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=20,
            pady=11,
        )
        self.search_button.grid(row=0, column=1, sticky="e")
        self.search_button.bind("<Enter>", lambda _event: self._button_hover(True))
        self.search_button.bind("<Leave>", lambda _event: self._button_hover(False))

        self.status = tk.Label(
            page,
            text="Enter a city to get started.",
            font=("Segoe UI", 9),
            fg=COLORS["subtle"],
            bg=COLORS["background"],
            anchor="w",
        )
        self.status.grid(row=4, column=0, sticky="ew", pady=(0, 10))

        self.weather_card = tk.Frame(page, bg=COLORS["card"], padx=30, pady=25)
        self.weather_card.grid(row=5, column=0, sticky="nsew")
        self.weather_card.grid_columnconfigure(0, weight=1)
        self.weather_card.grid_rowconfigure(0, weight=1)

        hero = tk.Frame(self.weather_card, bg=COLORS["card"])
        hero.grid(row=0, column=0, sticky="nsew")
        hero.grid_columnconfigure(0, weight=1)

        self.location_label = tk.Label(
            hero,
            text="YOUR CITY",
            font=("Segoe UI", 10, "bold"),
            fg=COLORS["accent"],
            bg=COLORS["card"],
            anchor="w",
        )
        self.location_label.grid(row=0, column=0, sticky="w")
        self.updated_label = tk.Label(
            hero,
            text="Live conditions from your location search",
            font=("Segoe UI", 9),
            fg=COLORS["muted"],
            bg=COLORS["card"],
            anchor="w",
        )
        self.updated_label.grid(row=1, column=0, sticky="w", pady=(5, 17))
        self.temperature_label = tk.Label(
            hero,
            text="—°",
            font=("Segoe UI Light", 76),
            fg=COLORS["text"],
            bg=COLORS["card"],
            anchor="w",
        )
        self.temperature_label.grid(row=2, column=0, sticky="w")
        self.condition_label = tk.Label(
            hero,
            text="Waiting for a city",
            font=("Segoe UI", 14, "bold"),
            fg=COLORS["text"],
            bg=COLORS["card"],
            anchor="w",
        )
        self.condition_label.grid(row=3, column=0, sticky="w", pady=(0, 18))
        self.icon_label = tk.Label(
            hero,
            text="☀",
            font=("Segoe UI Emoji", 76),
            fg="#FFD477",
            bg=COLORS["card"],
        )
        self.icon_label.grid(row=0, column=1, rowspan=4, sticky="e", padx=(18, 10))

        divider = tk.Frame(self.weather_card, height=1, bg="#2A3B56")
        divider.grid(row=1, column=0, sticky="ew", pady=(0, 17))

        self.metric_values: dict[str, tk.Label] = {}
        metrics = tk.Frame(self.weather_card, bg=COLORS["card"])
        metrics.grid(row=2, column=0, sticky="ew")
        for column in range(3):
            metrics.grid_columnconfigure(column, weight=1, uniform="metric")

        for column, (title, icon) in enumerate(
            (("FEELS LIKE", "◌"), ("HUMIDITY", "％"), ("WIND", "↗"))
        ):
            tile = tk.Frame(metrics, bg=COLORS["card_light"], padx=15, pady=14)
            tile.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 6 if column < 2 else 0))
            tk.Label(
                tile,
                text=f"{icon}  {title}",
                font=("Segoe UI", 8, "bold"),
                fg=COLORS["muted"],
                bg=COLORS["card_light"],
                anchor="w",
            ).pack(fill="x")
            value = tk.Label(
                tile,
                text="—",
                font=("Segoe UI", 16, "bold"),
                fg=COLORS["text"],
                bg=COLORS["card_light"],
                anchor="w",
            )
            value.pack(fill="x", pady=(9, 0))
            self.metric_values[title] = value

        footer = tk.Label(
            page,
            text="Weather data provided by Open-Meteo  ·  No API key required",
            font=("Segoe UI", 9),
            fg=COLORS["subtle"],
            bg=COLORS["background"],
        )
        footer.grid(row=6, column=0, pady=(17, 0))

    def _clear_placeholder(self, _event: tk.Event) -> None:
        if self.city_entry.get() == "Search a city, e.g. Tokyo":
            self.city_entry.delete(0, "end")
            self.city_entry.config(fg=COLORS["text"])

    def _button_hover(self, hovering: bool) -> None:
        color = COLORS["accent_hover"] if hovering else COLORS["accent"]
        self.search_button.configure(bg=color)

    def search(self) -> None:
        """Validate the city and fetch its weather without freezing the UI."""
        city = self.city_entry.get().strip()
        if not city or city == "Search a city, e.g. Tokyo":
            self.status.configure(text="Please enter a city name.", fg=COLORS["error"])
            self.city_entry.focus_set()
            return
        if self.loading:
            return

        self.loading = True
        self.search_button.configure(text="Loading…", state="disabled")
        self.status.configure(text=f"Looking up weather for {city}…", fg=COLORS["accent"])
        threading.Thread(target=self._fetch_weather, args=(city,), daemon=True).start()

    def _fetch_weather(self, city: str) -> None:
        try:
            location = weather_app.get_coordinates(city)
            weather = weather_app.get_current_weather(
                location["latitude"], location["longitude"]
            )
            self.results.put(("success", (location, weather)))
        except ValueError as error:
            self.results.put(("error", str(error)))
        except requests.RequestException:
            self.results.put(
                ("error", "Could not reach the weather service. Check your internet and try again.")
            )
        except (KeyError, TypeError):
            self.results.put(("error", "The weather service returned an unexpected response."))

    def _check_results(self) -> None:
        """Apply background request results on Tk's main thread."""
        try:
            result_type, payload = self.results.get_nowait()
        except queue.Empty:
            self.root.after(100, self._check_results)
            return

        self.loading = False
        self.search_button.configure(text="Get weather  →", state="normal")
        if result_type == "error":
            self.status.configure(text=str(payload), fg=COLORS["error"])
        else:
            location, weather = payload
            self._show_weather(location, weather)
        self.root.after(100, self._check_results)

    def _show_weather(self, location: dict, weather: dict) -> None:
        """Render weather data in the summary panel and metric tiles."""
        current = weather["current"]
        units = weather.get("current_units", {})
        place = location.get("name", "Unknown location")
        if location.get("country"):
            place = f"{place}, {location['country']}"

        temperature_unit = units.get("temperature_2m", "°C")
        wind_unit = units.get("wind_speed_10m", "km/h")
        self.location_label.configure(text=place.upper())
        self.updated_label.configure(
            text=f"Updated {current.get('time', 'just now')}  ·  Local time"
        )
        self.temperature_label.configure(
            text=f"{current['temperature_2m']}{temperature_unit}"
        )
        self.condition_label.configure(
            text=weather_app.describe_weather(current["weather_code"])
        )
        self.icon_label.configure(
            text=WEATHER_ICONS.get(current["weather_code"], "☁")
        )
        self.metric_values["FEELS LIKE"].configure(
            text=f"{current['apparent_temperature']}{temperature_unit}"
        )
        self.metric_values["HUMIDITY"].configure(
            text=f"{current['relative_humidity_2m']}%"
        )
        self.metric_values["WIND"].configure(
            text=f"{current['wind_speed_10m']} {wind_unit}"
        )
        self.status.configure(text="Weather updated successfully.", fg=COLORS["accent"])


def main() -> None:
    """Start the graphical weather application."""
    root = tk.Tk()
    WeatherWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
