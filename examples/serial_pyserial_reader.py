#!/usr/bin/env python3
"""
Read Seascape ROV Hand Controller via Serial/USB using PySerial.

This is the recommended method for reading serial data in Python.
The controller connects via USB and appears as /dev/ttyUSB0 (or similar).

Requirements:
    pip install pyserial

Usage:
    # Basic usage
    python3 serial_pyserial_reader.py

    # Specify custom serial port
    python3 serial_pyserial_reader.py --port /dev/ttyUSB1

    # Specify custom baud rate
    python3 serial_pyserial_reader.py --baud 9600

    # List available serial ports
    python3 serial_pyserial_reader.py --list-ports
"""

import argparse
import sys
from datetime import datetime

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("ERROR: PySerial is not installed.")
    print("Install it with: pip install pyserial")
    sys.exit(1)


# Default configuration
DEFAULT_PORT = "/dev/ttyACM1"
DEFAULT_BAUD = 115200
DEFAULT_TIMEOUT = 0.1


def list_serial_ports():
    """List all available serial ports."""
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("No serial ports found!")
        return
    
    print("\nAvailable serial ports:")
    print("=" * 60)
    for port in ports:
        print(f"  Port: {port.device}")
        print(f"    Description: {port.description}")
        print(f"    Hardware ID: {port.hwid}")
        if port.manufacturer:
            print(f"    Manufacturer: {port.manufacturer}")
        print()


def parse_controller_data(data: bytes) -> dict:
    """
    Parse controller data from serial port.
    
    Args:
        data: Raw bytes from serial port
        
    Returns:
        Dictionary with parsed data
    """
    try:
        # Try to decode as UTF-8 text
        text = data.decode("utf-8", errors="ignore").strip()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "raw_bytes": data.hex(),
            "raw_text": text if text else None,
            "length": len(data),
        }
    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "raw_bytes": data.hex(),
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Read Seascape ROV Hand Controller via Serial/USB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--port",
        "-p",
        default=DEFAULT_PORT,
        help=f"Serial port device (default: {DEFAULT_PORT})",
    )
    
    parser.add_argument(
        "--baud",
        "-b",
        type=int,
        default=DEFAULT_BAUD,
        help=f"Baud rate (default: {DEFAULT_BAUD})",
    )
    
    parser.add_argument(
        "--timeout",
        "-t",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"Read timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )
    
    parser.add_argument(
        "--list-ports",
        "-l",
        action="store_true",
        help="List available serial ports and exit",
    )
    
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enable debug output",
    )
    
    args = parser.parse_args()
    
    # List ports and exit
    if args.list_ports:
        list_serial_ports()
        return
    
    print("=" * 60)
    print("Seascape ROV Hand Controller - Serial Reader (PySerial)")
    print("=" * 60)
    print(f"Port:     {args.port}")
    print(f"Baud:     {args.baud}")
    print(f"Timeout:  {args.timeout}s")
    print("=" * 60)
    print()
    
    try:
        # Open serial port
        print(f"Opening serial port {args.port}...")
        ser = serial.Serial(
            port=args.port,
            baudrate=args.baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=args.timeout,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
        )
        
        print(f"Serial port opened successfully!")
        print(f"Press Ctrl+C to stop\n")
        
        packet_count = 0
        
        # Read data loop
        while True:
            # Read a line (until newline character)
            line = ser.readline()
            
            if line:
                packet_count += 1
                
                # Parse the data
                parsed = parse_controller_data(line)
                
                print(f"Packet #{packet_count} - {parsed['timestamp']}")
                print(f"  Length: {parsed['length']} bytes")
                print(f"  Hex:    {parsed['raw_bytes']}")
                
                if parsed.get('raw_text'):
                    print(f"  Text:   {parsed['raw_text']}")
                
                if args.debug and parsed.get('error'):
                    print(f"  Error:  {parsed['error']}")
                
                print()
            
    except serial.SerialException as e:
        print(f"\nSerial port error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check if the device is connected")
        print("  2. Verify the correct port with --list-ports")
        print("  3. Check permissions: sudo usermod -a -G dialout $USER")
        print("  4. Try running with sudo (not recommended)")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\nStopped by user")
        
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
        
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial port closed")


if __name__ == "__main__":
    main()
