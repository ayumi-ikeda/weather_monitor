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
import threading

# Check for Tkinter availability
try:
    import tkinter as tk
    from tkinter import font as tkfont
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

# =============================================================================
# Weather Monitor CLI & GUI (Python Port)
# =============================================================================

VERSION = "3.4.0"

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

def get_emoji(art_type):
    if art_type == "SUNNY": return "☀️"
    if art_type == "CLOUDY": return "☁️"
    if art_type == "RAIN": return "☔"
    if art_type == "SNOW": return "☃️"
    return "❓"

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
            self.usage_desc = "指定した間隔で天気情報をポーリングし、ターミナル(またはGUI)に表示します。"
            self.opt_header = "オプション:"
            self.opt_i = "  -i, --interval SECONDS   更新間隔（秒）。必須項目です（-o, -f, -g 指定時は不要）。"
            self.opt_o = "  -o, --once               1回だけ表示して終了します（エラー時はリトライします）。"
            self.opt_f = "  -f, --forecast           8時間先までの予報を確認します（--onceと同様に終了します）。"
            self.opt_g = "  -g, --gui                GUIモードで起動します（更新間隔は10分固定）。"
            self.opt_y = "  -y, --background         GUIモードをバックグラウンドで起動します（-g 指定時のみ有効）。"
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
            self.next_update = "次回の更新"
            
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
            self.err_gui_no_tk = "エラー: Tkinter がインストールされていないか、利用できません。"
            
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
            
            self.lbl_always_on_top = "常に最前面に表示"
            self.err_y_only_g = "エラー: -y/--background オプションは -g/--gui と併用する場合のみ有効です。"
            
            self.url_wttr = "https://wttr.in/?format=j1&lang=ja"
        else:
            self.is_jp = False
            self.usage_title = "Usage: {prog} [OPTIONS]"
            self.usage_desc = "Polls weather information at specified intervals and displays it in the terminal (or GUI)."
            self.opt_header = "Options:"
            self.opt_i = "  -i, --interval SECONDS   Update interval in seconds. Required (unless -o, -f, -g is used)."
            self.opt_o = "  -o, --once               Display once and exit (retry on error)."
            self.opt_f = "  -f, --forecast           Check forecast for next 8 hours (behaves like --once)."
            self.opt_g = "  -g, --gui                Launch in GUI mode (fixed 10 min interval)."
            self.opt_y = "  -y, --background         Launch GUI in background (only with -g)."
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
            self.next_update = "Next Update"
            
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
            self.err_gui_no_tk = "Error: Tkinter is not installed or available."
            
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
            
            self.lbl_always_on_top = "Always on Top"
            self.err_y_only_g = "Error: -y/--background option can only be used with -g/--gui."
            
            self.url_wttr = "https://wttr.in/?format=j1&lang=en"

        self.unit_temp = "°C"
        self.unit_precip = "mm"
        self.unit_wind = "km/h"
        self.unit_pressure = "hPa"

# -----------------------------------------------------------------------------
# Core Weather Logic
# -----------------------------------------------------------------------------

