# Keelson Subject Proposal: Generic Controller Inputs

## Summary

New generic Keelson subjects for joystick/gamepad controller inputs. The subjects describe **what type of input** occurred, while the source-id identifies **which controller and which physical control** produced it.

## Proposed Subjects

### Axis Subjects — `TimestampedFloat`

All axis values are normalized to **-1.0 to 1.0** range, regardless of hardware resolution.

| Subject | Value Range | Description |
|---------|-------------|-------------|
| `joystick_x` | -1.0 to 1.0 | Primary X axis (left-right) |
| `joystick_y` | -1.0 to 1.0 | Primary Y axis (forward-back) |
| `joystick_z` | -1.0 to 1.0 | Z axis (throttle/heave) |
| `joystick_rx` | -1.0 to 1.0 | Rotation X axis |
| `joystick_ry` | -1.0 to 1.0 | Rotation Y axis |
| `joystick_rz` | -1.0 to 1.0 | Rotation Z axis (twist/yaw) |
| `dpad_x` | -1.0, 0.0, 1.0 | D-pad horizontal (left/center/right) |
| `dpad_y` | -1.0, 0.0, 1.0 | D-pad vertical (down/center/up) |
| `joystick_lt` | 0.0 to 1.0 | Left trigger (analog or digital) |
| `joystick_rt` | 0.0 to 1.0 | Right trigger (analog or digital) |

### Button Subject — `TimestampedInt`

| Subject               | Value  | Description                              |
|-----------------------|--------|------------------------------------------|
| `button_state_change` | 1 or 0 | A button was pressed (1) or released (0) |

A single `button_state_change` subject is used for both press and release. The button identity is encoded in the source-id path (see below).

## Protobuf Messages

### Axes: `TimestampedFloat`

```protobuf
message TimestampedFloat {
  google.protobuf.Timestamp timestamp = 1;
  float value = 2;
}
```

Normalized float values. Sticks range from -1.0 to 1.0, triggers from 0.0 to 1.0, D-pad uses discrete -1.0/0.0/1.0.

### Buttons: `TimestampedInt`

```protobuf
message TimestampedInt {
  google.protobuf.Timestamp timestamp = 1;
  int32 value = 2;
}
```

Value is 1 (pressed) or 0 (released).

## Key Expression Pattern

```
{realm}/@v0/{entity_id}/pubsub/{subject}/controller/{hw}/{function}
```

Where `controller` is the source type, `{hw}` is the hardware profile (ssrov, logitech), and `{function}` is the specific control name.

### Axis keys

```
rise/@v0/rov/pubsub/joystick_x/controller/ssrov/joystick_x
rise/@v0/rov/pubsub/joystick_y/controller/logitech/joystick_y
rise/@v0/rov/pubsub/joystick_rz/controller/ssrov/joystick_rz
rise/@v0/rov/pubsub/dpad_x/controller/logitech/dpad_x
rise/@v0/rov/pubsub/joystick_lt/controller/logitech/joystick_lt
```

### Button keys

```
rise/@v0/rov/pubsub/button_state_change/controller/ssrov/arm
rise/@v0/rov/pubsub/button_state_change/controller/logitech/a
rise/@v0/rov/pubsub/button_state_change/controller/logitech/lb
```

## Zenoh Subscription Patterns

| Pattern | What you get |
|---------|-------------|
| `**/pubsub/button_state_change/**` | All button events from all controllers |
| `**/pubsub/button_state_change/controller/logitech/**` | All buttons from Logitech gamepad |
| `**/pubsub/button_state_change/controller/logitech/a` | Only the A button on the Logitech |
| `**/pubsub/joystick_x/**` | X-axis from all controllers |
| `**/pubsub/joystick_*/controller/logitech/*` | All stick axes from the Logitech |
| `**/pubsub/dpad_*/controller/logitech/*` | D-pad axes from the Logitech |
| `**/pubsub/*/controller/ssrov/**` | All events from the SSROV controller |

## Design Rationale

### Generic subjects, structured source-ids

The subject describes the **type of event** (axis movement, button state change). The source-id follows the pattern `controller/{hw}/{function}` — identifying the source type, the hardware profile, and the specific control. This lets a control manager subscribe to generic subjects and map them to vessel-specific functions without knowing which controller hardware is connected.

### Normalized float values for axes

Raw int16 values (-32768 to 32767) are tied to the Linux joystick API. Normalized floats (-1.0 to 1.0) are portable — any controller maps to the same range regardless of hardware resolution. Consumers don't need to know the underlying hardware precision.

### Single `button_state_change` subject

Using one subject for both press and release (instead of separate pressed/released subjects) simplifies subscriptions. The value (1/0) carries the state. A subscriber watching `**/button_state_change/controller/logitech/a` gets both events.

### D-pad as two axes

A D-pad is inherently a 2-axis discrete input. Publishing `dpad_x` and `dpad_y` is more natural than 4 separate buttons, handles diagonals as a single pair of events, and is consistent with how analog sticks are represented.

### Trigger axes

Triggers are published as axis values (0.0 to 1.0) regardless of whether the hardware reports them as buttons (digital) or axes (analog). This provides a uniform interface — consumers don't need to know if the trigger is analog or digital.

## Currently Supported Controllers

### Seascape ROV Hand Controller (`controller/ssrov`)

**Axes**: `joystick_x`, `joystick_y`, `joystick_z`, `joystick_rz`

**Button names**: `grip_open`, `grip_close`, `lights_up`, `lights_down`, `gain_up`, `gain_down`, `tilt_up`, `tilt_down`, `shift`, `mode_manual`, `mode_stabilize`, `mode_depth_hold`, `mode_poshold`, `arm`, `disarm`, `a`, `b`, `top_left`, `top_right`

### Logitech F310/F710 Gamepad (`controller/logitech`)

**Axes**: `joystick_x`, `joystick_y`, `joystick_rx`, `joystick_ry`, `dpad_x`, `dpad_y`, `joystick_lt`, `joystick_rt`

**Button names**: `x`, `a`, `b`, `y`, `lb`, `rb`, `back`, `start`, `l3`, `r3`
