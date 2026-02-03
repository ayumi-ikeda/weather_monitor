# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## What this repo is
A single-file Python app (`weather_monitor.py`) that fetches weather data from `wttr.in` (JSON format) and displays it either:
- in the terminal (ASCII art + ANSI colors), refreshing on an interval, or
- in a Tkinter GUI (fixed 10-minute refresh).

## Common commands
### Run (CLI)
```bash
# show help / options
python3 weather_monitor.py -h

# run continuously (required unless --once/--forecast/--gui)
python3 weather_monitor.py -i 60

# run once (good smoke test)
python3 weather_monitor.py --once

# forecast mode (analyzes next ~8 hours once and exits)
python3 weather_monitor.py --forecast
```

### Run (GUI)
```bash
# start GUI (updates every 10 minutes)
python3 weather_monitor.py --gui

# start GUI “in background” (forks on Unix; best-effort on Windows)
python3 weather_monitor.py --gui --background
```

### Quick sanity checks (no formal test suite)
```bash
# syntax check
python3 -m py_compile weather_monitor.py

# basic runtime smoke test (network required)
python3 weather_monitor.py --once
```

## Key architecture (big picture)
All logic lives in `weather_monitor.py` and is split into a few “layers”:

### 1) Localization / configuration
- `Strings`: chooses Japanese vs English UI text based on `LANG`.
- Also sets the upstream URL:
  - `https://wttr.in/?format=j1&lang=ja` or
  - `https://wttr.in/?format=j1&lang=en`

Practical tip: if you’re debugging output language, reproduce with a controlled locale, e.g. `LANG=ja_JP.UTF-8` or `LANG=en_US.UTF-8`.

### 2) Weather parsing + domain logic
- `WeatherLogic.parse(json_data, forecast_mode=False)`:
  - Reads `current_condition[0]`, `nearest_area[0]`, and `weather[...].hourly[...]` from the wttr.in JSON.
  - Computes a coarse category (`SUNNY`, `CLOUDY`, `RAIN`, `SNOW`) via `get_category_key()`.
  - Produces a normalized `info` dict consumed by both CLI and GUI:
    - `category`, `label_text`, `label_ascii`, `location`, `description`, core metrics
    - `precip_info[]` (human-readable precipitation/intensity lines)
    - `warnings[]` (based on description keywords, precip >= 15mm, wind >= 50km/h)
    - `forecast[]` (first detected category change within the next ~8 hours)

If you need to change how weather is classified or how forecast changes are detected, start here.

### 3) UI implementations
- CLI:
  - `WeatherApp.run()` is the CLI loop:
    - fetches JSON via `urllib.request.urlopen()`
    - calls `WeatherLogic.parse()`
    - renders via `WeatherApp.display_cli(info)` using ASCII art (`get_drawing`) + ANSI colors
  - The CLI loop retries quickly on fetch/parse failures.

- GUI:
  - `WeatherGUI` builds the Tkinter UI.
  - `WeatherGUI.update_data()`:
    - fetches JSON on a background thread
    - schedules UI updates via `root.after(...)`
    - retries after 1s on error, otherwise schedules the next update in 10 minutes.

### 4) App entrypoint / argument handling
- `WeatherApp.parse_args()` handles:
  - `--interval` (required only for continuous CLI mode)
  - `--once`, `--forecast`, `--gui`, `--background`
- `--forecast` implies `--once`.
- `--background` is only valid with `--gui`.

## Versioning convention used in-repo
This repo includes a semantic-versioning convention (see `.agent/skills/version_management/SKILL.md`). When changing behavior:
- Patch: bugfix/small adjustments
- Minor: feature additions or larger functional changes
- Major: breaking/large redesign

The runtime version string is `VERSION = "..."` in `weather_monitor.py`.