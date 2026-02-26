"""Shared fixtures for reolink-ctl tests."""

from __future__ import annotations

import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

from reolink_aio.typings import VOD_trigger


@pytest.fixture
def mock_host():
    """Create a mock Host object with common properties."""
    host = MagicMock()

    # Device info
    host.model = "RLC-811A"
    host.serial = "ABCDEF1234567890"
    host.sw_version = "v3.0.0.0_23010100"
    host.hardware_version = "IPC_523128M8MP"
    host.mac_address = "AA:BB:CC:DD:EE:FF"
    host.num_channels = 1
    host.is_nvr = False
    host.wifi_signal = None
    host.channels = [0]
    host.stream_channels = [0]
    host.hdd_info = []
    host.hdd_list = []

    # Per-channel properties
    host.camera_name.return_value = "Front Door"
    host.camera_model.return_value = "RLC-811A"
    host.camera_online.return_value = True
    host.camera_sw_version.return_value = "v3.0.0.0_23010100"

    # Async methods
    host.get_host_data = AsyncMock()
    host.logout = AsyncMock()
    host.get_snapshot = AsyncMock(return_value=b"\xff\xd8\xff\xe0fake_jpeg")
    host.get_rtsp_stream_source = AsyncMock(return_value="rtsp://192.168.1.100:554/h264Preview_01_main")
    host.get_rtmp_stream_source.return_value = "rtmp://192.168.1.100/bcs/channel0_main.bcs"
    host.get_flv_stream_source.return_value = "http://192.168.1.100/flv?port=1935&app=bcs&stream=channel0_main.bcs"

    # PTZ
    host.set_ptz_command = AsyncMock()
    host.set_zoom = AsyncMock()
    host.set_focus = AsyncMock()
    host.set_autofocus = AsyncMock()
    host.ptz_presets.return_value = {1: "Home", 2: "Gate"}
    host.ptz_patrols.return_value = {}
    host.ptz_pan_position.return_value = 180
    host.ptz_guard_enabled.return_value = False
    host.ptz_guard_time.return_value = 10
    host.ctrl_ptz_patrol = AsyncMock()
    host.set_ptz_guard = AsyncMock()
    host.ptz_callibrate = AsyncMock()
    host.set_auto_tracking = AsyncMock()
    host.set_auto_track_limit = AsyncMock()
    host.auto_track_enabled.return_value = False

    # Lights
    host.ir_enabled.return_value = True
    host.set_ir_lights = AsyncMock()
    host.set_spotlight = AsyncMock()
    host.whiteled_state.return_value = False
    host.whiteled_mode.return_value = 1
    host.whiteled_brightness.return_value = 100
    host.set_whiteled = AsyncMock()
    host.status_led_enabled.return_value = True
    host.set_status_led = AsyncMock()

    # Image
    host.image_brightness.return_value = 128
    host.image_contrast.return_value = 128
    host.image_saturation.return_value = 128
    host.image_sharpness.return_value = 128
    host.image_hue.return_value = 128
    host.daynight_state.return_value = "Auto"
    host.HDR_on.return_value = True
    host.set_image = AsyncMock()
    host.set_daynight = AsyncMock()
    host.set_HDR = AsyncMock()

    # Detection
    host.motion_detected.return_value = False
    host.md_sensitivity.return_value = 25
    host.set_motion_detection = AsyncMock()
    host.set_md_sensitivity = AsyncMock()
    host.set_ai_sensitivity = AsyncMock()
    host.set_ai_delay = AsyncMock()
    host.pir_enabled.return_value = True
    host.pir_sensitivity.return_value = 3
    host.set_pir = AsyncMock()

    # Audio
    host.audio_record.return_value = True
    host.volume.return_value = 75
    host.audio_alarm_enabled.return_value = False
    host.set_audio = AsyncMock()
    host.set_volume = AsyncMock()
    host.set_audio_alarm = AsyncMock()
    host.set_siren = AsyncMock()
    host.play_quick_reply = AsyncMock()

    # Notifications
    host.push_enabled.return_value = True
    host.email_enabled.return_value = False
    host.ftp_enabled.return_value = False
    host.recording_enabled.return_value = True
    host.buzzer_enabled.return_value = False
    host.set_push = AsyncMock()
    host.set_email = AsyncMock()
    host.set_ftp = AsyncMock()
    host.set_recording = AsyncMock()
    host.set_buzzer = AsyncMock()

    # Webhooks
    host.webhook_add = AsyncMock()
    host.webhook_test = AsyncMock()
    host.webhook_remove = AsyncMock()
    host.webhook_disable = AsyncMock()

    # System
    host.reboot = AsyncMock()
    host.check_new_firmware = AsyncMock(return_value=False)
    host.update_firmware = AsyncMock()
    host.update_progress = AsyncMock(return_value=False)
    host.async_get_time = AsyncMock(return_value=datetime(2026, 2, 26, 12, 0, 0))
    host.set_time = AsyncMock()
    host.set_ntp = AsyncMock()
    host.sync_ntp = AsyncMock()
    host.set_osd = AsyncMock()
    host.set_net_port = AsyncMock()

    # VOD
    host.request_vod_files = AsyncMock(return_value=([], []))
    host.download_vod = AsyncMock()

    return host


def make_vod(start_h, start_m, end_h, end_m, triggers, day=20):
    """Create a mock VOD_file object."""
    vod = MagicMock()
    vod.start_time = datetime(2026, 2, day, start_h, start_m, 0)
    vod.end_time = datetime(2026, 2, day, end_h, end_m, 0)
    vod.triggers = triggers
    vod.file_name = f"Mp4Record/2026-02-{day}/Rec_{start_h:02d}{start_m:02d}.mp4"
    vod.duration.total_seconds.return_value = (end_h - start_h) * 3600 + (end_m - start_m) * 60
    return vod
