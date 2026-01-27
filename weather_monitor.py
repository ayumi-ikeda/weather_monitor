#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time
import json
import argparse
import signal
import urllib.request
import urllib.error
from datetime import datetime
import math

# =============================================================================
# Weather Monitor CLI (Python Port)
# =============================================================================

VERSION = "3.0.0"

# -----------------------------------------------------------------------------
# ASCII Art & Constants
# -----------------------------------------------------------------------------

BANNER = r"""
  _       __           __  __                 
 | |     / /__  ____ _/ /_/ /_  ___  _____    
 | | /| / / _ \/ __ `/ __/ __ \/ _ \/ ___/    
 | |/ |/ /  __/ /_/ / /_/ / / /  __/ /        
 |__/|__/\___/\__,_/\__/_/ /_/\___/_/         
    __  ___            _ __                   
   /  |/  /___  ____  (_) /_____  _____       
  / /|_/ / __ \/ __ \/ / __/ __ \/ ___/       
 / /  / / /_/ / / / / / /_/ /_/ / /           
/_/  /_/\____/_/ /_/_/\__/\____/_/            
                                              
"""

def get_drawing(label, art_type):
    if art_type == "SUNNY":
        return f"       \\   /\n       .-.       [ {label} ]\n    -- (   ) --\n       `-’\n       /   \\"
    elif art_type == "CLOUDY":
        return f"       .--.\n    .-(    ).     [ {label} ]\n   (___.__)__)"
    elif art_type == "RAIN":
        return f"       .--.\n    .-(    ).     [ {label} ]\n   (___.__)__)\n    ' ' ' '\n     ' ' ' '"
    elif art_type == "SNOW":
        return f"       .--.\n    .-(    ).     [ {label} ]\n   (___.__)__)\n    *  *  *\n     *  *  *"
    return ""

# -----------------------------------------------------------------------------
# Colors
# -----------------------------------------------------------------------------
C_CYAN = "\033[0;36m"
C_BLUE = "\033[0;34m"
C_YELLOW = "\033[1;33m"
C_GREEN = "\033[1;32m"
C_RED_BRIGHT = "\033[91m"
C_RESET = "\033[0m"

# -----------------------------------------------------------------------------
# Localization
# -----------------------------------------------------------------------------

