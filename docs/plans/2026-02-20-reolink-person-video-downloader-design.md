# Reolink Person Detection Video Downloader — Design

## Goal

A Python CLI tool to download video recordings from a Reolink doorbell camera's SD card, filtered by AI detection type (person, vehicle, animal, etc.).

## Architecture

Single Python script (`download.py`) using `reolink_aio` library for camera API access.

**Flow:**
1. Parse CLI args (connection, trigger filters, time range, output options)
2. Connect to camera via `reolink_aio.api.Host`
3. Search recordings in the specified time range
4. Filter by selected trigger types (person, vehicle, etc.)
5. Apply `--latest N` limit if specified
6. Download matching files to output directory (or list in dry-run mode)
7. Print summary

## CLI Interface

### Connection flags (override `.env` fallback)

| Flag | Env var | Description |
|------|---------|-------------|
| `--host` / `-H` | `REOLINK_HOST` | Camera IP address |
| `--user` / `-u` | `REOLINK_USER` | Username |
| `--password` / `-p` | `REOLINK_PASSWORD` | Password |

Priority: CLI flags > `.env` file > defaults.

### Trigger type flags (combinable)

| Flag | VOD_trigger | Description |
|------|------------|-------------|
| `--person` | `PERSON` | Person detection (AI) |
| `--vehicle` | `VEHICLE` | Vehicle detection (AI) |
| `--animal` | `ANIMAL` | Animal/pet detection (AI) |
| `--face` | `FACE` | Face detection (AI) |
| `--doorbell` | `DOORBELL` | Doorbell button press |
| `--motion` | `MOTION` | Generic motion detection |
| `--all` | (no filter) | Any trigger type (default) |

Multiple trigger flags can be combined (OR logic): `--person --vehicle` returns recordings triggered by person OR vehicle.

### Time selection

| Flag | Description |
|------|-------------|
| `--date YYYY-MM-DD` | Specific date (also accepts `today`, `yesterday`) |
| `--from` + `--to` | Date range (inclusive) |
| `--since PERIOD` | Relative period: `30m`, `2h`, `1d`, `3d` |
| `--latest N` | Limit to N most recent matching recordings |

Default: `--date today` if no time option specified.

### Output/behavior

| Flag | Default | Description |
|------|---------|-------------|
| `--output-dir` | `./downloads` | Download destination |
| `--dry-run` | false | List matching files without downloading |
| `--stream` | `main` | Stream quality: `main` or `sub` |

### Examples

```bash
# Last 5 person detection videos
python download.py --person --latest 5

# All person + vehicle from today
python download.py --person --vehicle --date today

# Animal detections in last 3 hours, dry run
python download.py --animal --since 3h --dry-run

# Doorbell presses from a date range
python download.py --doorbell --from 2026-02-15 --to 2026-02-20

# With inline credentials
python download.py -H <camera-ip> -u admin -p mypass --person --latest 5
```

## Configuration

Camera credentials in `.env` (not committed to git):

```
REOLINK_HOST=<camera-ip>
REOLINK_USER=admin
REOLINK_PASSWORD=<password>
```

## Output Directory Structure

```
downloads/
  2026-02-20/
    person_103000_103115.mp4
    person_143022_143145.mp4
  2026-02-19/
    doorbell_091500_091530.mp4
```

Files organized by date, named by trigger type and time range.

## Technical Details

### How trigger detection works

The Reolink HTTP API `Search` command returns all recordings for a time range. AI detection type is encoded as hex bit flags in the recording filename. The `reolink_aio` library decodes these flags via `VOD_trigger` enum.

Key bit positions in filename hex flags:
- Bit 17: Person detection (`ai_pd`)
- Bit 18: Face detection (`ai_fd`)
- Bit 19: Vehicle detection (`ai_vd`)
- Bit 20: Animal detection (`ai_ad`)
- Bit 24: Motion detection
- Bit 26: Doorbell press

### Dependencies

- `reolink_aio` — Reolink camera API (officially authorized by Reolink)
- `python-dotenv` — load `.env` config
- `aiohttp` — async HTTP (transitive via reolink_aio)

### Error handling

- Connection timeout: retry once, then exit with clear message
- Auth failure: clear error pointing to credentials
- No recordings found: informative "no videos found" message
- Download failure: skip file, continue, report failures in summary