class WeatherLogic:
    def __init__(self, strings):
        self.strings = strings

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

        if c_snow > 50 or c_snow > c_rain:
            return "SNOW"

        snow_keywords = ["snow", "ice", "blizzard", "sleet", "freezing"]
        if any(w in desc_lower for w in snow_keywords):
            return "SNOW"

        sunny_keywords = ["sun", "clear"]
        if any(w in desc_lower for w in sunny_keywords):
            return "SUNNY"

        rain_keywords = ["rain", "drizzle", "shower", "thunder"]
        if any(w in desc_lower for w in rain_keywords):
            return "RAIN"

        return "CLOUDY"

    def get_label_for_cat(self, category):
        if category == "SUNNY": return self.strings.cat_sunny
        if category == "CLOUDY": return self.strings.cat_cloudy
        if category == "SNOW": return self.strings.cat_snow
        if category == "RAIN": return self.strings.cat_rain
        return ""

    def parse(self, json_data, forecast_mode=False):
        """
        Parses JSON data and returns a dictionary containing all display information
        """
        result = {}
        
        current_cond_list = json_data.get('current_condition', [])
        if not current_cond_list:
            raise ValueError(self.strings.err_parse)

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
        
        # Calculate Category
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
        
        # Determining Labels
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
            
        result['category'] = category
        result['label_ascii'] = label_ascii
        result['label_text'] = label_text
        result['location'] = location
        result['description'] = weather_desc
        result['description_en'] = desc_en # For warning checks
        result['temp'] = temp
        result['precip'] = precip
        result['humidity'] = humidity
        result['wind'] = wind
        result['pressure'] = pressure
        
        # Precip detail logic
        p_val = 0.0
        try:
            p_val = float(precip)
        except ValueError:
            pass
        
        precip_info = []
        if category == "RAIN":
            precip_info.append(f"{self.strings.lbl_precip}: {precip} {self.strings.unit_precip}")
            if p_val < 2.0:
                precip_info.append(f"{self.strings.lbl_intensity}: {self.strings.int_light}")
            elif p_val < 8.0:
                precip_info.append(f"{self.strings.lbl_intensity}: {self.strings.int_mod}")
            else:
                precip_info.append(f"{self.strings.lbl_intensity}: {self.strings.int_heavy}")
        elif category == "SNOW":
            precip_info.append(f"{self.strings.lbl_precip_liq}: {precip} {self.strings.unit_precip}")
            precip_info.append(self.strings.snow_acc)
        elif category in ["CLOUDY", "SUNNY"]:
            if p_val > 0:
                precip_info.append(f"{self.strings.lbl_precip}: {precip} {self.strings.unit_precip} {self.strings.shower_pos}")
            else:
                precip_info.append(f"{self.strings.lbl_precip}: 0.0 {self.strings.unit_precip}")
        
        result['precip_info'] = precip_info

        # Warnings
        warnings = []
        # Severe keywords
        severe_keywords = ["Heavy", "Storm", "Blizzard", "Thunder", "Torrential"]
        if any(k in desc_en for k in severe_keywords):
            warnings.append(f"{self.strings.warn_prefix} {self.strings.warn_severe}: {desc_en}")

        # Heavy Rain (> 15mm)
        if p_val >= 15.0:
            warnings.append(f"{self.strings.caution_prefix} {self.strings.warn_rain}: {precip}{self.strings.unit_precip}")

        # Strong Wind (> 50km/h)
        try:
            w_val = float(wind)
            if w_val >= 50.0:
                 warnings.append(f"{self.strings.caution_prefix} {self.strings.warn_wind}: {wind} {self.strings.unit_wind}")
        except ValueError:
            pass
            
        result['warnings'] = warnings
        
        # Forecast
        forecast_msgs = []
        if forecast_mode:
             # Similar logic to original check_forecast_change but returning strings
             start_hour = int(now.strftime('%H'))
             
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
                
                target_hourly = next((h for h in hourly_records if h.get('time') == time_str), None)
                
                if not target_hourly:
                    continue
                
                t_desc_list = target_hourly.get('weatherDesc', [])
                t_desc = t_desc_list[0].get('value', "") if t_desc_list else ""
                t_snow = target_hourly.get('chanceofsnow', "0")
                t_rain = target_hourly.get('chanceofrain', "0")
                
                target_cat = self.get_category_key(t_desc, t_rain, t_snow)
                
                if target_cat != category:
                    if target_cat == "RAIN":
                        forecast_msgs.append(self.strings.fc_rain.format(offset))
                    elif target_cat == "SNOW":
                        forecast_msgs.append(self.strings.fc_snow.format(offset))
                    elif category == "RAIN":
                        if target_cat == "CLOUDY":
                            forecast_msgs.append(self.strings.fc_no_rain_cloudy.format(offset))
                        elif target_cat == "SUNNY":
                            forecast_msgs.append(self.strings.fc_no_rain_sunny.format(offset))
                        else:
                            label_local = self.get_label_for_cat(target_cat)
                            forecast_msgs.append(self.strings.fc_generic.format(offset, label_local))
                    else:
                        label_local = self.get_label_for_cat(target_cat)
                        forecast_msgs.append(self.strings.fc_generic.format(offset, label_local))
                    # Only report first change
                    break
        
        result['forecast'] = forecast_msgs
        return result

