#!/usr/bin/env python3
"""
GPIO Relay Probe Script

Tests Raspberry Pi GPIO pins one at a time so you can identify
which pins are connected to your relay board.

Most relay boards are active LOW:
    pin.off() -> relay ON
    pin.on()  -> relay OFF
"""

import time
from gpiozero import OutputDevice

# Common GPIO pins that are safe to test
TEST_PINS = [
    4, 17, 18, 22, 23, 24, 25, 27
]


def test_pin(pin_number, duration=3):
    print(f"\nTesting GPIO {pin_number}...")

    # active_high=False means relay is active LOW
    relay = OutputDevice(
        pin_number,
        active_high=False,
        initial_value=False  # OFF initially
    )

    print(f"Turning GPIO {pin_number} ON for {duration} seconds...")
    relay.on()   # Energizes relay
    time.sleep(duration)

    print(f"Turning GPIO {pin_number} OFF...")
    relay.off()

    relay.close()


def main():
    print("=" * 50)
    print("Raspberry Pi GPIO Relay Probe")
    print("=" * 50)
    print("Listen for relay clicks or watch LEDs.")
    print("Press Ctrl+C to stop.\n")

    try:
        for pin in TEST_PINS:
            input(f"Press Enter to test GPIO {pin}...")
            test_pin(pin)

    except KeyboardInterrupt:
        print("\nExiting safely.")


if __name__ == "__main__":
    main()
