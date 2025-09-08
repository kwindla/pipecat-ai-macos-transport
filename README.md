# pipecat-ai-macos-transport

Local macOS transport for Pipecat using VoiceProcessingIO (AEC).

This package will host:
- A Python transport (`LocalMacTransport`) compatible with `BaseTransport`
- A C helper (`vpio_helper.c`) compiled into `libvpio.dylib`
- Minimal examples and docs to integrate with Pipecat pipelines

Status: skeleton. Code will be migrated from your existing repos.

## Install & Build (uv)

```
# From your workspace root
uv pip install -e ./pipecat-ai-macos-transport

# Build the VPIO helper dylib
bash ./pipecat-ai-macos-transport/scripts/build_vpio.sh
```

The transport looks for the helper at:
`pipecat_ai_macos_transport/src/pipecat_macos_transport/macos/libvpio.dylib`
or `VPIO_LIB` if set.

## Building the helper manually

```
# From repo root
./scripts/build_vpio.sh
```

This script compiles `macos/libvpio.dylib` from `macos/vpio_helper.c` using the
AudioUnit/AudioToolbox frameworks.

## Environment

- `VPIO_LIB` (optional): override path to `libvpio.dylib`
- `VPIO_DEBUG` (optional): enable periodic pacer/underflow logs

## Usage

```python
from pipecat_macos_transport.local_mac_transport import (
    LocalMacTransport, LocalMacTransportParams,
)

params = LocalMacTransportParams(audio_in_enabled=True, audio_out_enabled=True)
transport = LocalMacTransport(params)
# wire .input() / .output() into your pipeline
```

## Telemetry

The transport emits periodic telemetry (1 Hz) as transport messages that can be
consumed by TUIs:

```
{"type": "transport-telemetry", "data": {
  "avg_ms": 5.1,
  "max_ms": 12.3,
  "slow_count": 0,
  "underflows_delta": 0,
  "play_ring": 4096,
  "cap_ring": 2048,
  "stage_ring": 3200,   # if available
  "stage_cap": 8192
}}
```

## Device selection

Parameters `input_device_name` and `output_device_name` are accepted; current
helper uses system defaults. Future releases may wire device selection via
CoreAudio.

## Run a test bot

```bash
cd test
uv run bot.py
```

## Roadmap
- Device selection support
- Prebuilt universal2 wheels
- More telemetry and diagnostics
