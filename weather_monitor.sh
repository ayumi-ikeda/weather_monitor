#!/bin/bash

# =============================================================================
# Weather Monitor CLI (Bash)
# =============================================================================

VERSION="1.2.0"
INTERVAL=0
ONCE=false

# Check Language Environment
if [[ "${LANG:-}" == ja* ]]; then
    IS_JP=true
else
    IS_JP=false
fi

# -----------------------------------------------------------------------------
# Help and Version Functions
# -----------------------------------------------------------------------------

function show_help() {
    if [ "$IS_JP" = true ]; then
        echo "使用方法: $(basename "$0") [オプション]"
        echo ""
        echo "指定した間隔で天気情報をポーリングし、ターミナルに表示します。"
        echo ""
        echo "オプション:"
        echo "  -i, --interval SECONDS   更新間隔（秒）。必須項目です（--once 指定時は不要）。"
        echo "  -o, --once               1回だけ表示して終了します（エラー時はリトライします）。"
        echo "  -h, --help               このヘルプを表示して終了します。"
        echo "  -v, --version            バージョン情報を表示して終了します。"
        echo ""
        echo "例:"
        echo "  $(basename "$0") --interval 60"
    else
        echo "Usage: $(basename "$0") [OPTIONS]"
        echo ""
        echo "Polls weather information at specified intervals and displays it in the terminal."
        echo ""
        echo "Options:"
        echo "  -i, --interval SECONDS   Update interval in seconds. Required (unless --once is used)."
        echo "  -o, --once               Display once and exit (retry on error)."
        echo "  -h, --help               Display this help and exit."
        echo "  -v, --version            Display version information and exit."
        echo ""
        echo "Example:"
        echo "  $(basename "$0") --interval 60"
    fi
}

function show_version() {
    echo "Weather Monitor v$VERSION"
}

# -----------------------------------------------------------------------------
# Dependency Check
# -----------------------------------------------------------------------------

for cmd in curl jq bc; do
    if ! command -v $cmd &> /dev/null; then
        if [ "$IS_JP" = true ]; then
            echo "エラー: 必要なコマンド '$cmd' が見つかりません。インストールしてください。"
        else
            echo "Error: Required command '$cmd' not found. Please install it."
        fi
        exit 1
    fi
done

# -----------------------------------------------------------------------------
# Argument Parsing
# -----------------------------------------------------------------------------

if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        -i|--interval)
            if [[ -n "$2" && "$2" =~ ^[0-9]+$ ]]; then
                INTERVAL="$2"
                shift 2
            else
                if [ "$IS_JP" = true ]; then
                    echo "エラー: --interval には正の整数を指定してください。"
                else
                    echo "Error: Please specify a positive integer for --interval."
                fi
                exit 1
            fi
            ;;
        -o|--once)
            ONCE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--version)
            show_version
            exit 0
            ;;
        *)
            if [ "$IS_JP" = true ]; then
                echo "不明なオプション: $1"
            else
                echo "Unknown option: $1"
            fi
            show_help
            exit 1
            ;;
    esac
done

if [ "$ONCE" = false ] && [ "$INTERVAL" -eq 0 ]; then
    if [ "$IS_JP" = true ]; then
        echo "エラー: 更新間隔を指定してください。"
        echo "ヘルプを表示するには -h を使用してください。"
    else
        echo "Error: Please specify an update interval."
        echo "Use -h for help."
    fi
    exit 1
fi

# -----------------------------------------------------------------------------
# ASCII Art Functions
# -----------------------------------------------------------------------------

function show_banner() {
    # Colors
    local C_CYAN="\033[0;36m"
    local C_BLUE="\033[0;34m"
    local C_YELLOW="\033[1;33m"
    local C_GREEN="\033[1;32m"
    local C_RESET="\033[0m"

    # Clear screen
    echo -ne "\033[2J\033[H"

    echo -e "${C_CYAN}"
    cat << "EOF"
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
                                              
EOF
    echo -e "${C_YELLOW}        >>> Weather Monitor v${VERSION} <<<${C_RESET}"
    echo -e "${C_GREEN}    Designed for clear skies and happy days.${C_RESET}"
    echo ""
    sleep 2
}

