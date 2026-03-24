# Keelson Connector - Joystick/Gamepad Controllers

Reads joystick and gamepad controllers and publishes axes and button events to the Keelson/Zenoh maritime data protocol. Runs in Docker on **Linux, macOS, and Windows**.

## Supported Controllers

| Controller | Flag | Subject Naming | Shift Logic |
|------------|------|---------------|-------------|
| [Seascape ROV Hand Controller](https://www.seascapesubsea.com/product/rov-hand-controller/) | `--controller ssrov` (default) | ROV-function names (`arm`, `joystick_x`) | Yes (button 9) |
| Logitech F310 / F710 Gamepad | `--controller logitech` | Hardware names (`button_a`, `left_stick_x`) | No |

[SSROV DATASHEET.pdf](./doc/SSROV-HC-DATASHEET.pdf) | [SSROV MANUAL.pdf](./doc/SSROV-HC-MANUAL.pdf)

---

## Overview

**Key Features:**
- Real-time axes updates and fast button detection (press & release events)
- Same joystick HID interface used by QGroundControl
- Cross-platform via TCP relay (macOS/Windows) or direct device access (Linux)
- Docker container deployment

**Why Joystick Interface?**

The Seascape controller exposes two interfaces:
- `/dev/ttyACM1` - Serial interface (slower, custom text protocol)
- `/dev/input/js0` - **Joystick HID interface (RECOMMENDED)** - same as QGroundControl uses

---

## Quick Start

### Linux (Direct Device Access)

```bash
# Run directly
python3 bin/hc2keelson -r rise -e rov
```

### macOS / Windows (TCP Relay)

Since Docker Desktop cannot pass USB devices to containers, a host-side relay bridges the controller to the container over TCP.

```bash
# 1. Start relay(s) on host — one per controller, separate ports
uv run bin/hid_relay.py --port 9090                             # SSROV
uv run bin/hid_relay.py --no-mfi --port 9091 --joystick-index 0 # Logitech

# 2. Start the container(s)
docker compose -f docker-compose.hc.yml --profile relay up                     # SSROV only
docker compose -f docker-compose.hc.yml --profile relay --profile logitech-relay up  # Both
```

> **macOS note:** The `--no-mfi` flag is required for the Logitech F310 on macOS. Apple's
> GCController framework exclusively claims known gamepads, hiding them from SDL. Running
> `--no-mfi` disables this and uses IOKit instead. The SSROV must run without `--no-mfi`
> (in a separate relay instance) because IOKit doesn't deliver events for it on macOS.

```
[SSROV]    --> [hid_relay.py :9090] --> [Docker: --controller ssrov]    --> Zenoh/Keelson
[Logitech] --> [hid_relay.py :9091] --> [Docker: --controller logitech] --> Zenoh/Keelson
```

---

## Published Keelson Subjects

| Subject | Type | Description | Value Range |
|---------|------|-------------|-------------|
| `joystick_x` | TimestampedInt | X axis (left-right) | -32768 to 32767 |
| `joystick_y` | TimestampedInt | Y axis (forward-back) | -32768 to 32767 |
| `joystick_rz` | TimestampedInt | Rotation Z (twist) | -32768 to 32767 |
| `joystick_z` | TimestampedInt | Z axis/throttle | -32768 to 32767 |
| `{function}` | TimestampedInt | Mapped button event | 1 (pressed) / 0 (released) |
| `button_pressed` | TimestampedInt | Unmapped button pressed | Button number |
| `button_released` | TimestampedInt | Unmapped button released | Button number |

**Key Expression Pattern:**

```
{realm}/@v0/{entity_id}/pubsub/{subject}/controller/{hw}/{function}
# e.g.: rise/@v0/rov/pubsub/joystick_x/controller/ssrov/joystick_x
# e.g.: rise/@v0/rov/pubsub/button_state_change/controller/ssrov/arm
```

### SSROV Button Mapping (`--controller ssrov`)

| Button | Primary Function | Shift + Button |
|--------|-----------------|----------------|
| 1 | `servo_3_min_momentary` (Open Gripper) | `input_hold_set` |
| 2 | `servo_3_max_momentary` (Close Gripper) | `roll_pitch_toggle` |
| 3 (CCW) | `lights1_brighter` | `trim_roll_inc` |
| 4 (CW) | `lights1_dimmer` | `trim_roll_dec` |
| 5 (CCW) | `gain_inc` | `trim_pitch_inc` |
| 6 (CW) | `gain_dec` | `trim_pitch_dec` |
| 7 | `mount_tilt_up` | |
| 8 | `mount_tilt_down` | |
| 9 | `shift` (modifier) | |
| 10 | `mode_manual` | |
| 11 | `mode_stabilize` | |
| 12 | `mode_depth_hold` | |
| 13 | `mode_poshold` | |
| 14 | `arm` | |
| 15 | `disarm` | |
| 16-19 | User-defined (`a`, `b`, `joystick_top_left`, `joystick_top_right`) | |

### Logitech F310/F710 Mapping (`--controller logitech`)

Generic naming — no shift logic. Set the hardware switch on back to **D** (DirectInput mode). Shows as "Logitech Dual Action".

**Axes:**

| Control | Subject | Value Range |
|---------|---------|-------------|
| Left Stick X | `joystick_x` | -32768 to 32767 |
| Left Stick Y | `joystick_y` | -32768 to 32767 |
| Right Stick X | `joystick_rx` | -32768 to 32767 |
| Right Stick Y | `joystick_ry` | -32768 to 32767 |

**Buttons:** All buttons publish to `button_pressed` / `button_released` with the button number as value.

| Button # | Physical Control |
|----------|-----------------|
| 0 | X (left) |
| 1 | A (bottom) |
| 2 | B (right) |
| 3 | Y (top) |
| 4 | LB |
| 5 | RB |
| 6 | LT |
| 7 | RT |
| 8 | Back |
| 9 | Start |
| 10 | L3 (left stick click) |
| 11 | R3 (right stick click) |
| 12 | D-pad Up |
| 13 | D-pad Down |
| 14 | D-pad Left |
| 15 | D-pad Right |

---

## Usage

### Command-Line Options

```
Arguments:
  -r, --realm REALM              Keelson realm (default: "rise")
  -e, --entity-id ENTITY_ID      Entity identifier (default: "rov")

Device Configuration:
  --device, -d DEVICE            Joystick device path (default: "/dev/input/js0")
  --relay HOST:PORT              TCP relay address for cross-platform mode
                                 (e.g. --relay host.docker.internal:9090)
  -c, --controller {ssrov,logitech}
                                 Controller profile for axis/button mapping (default: ssrov)

Zenoh Configuration:
  --mode {peer,client}           Zenoh session mode (default: peer)
  --connect ENDPOINT             Zenoh router endpoint (can be repeated)

Logging:
  --log-level LEVEL              10=DEBUG, 20=INFO, 30=WARN (default: 20)
```

Source-id is constructed automatically as `controller/{hw}/{function}` from the `--controller` flag.

### Examples

```bash
# Basic usage (Linux, auto-detects /dev/input/js0)
python3 bin/hc2keelson -r rise -e rov

# Custom joystick device
python3 bin/hc2keelson -r rise -e rov --device /dev/input/js1

# TCP relay mode (macOS/Windows)
python3 bin/hc2keelson -r rise -e rov --relay host.docker.internal:9090

# Logitech gamepad via relay
python3 bin/hc2keelson -r rise -e rov --controller logitech --relay host.docker.internal:9091

# Connect to specific Zenoh router
python3 bin/hc2keelson -r rise -e rov \
  --mode client --connect tcp/192.168.1.100:7447
```

---

## Docker Deployment

### Docker Compose Profiles

| Profile | Mode | Platform | Description |
|---------|------|----------|-------------|
| `relay` | TCP relay (SSROV) | All | Connects to host-side `hid_relay.py` on port 9090 |
| `logitech-relay` | TCP relay (Logitech) | All | Logitech F310/F710 via `hid_relay.py` on port 9091 |

> **Note:** Linux direct-device services and client-mode variants are defined but commented out in the compose file. Uncomment and adjust as needed.

```bash
# Start relay on host first
uv run bin/hid_relay.py --port 9090

# Then start container (SSROV)
docker compose -f docker-compose.hc.yml --profile relay up

# Logitech
docker compose -f docker-compose.hc.yml --profile logitech-relay up

# Both controllers
docker compose -f docker-compose.hc.yml --profile relay --profile logitech-relay up
```

### Build Image

```bash
docker build -t keelson-connector-hand-controller .
```

---

## Host Relay (hid_relay.py)

The relay script reads the joystick on the host using pygame and forwards events over TCP to the container. It uses the same 8-byte binary format as the Linux joystick API.

```bash
# List available joysticks
uv run bin/hid_relay.py --list

# Start relay (default port 9090)
uv run bin/hid_relay.py

# Use second joystick on custom port
uv run bin/hid_relay.py --joystick-index 1 --port 5000

# Remap axis indices (pygame index -> wire index)
uv run bin/hid_relay.py --axis-map '{"3":5}'

# Remap button indices
uv run bin/hid_relay.py --button-map '{"0":2}'
```

---

## Installation

### Prerequisites

- Python 3.13+
- Docker (recommended)
- USB connection to Seascape ROV Hand Controller
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Install Dependencies

```bash
# Container dependencies (installed automatically by Docker)
uv pip install --system -r requirements.txt

# Host relay dependencies (only needed for macOS/Windows relay mode)
uv pip install --system -r requirements_relay.txt

# Development dependencies
uv pip install --system -r requirements_dev.txt
```

---

## Development

### Project Structure

```
keelson-connector-hand-controller/
├── bin/
│   ├── hc2keelson       # Main connector script
│   ├── hid_relay.py          # Cross-platform host-side relay
│   └── terminal_inputs.py    # Argument parsing
├── examples/
│   ├── joystick_reader.py    # Standalone joystick reader
│   └── serial_pyserial_reader.py  # Legacy serial reader
├── doc/                      # Datasheets and documentation
├── docker-compose.hc.yml
├── Dockerfile
├── requirements.txt          # Runtime dependencies
├── requirements_dev.txt      # Dev tools (black, pylint)
├── requirements_relay.txt    # Host relay dependencies (pygame)
└── README.md
```

### Linting

```bash
black --check bin/*    # Check formatting
black bin/*            # Auto-format
pylint bin/*           # Lint
```

### Testing Without Zenoh

```bash
# List available joystick devices (Linux)
python3 examples/joystick_reader.py --list

# Read controller data directly
python3 examples/joystick_reader.py --device /dev/input/js0

# List joysticks cross-platform (via pygame)
uv run bin/hid_relay.py --list
```

---

## Controller Data Format

The connector uses the standard Linux joystick event structure (8 bytes):

```c
struct js_event {
    uint32_t timestamp;  // Milliseconds since device opened
    int16_t  value;      // -32768 to 32767 for axes, 0/1 for buttons
    uint8_t  type;       // JS_EVENT_BUTTON (0x01) or JS_EVENT_AXIS (0x02)
    uint8_t  number;     // Button/axis number
};
```

The TCP relay uses this same binary format over the wire.

---

## Troubleshooting

### Controller Not Detected

```bash
# Linux: check joystick devices
ls -l /dev/input/js*
cat /sys/class/input/js0/device/name
# Should show: seascapesubsea ROV-Controller V1.0.2

# Any OS: list via pygame
uv run bin/hid_relay.py --list
```

### Permission Denied (Linux)

```bash
# Temporary
sudo chmod a+r /dev/input/js0

# Permanent - add user to input group
sudo usermod -a -G input $USER
# Log out and back in
```

### No Events Received

1. Verify controller is powered (LEDs should be lit)
2. Test with `python3 examples/joystick_reader.py` (Linux) or `uv run bin/hid_relay.py --list` (any OS)
3. Move joysticks and press buttons
4. Check kernel module: `lsmod | grep joydev` (Linux)
5. Enable debug logging: `--log-level 10`

### Relay Connection Issues (macOS/Windows)

1. Ensure `hid_relay.py` is running on the host before starting the container
2. Check that the relay port (default 9090) is not blocked by a firewall
3. The container uses `host.docker.internal` to reach the host - this works automatically on Docker Desktop

---

## References

- **Linux Joystick API**: [Documentation](https://www.kernel.org/doc/Documentation/input/joystick-api.txt)
- **Keelson Protocol**: [https://rise-maritime.github.io/keelson/](https://rise-maritime.github.io/keelson/)
- **Zenoh**: [https://zenoh.io/](https://zenoh.io/)
- **Skarv**: [https://freol35241.github.io/skarv/](https://freol35241.github.io/skarv/)
- **uv**: [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)

---

## Contributing

Contributions are welcome! This connector follows the design patterns established in:
- [keelson-connector-nmea](https://github.com/RISE-Maritime/keelson-connector-nmea)
- [keelson-connector-ais](https://github.com/RISE-Maritime/keelson-connector-ais)
