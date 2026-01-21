#!/bin/bash

# =============================================================================
# Weather Monitor CLI (Bash)
# =============================================================================

VERSION="2.0.0"
INTERVAL=0
ONCE=false
FORECAST=false

# -----------------------------------------------------------------------------
# Localization / Strings
# -----------------------------------------------------------------------------

if [[ "${LANG:-}" == ja* ]]; then
    IS_JP=true
    
    # Usage / Help
    TXT_USAGE_TITLE="使用方法: $(basename "$0") [オプション]"
    TXT_USAGE_DESC="指定した間隔で天気情報をポーリングし、ターミナルに表示します。"
    TXT_OPT_HEADER="オプション:"
    TXT_OPT_I="  -i, --interval SECONDS   更新間隔（秒）。必須項目です（--once 指定時は不要）。"
    TXT_OPT_O="  -o, --once               1回だけ表示して終了します（エラー時はリトライします）。"
    TXT_OPT_F="  -f, --forecast           8時間先までの予報を確認します（--onceと同様に終了します）。"
    TXT_OPT_H="  -h, --help               このヘルプを表示して終了します。"
    TXT_OPT_V="  -v, --version            バージョン情報を表示して終了します。"
    TXT_USAGE_EX="例:"
    
    # Errors & Status
    TXT_ERR_REQ_CMD="エラー: 必要なコマンド '%s' が見つかりません。インストールしてください。"
    TXT_ERR_INT_POS="エラー: --interval には正の整数を指定してください。"
    TXT_ERR_UNKNOWN_OPT="不明なオプション"
    TXT_ERR_NO_INTERVAL="エラー: 更新間隔を指定してください。"
    TXT_USE_H="ヘルプを表示するには -h を使用してください。"
    TXT_EXIT_MSG="プログラムを終了します。"
    TXT_EXIT_HINT="(終了: Ctrl+C)"
    TXT_FETCHING="天気情報を取得中..."
    TXT_ERR_FETCH="データの取得に失敗、またはデータが破損しています"
    TXT_WAIT_RETRY="再試行まで待機中... (1秒)"
    TXT_LAST_UPDATE="最終更新"
    
    # Weather Display Labels
    TXT_LBL_SUNNY=" 晴れ "
    TXT_LBL_CLOUDY=" 曇り "
    TXT_LBL_RAIN="  雨  "
    TXT_LBL_SNOW="  雪  "
    
    # Weather Data Labels
    TXT_CUR_WEATHER="現在の天気"
    TXT_DETAIL="詳細"
    TXT_LOCATION="地点"
    TXT_TEMP="気温"
    TXT_HUMIDITY="湿度"
    TXT_WIND="風速"
    TXT_PRESSURE="気圧"
    TXT_PRECIP="降水量"
    TXT_PRECIP_LIQ="降水量(水換算)"
    TXT_INTENSITY="強度"
    
    # Weather Categories & Descriptions
    TXT_CAT_SUNNY="晴れ"
    TXT_CAT_SNOW="雪"
    TXT_CAT_RAIN="雨"
    TXT_CAT_CLOUDY="曇り"
    
    TXT_INT_LIGHT="バラツキあり/小雨"
    TXT_INT_MOD="通常の雨"
    TXT_INT_HEAVY="大雨"
    TXT_SNOW_ACC="積雪の可能性があります。"
    TXT_SHOWER_POS="(通り雨の可能性)"
    TXT_ERR_PARSE="天気情報の解析に失敗しました。"
    
    # Warnings
    TXT_WARN_PREFIX="[警報]"
    TXT_CAUTION_PREFIX="[注意]"
    TXT_WARN_SEVERE="激しい天候が検出されました"
    TXT_WARN_RAIN="激しい雨が降っています"
    TXT_WARN_WIND="強風が吹いています"
    TXT_WARN_UPDATE="最新の気象情報に注意してください。"

    # Forecast
    TXT_FC_TITLE="[予報]"
    TXT_FC_RAIN="%d時間後に雨になります。"
    TXT_FC_NO_RAIN_CLOUDY="%d時間後に雨はやみます。曇るでしょう。"
    TXT_FC_NO_RAIN_SUNNY="%d時間後に雨はやみます。晴れるでしょう。"
    TXT_FC_GENERIC="%d時間後に%sになります。"
    
    # Logic
    URL_WTTR="https://wttr.in/?format=j1&lang=ja"
    
    # Units (explicitly defined for flexibility)
    UNIT_TEMP="°C"
    UNIT_PRECIP="mm"
    UNIT_WIND="km/h"
    UNIT_PRESSURE="hPa"

