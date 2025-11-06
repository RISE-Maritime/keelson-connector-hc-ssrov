#!/usr/bin/env python3
"""
Test script to measure the maximum poll rate of the ROV hand controller.
Measures both button press timing and joystick axes update timing.
"""

import serial
import time
import re
from collections import defaultdict
from datetime import datetime

# Configuration
PORT = '/dev/ttyACM1'
BAUD = 115200
TEST_DURATION = 30  # seconds

def parse_button_press(line: str):
    """Parse button press event."""
    match = re.search(r'Button\s+(\d+)\s+pressed', line)
    if match:
        return int(match.group(1))
    return None

def parse_axes(line: str):
    """Parse axes data."""
    if '|' not in line:
        return None
    
    try:
        _, filtered = line.split('|', 1)
        x_match = re.search(r'X-Axis:\s*(\d+)', filtered)
        y_match = re.search(r'Y-Axis:\s*(\d+)', filtered)
        rz_match = re.search(r'Rz-Axis:\s*(\d+)', filtered)
        z_match = re.search(r'Z-Axis:\s*(\d+)', filtered)
        
        if all([x_match, y_match, rz_match, z_match]):
            return {
                'x': int(x_match.group(1)),
                'y': int(y_match.group(1)),
                'rz': int(rz_match.group(1)),
                'z': int(z_match.group(1)),
            }
    except:
        pass
    return None