class Strings:
    def __init__(self):
        lang = os.environ.get('LANG', '')
        self.is_jp = lang.startswith('ja')
        
        if self.is_jp:
            self.usage_title = "使用方法: {prog} [オプション]"
            self.usage_desc = "指定した間隔で天気情報をポーリングし、ターミナルに表示します。"
            self.opt_header = "オプション:"
            self.opt_i = "  -i, --interval SECONDS   更新間隔（秒）。必須項目です（--once 指定時は不要）。"
            self.opt_o = "  -o, --once               1回だけ表示して終了します（エラー時はリトライします）。"
            self.opt_f = "  -f, --forecast           8時間先までの予報を確認します（--onceと同様に終了します）。"
            self.opt_h = "  -h, --help               このヘルプを表示して終了します。"
            self.opt_v = "  -v, --version            バージョン情報を表示して終了します。"
            self.usage_ex = "例:"
            
            self.err_int_pos = "エラー: --interval には正の整数を指定してください。"
            self.err_unknown_opt = "不明なオプション"
            self.err_no_interval = "エラー: 更新間隔を指定してください。"
            self.use_h = "ヘルプを表示するには -h を使用してください。"
            self.exit_msg = "プログラムを終了します。"
            self.exit_hint = "(終了: Ctrl+C)"
            self.fetching = "天気情報を取得中..."
            self.err_fetch = "データの取得に失敗、またはデータが破損しています"
            self.wait_retry = "再試行まで待機中... (1秒)"
            self.last_update = "最終更新"
            
            self.lbl_sunny = " 晴れ "
            self.lbl_cloudy = " 曇り "
            self.lbl_rain = "  雨  "
            self.lbl_snow = "  雪  "
            
            self.lbl_cur_weather = "現在の天気"
            self.lbl_detail = "詳細"
            self.lbl_location = "地点"
            self.lbl_temp = "気温"
            self.lbl_humidity = "湿度"
            self.lbl_wind = "風速"
            self.lbl_pressure = "気圧"
            self.lbl_precip = "降水量"
            self.lbl_precip_liq = "降水量(水換算)"
            self.lbl_intensity = "強度"
            
            self.cat_sunny = "晴れ"
            self.cat_snow = "雪"
            self.cat_rain = "雨"
            self.cat_cloudy = "曇り"
            
            self.int_light = "バラツキあり/小雨"
            self.int_mod = "通常の雨"
            self.int_heavy = "大雨"
            self.snow_acc = "積雪の可能性があります。"
            self.shower_pos = "(通り雨の可能性)"
            self.err_parse = "天気情報の解析に失敗しました。"
            
            self.warn_prefix = "[警報]"
            self.caution_prefix = "[注意]"
            self.warn_severe = "激しい天候が検出されました"
            self.warn_rain = "激しい雨が降っています"
            self.warn_wind = "強風が吹いています"
            self.warn_update = "最新の気象情報に注意してください。"
            
            self.fc_title = "[予報]"
            self.fc_rain = "{}時間後に雨になります。"
            self.fc_snow = "{}時間後に雪になります。"
            self.fc_no_rain_cloudy = "{}時間後に雨はやみます。曇るでしょう。"
            self.fc_no_rain_sunny = "{}時間後に雨はやみます。晴れるでしょう。"
            self.fc_generic = "{}時間後に{}になります。"
            
            self.url_wttr = "https://wttr.in/?format=j1&lang=ja"
        else:
            self.is_jp = False
            self.usage_title = "Usage: {prog} [OPTIONS]"
            self.usage_desc = "Polls weather information at specified intervals and displays it in the terminal."
            self.opt_header = "Options:"
            self.opt_i = "  -i, --interval SECONDS   Update interval in seconds. Required (unless --once is used)."
            self.opt_o = "  -o, --once               Display once and exit (retry on error)."
            self.opt_f = "  -f, --forecast           Check forecast for next 8 hours (behaves like --once)."
            self.opt_h = "  -h, --help               Display this help and exit."
            self.opt_v = "  -v, --version            Display version information and exit."
            self.usage_ex = "Example:"
            
            self.err_int_pos = "Error: Please specify a positive integer for --interval."
            self.err_unknown_opt = "Unknown option"
            self.err_no_interval = "Error: Please specify an update interval."
            self.use_h = "Use -h for help."
            self.exit_msg = "Exiting program."
            self.exit_hint = "(Exit: Ctrl+C)"
            self.fetching = "Fetching weather info..."
            self.err_fetch = "Failed to retrieve data or data is corrupted."
            self.wait_retry = "Waiting to retry... (1s)"
            self.last_update = "Last Update"
            
            self.lbl_sunny = "SUNNY"
            self.lbl_cloudy = "CLOUDY"
            self.lbl_rain = " RAIN "
            self.lbl_snow = " SNOW "
            
            self.lbl_cur_weather = "Current Weather"
            self.lbl_detail = "Detail"
            self.lbl_location = "Location"
            self.lbl_temp = "Temp"
            self.lbl_humidity = "Humidity"
            self.lbl_wind = "Wind"
            self.lbl_pressure = "Pressure"
            self.lbl_precip = "Precip"
            self.lbl_precip_liq = "Precip (Liquid)"
            self.lbl_intensity = "Intensity"
            
            self.cat_sunny = "Sunny"
            self.cat_snow = "Snow"
            self.cat_rain = "Rain"
            self.cat_cloudy = "Cloudy"
            
            self.int_light = "Light/Patchy"
            self.int_mod = "Moderate"
            self.int_heavy = "Heavy"
            self.snow_acc = "Possibility of snow accumulation."
            self.shower_pos = "(Possible showers)"
            self.err_parse = "Failed to parse weather information."
            
            self.warn_prefix = "[WARNING]"
            self.caution_prefix = "[CAUTION]"
            self.warn_severe = "Severe weather detected"
            self.warn_rain = "Heavy rain"
            self.warn_wind = "Strong wind"
            self.warn_update = "Please stay updated with the latest weather info."
            
            self.fc_title = "[Forecast]"
            self.fc_rain = "It will rain in {} hours."
            self.fc_snow = "It will snow in {} hours."
            self.fc_no_rain_cloudy = "Rain will stop in {} hours. It will be cloudy."
            self.fc_no_rain_sunny = "Rain will stop in {} hours. It will be sunny."
            self.fc_generic = "It will be {} in {} hours."
            
            self.url_wttr = "https://wttr.in/?format=j1&lang=en"

        self.unit_temp = "°C"
        self.unit_precip = "mm"
        self.unit_wind = "km/h"
        self.unit_pressure = "hPa"

# -----------------------------------------------------------------------------
# Main Class
# -----------------------------------------------------------------------------