# -----------------------------------------------------------------------------
# GUI Implementation
# -----------------------------------------------------------------------------

class WeatherGUI:
    def __init__(self, strings, logic):
        self.strings = strings
        self.logic = logic
        
        self.root = tk.Tk()
        self.root.title("Weather Monitor")
        self.root.geometry("400x600")
        self.root.configure(bg="#222222")
        
        self.setup_ui()
        
        # Always on Top state
        self.always_on_top = tk.BooleanVar(value=False)
        
        # Auto Update Interval (10 mins = 600000 ms)
        self.update_interval_ms = 10 * 60 * 1000 
        
    def setup_ui(self):
        # Styles
        style_bg = "#222222"
        style_fg = "#ffffff"
        font_emoji = ("Segoe UI Emoji", 64, "bold") if os.name == 'nt' else ("Noto Color Emoji", 64, "bold")
        # On Linux standard fonts might be simpler
        if sys.platform.startswith('linux'):
             font_emoji = ("sans-serif", 64)

        font_large = ("Helvetica", 24, "bold")
        font_med = ("Helvetica", 14)
        font_small = ("Helvetica", 10)
        
        # Container
        self.main_frame = tk.Frame(self.root, bg=style_bg, padx=20, pady=20)
        self.main_frame.pack(expand=True, fill='both')
        
        # Location
        self.lbl_location = tk.Label(self.main_frame, text="---", font=font_med, bg=style_bg, fg="#cccccc")
        self.lbl_location.pack(pady=(20, 10))
        
        # Emoji Icon
        self.lbl_icon = tk.Label(self.main_frame, text="⏳", font=font_emoji, bg=style_bg, fg=style_fg)
        self.lbl_icon.pack(pady=10)
        
        # Weather Text
        self.lbl_weather = tk.Label(self.main_frame, text="Loading...", font=font_large, bg=style_bg, fg=style_fg)
        self.lbl_weather.pack(pady=5)
        
        # Description
        self.lbl_desc = tk.Label(self.main_frame, text="", font=font_med, bg=style_bg, fg="#aaaaaa")
        self.lbl_desc.pack(pady=5)
        
        # Details Frame
        self.details_frame = tk.Frame(self.main_frame, bg=style_bg, pady=20)
        self.details_frame.pack(fill='x')
        
        self.lbl_temp = tk.Label(self.details_frame, text="Temp: --", font=font_med, bg=style_bg, fg=style_fg)
        self.lbl_temp.pack()
        
        self.lbl_wind = tk.Label(self.details_frame, text="Wind: --", font=font_med, bg=style_bg, fg=style_fg)
        self.lbl_wind.pack()
        
        self.lbl_humid = tk.Label(self.details_frame, text="Humid: --", font=font_med, bg=style_bg, fg=style_fg)
        self.lbl_humid.pack()
        
        self.lbl_precip = tk.Label(self.details_frame, text="Precip: --", font=font_med, bg=style_bg, fg=style_fg)
        self.lbl_precip.pack()

        # Forecast Frame
        self.forecast_frame = tk.Frame(self.main_frame, bg=style_bg, pady=10)
        self.forecast_frame.pack(fill='x')
        
        self.lbl_forecast = tk.Label(self.forecast_frame, text="", font=font_med, bg=style_bg, fg="#00ff00", wraplength=350)
        self.lbl_forecast.pack()

        # Footer Container (Status and Update Info)
        self.footer_frame = tk.Frame(self.main_frame, bg=style_bg)
        self.footer_frame.pack(side='bottom', fill='x', pady=(10, 0))

        # Update Info
        self.lbl_update = tk.Label(self.footer_frame, text="", font=font_small, bg=style_bg, fg="#666666")
        self.lbl_update.pack(side='bottom')

        # Status / Warnings
        self.lbl_status = tk.Label(self.footer_frame, text=self.strings.fetching, font=font_small, bg=style_bg, fg="#ffff00", wraplength=350, justify='center')
        self.lbl_status.pack(side='bottom', pady=(0, 5), fill='x')

        # Context Menu Binding (Right Click)
        self.root.bind("<Button-3>", self.show_context_menu)
        # For macOS (usually Button-2 is right click)
        self.root.bind("<Button-2>", self.show_context_menu)

    def show_context_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_checkbutton(label=self.strings.lbl_always_on_top, 
                             variable=self.always_on_top, 
                             command=self.toggle_always_on_top)
        menu.post(event.x_root, event.y_root)

    def toggle_always_on_top(self):
        self.root.attributes("-topmost", self.always_on_top.get())

    def update_data(self):
        def task():
            success = False
            try:
                self.root.after(0, lambda: self.lbl_status.config(text=self.strings.fetching, fg="#ffff00"))
                with urllib.request.urlopen(self.strings.url_wttr, timeout=10) as response:
                    data = response.read()
                    json_data = json.loads(data)
                    info = self.logic.parse(json_data, forecast_mode=True)
                    self.root.after(0, lambda: self.refresh_ui(info))
                    success = True
            except Exception as e:
                print(f"Update error: {e}")
                error_msg = self.strings.err_fetch
                self.root.after(0, lambda: self.lbl_status.config(text=error_msg, fg="#ff5555"))
            
            # Schedule next update
            if success:
                # Normal interval
                self.root.after(self.update_interval_ms, self.update_data)
            else:
                # Retry in 1 second
                self.root.after(1000, self.update_data)

        threading.Thread(target=task, daemon=True).start()

    def refresh_ui(self, info):
        self.lbl_location.config(text=info['location'])
        
        # Icon
        emoji = get_emoji(info['category'])
        self.lbl_icon.config(text=emoji)
        
        # Text
        self.lbl_weather.config(text=info['label_text'])
        self.lbl_desc.config(text=info['description'])
        
        # Details
        self.lbl_temp.config(text=f"{self.strings.lbl_temp}: {info['temp']}{self.strings.unit_temp}")
        self.lbl_wind.config(text=f"{self.strings.lbl_wind}: {info['wind']} {self.strings.unit_wind}")
        self.lbl_humid.config(text=f"{self.strings.lbl_humidity}: {info['humidity']}%")
        
        p_text = info['precip_info'][0] if info['precip_info'] else ""
        self.lbl_precip.config(text=p_text)
        
        # Forecast
        if info['forecast']:
            fc_text = "\n".join(info['forecast'])
            self.lbl_forecast.config(text=fc_text)
        else:
            self.lbl_forecast.config(text="")

        # Warnings (Overlay or change color)
        if info['warnings']:
            self.lbl_status.config(text=" | ".join(info['warnings']), fg="#ff5555")
        else:
            self.lbl_status.config(text="")
            
        now_str = datetime.now().strftime('%H:%M:%S')
        self.lbl_update.config(text=f"{self.strings.last_update}: {now_str}")

    def run(self):
        # Initial update
        self.update_data()
        self.root.mainloop()

