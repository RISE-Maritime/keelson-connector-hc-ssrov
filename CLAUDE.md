# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Keelson/Zenoh connector that reads from a Seascape ROV Hand Controller via the Linux joystick interface (`/dev/input/js0`) and publishes real-time HID events to the Keelson maritime protocol as protobuf `TimestampedInt` messages.

## Commands

**Linting:**
```bash
black --check bin/*
pylint bin/*
black bin/*          # auto-format
```

**Testing (manual, requires joystick device):**
```bash
python examples/joystick_reader.py --list       # list available devices
python examples/joystick_reader.py              # read joystick events live
python test_poll_rate.py                        # measure poll rate (30s)
python test_fast_buttons.py                     # measure button detection (15s)
```

**Run the connector:**
```bash
python bin/hcssrov2keelson --realm rise --entity-id rov --source-id controller/hc
docker compose -f docker-compose.hc-ssrov.yml up
```

## Architecture

**Main script:** [bin/hcssrov2keelson](bin/hcssrov2keelson) — reads 8-byte HID events from `/dev/input/js0` and publishes to Zenoh/Keelson.

**Argument parsing:** [bin/terminal_inputs.py](bin/terminal_inputs.py) — CLI args (`-r/--realm`, `-e/--entity-id`, `-s/--source-id`, `-d/--device`, `-m/--mode`, `--connect`, `-l/--log-level`).

### HID Event Format (8 bytes, struct `IhBB`)
| Field | Size | Type | Description |
|-------|------|------|-------------|
| timestamp | 4 bytes | uint32 | ms since device opened |
| value | 2 bytes | int16 | -32768–32767 (axes) or 0/1 (buttons) |
| type | 1 byte | uint8 | 0x01=button, 0x02=axis, 0x80=init flag |
| number | 1 byte | uint8 | button/axis index |

### Axis Mapping
```python
AXIS_MAP = {0: 'joystick_x', 1: 'joystick_y', 2: 'joystick_z', 5: 'joystick_rz'}
```

Buttons publish to `button_pressed` or `button_released` with the button number as value.

### Keelson Key Expression Pattern
```
{realm}/@v0/{entity_id}/pubsub/{subject}/{source_id}
# e.g.: rise/@v0/rov/pubsub/joystick_x/controller/hc
```

### Key Design Decisions
- **Joystick interface over serial**: kernel-driven events are much faster than the legacy `/dev/ttyACM1` serial at 5-second polling intervals
- **Publisher caching**: `get_or_create_publisher()` lazily creates and caches Zenoh publishers to avoid re-instantiation per event
- **Init events skipped**: events with type `& 0x80` (JS_EVENT_INIT) are ignored to avoid publishing stale state on startup
- **1ms sleep**: prevents busy-waiting without missing events

## Dependencies

- `keelson==0.4.4` — Keelson protocol (Zenoh + protobuf)
- `skarv==0.3.0` — in-memory data vault
- `environs==14.5.0` — env var management
- Dev: `black==25.9.0`, `pylint==4.0.2`

## Docker

Base image: `ghcr.io/rise-maritime/porla:v0.4.1`. The compose file includes two services: a peer-mode service and a client-mode service (enabled via `--profile client`). Both mount `/dev/input/js0` with `privileged: true` and `network_mode: host`.
