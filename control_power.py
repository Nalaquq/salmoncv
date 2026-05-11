#!/usr/bin/env python3
"""
Control Starlink and LED lights from Raspberry Pi GPIO.

Assumes:
- IN1 = GPIO17 = lights
- IN2 = GPIO27 = Starlink
- Relay board is active LOW
"""

import argparse
import time
from gpiozero import OutputDevice

# GPIO pin assignments
LIGHTS_PIN = 17
STARLINK_PIN = 27

# Most relay boards are active LOW:
# ON = GPIO LOW
# OFF = GPIO HIGH
lights = OutputDevice(LIGHTS_PIN, active_high=False, initial_value=False)
starlink = OutputDevice(STARLINK_PIN, active_high=False, initial_value=False)


def lights_on():
    lights.on()
    print("Lights ON")


def lights_off():
    lights.off()
    print("Lights OFF")


def starlink_on():
    starlink.on()
    print("Starlink ON")


def starlink_off():
    starlink.off()
    print("Starlink OFF")


def all_off():
    lights_off()
    starlink_off()


def main():
    parser = argparse.ArgumentParser(description="Control lights and Starlink relays.")
    parser.add_argument(
        "command",
        choices=[
            "lights-on",
            "lights-off",
            "starlink-on",
            "starlink-off",
            "all-on",
            "all-off",
            "test",
        ],
    )
    args = parser.parse_args()

    if args.command == "lights-on":
        lights_on()

    elif args.command == "lights-off":
        lights_off()

    elif args.command == "starlink-on":
        starlink_on()

    elif args.command == "starlink-off":
        starlink_off()

    elif args.command == "all-on":
        lights_on()
        starlink_on()

    elif args.command == "all-off":
        all_off()

    elif args.command == "test":
        print("Testing lights for 5 seconds...")
        lights_on()
        time.sleep(5)
        lights_off()

        print("Testing Starlink for 5 seconds...")
        starlink_on()
        time.sleep(5)
        starlink_off()

        print("Test complete.")


if __name__ == "__main__":
    try:
        main()
    finally:
        # Safety: leave both off when script exits
        all_off()
