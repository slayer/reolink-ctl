# reolink-ctl

CLI for Reolink camera control — device info, snapshots, streams, recording downloads, PTZ, lights, image settings, detection config, audio, notifications, webhooks, and system management.

## Install

```bash
pip install -e ".[dev]"
```

## Standalone Download Script

The original `download.py` still works standalone via [uv](https://docs.astral.sh/uv/) with no install:

```bash
uv run download.py --person --since 2h --dry-run
```

## Configuration

Copy `.env.example` to `.env` and fill in your camera details:

```env
REOLINK_HOST=192.168.1.100
REOLINK_USER=admin
REOLINK_PASSWORD=your_password
```

All connection settings can also be passed as CLI flags (`-H`, `-u`, `-p`).

## Usage

```bash
reolink-ctl [-H HOST] [-u USER] [-p PASSWORD] [-c CHANNEL] [--json] [-v] <command>
```

### Global Flags

| Flag | Description |
|---|---|
| `-H`, `--host` | Camera IP (env: `REOLINK_HOST`) |
| `-u`, `--user` | Username (env: `REOLINK_USER`, default: `admin`) |
| `-p`, `--password` | Password (env: `REOLINK_PASSWORD`) |
| `-c`, `--channel` | Camera channel (default: `0`) |
| `--json` | Output as JSON |
| `-v`, `--verbose` | Verbose output |

### Commands

#### `info` — Device information

```bash
reolink-ctl info                # Device overview
reolink-ctl info --channels     # List channels
reolink-ctl info --storage      # Storage/HDD info
```

#### `snapshot` — Capture JPEG still

```bash
reolink-ctl snapshot                        # Save to timestamped file
reolink-ctl snapshot --output photo.jpg     # Save to specific file
reolink-ctl snapshot --stream sub           # Use sub-stream
```

#### `stream` — Print stream URLs

```bash
reolink-ctl stream                      # RTSP URL (default)
reolink-ctl stream --format rtmp        # RTMP URL
reolink-ctl stream --format flv         # FLV URL
reolink-ctl stream --stream sub         # Sub-stream
```

#### `download` — Download recordings

```bash
reolink-ctl download --person                               # Today's person detections
reolink-ctl download --person --vehicle --date yesterday    # Multiple triggers
reolink-ctl download --since 2h --dry-run                   # List without downloading
reolink-ctl download --from 2026-02-15 --to 2026-02-18     # Date range
reolink-ctl download --motion --latest 5 --progress         # Latest N with progress
```

#### `ptz` — Pan/Tilt/Zoom control

```bash
reolink-ctl ptz move left --speed 5     # Move in direction
reolink-ctl ptz stop                    # Stop movement
reolink-ctl ptz zoom in                 # Zoom in/out
reolink-ctl ptz zoom set 50            # Set absolute zoom
reolink-ctl ptz focus set 30           # Set focus
reolink-ctl ptz focus auto on          # Enable autofocus
reolink-ctl ptz preset list            # List presets
reolink-ctl ptz preset goto 1          # Go to preset
reolink-ctl ptz patrol start           # Start patrol
reolink-ctl ptz guard on --time 10     # Enable guard position
reolink-ctl ptz calibrate              # Calibrate PTZ
reolink-ctl ptz track on --method digital   # Enable tracking
reolink-ctl ptz position               # Show pan position
```

#### `light` — Lighting control

```bash
reolink-ctl light ir on                # IR lights on/off
reolink-ctl light spotlight on         # Spotlight on/off
reolink-ctl light whiteled --state on --brightness 200 --mode 1
reolink-ctl light status-led auto      # Status LED mode
```

#### `image` — Image settings

```bash
reolink-ctl image get                  # Show current settings
reolink-ctl image set --bright 128 --contrast 128
reolink-ctl image daynight auto        # auto/color/blackwhite
reolink-ctl image hdr on               # off/auto/on
```

#### `detect` — Detection config

```bash
reolink-ctl detect motion on                       # Enable motion detection
reolink-ctl detect motion sensitivity 30           # Set sensitivity (1-50)
reolink-ctl detect ai sensitivity 50 --type person # AI sensitivity
reolink-ctl detect ai delay 1 --type vehicle       # AI delay
reolink-ctl detect pir on                          # PIR sensor
```

#### `audio` — Audio and siren

```bash
reolink-ctl audio record on            # Audio recording on/off
reolink-ctl audio volume 80            # Set volume
reolink-ctl audio alarm on             # Audio alarm on/off
reolink-ctl audio siren --duration 5   # Sound siren for N seconds
reolink-ctl audio siren off            # Stop siren
reolink-ctl audio reply play 0         # Play quick reply
```

#### `notify` — Notification toggles

```bash
reolink-ctl notify push on             # Push notifications
reolink-ctl notify email off           # Email notifications
reolink-ctl notify ftp status          # Check FTP status
reolink-ctl notify recording on        # Recording on event
reolink-ctl notify buzzer off          # Buzzer
```

#### `webhook` — Webhook management

```bash
reolink-ctl webhook add http://example.com/hook
reolink-ctl webhook test http://example.com/hook
reolink-ctl webhook remove http://example.com/hook
reolink-ctl webhook disable http://example.com/hook
```

#### `system` — System management

```bash
reolink-ctl system reboot              # Reboot camera
reolink-ctl system firmware check      # Check for updates
reolink-ctl system firmware update     # Install firmware update
reolink-ctl system time get            # Show camera time
reolink-ctl system time set --tz-offset 3600
reolink-ctl system ntp set --server pool.ntp.org
reolink-ctl system ntp sync            # Force NTP sync
reolink-ctl system osd set --name-pos UL --date-pos LR
reolink-ctl system ports set --rtsp 554 --rtmp 1935
```

## How trigger detection works

Reolink cameras encode AI detection types (person, vehicle, pet, motion) in hex flags embedded in recording filenames. The `reolink_aio` library parses these for older firmware formats, but newer firmware uses a different filename layout that the library doesn't recognize. This tool includes its own filename parser as a fallback to handle both old and new formats.

## Tests

```bash
pytest tests/ -v
```

All tests use mocks — no camera connection needed.
