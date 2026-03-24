#!/usr/bin/env python3
"""
Raw data dump - shows exactly what the controller sends.
Press buttons and watch the output in real-time.
"""

import serial
import time

PORT = '/dev/ttyACM1'
BAUD = 115200

print("Raw Controller Output")
print("Press buttons and move joysticks, watch what gets sent...")
print("Press Ctrl+C to exit")
print("-" * 80)

ser = serial.Serial(PORT, BAUD, timeout=0.01)
buffer = b''
line_count = 0

try:
    while True:
        if ser.in_waiting > 0:
            chunk = ser.read(ser.in_waiting)
            buffer += chunk
            
            while b'\n' in buffer:
                line, buffer = buffer.split(b'\n', 1)
                if line:
                    line_count += 1
                    timestamp = time.time()
                    decoded = line.decode('utf-8', errors='ignore').strip()
                    print(f"[{line_count:4d}] {timestamp:.3f}: {decoded}")
        else:
            time.sleep(0.001)
except KeyboardInterrupt:
    print("\nDone")
finally:
    ser.close()
