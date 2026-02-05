# ASL3 Weather Announcer

**ASL3 Weather Announcer** is a flexible, multi-country weather alert and reporting system designed for AllStarLink 3 (Asterisk) nodes.

It provides **automated verbal announcements** for:
*   **Active Weather Alerts**: Warnings, watches, and advisories as they are issued.
*   **Daily Reports**: Detailed forecast, current conditions, sunrise/sunset, and moon phase.
*   **Time Announcements**: Current local time at start of report.

## Features

*   **Multi-Provider Support**:
    *   🇺🇸 **USA**: Uses National Weather Service (NWS) API.
    *   🇨🇦 **Canada**: Uses Environment Canada data.
    *   *Extensible*: Plugin architecture allows adding more countries easily.
*   **Smart Location**:
    *   **GPS/GNSS**: Automatically detects location using `gpsd`.
    *   **Static**: Configurable fallback lat/lon.
    *   **Auto-Zone**: Automatically monitors the correct County, Forecast Zone, and Fire Weather Zone for your location.
*   **Multi-Language Support** (New!):
    *   **Languages**: Full support for **English** and **French** (added 2/4/26).
    *   **Extensible**: Designed to easily adapt for **Spanish, German, and Italian**. 
    *   *Contributors Welcome*: We are looking for fluent speakers to help refine translations for new languages.
*   **Customizable**:
    *   **Extra Zones**: Manually monitor adjacent counties or specific stations (e.g., `VAC001` or `ON/s0000430`).
    *   **Audio**: Defaults to `pico2wave` — a lightweight, nimble offline TTS engine that sounds clear and runs efficiently on Raspberry Pi. Also works with `flite` or other CLI engines.

## Installation

### Prerequisites
On your ASL3 server (Debian/Raspbian):
```bash
sudo apt update
sudo apt install python3-pip libttspico-utils gpsd
```

### Install Package
1.  Clone this repository to your scripts directory (e.g., `/etc/asterisk/scripts/`).
2.  Install python dependencies:
    ```bash
    pip3 install -r requirements.txt
    ```

## Configuration

Copy the example config:
```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml`:
```yaml
location:
  type: auto         # Use 'auto' for GPS, or 'static' for fixed lat/lon
  # latitude: 45.123
  # longitude: -75.123

language: en         # Options: en, fr

voice:
  tts_command: 'pico2wave -l {lang} -w {file} "{text}"'

audio:
  nodes: 
    - "1966"         # Your Private Node
    - "92394"        # Your Public Node

alerts:
  min_severity: "Watch"
  extra_zones:       # Optional: Monitor extra areas
    - "VAC001"       # US County FIPS
    - "ON/s0000430"  # Canadian Station ID
```

## Usage

### Test Full Report
Announce current conditions, forecast, and time immediately:
```bash
python3 -m asl3_wx_announce.main --config config.yaml --report
```

### Run Alert Monitor
Run in the background to announce *new* alerts as they happen:
```bash
python3 -m asl3_wx_announce.main --config config.yaml --monitor
```

### Scheduled Hourly Reports
To announce the weather every hour, add to `crontab -u asterisk -e`:
```cron
0 * * * * /usr/bin/python3 -m asl3_wx_announce.main --config /path/to/config.yaml --report
```

## Contributing
Pull requests are welcome! See `provider/` directory to add support for new countries.

## License
MIT License
