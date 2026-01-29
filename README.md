/# ASL3 Weather Announcer

**ASL3 Weather Announcer** is a flexible, multi-country weather alert and reporting system designed for AllStarLink 3 (Asterisk) nodes.  This is for code is for informational purposes only, and it not intended to be used as the sole source for life and/or property safety notifications.  Use at your own risk.  There are many situations that might prevent this code from working with the reliability needed to protect life and property - including but not limited to loss of connectivity, power failure, malicious attacks on software and hardware, low accuracy location information, low accuracy time setting, etc.  Repeat - use at your own risk.  This works in both the US and Canada currently.  I am happy to delve into coding for other countries, as time and resources allow.

I beleive this to be a legal radio transmission in both the US and Canada.  It uses official sources (National Weather Service in the US, Environment Canada and Alert Ready Canada for Canada).  The information provided is of general interest to the amateur radio community.  Severe weather can cause damage to an amateur operators equipment (ice and wind on antennas, for example). Some amatuers also serve as official weather observers or volunteer to assist local agencies to respond to emergencies - and advanced information about severe weather, civil emergencies is useful to make final preparations for responding.  The time of the sunrise and set, moon phases and solar flux are all information that assist in radio propagation - which is of vital interest to the amateur community.  These transmissions are not intended for the general public, although, given the transparent nature and spirit of amateur radio, these transmissions are not obscured in any manner.  Incidental reception by the general public is unavoidable.  The operator assumes all risk for what constitutes a legal transmission.  Operators are advised to configure announcements to provide content that is of general interest to the amateur radio community to avoid legal issues about the legality of  the transmission. 

It provides **automated verbal announcements** for:
*   **Active Weather Alerts**: Warnings, watches, and advisories as they are issued.
*   **Civil Emergencies**: Amber Alerts, Chemical, Wildfire events, etc. (via Alert Ready Canada / NWS).
*   **Daily Reports**: Detailed forecast, current conditions, sunrise/sunset, solar flux index
*   **Startup Status**: System readiness and monitoring interval announcements.

## Features
    
*   **Multi-Provider Support**:
    *   🇺🇸 **USA**: Uses National Weather Service (NWS) API.
    *   🇨🇦 **Canada**: Uses Environment Canada & NAAD Alert Ready (CAP).
*   **Dynamic Polling**:
    *   Polls every 10 minutes (configurable) normally.
    *   **Automatically speeds up** (configurable, e.g., 1 min) during active Watches/Warnings.
    *   Verbal announcements when polling interval changes.
*   **Hourly Reports**:
    *   Configurable content: Conditions, Forecast, Astro (Sun/Moon), **Solar Flux Index**, System Status, **Exact Time**.
    *   **Time Accuracy Check**: Checks system clock against NIST/NRC and warns if drift > 60s.
    *   Reports have silent breaks built in, to allow for emergency traffic to interupt.
*   **Smart Location**:
    *   **Geospatial Filtering**: Uses CAP polygons to determine if *your* specific location is in the alert area.
    *   **Static**: Configurable fixed lat/lon.
*   **Audio**:
    *   Generates prompts using `pico2wave` (or configurable TTS).
    *   Plays directly to local or remote ASL3 nodes via `rpt playback`.
    *   Callsigns are correctly appended for US operators operating in Canada, and Canadian operators operating in the US.
*   ** System Reliability**:
    *   Systemd service integration (runs in dedicated `venv`).
    *   Robust "Wait for Asterisk" boot logic.

## Installation

### Prerequisites
On your ASL3 server (Debian/Raspbian):
```bash
sudo apt update
sudo apt install python3-pip libttspico-utils gpsd sox chrony
```
*(Note: `chrony` is recommended for time accuracy checks)*

### Deploying Code
The recommended install location is `/opt/asl3_wx_announce`.

**Using the Deployment Script (Windows/PowerShell):**
1.  Update `config.yaml` with your settings.
2.  Run `.\deploy.ps1`.
   *   This script bundles the code, uploads it via SSH, creates a Python virtual environment, installs dependencies, and registers/restarts the systemd service.

**Manual Installation (Linux):**
1.  Copy files to `/opt/asl3_wx_announce`.
2.  Create venv: `python3 -m venv venv`
3.  Install requirements: `venv/bin/pip install -r requirements.txt`.
4.  Copy `asl3-wx.service` to `/etc/systemd/system/`.
5.  Enable and start: `sudo systemctl enable --now asl3-wx`.

## Configuration

Copy the example config:
```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` (See `config.example.yaml` for full options):
```yaml
location:
  source: fixed
  latitude: 46.8139
  longitude: -71.2080

station:
  callsign: "N7XOB"
  hourly_report:
    enabled: true
    minute: 0
    content:
      time: true
      time_error: true # Check clock accuracy
      conditions: true
      forecast: true
      forecast_verbose: false
      astro: true
      solar_flux: true # NOAA SWPC Data
      status: true

alerts:
  min_severity: "Watch"
  check_interval_minutes: 10
  active_check_interval_minutes: 1 # Faster polling during events
```

## Usage

### Test Full Report
Trigger an immediate weather report:
```bash
cd /opt/asl3_wx_announce
sudo python3 -m asl3_wx_announce.main --report
```

### Test Alert Simulation
Simulate a full emergency alert sequence (Tone + Message) to test audio:
```bash
sudo python3 -m asl3_wx_announce.main --test-alert
```

### Service Status
Check the background monitor:
```bash
sudo systemctl status asl3-wx
sudo journalctl -u asl3-wx -f
```

## Contributing
Pull requests are welcome!

## License
MIT License