class WeatherApp:
    def __init__(self):
        self.strings = Strings()
        self.interval = 0
        self.once = False
        self.forecast = False
        
        self.setup_signal_handlers()

    def show_help(self):
        prog = os.path.basename(sys.argv[0])
        print(self.strings.usage_title.format(prog=prog))
        print("")
        print(self.strings.usage_desc)
        print("")
        print(self.strings.opt_header)
        print(self.strings.opt_i)
        print(self.strings.opt_o)
        print(self.strings.opt_f)
        print(self.strings.opt_h)
        print(self.strings.opt_v)
        print("")
        print(self.strings.usage_ex)
        print(f"  {prog} --interval 60")

    def show_version(self):
        print(f"Weather Monitor v{VERSION}")

    def parse_args(self):
        # We perform manual parsing to match the bash behavior closer/simpler or use argparse
        # The bash script checks for no args first.
        if len(sys.argv) == 1:
            self.show_help()
            sys.exit(0)

        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('-i', '--interval', type=int)
        parser.add_argument('-o', '--once', action='store_true')
        parser.add_argument('-f', '--forecast', action='store_true')
        parser.add_argument('-h', '--help', action='store_true')
        parser.add_argument('-v', '--version', action='store_true')
        
        # We parse known args to handle unknown options manually if needed, 
        # but argparse default behavior is raising error which is fine.
        # However, to exactly match bash error messages:
        try:
            args, unknown = parser.parse_known_args()
        except SystemExit:
            # Replaced by manual handling if needed, but argparse is better.
            sys.exit(1)

        if unknown:
            print(f"{self.strings.err_unknown_opt}: {unknown[0]}")
            self.show_help()
            sys.exit(1)

        if args.help:
            self.show_help()
            sys.exit(0)

        if args.version:
            self.show_version()
            sys.exit(0)

        self.interval = args.interval if args.interval is not None else 0
        self.once = args.once
        self.forecast = args.forecast

        if self.forecast:
            self.once = True
            
        if not self.once and self.interval == 0:
            print(self.strings.err_no_interval)
            print(self.strings.use_h)
            sys.exit(1)
            
        if self.interval < 0: # Bash script checks for positive integer regex, so 0 might be allowed by regex but logic implies >0 logic typically. Bash regex ^[0-9]+$ allows 0. But variable is initialized to 0.
            # Bash script: if [ -n "$2" && ... ]. If interval is 0, line 264 checks: if [ "$ONCE" = false ] && [ "$INTERVAL" -eq 0 ]; then ...
            # So if user passes -i 0, it will likely fail that check.
            pass

        if not self.once and self.interval <= 0:
             # If user explicitly passed 0
            if self.interval == 0:
                print(self.strings.err_no_interval) # Logic matches bash line 264 if interval is 0
                print(self.strings.use_h)
                sys.exit(1)
            else:
                 # Check negative
                 print(self.strings.err_int_pos)
                 sys.exit(1)

    def setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)

    def cleanup(self, signum=None, frame=None):
        self.show_cursor()
        print("") # Newline
        sys.exit(0)

    def show_banner(self):
        self.clear_screen()
        print(f"{C_CYAN}{BANNER}")
        print(f"{C_YELLOW}        >>> Weather Monitor v{VERSION} <<<{C_RESET}")
        print(f"{C_GREEN}    Designed for clear skies and happy days.{C_RESET}")
        print("")
        time.sleep(2)

    def clear_screen(self):
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

    def hide_cursor(self):
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

    def show_cursor(self):
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

    def get_category_key(self, desc, chance_rain, chance_snow):
        desc_lower = desc.lower() if desc else ""
        try:
            c_rain = int(chance_rain)
        except (ValueError, TypeError):
            c_rain = 0
            
        try:
            c_snow = int(chance_snow)
        except (ValueError, TypeError):
            c_snow = 0

        # Priority 1: High chance of snow
        if c_snow > 50 or c_snow > c_rain:
            return "SNOW"

        # Priority 2: Keywords (SNOW)
        snow_keywords = ["snow", "ice", "blizzard", "sleet", "freezing"]
        if any(w in desc_lower for w in snow_keywords):
            return "SNOW"

        # Priority 3: Keywords (SUNNY)
        sunny_keywords = ["sun", "clear"]
        if any(w in desc_lower for w in sunny_keywords):
            return "SUNNY"

        # Priority 4: Keywords (RAIN)
        rain_keywords = ["rain", "drizzle", "shower", "thunder"]
        if any(w in desc_lower for w in rain_keywords):
            return "RAIN"

        return "CLOUDY"

    def check_warnings(self, desc, precip, wind):
        desc = desc or ""
        has_warning = False
        
        # Heavy/Severe keywords
        severe_keywords = ["Heavy", "Storm", "Blizzard", "Thunder", "Torrential"]
        if any(k in desc for k in severe_keywords):
            print(f"{C_RED_BRIGHT}{self.strings.warn_prefix} {self.strings.warn_severe}: {desc}{C_RESET}")
            has_warning = True

        # Heavy Rain (> 15mm)
        try:
            p_val = float(precip)
            if p_val >= 15.0:
                print(f"{C_RED_BRIGHT}{self.strings.caution_prefix} {self.strings.warn_rain}: {precip}{self.strings.unit_precip}{C_RESET}")
                has_warning = True
        except ValueError:
            pass

        # Strong Wind (> 50km/h)
        try:
            w_val = float(wind)
            if w_val >= 50.0:
                print(f"{C_RED_BRIGHT}{self.strings.caution_prefix} {self.strings.warn_wind}: {wind} {self.strings.unit_wind}{C_RESET}")
                has_warning = True
        except ValueError:
            pass

        if has_warning:
            print(f"{C_RED_BRIGHT}{self.strings.warn_update}{C_RESET}")

    def check_forecast_change(self, json_data, current_cat):
        now = datetime.now()
        start_hour = int(now.strftime('%H'))

        # wttr.in hourly data is usually in 'weather' (array of days) -> 'hourly' (array of 3h blocks)
        # We need to flatten or iterate carefully.
        
        # Map logic from bash:
        # for offset in 1..8
        # check_hour = start_hour + offset
        # day_offset = check_hour / 24
        # hour_of_day = check_hour % 24
        # block_idx = hour_of_day / 3
        # time_str = block_idx * 300
        
        days_data = json_data.get('weather', [])
        
        for offset in range(1, 9):
            check_hour = start_hour + offset
            day_offset = check_hour // 24
            hour_of_day = check_hour % 24
            
            block_idx = hour_of_day // 3
            time_str = str(block_idx * 300)
            
            if day_offset >= len(days_data):
                continue
                
            day_record = days_data[day_offset]
            hourly_records = day_record.get('hourly', [])
            
            # Find matching time
            target_hourly = next((h for h in hourly_records if h.get('time') == time_str), None)
            
            if not target_hourly:
                continue
            
            t_desc_list = target_hourly.get('weatherDesc', [])
            t_desc = t_desc_list[0].get('value', "") if t_desc_list else ""
            t_snow = target_hourly.get('chanceofsnow', "0")
            t_rain = target_hourly.get('chanceofrain', "0")
            
            target_cat = self.get_category_key(t_desc, t_rain, t_snow)
            
            if target_cat != current_cat:
                print(self.strings.fc_title)
                
                # Logic from Bash Lines 407-434
                if target_cat == "RAIN":
                    print(self.strings.fc_rain.format(offset))
                elif target_cat == "SNOW":
                    print(self.strings.fc_snow.format(offset))
                elif current_cat == "RAIN":
                    if target_cat == "CLOUDY":
                        print(self.strings.fc_no_rain_cloudy.format(offset))
                    elif target_cat == "SUNNY":
                        print(self.strings.fc_no_rain_sunny.format(offset))
                    else:
                        label_local = self.get_label_for_cat(target_cat)
                        print(self.strings.fc_generic.format(offset, label_local))
                else:
                    label_local = self.get_label_for_cat(target_cat)
                    print(self.strings.fc_generic.format(offset, label_local))
                return

    def get_label_for_cat(self, category):
        if category == "SUNNY": return self.strings.cat_sunny
        if category == "CLOUDY": return self.strings.cat_cloudy
        if category == "SNOW": return self.strings.cat_snow
        if category == "RAIN": return self.strings.cat_rain
        return ""

    def process_weather(self, json_data):
        try:
            current_cond_list = json_data.get('current_condition', [])
            if not current_cond_list:
                print(self.strings.err_parse)
                return

            current = current_cond_list[0]
            
            nearest_area = json_data.get('nearest_area', [])
            location = ""
            if nearest_area:
                 area_names = nearest_area[0].get('areaName', [])
                 if area_names:
                     location = area_names[0].get('value', "")
            
            desc_list = current.get('weatherDesc', [])
            desc_en = desc_list[0].get('value', "") if desc_list else ""
            weather_desc = desc_en
            
            if self.strings.is_jp:
                lang_ja = current.get('lang_ja', [])
                if lang_ja:
                    weather_desc = lang_ja[0].get('value', "")
            
            temp = current.get('temp_C', "")
            precip = current.get('precipMM', "0.0")
            humidity = current.get('humidity', "")
            wind = current.get('windspeedKmph', "")
            pressure = current.get('pressure', "")
            
            # Determine Category using current hourly block if available for chance data
            now = datetime.now()
            start_hour = int(now.strftime('%H'))
            block_idx = start_hour // 3
            time_str = str(block_idx * 300)
            
            days_data = json_data.get('weather', [])
            c_snow = "0"
            c_rain = "0"
            
            if days_data:
                hourly = days_data[0].get('hourly', [])
                current_hourly = next((h for h in hourly if h.get('time') == time_str), None)
                if current_hourly:
                    c_snow = current_hourly.get('chanceofsnow', "0")
                    c_rain = current_hourly.get('chanceofrain', "0")
            
            category = self.get_category_key(desc_en, c_rain, c_snow)
            
            label_ascii = ""
            label_text = ""
            
            if category == "SUNNY":
                label_ascii = self.strings.lbl_sunny
                label_text = self.strings.cat_sunny
            elif category == "SNOW":
                label_ascii = self.strings.lbl_snow
                label_text = self.strings.cat_snow
            elif category == "RAIN":
                label_ascii = self.strings.lbl_rain
                label_text = self.strings.cat_rain
            else:
                category = "CLOUDY"
                label_ascii = self.strings.lbl_cloudy
                label_text = self.strings.cat_cloudy
            
            print(get_drawing(label_ascii, category))
            
            print("========================================")
            print(f" {self.strings.lbl_cur_weather}: {label_text}")
            print(f" {self.strings.lbl_detail}: {weather_desc}")
            print("----------------------------------------")
            print(f" {self.strings.lbl_location}: {location}")
            print(f" {self.strings.lbl_temp}: {temp}{self.strings.unit_temp}")
            print(f" {self.strings.lbl_humidity}: {humidity}%")
            print(f" {self.strings.lbl_wind}: {wind} {self.strings.unit_wind}")
            print(f" {self.strings.lbl_pressure}: {pressure} {self.strings.unit_pressure}")
            
            p_val = 0.0
            try:
                p_val = float(precip)
            except ValueError:
                pass

            if category == "RAIN":
                print(f" {self.strings.lbl_precip}: {precip} {self.strings.unit_precip}")
                if p_val < 2.0:
                    print(f" {self.strings.lbl_intensity}: {self.strings.int_light}")
                elif p_val < 8.0:
                    print(f" {self.strings.lbl_intensity}: {self.strings.int_mod}")
                else:
                    print(f" {self.strings.lbl_intensity}: {self.strings.int_heavy}")
            elif category == "SNOW":
                print(f" {self.strings.lbl_precip_liq}: {precip} {self.strings.unit_precip}")
                print(f" {self.strings.snow_acc}")
            elif category in ["CLOUDY", "SUNNY"]:
                if p_val > 0:
                    print(f" {self.strings.lbl_precip}: {precip} {self.strings.unit_precip} {self.strings.shower_pos}")
                else:
                    print(f" {self.strings.lbl_precip}: 0.0 {self.strings.unit_precip}")

            print("========================================")
            
            self.check_warnings(desc_en, precip, wind)
            
            if self.forecast:
                self.check_forecast_change(json_data, category)

        except Exception as e:
            # print(e) # Debug
            print(self.strings.err_parse)

    def run(self):
        self.parse_args()
        self.hide_cursor()
        self.show_banner()
        
        while True:
            print(self.strings.fetching)
            
            try:
                # Set 10 second timeout
                with urllib.request.urlopen(self.strings.url_wttr, timeout=10) as response:
                    data = response.read()
                    json_data = json.loads(data)
                    
                    self.clear_screen()
                    self.process_weather(json_data)
                    
                    if self.once:
                        self.show_cursor()
                        sys.exit(0)
                    
                    print("")
                    now_str = datetime.now().strftime('%H:%M:%S')
                    print(f"{self.strings.last_update}: {now_str}")
                    print(self.strings.exit_hint)
                    time.sleep(self.interval)
                    
            except (urllib.error.URLError, json.JSONDecodeError, Exception):
                self.clear_screen()
                print(self.strings.err_fetch)
                print(self.strings.wait_retry)
                time.sleep(1)

if __name__ == "__main__":
    app = WeatherApp()
    app.run()
