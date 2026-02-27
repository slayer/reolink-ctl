# reolink-ctl

A command-line tool for controlling Reolink cameras. Manage device info, configuration, snapshots, live streams, recording downloads, PTZ, lighting, image settings, motion detection, audio, notifications, webhooks, and system administration.

Built on top of [reolink_aio](https://github.com/starkillerOG/reolink_aio).

## Quick Start

No install needed — run directly with [uvx](https://docs.astral.sh/uv/):

```bash
uvx reolink-ctl -H 192.168.1.100 -p your_password info
```

Or set credentials once and forget:

```bash
export REOLINK_HOST=192.168.1.100
export REOLINK_PASSWORD=your_password

uvx reolink-ctl info
uvx reolink-ctl snapshot
uvx reolink-ctl stream
```

## Install

Requires Python 3.9+ and [uv](https://docs.astral.sh/uv/).

**Run without installing** (fetches from PyPI on first use):

```bash
uvx reolink-ctl info
```

**Install globally** (faster repeated use):

```bash
uv tool install reolink-ctl
reolink-ctl info
```

**From source** (for development):

```bash
git clone https://github.com/slayer/reolink-ctl.git && cd reolink-ctl
uv sync --all-extras    # includes dev dependencies (pytest)
uv run reolink-ctl info
```

## Configuration

Camera credentials can be provided in three ways (in priority order):

1. **CLI flags** — `-H`, `-u`, `-p`
2. **Environment variables** — `REOLINK_HOST`, `REOLINK_USER`, `REOLINK_PASSWORD`
3. **`.env` file** — automatically loaded from the project root

| Variable | Flag | Default | Description |
|---|---|---|---|
| `REOLINK_HOST` | `-H`, `--host` | *(required)* | Camera IP address |
| `REOLINK_USER` | `-u`, `--user` | `admin` | Username |
| `REOLINK_PASSWORD` | `-p`, `--password` | *(required)* | Password |

Example `.env` file:

```env
REOLINK_HOST=192.168.1.100
REOLINK_USER=admin
REOLINK_PASSWORD=your_password
```

## Usage

```bash
uv run reolink-ctl [global flags] <command> [subcommand] [options]
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
| `--version` | Show version |

### Commands

---

#### `info` — Device Information

```bash
reolink-ctl info                # Model, firmware, MAC, serial, channel count
reolink-ctl info --channels     # Per-channel details (name, model, online status)
reolink-ctl info --storage      # Storage devices (SD card/HDD with type and size)
```

Example output:

```
  model     Reolink TrackMix PoE
  serial    00316417584066
  firmware  v3.0.0.5428_2509171972
  hardware  IPC_529SD78MP
  mac       ec:71:db:13:82:09
  channels  1
  nvr       False
```

---

#### `config` — Camera Configuration Dump

```bash
reolink-ctl config                          # All settings grouped by section
reolink-ctl config device                   # Device info only
reolink-ctl config image                    # Image settings only
reolink-ctl config audio                    # Audio settings only
reolink-ctl config detection                # Detection settings only
reolink-ctl config lighting                 # Lighting settings only
reolink-ctl config notifications            # Notification settings only
reolink-ctl config ptz                      # PTZ settings only
reolink-ctl config system                   # System info (time, storage)
```

Sections: `device`, `image`, `audio`, `detection`, `lighting`, `notifications`, `ptz`, `system`.

With `--json`, outputs a nested dict with section keys (or a flat dict for a single section).

---

#### `snapshot` — Capture JPEG Still

```bash
reolink-ctl snapshot                        # Save to snapshot_YYYYMMDD_HHMMSS.jpg
reolink-ctl snapshot -o photo.jpg           # Save to specific file
reolink-ctl snapshot --stream sub           # Use sub-stream (lower resolution)
```

---

#### `stream` — Show Stream URLs

```bash
reolink-ctl stream                          # All available URLs (RTSP, RTMP, FLV)
reolink-ctl stream --format rtsp            # RTSP URL only
reolink-ctl stream --format rtmp            # RTMP URL only
reolink-ctl stream --format flv             # FLV URL only
reolink-ctl stream --stream sub             # Sub-stream URLs
```

Use the output URLs with VLC, ffmpeg, or any media player:

```bash
vlc "$(reolink-ctl --json stream --format rtsp | jq -r .rtsp)"
```

---

#### `download` — Download Recordings

Download VOD recordings with trigger-based filtering and time selection.

**Trigger filters** (combine any):

```bash
reolink-ctl download --person               # Person detections only
reolink-ctl download --vehicle              # Vehicle/car detections
reolink-ctl download --pet                  # Pet/animal detections
reolink-ctl download --motion               # Motion detections
reolink-ctl download --person --vehicle     # Multiple triggers
reolink-ctl download --all                  # All types (default)
```

**Time selection:**

```bash
reolink-ctl download --since 2h             # Last 2 hours (also: 30m, 1d, 3d)
reolink-ctl download --date today           # Today's recordings
reolink-ctl download --date yesterday       # Yesterday's recordings
reolink-ctl download --date 2026-02-15      # Specific date
reolink-ctl download --from 2026-02-15 --to 2026-02-18   # Date range
```

**Output options:**

```bash
reolink-ctl download --dry-run              # List files without downloading
reolink-ctl download --latest 5             # Only the 5 most recent
reolink-ctl download --output-dir ./clips   # Custom download directory (default: ./downloads)
reolink-ctl download --high                 # High quality / main stream (default)
reolink-ctl download --low                  # Low quality / sub stream
reolink-ctl download --stream sub           # Same as --low
reolink-ctl download --progress             # Show progress bar
```

**Combined example:**

```bash
reolink-ctl download --person --since 2h --dry-run     # Preview recent person detections
reolink-ctl download --motion --latest 5 --progress    # Download last 5 motion clips
```

---

#### `ptz` — Pan / Tilt / Zoom

**Movement:**

```bash
reolink-ctl ptz move left                   # Move left (default speed: 25)
reolink-ctl ptz move right --speed 50       # Move right faster
reolink-ctl ptz move up
reolink-ctl ptz move down
reolink-ctl ptz stop                        # Stop movement
reolink-ctl ptz position                    # Show current pan position
```

**Zoom and focus:**

```bash
reolink-ctl ptz zoom in                     # Zoom in
reolink-ctl ptz zoom out                    # Zoom out
reolink-ctl ptz zoom set 50                 # Set absolute zoom level
reolink-ctl ptz focus set 30                # Set absolute focus
reolink-ctl ptz focus auto on               # Enable autofocus
reolink-ctl ptz focus auto off              # Disable autofocus
```

**Presets:**

```bash
reolink-ctl ptz preset list                 # List saved presets
reolink-ctl ptz preset goto 1               # Go to preset by ID
```

**Patrol:**

```bash
reolink-ctl ptz patrol start                # Start patrol
reolink-ctl ptz patrol stop                 # Stop patrol
reolink-ctl ptz patrol list                 # List patrol configurations
```

**Guard position:**

```bash
reolink-ctl ptz guard on                    # Enable guard return
reolink-ctl ptz guard on --time 10          # Enable with 10s return delay
reolink-ctl ptz guard off                   # Disable guard
reolink-ctl ptz guard set                   # Set current position as guard
reolink-ctl ptz guard goto                  # Go to guard position
```

**Auto-tracking:**

```bash
reolink-ctl ptz track on                    # Enable (default: digital method)
reolink-ctl ptz track on --method pantiltfirst   # Use pan/tilt-first method
reolink-ctl ptz track off                   # Disable
reolink-ctl ptz track limit --left 90 --right 270   # Set pan limits
reolink-ctl ptz calibrate                   # Calibrate PTZ motor
```

---

#### `light` — Lighting Control

**Infrared:**

```bash
reolink-ctl light ir on                     # Enable IR lights
reolink-ctl light ir off                    # Disable IR lights
reolink-ctl light ir status                 # Check IR status
```

**Spotlight:**

```bash
reolink-ctl light spotlight on              # Enable spotlight
reolink-ctl light spotlight off
reolink-ctl light spotlight status
```

**White LED:**

```bash
reolink-ctl light whiteled                             # Show current settings
reolink-ctl light whiteled --state on                  # Turn on
reolink-ctl light whiteled --brightness 200            # Set brightness
reolink-ctl light whiteled --state on --brightness 200 --mode 1   # Set all at once
```

**Status LED:**

```bash
reolink-ctl light status-led status         # Check current mode
reolink-ctl light status-led auto           # Auto mode
reolink-ctl light status-led stayoff        # Always off
reolink-ctl light status-led alwayson       # Always on
reolink-ctl light status-led alwaysonatnight   # On at night only
```

---

#### `image` — Image Settings

```bash
reolink-ctl image get                       # Show all settings (brightness, contrast, etc.)
reolink-ctl image set --bright 128          # Set brightness
reolink-ctl image set --contrast 128        # Set contrast
reolink-ctl image set --saturation 128      # Set saturation
reolink-ctl image set --sharpness 128       # Set sharpness
reolink-ctl image set --hue 128             # Set hue
reolink-ctl image daynight auto             # Day/night: auto, color, blackwhite
reolink-ctl image hdr on                    # HDR: on, off, auto
```

Multiple settings can be changed at once:

```bash
reolink-ctl image set --bright 140 --contrast 120 --sharpness 100
```

---

#### `detect` — Detection Config

**Motion detection:**

```bash
reolink-ctl detect motion status            # Show motion status and sensitivity
reolink-ctl detect motion on                # Enable
reolink-ctl detect motion off               # Disable
reolink-ctl detect motion sensitivity 30    # Set sensitivity (1-50)
```

**AI detection:**

```bash
reolink-ctl detect ai sensitivity 50 --type person    # AI sensitivity by type
reolink-ctl detect ai sensitivity 40 --type vehicle
reolink-ctl detect ai delay 1 --type person            # AI delay by type
```

**PIR sensor:**

```bash
reolink-ctl detect pir status               # Check PIR status
reolink-ctl detect pir on                   # Enable PIR
reolink-ctl detect pir off                  # Disable PIR
```

Running `detect` without a subcommand shows a summary of motion and PIR status.

---

#### `audio` — Audio Controls

**Recording:**

```bash
reolink-ctl audio record status             # Check recording state
reolink-ctl audio record on                 # Enable
reolink-ctl audio record off                # Disable
```

**Volume:**

```bash
reolink-ctl audio volume status             # Check current volume
reolink-ctl audio volume 80                 # Set volume level
```

**Alarm:**

```bash
reolink-ctl audio alarm status              # Check alarm state
reolink-ctl audio alarm on                  # Enable
reolink-ctl audio alarm off                 # Disable
```

**Siren:**

```bash
reolink-ctl audio siren                     # Sound siren (default: 2s)
reolink-ctl audio siren --duration 5        # Sound for 5 seconds
reolink-ctl audio siren off                 # Stop siren
```

**Quick reply:**

```bash
reolink-ctl audio reply play 0              # Play quick-reply file by ID
```

---

#### `notify` — Notifications

Each notification type supports `on`, `off`, and `status`:

```bash
reolink-ctl notify push status              # Check push notification state
reolink-ctl notify push on                  # Enable push notifications
reolink-ctl notify email off                # Disable email notifications
reolink-ctl notify ftp status               # Check FTP upload status
reolink-ctl notify recording on             # Enable recording on event
reolink-ctl notify buzzer off               # Disable buzzer
```

---

#### `webhook` — Webhook Management

```bash
reolink-ctl webhook add http://example.com/hook       # Register webhook
reolink-ctl webhook test http://example.com/hook      # Send test event
reolink-ctl webhook remove http://example.com/hook    # Remove webhook
reolink-ctl webhook disable http://example.com/hook   # Disable webhook
```

---

#### `system` — System Administration

**Reboot:**

```bash
reolink-ctl system reboot
```

**Firmware:**

```bash
reolink-ctl system firmware check           # Check for updates
reolink-ctl system firmware update          # Install firmware update
reolink-ctl system firmware progress        # Check update progress
```

**Time and NTP:**

```bash
reolink-ctl system time get                 # Show camera time
reolink-ctl system time set --tz-offset 3600   # Set timezone offset (seconds)
reolink-ctl system ntp set --server pool.ntp.org   # Configure NTP server
reolink-ctl system ntp set --server pool.ntp.org --port 123
reolink-ctl system ntp sync                 # Force NTP sync
```

**OSD (on-screen display):**

```bash
reolink-ctl system osd set --name-pos UL              # Camera name position
reolink-ctl system osd set --date-pos LR              # Date/time position
reolink-ctl system osd set --watermark off            # Disable watermark
```

**Network ports:**

```bash
reolink-ctl system ports set --rtsp on                # Enable/disable RTSP
reolink-ctl system ports set --rtmp on                # Enable/disable RTMP
reolink-ctl system ports set --onvif off              # Enable/disable ONVIF
```

## JSON Output

Add `--json` to any command for machine-readable output:

```bash
reolink-ctl --json info
```

```json
{
  "model": "Reolink TrackMix PoE",
  "serial": "00326417514496",
  "firmware": "v3.0.0.5428_2509171972",
  "hardware": "IPC_529SD78MP",
  "mac": "ec:71:db:13:82:09",
  "channels": 1,
  "nvr": false
}
```

Useful for scripting:

```bash
# Get RTSP URL for ffmpeg
reolink-ctl --json stream --format rtsp | jq -r .rtsp

# Check if motion is detected
reolink-ctl --json detect motion status | jq .motion_detected
```

## Multi-Channel (NVR)

For NVR setups with multiple cameras, use `-c` to select a channel:

```bash
reolink-ctl -c 0 info --channels       # List all channels
reolink-ctl -c 2 snapshot              # Snapshot from channel 2
reolink-ctl -c 1 stream --format rtsp  # Stream URL for channel 1
```

## Standalone Download Script

The original `download.py` still works standalone via [uv](https://docs.astral.sh/uv/) with no install:

```bash
uv run download.py --person --since 2h --dry-run
```

## How Trigger Detection Works

Reolink cameras encode AI detection types (person, vehicle, pet, motion) in hex flags embedded in recording filenames. The `reolink_aio` library parses these for older firmware, but newer firmware uses a different filename layout that the library doesn't recognize. This tool includes its own filename parser as a fallback to handle both formats.

## Tests

```bash
# Run all unit tests (no camera needed, all mocked)
uv run pytest tests/ -v

# Run end-to-end tests against a real camera
REOLINK_HOST=192.168.1.100 REOLINK_PASSWORD=secret uv run pytest tests/test_e2e.py -v
```

E2E tests auto-skip when `REOLINK_HOST` is not set, so CI stays green. They only run read-only commands (info, snapshot, stream, image get, detect status, etc.) and never change camera state.
