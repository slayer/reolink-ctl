# Design: `config` command

## Purpose

Show all readable configuration from a Reolink camera as a grouped dump. Supports filtering to a single section.

## Interface

```
reolink-ctl config              # all sections
reolink-ctl config image        # single section
reolink-ctl config --json       # JSON output
```

Positional argument `section` (`nargs="?"`, `choices=[...]`). Argparse validates section names.

## Sections

| Section         | Properties                                                                                     |
|-----------------|-----------------------------------------------------------------------------------------------|
| device          | model, serial, sw_version, hardware_version, mac_address, wifi_signal, is_nvr, camera_name, camera_online |
| image           | brightness, contrast, saturation, sharpness, hue, daynight_state, HDR_on                     |
| audio           | audio_record, volume, audio_alarm_enabled                                                     |
| detection       | motion_detected, md_sensitivity, pir_enabled, pir_sensitivity                                 |
| lighting        | ir_enabled, whiteled_state, whiteled_mode, whiteled_brightness, status_led_enabled            |
| notifications   | push_enabled, email_enabled, ftp_enabled, recording_enabled, buzzer_enabled                   |
| ptz             | ptz_presets, ptz_pan_position, ptz_guard_enabled, ptz_guard_time, auto_track_enabled          |
| system          | device time (via async_get_time), storage info (hdd_list, hdd_type, hdd_storage, hdd_available) |

## Output

- **Human mode:** Section headers, key-value pairs underneath.
- **JSON mode:** Nested dict `{"device": {...}, "image": {...}, ...}` or single section dict if filtered.

## Error handling

Properties that raise on unsupported cameras are caught per-property and omitted (or `null` in JSON). Invalid section names rejected by argparse `choices`.

## Files

- `reolink_ctl/commands/config.py` — standard 3-function pattern
- Register in `cli.py`
- `tests/test_cmd_config.py` — unit tests
- E2E test in `tests/test_e2e.py`
