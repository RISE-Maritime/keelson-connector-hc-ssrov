#!/usr/bin/env python3
"""
Test script specifically for measuring fast button press detection.
Press ONE button as rapidly as possible to measure minimum detectable interval.
"""

import serial
import time
import re
from datetime import datetime

PORT = '/dev/ttyACM1'
BAUD = 115200
TEST_DURATION = 15  # seconds

def parse_button_press(line: str):
    """Parse button press event."""
    match = re.search(r'Button\s+(\d+)\s+pressed', line)
    if match:
        return int(match.group(1))
    return None

def main():
    print("=" * 80)
    print("FAST BUTTON PRESS TEST")
    print("=" * 80)
    print()
    print(f"Test Duration: {TEST_DURATION} seconds")
    print()
    print("Instructions:")
    print("1. Pick ONE button (any button)")
    print("2. When test starts, press it AS FAST AS POSSIBLE")
    print("3. TAP TAP TAP as rapidly as you can!")
    print("4. This tests the minimum detectable button press interval")
    print()
    input("Press Enter to start...")
    
    try:
        ser = serial.Serial(
            port=PORT,
            baudrate=BAUD,
            timeout=0.01,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
        )
        print(f"✓ Opened {PORT}")
    except serial.SerialException as e:
        print(f"✗ Failed: {e}")
        return
    
    print()
    print("GO! Press as fast as you can!")
    print()
    
    button_events = []  # (timestamp, button_num)
    buffer = b''
    start_time = time.time()
    
    try:
        while (time.time() - start_time) < TEST_DURATION:
            if ser.in_waiting > 0:
                chunk = ser.read(ser.in_waiting)
                buffer += chunk
                
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    if not line:
                        continue
                    
                    try:
                        decoded = line.decode('utf-8', errors='ignore').strip()
                        button_num = parse_button_press(decoded)
                        
                        if button_num is not None:
                            timestamp = time.time()
                            button_events.append((timestamp, button_num))
                            
                            # Provide immediate feedback
                            if len(button_events) > 1:
                                interval = (timestamp - button_events[-2][0]) * 1000
                                print(f"  Button {button_num}: {len(button_events):3d} presses, last interval: {interval:6.2f} ms")
                            else:
                                print(f"  Button {button_num}: First press detected!")
                    except:
                        pass
            else:
                time.sleep(0.0005)  # 0.5ms sleep
    
    except KeyboardInterrupt:
        print("\nStopped early")
    finally:
        ser.close()
        duration = time.time() - start_time
    
    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()
    
    if len(button_events) < 2:
        print("Not enough button presses detected! Try pressing faster.")
        return
    
    # Analyze by button
    from collections import defaultdict
    by_button = defaultdict(list)
    for ts, btn in button_events:
        by_button[btn].append(ts)
    
    print(f"Total Duration: {duration:.2f} seconds")
    print(f"Total Presses Detected: {len(button_events)}")
    print(f"Average Rate: {len(button_events)/duration:.2f} presses/second")
    print()
    
    for btn in sorted(by_button.keys()):
        times = by_button[btn]
        print(f"Button {btn}: {len(times)} presses")
        
        if len(times) >= 2:
            intervals = [(times[i+1] - times[i]) * 1000 for i in range(len(times)-1)]
            
            print(f"  Average interval: {sum(intervals)/len(intervals):.2f} ms")
            print(f"  Minimum interval: {min(intervals):.2f} ms ⚡ FASTEST")
            print(f"  Maximum interval: {max(intervals):.2f} ms")
            
            # Show fastest 5
            sorted_intervals = sorted(intervals)
            print(f"  Top 5 fastest:")
            for i, interval in enumerate(sorted_intervals[:5], 1):
                print(f"    {i}. {interval:.2f} ms")
            
            # Distribution
            ranges = [
                (0, 50, "0-50ms (very fast)"),
                (50, 100, "50-100ms (fast)"),
                (100, 200, "100-200ms (normal)"),
                (200, 500, "200-500ms (slow)"),
                (500, float('inf'), ">500ms (very slow)"),
            ]
            
            print(f"  Distribution:")
            for min_r, max_r, label in ranges:
                count = sum(1 for i in intervals if min_r <= i < max_r)
                if count > 0:
                    pct = (count / len(intervals)) * 100
                    print(f"    {label:25s}: {count:3d} ({pct:5.1f}%)")
        print()
    
    print("=" * 80)
    all_intervals = []
    for times in by_button.values():
        if len(times) >= 2:
            all_intervals.extend([(times[i+1] - times[i]) * 1000 for i in range(len(times)-1)])
    
    if all_intervals:
        min_interval = min(all_intervals)
        print(f"✓ FASTEST BUTTON PRESS DETECTED: {min_interval:.2f} ms")
        print(f"✓ Maximum theoretical detection rate: {1000/min_interval:.1f} presses/second")
        print()
        
        if min_interval < 50:
            print("⚡ Excellent! System can detect very fast button presses (<50ms)")
        elif min_interval < 100:
            print("✓ Good! System can detect fast button presses (<100ms)")
        elif min_interval < 200:
            print("⚠ Moderate. System detects normal speed presses (<200ms)")
        else:
            print("⚠ Slow. May be missing some fast presses (>200ms)")

if __name__ == "__main__":
    main()