else
    IS_JP=false
    
    # Usage / Help
    TXT_USAGE_TITLE="Usage: $(basename "$0") [OPTIONS]"
    TXT_USAGE_DESC="Polls weather information at specified intervals and displays it in the terminal."
    TXT_OPT_HEADER="Options:"
    TXT_OPT_I="  -i, --interval SECONDS   Update interval in seconds. Required (unless --once is used)."
    TXT_OPT_O="  -o, --once               Display once and exit (retry on error)."
    TXT_OPT_F="  -f, --forecast           Check forecast for next 8 hours (behaves like --once)."
    TXT_OPT_H="  -h, --help               Display this help and exit."
    TXT_OPT_V="  -v, --version            Display version information and exit."
    TXT_USAGE_EX="Example:"
    
    # Errors & Status
    TXT_ERR_REQ_CMD="Error: Required command '%s' not found. Please install it."
    TXT_ERR_INT_POS="Error: Please specify a positive integer for --interval."
    TXT_ERR_UNKNOWN_OPT="Unknown option"
    TXT_ERR_NO_INTERVAL="Error: Please specify an update interval."
    TXT_USE_H="Use -h for help."
    TXT_EXIT_MSG="Exiting program."
    TXT_EXIT_HINT="(Exit: Ctrl+C)"
    TXT_FETCHING="Fetching weather info..."
    TXT_ERR_FETCH="Failed to retrieve data or data is corrupted."
    TXT_WAIT_RETRY="Waiting to retry... (1s)"
    TXT_LAST_UPDATE="Last Update"
    
    # Weather Display Labels
    TXT_LBL_SUNNY="SUNNY"
    TXT_LBL_CLOUDY="CLOUDY"
    TXT_LBL_RAIN=" RAIN "
    TXT_LBL_SNOW=" SNOW "
    
    # Weather Data Labels
    TXT_CUR_WEATHER="Current Weather"
    TXT_DETAIL="Detail"
    TXT_LOCATION="Location"
    TXT_TEMP="Temp"
    TXT_HUMIDITY="Humidity"
    TXT_WIND="Wind"
    TXT_PRESSURE="Pressure"
    TXT_PRECIP="Precip"
    TXT_PRECIP_LIQ="Precip (Liquid)"
    TXT_INTENSITY="Intensity"
    
    # Weather Categories & Descriptions
    TXT_CAT_SUNNY="Sunny"
    TXT_CAT_SNOW="Snow"
    TXT_CAT_RAIN="Rain"
    TXT_CAT_CLOUDY="Cloudy"
    
    TXT_INT_LIGHT="Light/Patchy"
    TXT_INT_MOD="Moderate"
    TXT_INT_HEAVY="Heavy"
    TXT_SNOW_ACC="Possibility of snow accumulation."
    TXT_SHOWER_POS="(Possible showers)"
    TXT_ERR_PARSE="Failed to parse weather information."
    
    # Warnings
    TXT_WARN_PREFIX="[WARNING]"
    TXT_CAUTION_PREFIX="[CAUTION]"
    TXT_WARN_SEVERE="Severe weather detected"
    TXT_WARN_RAIN="Heavy rain"
    TXT_WARN_WIND="Strong wind"
    TXT_WARN_UPDATE="Please stay updated with the latest weather info."

    # Forecast
    TXT_FC_TITLE="[Forecast]"
    TXT_FC_RAIN="It will rain in %d hours."
    TXT_FC_NO_RAIN_CLOUDY="Rain will stop in %d hours. It will be cloudy."
    TXT_FC_NO_RAIN_SUNNY="Rain will stop in %d hours. It will be sunny."
    TXT_FC_GENERIC="It will be %s in %d hours."
    
    # Logic
    URL_WTTR="https://wttr.in/?format=j1&lang=en"

    # Units
    UNIT_TEMP="°C"
    UNIT_PRECIP="mm"
    UNIT_WIND="km/h"
    UNIT_PRESSURE="hPa"

