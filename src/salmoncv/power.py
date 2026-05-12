#!/usr/bin/env python3

import argparse
import subprocess
import time
from datetime import datetime
from pathlib import Path

LIGHTS_PIN = 17
STARLINK_PIN = 27

STATE_DIR = Path.home() / "salmoncv" / "data"
LIGHTS_STATE = STATE_DIR / ".lights_on_since"
STARLINK_STATE = STATE_DIR / ".starlink_on_since"


def _set_pin(pin, active):
    level = "dh" if active else "dl"
    subprocess.run(["pinctrl", "set", str(pin), "op", level], check=True)


def _write_state(state_file):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file.write_text(datetime.now().isoformat())


def _clear_state(state_file):
    if state_file.exists():
        state_file.unlink()


def lights_on():
    _set_pin(LIGHTS_PIN, True)
    _write_state(LIGHTS_STATE)
    print("Lights ON")


def lights_off():
    _set_pin(LIGHTS_PIN, False)
    _clear_state(LIGHTS_STATE)
    print("Lights OFF")


def starlink_on():
    _set_pin(STARLINK_PIN, True)
    _write_state(STARLINK_STATE)
    print("Starlink ON")


def starlink_off():
    _set_pin(STARLINK_PIN, False)
    _clear_state(STARLINK_STATE)
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
    main()
