# Weather Monitor CLI

ターミナル上で動作する、シンプルで視覚的な天気情報モニターです。
ASCIIアートを使用して天気を表示し、指定した更新間隔で[wttr.in](https://wttr.in)から最新の天気情報を取得・更新します。

## 機能

- **ASCIIアート表示**: 晴れ、曇り、雨、雪などの天気を視覚的なアスキーアートで表示します。
- **詳細情報**: 気温、湿度、風速、気圧、降水量などの詳細な気象データを表示します。
- **警報・注意報**: 激しい雨や強風、荒天（雷雨、吹雪など）を検知すると、赤字で警告メッセージを表示します。
- **自動更新**: ユーザーが指定した間隔（秒）で情報を定期的に更新します。
- **多言語対応**: システムの言語設定 (`LANG`) に応じて、日本語と英語の表示を自動的に切り替えます。

## 動作環境

以下のコマンドがシステムにインストールされている必要があります。

- `bash` (4.0以上推奨)
- `curl` (データ取得用)
- `jq` (JSON解析用)
- `bc` (数値計算用)

**インストール確認（Ubuntu/Debian系）:**

```bash
sudo apt update
sudo apt install curl jq bc
```

## 使用方法

スクリプトに実行権限を与えてから実行してください。

### 1. 実行権限の付与

```bash
chmod +x weather_monitor.sh
```

### 2. プログラムの実行

更新間隔（秒）を `--interval` オプションで指定して実行します。

```bash
# 例: 60秒ごとに更新
./weather_monitor.sh --interval 60

# 短縮形 (-i) も使用可能
./weather_monitor.sh -i 300
```

終了するには `Ctrl+C` を押してください。

### オプション一覧

| オプション | 説明 |
| :--- | :--- |
| `-i, --interval SECONDS` | **[必須]** 天気情報の更新間隔を秒単位で指定します。 |
| `-h, --help` | ヘルプメッセージを表示して終了します。 |
| `-v, --version` | バージョン情報を表示して終了します。 |

## スクリーンショットイメージ

実行すると、以下のような情報が表示されます（イメージ）。

```text
       \   /
        .-.       [ 晴れ ]
     -- (   ) --
        `-’
       /   \

========================================
 現在の天気: 晴れ
 詳細: 快晴
----------------------------------------
 地点: Tokyo
 気温: 25℃
 湿度: 40%
 風速: 15 km/h
 ...
```

## ライセンス

LICENSEファイルを参照してください。

---

# Weather Monitor CLI (English)

A simple, visual weather information monitor for the terminal.
It uses ASCII art to display weather conditions and fetches updates from [wttr.in](https://wttr.in) at specified intervals.

## Features

- **ASCII Art Display**: Visual representation of weather (Sunny, Cloudy, Rain, Snow, etc.).
- **Detailed Information**: Displays temperature, humidity, wind speed, pressure, precipitation, and more.
- **Warnings/Alerts**: Displays warnings in red for heavy rain, strong winds, or severe weather (storms, blizzards).
- **Auto Update**: Regularly updates information at user-defined intervals (in seconds).
- **Multi-language Support**: Automatically switches between Japanese and English based on your system language (`LANG`).

## Requirements

The following commands must be installed:

- `bash` (4.0+ recommended)
- `curl` (for data fetching)
- `jq` (for JSON parsing)
- `bc` (for calculations)

**Installation (Ubuntu/Debian):**

```bash
sudo apt update
sudo apt install curl jq bc
```

## Usage

Make sure to give execution permission to the script.

### 1. Grant Permission

```bash
chmod +x weather_monitor.sh
```

### 2. Run Program

Specify the update interval (in seconds) using `--interval`.

```bash
# Example: Update every 60 seconds
./weather_monitor.sh --interval 60

# Short form (-i)
./weather_monitor.sh -i 300
```

To exit, press `Ctrl+C`.

### Options

| Option | Description |
| :--- | :--- |
| `-i, --interval SECONDS` | **[Required]** Update interval in seconds. |
| `-o, --once` | Display once and exit. |
| `-h, --help` | Display help message. |
| `-v, --version` | Display version information. |

## Screenshot

```text
       \   /
        .-.       [ SUNNY ]
     -- (   ) --
        `-’
       /   \

========================================
 Current Weather: Sunny
 Detail: Clear
----------------------------------------
 Location: Tokyo
 Temp: 25C
 Humidity: 40%
 Wind: 15 km/h
 ...
```

## License

See the LICENSE file.