fi

# -----------------------------------------------------------------------------
# Help and Version Functions
# -----------------------------------------------------------------------------

function show_help() {
    echo "$TXT_USAGE_TITLE"
    echo ""
    echo "$TXT_USAGE_DESC"
    echo ""
    echo "$TXT_OPT_HEADER"
    echo "$TXT_OPT_I"
    echo "$TXT_OPT_O"
    echo "$TXT_OPT_F"
    echo "$TXT_OPT_H"
    echo "$TXT_OPT_V"
    echo ""
    echo "$TXT_USAGE_EX"
    echo "  $(basename "$0") --interval 60"
}

function show_version() {
    echo "Weather Monitor v$VERSION"
}

# -----------------------------------------------------------------------------
# Dependency Check
# -----------------------------------------------------------------------------

for cmd in curl jq bc; do
    if ! command -v $cmd &> /dev/null; then
        printf "$TXT_ERR_REQ_CMD\n" "$cmd"
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
                echo "$TXT_ERR_INT_POS"
                exit 1
            fi
            ;;
        -o|--once)
            ONCE=true
            shift
            ;;
        -f|--forecast)
            FORECAST=true
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
            echo "$TXT_ERR_UNKNOWN_OPT: $1"
            show_help
            exit 1
            ;;
    esac
done

