# Keelson Connector - Seascape ROV Hand Controller

[Seascape Subsea Product Page](https://www.seascapesubsea.com/product/rov-hand-controller/)

![Seascape ROV Hand Controller](./doc/Seascape-ROV.jpg)

[DATASHEET.pdf](./doc/SSROV-HC-DATASHEET.pdf) | [MANUAL.pdf](./doc/SSROV-HC-MANUAL.pdf)

---

## Overview

This connector reads data from the Seascape ROV Hand Controller via the Linux joystick interface (`/dev/input/js0`) and publishes joystick axes and button events to the Keelson/Zenoh maritime data protocol.

**Key Features:**
- ✅ Uses standard Linux joystick HID interface for maximum reliability
- ✅ **Fast button detection** - catches even very quick button taps
- ✅ Real-time axes updates (no polling delay)
- ✅ Button press AND release events
- ✅ Same interface used by QGroundControl
- ✅ No external dependencies needed (uses Python built-ins)
- ✅ Docker container support for easy deployment

**Why Joystick Interface?**

The Seascape controller exposes TWO interfaces:
- `/dev/ttyACM1` - Serial interface (slower, custom text protocol)
- `/dev/input/js0` - **Joystick HID interface (RECOMMENDED)** - same as QGroundControl uses

This connector uses the joystick interface for best performance and reliability.

---

## Quick Start

### Python Direct

```bash
# Basic usage (auto-detects /dev/input/js0)
python3 bin/hcssrov2keelson -r rise -e rov -s controller/hc
```

### Docker

```bash
# Build and run with docker-compose
docker-compose -f docker-compose.hc-ssrov.yml up hc-ssrov-to-keelson

# Or run in detached mode
docker-compose -f docker-compose.hc-ssrov.yml up -d hc-ssrov-to-keelson
```

---

## Published Keelson Subjects

The connector publishes to the following subjects:

| Subject | Type | Description | Value Range |
|---------|------|-------------|-------------|
| `joystick_x` | TimestampedInt | X axis (left-right) | -32768 to 32767, center ~0 |
| `joystick_y` | TimestampedInt | Y axis (forward-back) | -32768 to 32767, center ~0 |
| `joystick_rz` | TimestampedInt | Rotation Z (twist) | -32768 to 32767, center ~0 |
| `joystick_z` | TimestampedInt | Z axis/throttle | -32768 to 32767, center ~0 |
| `button_pressed` | TimestampedInt | Button pressed event | Button number (0-15) |
| `button_released` | TimestampedInt | Button released event | Button number (0-15) |

**Key Expressions:**
```
rise/@v0/rov/pubsub/joystick_x/controller/hc
rise/@v0/rov/pubsub/joystick_y/controller/hc
rise/@v0/rov/pubsub/joystick_rz/controller/hc
rise/@v0/rov/pubsub/joystick_z/controller/hc
rise/@v0/rov/pubsub/button_pressed/controller/hc
rise/@v0/rov/pubsub/button_released/controller/hc
```

---

## Controller Data Format

The connector reads from the standard Linux joystick interface using the HID protocol.

**Device Characteristics:**
- Device path: `/dev/input/js0` (ROV-Controller V1.0.2 from seascapesubsea)
- Protocol: **Linux joystick API** (HID - Human Interface Device)
- Update rate: **Real-time** events (kernel-driven, no polling delay)
- Axes range: -32768 to 32767 (16-bit signed integer)
- Button states: 0 (released) or 1 (pressed)
- Button numbering: 0-15 (16 buttons)

**Event Structure:**
```c
struct js_event {
    uint32_t timestamp;  // Milliseconds since device opened
    int16_t  value;      // -32768 to 32767 for axes, 0/1 for buttons
    uint8_t  type;       // JS_EVENT_BUTTON (0x01) or JS_EVENT_AXIS (0x02)
    uint8_t  number;     // Button/axis number
};
```

---

## Usage

### Command-Line Options

```
Required Arguments:
  -r, --realm REALM              Keelson realm (default: "rise")
  -e, --entity-id ENTITY_ID      Entity identifier (default: "rov")
  -s, --source-id SOURCE_ID      Source identifier (default: "controller/hc")

Device Configuration:
  --device, -d DEVICE            Joystick device path (default: "/dev/input/js0")

Zenoh Configuration:
  --mode {peer,client}           Zenoh session mode (default: peer)
  --connect ENDPOINT             Zenoh router endpoint (can be used multiple times)

Logging:
  --log-level LEVEL              Log level: 10=DEBUG, 20=INFO, 30=WARN (default: 20)
```

### Examples

**Basic usage:**
```bash
python3 bin/hcssrov2keelson -r rise -e rov -s controller/hc
```

**Custom joystick device:**
```bash
python3 bin/hcssrov2keelson -r rise -e rov -s controller/hc --device /dev/input/js1
```

**Connect to specific Zenoh router:**
```bash
python3 bin/hcssrov2keelson -r rise -e rov -s controller/hc \
  --mode client \
  --connect tcp/192.168.1.100:7447
```

**Debug logging:**
```bash
python3 bin/hcssrov2keelson -r rise -e rov -s controller/hc --log-level 10
```

---

## Docker Deployment

### Build Image

```bash
docker build -t keelson-connector-hc-ssrov .
```

### Run with Docker Compose

```bash
# Start the connector
docker-compose -f docker-compose.hc-ssrov.yml up hc-ssrov-to-keelson

# Start in detached mode
docker-compose -f docker-compose.hc-ssrov.yml up -d hc-ssrov-to-keelson

# View logs
docker-compose -f docker-compose.hc-ssrov.yml logs -f hc-ssrov-to-keelson

# Stop the connector
docker-compose -f docker-compose.hc-ssrov.yml down
```

### Client Mode (Connect to Router)

```bash
# Use the client profile to connect to a specific Zenoh router
docker-compose -f docker-compose.hc-ssrov.yml --profile client up hc-ssrov-to-keelson-client
```

---

## Installation

### Prerequisites

- Python 3.8 or later
- USB connection to Seascape ROV Hand Controller
- Linux with joystick driver support (kernel module: joydev)
- Access to Zenoh router (optional for peer-to-peer mode)

### Install Dependencies

```bash
pip install -r requirements.txt
```

Key dependencies:
- `eclipse-zenoh` - Zenoh messaging library
- `keelson` - Keelson protocol implementation  
- `skarv` - In-memory data vault for state management

**No external joystick libraries needed!** Uses Python's built-in `struct` module.

---

## Development

### Project Structure

```
keelson-connector-hc-ssrov/
├── bin/
│   ├── hcssrov2keelson       # Main connector script (joystick interface)
│   ├── terminal_inputs.py    # Argument parsing
│   └── main                  # Legacy serial script (deprecated)
├── examples/                 # Python examples
│   ├── joystick_reader.py    # RECOMMENDED: Read from joystick device
│   ├── serial_pyserial_reader.py  # Legacy: Serial interface
│   └── README.md
├── doc/                      # Documentation and datasheets
├── docker-compose.hc-ssrov.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

### Testing Without Zenoh

See the [examples/](examples/) directory for standalone Python scripts to test controller reading:

```bash
# List available joystick devices
python3 examples/joystick_reader.py --list

# Read controller data directly (with visual axis bars!)
python3 examples/joystick_reader.py --device /dev/input/js0
```

---

## Troubleshooting

### Controller Not Detected

**Check if joystick device exists:**
```bash
ls -l /dev/input/js*
```

**List all joystick devices:**
```bash
python3 examples/joystick_reader.py --list
```

**Check device name:**
```bash
cat /sys/class/input/js0/device/name
# Should show: seascapesubsea ROV-Controller V1.0.2
```

### Permission Denied

On Linux, grant read access to joystick device:

```bash
# Temporary (current session only)
sudo chmod a+r /dev/input/js0

# Permanent - add user to input group
sudo usermod -a -G input $USER
# Log out and back in for group change to take effect
```

### Wrong Joystick Device

The controller usually appears as:
- `/dev/input/js0` - Most common
- `/dev/input/js1` or higher - If multiple joysticks connected

Specify the correct device with `--device`:
```bash
python3 bin/hcssrov2keelson --device /dev/input/js1 ...
```

### No Events Received

1. **Verify controller is powered** - LEDs should be lit
2. **Test with example script** - `python3 examples/joystick_reader.py`
3. **Move joysticks and press buttons** - Events appear immediately
4. **Check kernel module** - `lsmod | grep joydev`
5. **Enable debug logging** - `--log-level 10`

### Comparison with Serial Interface

| Feature | Joystick (`/dev/input/js0`) | Serial (`/dev/ttyACM1`) |
|---------|---------------------------|------------------------|
| Speed | **Real-time** (kernel events) | ~5 sec polling |
| Button detection | **Excellent** (press & release) | Slow, misses fast taps |
| Reliability | **High** (standard HID) | Medium (custom protocol) |
| Used by QGC | **✅ Yes** | ❌ No |
| Dependencies | None (built-in) | pyserial library |
| Recommended | **✅ YES** | ❌ Legacy only |

---

## References

- **Linux Joystick API**: [Documentation](https://www.kernel.org/doc/Documentation/input/joystick-api.txt)
- **Keelson Protocol**: [https://rise-maritime.github.io/keelson/](https://rise-maritime.github.io/keelson/)
- **Zenoh**: [https://zenoh.io/](https://zenoh.io/)
- **Skarv**: [https://freol35241.github.io/skarv/](https://freol35241.github.io/skarv/)

---

## License

[Include your license information here]

---

## Contributing

Contributions are welcome! This connector follows the design patterns established in:
- [keelson-connector-nmea](https://github.com/RISE-Maritime/keelson-connector-nmea)
- [keelson-connector-ais](https://github.com/RISE-Maritime/keelson-connector-ais)

---

## Support

For issues and questions:
- Open an issue on GitHub
- Refer to the [examples/](examples/) directory for standalone testing scripts
- Check the Keelson documentation for protocol details

---

## Migration from Serial Interface

If you were using the old serial interface (`/dev/ttyACM1`), here's what changed:

**Old (Serial):**
```bash
python3 bin/hcssrov2keelson --port /dev/ttyACM1 --baud 115200 ...
```

**New (Joystick):**
```bash
python3 bin/hcssrov2keelson --device /dev/input/js0 ...
```

**Benefits:**
- ⚡ Much faster response time
- ✅ Reliable button press detection
- ✅ Button release events now available
- 🎯 Matches QGroundControl behavior
- 📦 Fewer dependencies (no pyserial needed)