def main():
    print("=" * 80)
    print("ROV Hand Controller Poll Rate Test")
    print("=" * 80)
    print(f"Port: {PORT}")
    print(f"Baud: {BAUD}")
    print(f"Test Duration: {TEST_DURATION} seconds")
    print()
    print("Instructions:")
    print("1. Press buttons rapidly and repeatedly during the test")
    print("2. Move joysticks continuously during the test")
    print("3. Test will run for {} seconds".format(TEST_DURATION))
    print()
    input("Press Enter to start the test...")
    
    # Open serial port
    try:
        ser = serial.Serial(
            port=PORT,
            baudrate=BAUD,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.01,  # 10ms timeout
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
        )
        print(f"✓ Opened {PORT} at {BAUD} baud")
    except serial.SerialException as e:
        print(f"✗ Failed to open {PORT}: {e}")
        return
    
    # Statistics
    button_times = defaultdict(list)  # button_num -> list of timestamps
    axes_times = []  # list of timestamps for axes updates
    axes_intervals = []  # intervals between axes updates
    button_intervals = defaultdict(list)  # button_num -> list of intervals
    total_lines = 0
    unknown_lines = 0
    
    start_time = time.time()
    last_axes_time = None
    last_button_time = defaultdict(lambda: None)
    
    buffer = b''
    
    print()
    print("=" * 80)
    print("COLLECTING DATA...")
    print("=" * 80)
    print()
    
    try:
        while (time.time() - start_time) < TEST_DURATION:
            elapsed = time.time() - start_time
            
            # Progress indicator
            if int(elapsed) % 5 == 0 and elapsed > 0:
                print(f"  {int(elapsed)}s elapsed... (buttons: {sum(len(v) for v in button_times.values())}, axes: {len(axes_times)})")
                time.sleep(0.1)  # Avoid printing multiple times in same second
            
            if ser.in_waiting > 0:
                chunk = ser.read(ser.in_waiting)
                buffer += chunk
                
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    if not line:
                        continue
                    
                    total_lines += 1
                    current_time = time.time()
                    
                    try:
                        decoded = line.decode('utf-8', errors='ignore').strip()
                        
                        # Check for button press
                        button_num = parse_button_press(decoded)
                        if button_num is not None:
                            button_times[button_num].append(current_time)
                            
                            # Calculate interval
                            if last_button_time[button_num] is not None:
                                interval = current_time - last_button_time[button_num]
                                button_intervals[button_num].append(interval)
                            
                            last_button_time[button_num] = current_time
                            continue
                        
                        # Check for axes data
                        axes = parse_axes(decoded)
                        if axes is not None:
                            axes_times.append(current_time)
                            
                            # Calculate interval
                            if last_axes_time is not None:
                                interval = current_time - last_axes_time
                                axes_intervals.append(interval)
                            
                            last_axes_time = current_time
                            continue
                        
                        unknown_lines += 1
                        
                    except Exception as e:
                        unknown_lines += 1
            else:
                time.sleep(0.001)
    
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    
    finally:
        ser.close()
        actual_duration = time.time() - start_time
    
    # Print results
    print()
    print("=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    print()
    print(f"Actual Test Duration: {actual_duration:.2f} seconds")
    print(f"Total Lines Received: {total_lines}")
    print(f"Unknown/Unparsed Lines: {unknown_lines}")
    print()
    
    # Axes statistics
    print("-" * 80)
    print("JOYSTICK AXES UPDATE RATE")
    print("-" * 80)
    if axes_times:
        print(f"Total axes updates: {len(axes_times)}")
        print(f"Average rate: {len(axes_times)/actual_duration:.2f} updates/second")
        
        if axes_intervals:
            avg_interval = sum(axes_intervals) / len(axes_intervals)
            min_interval = min(axes_intervals)
            max_interval = max(axes_intervals)
            
            print(f"Average interval: {avg_interval*1000:.2f} ms ({1/avg_interval:.2f} Hz)")
            print(f"Min interval: {min_interval*1000:.2f} ms ({1/min_interval:.2f} Hz)")
            print(f"Max interval: {max_interval*1000:.2f} ms ({1/max_interval:.2f} Hz)")
            
            # Show distribution
            print("\nInterval distribution:")
            ranges = [
                (0, 0.010, "0-10 ms"),
                (0.010, 0.050, "10-50 ms"),
                (0.050, 0.100, "50-100 ms"),
                (0.100, 0.500, "100-500 ms"),
                (0.500, 1.0, "500-1000 ms"),
                (1.0, 5.0, "1-5 sec"),
                (5.0, float('inf'), ">5 sec"),
            ]
            
            for min_r, max_r, label in ranges:
                count = sum(1 for i in axes_intervals if min_r <= i < max_r)
                if count > 0:
                    pct = (count / len(axes_intervals)) * 100
                    print(f"  {label:15s}: {count:4d} ({pct:5.1f}%)")
    else:
        print("No axes data received during test!")
    
    print()
    
    # Button statistics
    print("-" * 80)
    print("BUTTON PRESS RATE")
    print("-" * 80)
    total_button_presses = sum(len(v) for v in button_times.values())
    
    if total_button_presses > 0:
        print(f"Total button presses detected: {total_button_presses}")
        print(f"Average rate: {total_button_presses/actual_duration:.2f} presses/second")
        print()
        
        # Per-button statistics
        print("Per-button breakdown:")
        for button_num in sorted(button_times.keys()):
            times = button_times[button_num]
            intervals = button_intervals[button_num]
            
            print(f"\n  Button {button_num}:")
            print(f"    Total presses: {len(times)}")
            
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                min_interval = min(intervals)
                max_interval = max(intervals)
                
                print(f"    Avg interval: {avg_interval*1000:.2f} ms ({1/avg_interval:.2f} Hz)")
                print(f"    Min interval: {min_interval*1000:.2f} ms ({1/min_interval:.2f} Hz)")
                print(f"    Max interval: {max_interval*1000:.2f} ms")
                
                # Fast presses (< 100ms)
                fast_presses = sum(1 for i in intervals if i < 0.1)
                if fast_presses > 0:
                    print(f"    Fast presses (<100ms): {fast_presses} ({fast_presses/len(intervals)*100:.1f}%)")
    else:
        print("No button presses detected during test!")
    
    print()
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if axes_intervals:
        avg_axes_interval = sum(axes_intervals) / len(axes_intervals)
        print(f"• Joystick polling can safely use {avg_axes_interval*1000:.0f}ms intervals")
        print(f"• Maximum joystick update rate: ~{1/min(axes_intervals):.1f} Hz")
    
    if total_button_presses > 0:
        all_intervals = []
        for intervals in button_intervals.values():
            all_intervals.extend(intervals)
        
        if all_intervals:
            min_btn_interval = min(all_intervals)
            print(f"• Button press detection needs <{min_btn_interval*1000:.0f}ms polling to catch all events")
            print(f"• Recommended poll rate for buttons: ≤{min_btn_interval/2*1000:.1f}ms (safety margin)")
    
    print()


if __name__ == "__main__":
    main()
