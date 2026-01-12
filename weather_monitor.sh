#!/bin/bash

# =============================================================================
# Weather Monitor CLI (Bash)
# =============================================================================

VERSION="1.0.0"
INTERVAL=0

# -----------------------------------------------------------------------------
# Help and Version Functions
# -----------------------------------------------------------------------------

function show_help() {
    echo "使用方法: $(basename "$0") [オプション]"
    echo ""
    echo "指定した間隔で天気情報をポーリングし、ターミナルに表示します。"
    echo ""
    echo "オプション:"
    echo "  -i, --interval SECONDS   更新間隔（秒）。必須項目です。"
    echo "  -h, --help               このヘルプを表示して終了します。"
    echo "  -v, --version            バージョン情報を表示して終了します。"
    echo ""
    echo "例:"
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
        echo "エラー: 必要なコマンド '$cmd' が見つかりません。インストールしてください。"
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
                echo "エラー: --interval には正の整数を指定してください。"
                exit 1
            fi
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
            echo "不明なオプション: $1"
            show_help
            exit 1
            ;;
    esac
done

if [ "$INTERVAL" -eq 0 ]; then
    echo "エラー: 更新間隔を指定してください。"
    echo "ヘルプを表示するには -h を使用してください。"
    exit 0
fi

# -----------------------------------------------------------------------------
# ASCII Art Functions
# -----------------------------------------------------------------------------

function draw_sunny() {
    cat << "EOF"
      \   /
       .-.       [ 晴れ ]
    -- (   ) --
       `-’
      /   \
EOF
}

function draw_cloudy() {
    cat << "EOF"
      .--.
   .-(    ).     [ 曇り ]
  (___.__)__)
EOF
}

function draw_rainy() {
    cat << "EOF"
      .--.
   .-(    ).     [ 雨 ]
  (___.__)__)
   ' ' ' '
    ' ' ' '
EOF
}

function draw_snowy() {
    cat << "EOF"
      .--.
   .-(    ).     [ 雪 ]
  (___.__)__)
   *  *  *
    *  *  *
EOF
}

# -----------------------------------------------------------------------------
# Weather Logic
# -----------------------------------------------------------------------------

# wttr.in with JSON output and Japanese language
WEATHER_URL="https://wttr.in/?format=j1&lang=ja"

# Function to check and display warnings in RED
function check_warnings() {
    local desc="$1"
    local precip="$2"
    local wind="$3"
    
    local has_warning=0
    
    # Keywords for severe weather in English description
    if [[ "$desc" =~ "Heavy" ]] || [[ "$desc" =~ "Storm" ]] || [[ "$desc" =~ "Blizzard" ]] || [[ "$desc" =~ "Thunder" ]] || [[ "$desc" =~ "Torrential" ]]; then
        echo -e "\033[91m[警報] 激しい天候が検出されました: $desc\033[0m"
        has_warning=1
    fi
    
    # Heavy Rain warning (> 15mm)
    if (( $(echo "$precip >= 15.0" | bc -l) )); then
        echo -e "\033[91m[注意] 激しい雨が降っています: ${precip}mm\033[0m"
        has_warning=1
    fi

    # Strong Wind warning (> 50km/h)
    if (( $(echo "$wind >= 50.0" | bc -l) )); then
        echo -e "\033[91m[注意] 強風が吹いています: ${wind} km/h\033[0m"
        has_warning=1
    fi
    
    if [ $has_warning -eq 1 ]; then
        echo -e "\033[91m最新の気象情報に注意してください。\033[0m"
    fi
}

function process_weather() {
    local json="$1"
    
    # Extract current condition
    local current=$(echo "$json" | jq -r '.current_condition[0]')
    local location=$(echo "$json" | jq -r '.nearest_area[0].areaName[0].value')

    if [ "$current" == "null" ]; then
        echo "天気情報の解析に失敗しました。"
        return
    fi
    
    # Extract Data
    local desc_en=$(echo "$current" | jq -r '.weatherDesc[0].value')
    local desc_ja=$(echo "$current" | jq -r '.lang_ja[0].value')
    local temp=$(echo "$current" | jq -r '.temp_C')
    local precip=$(echo "$current" | jq -r '.precipMM')
    local humidity=$(echo "$current" | jq -r '.humidity')
    local wind=$(echo "$current" | jq -r '.windspeedKmph')
    local pressure=$(echo "$current" | jq -r '.pressure')
    
    # Determine Category
    local desc_lower=$(echo "$desc_en" | tr '[:upper:]' '[:lower:]')
    local category_ja=""
    
    # Basic logic to map description to 4 categories
    if [[ "$desc_lower" =~ "sun" ]] || [[ "$desc_lower" =~ "clear" ]]; then
        draw_sunny
        category_ja="晴れ"
    elif [[ "$desc_lower" =~ "rain" ]] || [[ "$desc_lower" =~ "drizzle" ]] || [[ "$desc_lower" =~ "shower" ]] || [[ "$desc_lower" =~ "thunder" ]]; then
        draw_rainy
        category_ja="雨"
    elif [[ "$desc_lower" =~ "snow" ]] || [[ "$desc_lower" =~ "ice" ]] || [[ "$desc_lower" =~ "blizzard" ]] || [[ "$desc_lower" =~ "sleet" ]]; then
        draw_snowy
        category_ja="雪"
    else
        # Default fallback for Cloudy, Mist, Fog, Overcast
        draw_cloudy
        category_ja="曇り"
    fi
    
    echo "========================================"
    echo " 現在の天気: $category_ja"
    echo " 詳細: $desc_ja"
    echo "----------------------------------------"
    echo " 地点: $location"
    echo " 気温: ${temp}℃"
    echo " 湿度: ${humidity}%"
    echo " 風速: ${wind} km/h"
    echo " 気圧: ${pressure} hPa"
    
    # Text details based on category
    if [[ "$category_ja" == "雨" ]]; then
        echo " 降水量: ${precip} mm"
        if (( $(echo "$precip < 2.0" | bc -l) )); then
             echo " 強度: バラツキあり/小雨"
        elif (( $(echo "$precip < 8.0" | bc -l) )); then
             echo " 強度: 通常の雨"
        else
             echo " 強度: 大雨"
        fi
    elif [[ "$category_ja" == "雪" ]]; then
        echo " 降水量(水換算): ${precip} mm"
        echo " 積雪の可能性があります。"
    elif [[ "$category_ja" == "曇り" ]] || [[ "$category_ja" == "晴れ" ]]; then
         # Usually precip is 0, but check just in case
         if (( $(echo "$precip > 0" | bc -l) )); then
             echo " 降水量: ${precip} mm (通り雨の可能性)"
         else
             echo " 降水量: 0.0 mm"
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
    echo -e "\nプログラムを終了します。"
    exit 0
}

trap cleanup SIGINT

while true; do
    # Clear screen and move to top
    echo -ne "\033[2J\033[H"
    
    echo "天気情報を取得中..."
    
    DATA=$(curl -s --max-time 10 "$WEATHER_URL")
    
    # Validate if we got JSON
    if [[ -z "$DATA" ]] || [[ "${DATA:0:1}" != "{" ]]; then
        echo -ne "\033[2J\033[H"
        echo "データの取得に失敗しました (Network Error or Invalid Response)"
        echo "再試行まで待機中... (${INTERVAL}秒)"
    else
        echo -ne "\033[2J\033[H"
        process_weather "$DATA"
        echo ""
        echo "最終更新: $(date '+%H:%M:%S')"
        echo "(終了: Ctrl+C)"
    fi
    
    sleep "$INTERVAL"
done