# -----------------------------------------------------------------------------
# Main Application Class (CLI)
# -----------------------------------------------------------------------------

class WeatherApp:
    def __init__(self):
        self.strings = Strings()
        self.logic = WeatherLogic(self.strings)
        self.interval = 0
        self.once = False
        self.forecast = False
        self.gui = False
        self.background = False
        
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
        print(self.strings.opt_g)
        print(self.strings.opt_y)
        print(self.strings.opt_h)
        print(self.strings.opt_v)
        print("")
        print(self.strings.usage_ex)
        print(f"  {prog} --interval 60")

    def show_version(self):
        print(f"Weather Monitor v{VERSION}")

    def parse_args(self):
        if len(sys.argv) == 1:
            self.show_help()
            sys.exit(0)

        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('-i', '--interval', type=int)
        parser.add_argument('-o', '--once', action='store_true')
        parser.add_argument('-f', '--forecast', action='store_true')
        parser.add_argument('-g', '--gui', action='store_true')
        parser.add_argument('-y', '--background', action='store_true')
        parser.add_argument('-h', '--help', action='store_true')
        parser.add_argument('-v', '--version', action='store_true')
        
        try:
            args, unknown = parser.parse_known_args()
        except SystemExit:
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
        self.gui = args.gui
        self.background = args.background

        if self.forecast:
            self.once = True
            
        # Validation
        if self.background and not self.gui:
            print(self.strings.err_y_only_g)
            sys.exit(1)

        if not self.once and not self.gui:
            if self.interval == 0:
                print(self.strings.err_no_interval)
                print(self.strings.use_h)
                sys.exit(1)
            elif self.interval < 0:
                print(self.strings.err_int_pos)
                sys.exit(1)

    def setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)

    def cleanup(self, signum=None, frame=None):
        if not self.gui:
            self.show_cursor()
        print("")
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

    def run(self):
        self.parse_args()
        
        if self.gui:
            if not HAS_TKINTER:
                print(self.strings.err_gui_no_tk)
                sys.exit(1)
                
            if self.background:
                try:
                    pid = os.fork()
                    if pid > 0:
                        # Parent process
                        return
                    os.setsid()
                except AttributeError:
                    # Windows
                    pass
                except Exception as e:
                    print(f"Background error: {e}")

            gui = WeatherGUI(self.strings, self.logic)
            gui.run()
            return

        # CLI Mode
        self.hide_cursor()
        self.show_banner()
        
        while True:
            print(self.strings.fetching)
            
            try:
                with urllib.request.urlopen(self.strings.url_wttr, timeout=10) as response:
                    data = response.read()
                    json_data = json.loads(data)
                    
                    self.clear_screen()
                    
                    info = self.logic.parse(json_data, self.forecast)
                    self.display_cli(info)
                    
                    if self.once:
                        self.show_cursor()
                        sys.exit(0)
                    
                    print("")
                    now_str = datetime.now().strftime('%H:%M:%S')
                    print(f"{self.strings.last_update}: {now_str}")
                    print(self.strings.exit_hint)
                    time.sleep(self.interval)
                    
            except (urllib.error.URLError, json.JSONDecodeError, ValueError) as e:
                self.clear_screen()
                print(self.strings.err_fetch)
                # print(e)
                print(self.strings.wait_retry)
                time.sleep(1)
            except KeyboardInterrupt:
                self.cleanup()

    def display_cli(self, info):
        print(get_drawing(info['label_ascii'], info['category']))
        
        print("========================================")
        print(f" {self.strings.lbl_cur_weather}: {info['label_text']}")
        print(f" {self.strings.lbl_detail}: {info['description']}")
        print("----------------------------------------")
        print(f" {self.strings.lbl_location}: {info['location']}")
        print(f" {self.strings.lbl_temp}: {info['temp']}{self.strings.unit_temp}")
        print(f" {self.strings.lbl_humidity}: {info['humidity']}%")
        print(f" {self.strings.lbl_wind}: {info['wind']} {self.strings.unit_wind}")
        print(f" {self.strings.lbl_pressure}: {info['pressure']} {self.strings.unit_pressure}")
        
        for line in info['precip_info']:
            print(f" {line}")

        print("========================================")
        
        for w in info['warnings']:
            print(f"{C_RED_BRIGHT}{w}{C_RESET}")
        
        if info['warnings']:
             print(f"{C_RED_BRIGHT}{self.strings.warn_update}{C_RESET}")
             
        if self.forecast and info['forecast']:
             print(self.strings.fc_title)
             for msg in info['forecast']:
                 print(msg)

if __name__ == "__main__":
    app = WeatherApp()
    app.run()
