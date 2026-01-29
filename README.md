# ASL3 Weather Announcer

**ASL3 Weather Announcer** is a flexible, multi-country weather alert and reporting system designed for AllStarLink 3 (Asterisk) nodes.

It provides **automated verbal announcements** for:
*   **Active Weather Alerts**: Warnings, watches, and advisories as they are issued.
*   **Civil Emergencies**: Amber Alerts, Nuclear events, etc. (via Alert Ready Canada / NWS).
*   **Daily Reports**: Detailed forecast, current conditions, sunrise/sunset.
*   **Startup Status**: System readiness and monitoring interval announcements.

## Features

*   **Multi-Provider Support**:
    *   🇺🇸 **USA**: Uses National Weather Service (NWS) API.
    *   🇨🇦 **Canada**: Uses Environment Canada & NAAD Alert Ready (CAP).
*   **Dynamic Polling**:
    *   Polls every 10 minutes (configurable) normally.
    *   **Automatically speeds up to 1 minute** during active Watches/Warnings.
    *   Verbal announcements when polling interval changes.
*   **Smart Location**:
    *   **Geospatial Filtering**: Uses CAP polygons to determine if *your* specific location is in the alert area.
    *   **Static**: Configurable fixed lat/lon.
*   **Audio**:
    *   Generates prompts using `pico2wave` (or configurable TTS).
    *   Plays directly to local or remote ASL3 nodes via `rpt playback`.
*   **Reliability**:
    *   Systemd service integration.
    *   Robust "Wait for Asterisk" boot logic.

## Installation

### Prerequisites
On your ASL3 server (Debian/Raspbian):
```bash
sudo apt update
sudo apt install python3-pip libttspico-utils gpsd sox
```

### Deploying Code
The recommended install location is `/opt/asl3_wx_announce`.

**Using the Deployment Script (Windows/PowerShell):**
1.  Update `config.yaml` with your settings.
2.  Run `.\deploy.ps1`.
   *   This script bundles the code, uploads it via SSH, installs dependencies, and registers/restarts the systemd service.

**Manual Installation (Linux):**
1.  Copy files to `/opt/asl3_wx_announce`.
2.  Install requirements: `pip3 install -r requirements.txt`.
3.  Copy `asl3-wx.service` to `/etc/systemd/system/`.
4.  Enable and start: `sudo systemctl enable --now asl3-wx`.

## Configuration

Copy the example config:
```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml`:
```yaml
location:
  source: fixed
  latitude: 46.8139
  longitude: -71.2080

station:
  callsign: "N7XOB"
  report_style: "quick" # 'quick' (2 days) or 'verbose' (7 days)

alerts:
  min_severity: "Watch"
  check_interval_minutes: 10
  # Alert Ready (Canada)
  enable_alert_ready: true
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