if [ "$ONCE" = false ] && [ "$INTERVAL" -eq 0 ]; then
    echo "$TXT_ERR_NO_INTERVAL"
    echo "$TXT_USE_H"
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
    cat << EOF
       \\   /
       .-.       [ $TXT_LBL_SUNNY ]
    -- (   ) --
       \`-’
       /   \\
EOF
}

function draw_cloudy() {
    cat << EOF
       .--.
    .-(    ).     [ $TXT_LBL_CLOUDY ]
   (___.__)__)
EOF
}

function draw_rainy() {
    cat << EOF
       .--.
    .-(    ).     [ $TXT_LBL_RAIN ]
   (___.__)__)
    ' ' ' '
     ' ' ' '
EOF
}

function draw_snowy() {
    cat << EOF
       .--.
    .-(    ).     [ $TXT_LBL_SNOW ]
   (___.__)__)
    *  *  *
     *  *  *
EOF
}

# -----------------------------------------------------------------------------
# Weather Logic
# -----------------------------------------------------------------------------

function get_category_key() {
    local desc_lower=$(echo "$1" | tr '[:upper:]' '[:lower:]')
    if [[ "$desc_lower" =~ "sun" ]] || [[ "$desc_lower" =~ "clear" ]]; then
        echo "SUNNY"
    elif [[ "$desc_lower" =~ "snow" ]] || [[ "$desc_lower" =~ "ice" ]] || [[ "$desc_lower" =~ "blizzard" ]] || [[ "$desc_lower" =~ "sleet" ]]; then
        echo "SNOW"
    elif [[ "$desc_lower" =~ "rain" ]] || [[ "$desc_lower" =~ "drizzle" ]] || [[ "$desc_lower" =~ "shower" ]] || [[ "$desc_lower" =~ "thunder" ]]; then
        echo "RAIN"
    else
        echo "CLOUDY"
    fi
}

function check_forecast_change() {
    local json="$1"
    local current_cat="$2"
    
    local start_hour=$((10#$(date +%H)))
    
    for offset in {1..8}; do
        local check_hour=$((start_hour + offset))
        local day_offset=$((check_hour / 24))
        local hour_of_day=$((check_hour % 24))
        
        # 3-hour block index
        local block_idx=$((hour_of_day / 3))
        # time string for jq (0, 300, 600...)
        local time_str=$((block_idx * 300))
        
        local target_desc=$(echo "$json" | jq -r ".weather[$day_offset].hourly[] | select(.time == \"$time_str\") | .weatherDesc[0].value" 2>/dev/null | head -n 1)
        
        if [ -z "$target_desc" ]; then continue; fi
        
        local target_cat=$(get_category_key "$target_desc")
        
        if [ "$target_cat" != "$current_cat" ]; then
             echo "$TXT_FC_TITLE"
             
             if [ "$target_cat" == "RAIN" ]; then
                 printf "$TXT_FC_RAIN\n" "$offset"
             elif [ "$current_cat" == "RAIN" ]; then
                  if [ "$target_cat" == "CLOUDY" ]; then
                      printf "$TXT_FC_NO_RAIN_CLOUDY\n" "$offset"
                  elif [ "$target_cat" == "SUNNY" ]; then
                      printf "$TXT_FC_NO_RAIN_SUNNY\n" "$offset"
                  else
                      local label_local=""
                      case "$target_cat" in
                          SUNNY) label_local="$TXT_CAT_SUNNY" ;;
                          CLOUDY) label_local="$TXT_CAT_CLOUDY" ;;
                          SNOW) label_local="$TXT_CAT_SNOW" ;;
                      esac
                       printf "$TXT_FC_GENERIC\n" "$offset" "$label_local"
                  fi
             else
                  local label_local=""
                  case "$target_cat" in
                      SUNNY) label_local="$TXT_CAT_SUNNY" ;;
                      CLOUDY) label_local="$TXT_CAT_CLOUDY" ;;
                      SNOW) label_local="$TXT_CAT_SNOW" ;;
                      RAIN) label_local="$TXT_CAT_RAIN" ;;
                  esac
                  printf "$TXT_FC_GENERIC\n" "$offset" "$label_local"
             fi
             return 0
        fi
    done
}

# Function to check and display warnings in RED
function check_warnings() {
    local desc="$1"
    local precip="$2"
    local wind="$3"
    
    local has_warning=0
    
    # Keywords for severe weather in English description
    if [[ "$desc" =~ "Heavy" ]] || [[ "$desc" =~ "Storm" ]] || [[ "$desc" =~ "Blizzard" ]] || [[ "$desc" =~ "Thunder" ]] || [[ "$desc" =~ "Torrential" ]]; then
        echo -e "\033[91m${TXT_WARN_PREFIX} ${TXT_WARN_SEVERE}: $desc\033[0m"
        has_warning=1
    fi
    
    # Heavy Rain warning (> 15mm)
    if (( $(echo "$precip >= 15.0" | bc -l) )); then
        echo -e "\033[91m${TXT_CAUTION_PREFIX} ${TXT_WARN_RAIN}: ${precip}${UNIT_PRECIP}\033[0m"
        has_warning=1
    fi

    # Strong Wind warning (> 50km/h)
    if (( $(echo "$wind >= 50.0" | bc -l) )); then
        echo -e "\033[91m${TXT_CAUTION_PREFIX} ${TXT_WARN_WIND}: ${wind} ${UNIT_WIND}\033[0m"
        has_warning=1
    fi
    
    if [ $has_warning -eq 1 ]; then
        echo -e "\033[91m${TXT_WARN_UPDATE}\033[0m"
    fi
}

function process_weather() {
    local json="$1"
    
    # Extract current condition
    local current=$(echo "$json" | jq -r '.current_condition[0]')
    local location=$(echo "$json" | jq -r '.nearest_area[0].areaName[0].value')

    if [ "$current" == "null" ]; then
        echo "$TXT_ERR_PARSE"
        return
    fi
    
    # Extract Data
    local desc_en=$(echo "$current" | jq -r '.weatherDesc[0].value')
    local weather_desc="$desc_en"
    
    # If JA, try to get localized description
    if [ "$IS_JP" = true ]; then
        weather_desc=$(echo "$current" | jq -r '.lang_ja[0].value')
    fi
    
    local temp=$(echo "$current" | jq -r '.temp_C')
    local precip=$(echo "$current" | jq -r '.precipMM')
    local humidity=$(echo "$current" | jq -r '.humidity')
    local wind=$(echo "$current" | jq -r '.windspeedKmph')
    local pressure=$(echo "$current" | jq -r '.pressure')
    
    # Determine Category
    # Use helper
    local category=$(get_category_key "$desc_en")
    local category_label=""
    
    if [ "$category" == "SUNNY" ]; then
        draw_sunny
        category_label="$TXT_CAT_SUNNY"
    elif [ "$category" == "SNOW" ]; then
        draw_snowy
        category_label="$TXT_CAT_SNOW"
    elif [ "$category" == "RAIN" ]; then
        draw_rainy
        category_label="$TXT_CAT_RAIN"
    else
        # Default fallback for Cloudy, Mist, Fog, Overcast
        draw_cloudy
        category="CLOUDY"
        category_label="$TXT_CAT_CLOUDY"
    fi
    
    echo "========================================"
    echo " $TXT_CUR_WEATHER: $category_label"
    echo " $TXT_DETAIL: $weather_desc"
    echo "----------------------------------------"
    echo " $TXT_LOCATION: $location"
    echo " $TXT_TEMP: ${temp}${UNIT_TEMP}"
    echo " $TXT_HUMIDITY: ${humidity}%"
    echo " $TXT_WIND: ${wind} ${UNIT_WIND}"
    echo " $TXT_PRESSURE: ${pressure} ${UNIT_PRESSURE}"
    
    # Text details based on category
    if [[ "$category" == "RAIN" ]]; then
        echo " $TXT_PRECIP: ${precip} ${UNIT_PRECIP}"
        
        if (( $(echo "$precip < 2.0" | bc -l) )); then
             echo " $TXT_INTENSITY: $TXT_INT_LIGHT"
        elif (( $(echo "$precip < 8.0" | bc -l) )); then
             echo " $TXT_INTENSITY: $TXT_INT_MOD"
        else
             echo " $TXT_INTENSITY: $TXT_INT_HEAVY"
        fi
    elif [[ "$category" == "SNOW" ]]; then
        echo " $TXT_PRECIP_LIQ: ${precip} ${UNIT_PRECIP}"
        echo " $TXT_SNOW_ACC"
    elif [[ "$category" == "CLOUDY" ]] || [[ "$category" == "SUNNY" ]]; then
         # Usually precip is 0, but check just in case
         if (( $(echo "$precip > 0" | bc -l) )); then
             echo " $TXT_PRECIP: ${precip} ${UNIT_PRECIP} $TXT_SHOWER_POS"
         else
             echo " $TXT_PRECIP: 0.0 ${UNIT_PRECIP}"
         fi
    fi 

    echo "========================================"
    
    # Check for warnings
    check_warnings "$desc_en" "$precip" "$wind"

    if [ "$FORECAST" = true ]; then
        check_forecast_change "$json" "$category"
    fi
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
    trap - EXIT SIGINT SIGTERM
    if command -v tput &> /dev/null; then
        tput cnorm
    else
        echo -ne "\033[?25h"
    fi
    echo ""
    exit 0
}

trap cleanup EXIT SIGINT SIGTERM

# Show startup banner
show_banner

while true; do
    # Show loading status
    echo "$TXT_FETCHING"
    
    DATA=$(curl -s --max-time 10 "$URL_WTTR")
    
    # Validate if we got JSON and check for parse errors
    if [[ -z "$DATA" ]] || [[ "${DATA:0:1}" != "{" ]] || ! echo "$DATA" | jq empty > /dev/null 2>&1; then
        echo -ne "\033[2J\033[H"
        echo "$TXT_ERR_FETCH"
        echo "$TXT_WAIT_RETRY"
        sleep 1
    else
        echo -ne "\033[2J\033[H"
        process_weather "$DATA"
        echo ""
        echo "$TXT_LAST_UPDATE: $(date '+%H:%M:%S')"
        
        if [ "$ONCE" = true ]; then
            exit 0
        fi

        echo "$TXT_EXIT_HINT"
        sleep "$INTERVAL"
    fi
done
