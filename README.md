# reolink-downloader

Download Reolink camera recordings filtered by AI detection type (person, vehicle, pet, motion).

## Install

```bash
pip install -e .
```

Or run directly with [uv](https://docs.astral.sh/uv/) (no install needed):

```bash
uv run download.py --help
```

## Configuration

Copy `.env.example` to `.env` and fill in your camera details:

```bash
cp .env.example .env
```

```env
REOLINK_HOST=192.168.1.100
REOLINK_USER=admin
REOLINK_PASSWORD=your_password
```

All connection settings can also be passed as CLI flags (`--host`, `--user`, `--password`).

## Usage

```bash
# Download today's person detections
python download.py --person

# Download vehicle + person clips from yesterday
python download.py --person --vehicle --date yesterday

# Last 2 hours, dry run (list without downloading)
python download.py --since 2h --dry-run

# Date range, only pets, sub-stream quality
python download.py --from 2026-02-15 --to 2026-02-18 --pet --stream sub

# Latest 5 motion recordings with progress bar
python download.py --motion --latest 5 --progress

# With uv (no install needed)
uv run download.py --person --since 1d --dry-run
```

## CLI Reference

| Flag | Description |
|---|---|
| `-H`, `--host` | Camera IP (env: `REOLINK_HOST`) |
| `-u`, `--user` | Username (env: `REOLINK_USER`, default: `admin`) |
| `-p`, `--password` | Password (env: `REOLINK_PASSWORD`) |
| `--person` | Filter: person detection |
| `--vehicle`, `--car` | Filter: vehicle detection |
| `--pet` | Filter: pet/animal detection |
| `--motion` | Filter: motion detection |
| `--all` | All trigger types (default if none selected) |
| `--date DATE` | Specific date: `YYYY-MM-DD`, `today`, `yesterday` |
| `--from` / `--to` | Date range (both required) |
| `--since` | Relative period: `30m`, `2h`, `1d`, `3d` |
| `--latest N` | Limit to N most recent recordings |
| `--output-dir` | Download directory (default: `./downloads`) |
| `--dry-run` | List files without downloading |
| `--stream` | `main` (full quality) or `sub` (lower quality) |
| `-v`, `--verbose` | Show filenames and trigger flags |
| `--progress` | Show download progress bar |

## How trigger detection works

Reolink cameras encode AI detection types (person, vehicle, pet, motion) in hex flags embedded in recording filenames. The `reolink_aio` library parses these for older firmware formats, but newer firmware uses a different filename layout that the library doesn't recognize. This tool includes its own filename parser as a fallback to handle both old and new formats.

## Tests

```bash
python -m pytest tests/ -v
```

All tests use mocks -- no camera connection needed.
