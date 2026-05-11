#!/usr/bin/env python3

import argparse
import csv
import time
from datetime import datetime
from pathlib import Path

import bme280
import smbus2

PORT = 1
ADDRESS = 0x76


def read_sensor(bus, calibration_params):
    data = bme280.sample(bus, ADDRESS, calibration_params)
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "temperature_c": round(data.temperature, 2),
        "temperature_f": round(data.temperature * 9 / 5 + 32, 2),
        "humidity": round(data.humidity, 2),
        "pressure_hpa": round(data.pressure, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="Log BME280 sensor data to CSV.")
    default_log = Path.home() / "salmoncv" / "data" / "sensor_log.csv"
    parser.add_argument(
        "--logfile",
        default=str(default_log),
        help=f"Path to the CSV log file (default: {default_log})",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Seconds between readings (default: 2.0)",
    )
    args = parser.parse_args()

    log_path = Path(args.logfile)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    bus = smbus2.SMBus(PORT)
    calibration_params = bme280.load_calibration_params(bus, ADDRESS)

    fieldnames = [
        "timestamp",
        "temperature_c",
        "temperature_f",
        "humidity",
        "pressure_hpa",
    ]

    write_header = not log_path.exists() or log_path.stat().st_size == 0

    print(f"Logging BME280 data to {log_path} every {args.interval}s\n")

    try:
        with open(log_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            if write_header:
                writer.writeheader()

            while True:
                reading = read_sensor(bus, calibration_params)
                writer.writerow(reading)
                f.flush()

                print(
                    f"{reading['timestamp']}  "
                    f"{reading['temperature_c']}°C / {reading['temperature_f']}°F  "
                    f"{reading['humidity']}%  "
                    f"{reading['pressure_hpa']} hPa"
                )

                time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