function draw_sunny() {
    local label="SUNNY"
    [ "$IS_JP" = true ] && label=" 晴れ "
    cat << EOF
      \   /
       .-.       [ $label ]
    -- (   ) --
       \`-’
      /   \
EOF
}

function draw_cloudy() {
    local label="CLOUDY"
    [ "$IS_JP" = true ] && label=" 曇り "
    cat << EOF
      .--.
   .-(    ).     [ $label ]
  (___.__)__)
EOF
}

function draw_rainy() {
    local label=" RAIN "
    [ "$IS_JP" = true ] && label="  雨  "
    cat << EOF
      .--.
   .-(    ).     [ $label ]
  (___.__)__)
   ' ' ' '
    ' ' ' '
EOF
}

function draw_snowy() {
    local label=" SNOW "
    [ "$IS_JP" = true ] && label="  雪  "
    cat << EOF
      .--.
   .-(    ).     [ $label ]
  (___.__)__)
   *  *  *
    *  *  *
EOF
}

# -----------------------------------------------------------------------------
# Weather Logic
# -----------------------------------------------------------------------------

# wttr.in with JSON output
# If Japanese, request localized. Otherwise default (English).
if [ "$IS_JP" = true ]; then
    WEATHER_URL="https://wttr.in/?format=j1&lang=ja"
else
    WEATHER_URL="https://wttr.in/?format=j1&lang=en"
fi

# Function to check and display warnings in RED
function check_warnings() {
    local desc="$1"
    local precip="$2"
    local wind="$3"
    
    local has_warning=0
    
    # Keywords for severe weather in English description
    if [[ "$desc" =~ "Heavy" ]] || [[ "$desc" =~ "Storm" ]] || [[ "$desc" =~ "Blizzard" ]] || [[ "$desc" =~ "Thunder" ]] || [[ "$desc" =~ "Torrential" ]]; then
        if [ "$IS_JP" = true ]; then
            echo -e "\033[91m[警報] 激しい天候が検出されました: $desc\033[0m"
        else
            echo -e "\033[91m[WARNING] Severe weather detected: $desc\033[0m"
        fi
        has_warning=1
    fi
    
    # Heavy Rain warning (> 15mm)
    if (( $(echo "$precip >= 15.0" | bc -l) )); then
        if [ "$IS_JP" = true ]; then
            echo -e "\033[91m[注意] 激しい雨が降っています: ${precip}mm\033[0m"
        else
            echo -e "\033[91m[CAUTION] Heavy rain: ${precip}mm\033[0m"
        fi
        has_warning=1
    fi

    # Strong Wind warning (> 50km/h)
    if (( $(echo "$wind >= 50.0" | bc -l) )); then
        if [ "$IS_JP" = true ]; then
            echo -e "\033[91m[注意] 強風が吹いています: ${wind} km/h\033[0m"
        else
            echo -e "\033[91m[CAUTION] Strong wind: ${wind} km/h\033[0m"
        fi
        has_warning=1
    fi
    
    if [ $has_warning -eq 1 ]; then
        if [ "$IS_JP" = true ]; then
            echo -e "\033[91m最新の気象情報に注意してください。\033[0m"
        else
            echo -e "\033[91mPlease stay updated with the latest weather info.\033[0m"
        fi
    fi
}

function process_weather() {
    local json="$1"
    
    # Extract current condition
    local current=$(echo "$json" | jq -r '.current_condition[0]')
    local location=$(echo "$json" | jq -r '.nearest_area[0].areaName[0].value')

    if [ "$current" == "null" ]; then
        if [ "$IS_JP" = true ]; then
            echo "天気情報の解析に失敗しました。"
        else
            echo "Failed to parse weather information."
        fi
        return
    fi
    
    # Extract Data
    local desc_en=$(echo "$current" | jq -r '.weatherDesc[0].value')
    local desc_ja=""
    if [ "$IS_JP" = true ]; then
        desc_ja=$(echo "$current" | jq -r '.lang_ja[0].value')
    fi
    local temp=$(echo "$current" | jq -r '.temp_C')
    local precip=$(echo "$current" | jq -r '.precipMM')
    local humidity=$(echo "$current" | jq -r '.humidity')
    local wind=$(echo "$current" | jq -r '.windspeedKmph')
    local pressure=$(echo "$current" | jq -r '.pressure')
    
    # Determine Category
    local desc_lower=$(echo "$desc_en" | tr '[:upper:]' '[:lower:]')
    local category=""
    local category_label=""
    
    # Basic logic to map description to 4 categories
    if [[ "$desc_lower" =~ "sun" ]] || [[ "$desc_lower" =~ "clear" ]]; then
        draw_sunny
        category="SUNNY"
        if [ "$IS_JP" = true ]; then category_label="晴れ"; else category_label="Sunny"; fi
    elif [[ "$desc_lower" =~ "snow" ]] || [[ "$desc_lower" =~ "ice" ]] || [[ "$desc_lower" =~ "blizzard" ]] || [[ "$desc_lower" =~ "sleet" ]]; then
        draw_snowy
        category="SNOW"
        if [ "$IS_JP" = true ]; then category_label="雪"; else category_label="Snow"; fi
    elif [[ "$desc_lower" =~ "rain" ]] || [[ "$desc_lower" =~ "drizzle" ]] || [[ "$desc_lower" =~ "shower" ]] || [[ "$desc_lower" =~ "thunder" ]]; then
        draw_rainy
        category="RAIN"
        if [ "$IS_JP" = true ]; then category_label="雨"; else category_label="Rain"; fi
    else
        # Default fallback for Cloudy, Mist, Fog, Overcast
        draw_cloudy
        category="CLOUDY"
        if [ "$IS_JP" = true ]; then category_label="曇り"; else category_label="Cloudy"; fi
    fi
    
    echo "========================================"
    if [ "$IS_JP" = true ]; then
        echo " 現在の天気: $category_label"
        echo " 詳細: $desc_ja"
        echo "----------------------------------------"
        echo " 地点: $location"
        echo " 気温: ${temp}℃"
        echo " 湿度: ${humidity}%"
        echo " 風速: ${wind} km/h"
        echo " 気圧: ${pressure} hPa"
    else
        echo " Current Weather: $category_label"
        echo " Detail: $desc_en"
        echo "----------------------------------------"
        echo " Location: $location"
        echo " Temp: ${temp}C"
        echo " Humidity: ${humidity}%"
        echo " Wind: ${wind} km/h"
        echo " Pressure: ${pressure} hPa"
    fi
    
    # Text details based on category
    if [[ "$category" == "RAIN" ]]; then
        if [ "$IS_JP" = true ]; then
            echo " 降水量: ${precip} mm"
        else
            echo " Precip: ${precip} mm"
        fi
        
        if (( $(echo "$precip < 2.0" | bc -l) )); then
             if [ "$IS_JP" = true ]; then echo " 強度: バラツキあり/小雨"; else echo " Intensity: Light/Patchy"; fi
        elif (( $(echo "$precip < 8.0" | bc -l) )); then
             if [ "$IS_JP" = true ]; then echo " 強度: 通常の雨"; else echo " Intensity: Moderate"; fi
        else
             if [ "$IS_JP" = true ]; then echo " 強度: 大雨"; else echo " Intensity: Heavy"; fi
        fi
    elif [[ "$category" == "SNOW" ]]; then
        if [ "$IS_JP" = true ]; then
            echo " 降水量(水換算): ${precip} mm"
            echo " 積雪の可能性があります。"
        else
            echo " Precip (Liquid): ${precip} mm"
            echo " Possibility of snow accumulation."
        fi
    elif [[ "$category" == "CLOUDY" ]] || [[ "$category" == "SUNNY" ]]; then
         # Usually precip is 0, but check just in case
         if (( $(echo "$precip > 0" | bc -l) )); then
             if [ "$IS_JP" = true ]; then
                 echo " 降水量: ${precip} mm (通り雨の可能性)"
             else
                 echo " Precip: ${precip} mm (Possible showers)"
             fi
         else
             if [ "$IS_JP" = true ]; then
                 echo " 降水量: 0.0 mm"
             else
                 echo " Precip: 0.0 mm"
             fi
         fi
    fi 

    echo "========================================"
    
    # Check for warnings
    check_warnings "$desc_en" "$precip" "$wind"
}

# -----------------------------------------------------------------------------
# Main Loop
# -----------------------------------------------------------------------------

# Hide cursor if tput available
if command -v tput &> /dev/null; then
    tput civis
else
    echo -ne "\033[?25l"
fi

# Cleanup on exit
cleanup() {
    if command -v tput &> /dev/null; then
        tput cnorm
    else
        echo -ne "\033[?25h"
    fi
    echo ""
    if [ "$IS_JP" = true ]; then
        echo "プログラムを終了します。"
    else
        echo "Exiting program."
    fi
    exit 0
}

trap cleanup SIGINT

# Show startup banner
show_banner

while true; do
    # Show loading status
    if [ "$IS_JP" = true ]; then
        echo "天気情報を取得中..."
    else
        echo "Fetching weather info..."
    fi
    
    DATA=$(curl -s --max-time 10 "$WEATHER_URL")
    
    # Validate if we got JSON and check for parse errors
    if [[ -z "$DATA" ]] || [[ "${DATA:0:1}" != "{" ]] || ! echo "$DATA" | jq empty > /dev/null 2>&1; then
        echo -ne "\033[2J\033[H"
        if [ "$IS_JP" = true ]; then
            echo "データの取得に失敗、またはデータが破損しています"
            echo "再試行まで待機中... (1秒)"
        else
            echo "Failed to retrieve data or data is corrupted."
            echo "Waiting to retry... (1s)"
        fi
        sleep 1
    else
        echo -ne "\033[2J\033[H"
        process_weather "$DATA"
        echo ""
        if [ "$IS_JP" = true ]; then
            echo "最終更新: $(date '+%H:%M:%S')"
        else
            echo "Last Update: $(date '+%H:%M:%S')"
        fi
        
        if [ "$ONCE" = true ]; then
            exit 0
        fi

        if [ "$IS_JP" = true ]; then
            echo "(終了: Ctrl+C)"
        else
            echo "(Exit: Ctrl+C)"
        fi
        sleep "$INTERVAL"
    fi
done
