#!/usr/bin/env python3

import argparse
import csv
import subprocess
import time
from datetime import datetime
from pathlib import Path


def load_labels(path):
    labels = {}
    if not path:
        return labels

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(maxsplit=1)
            if len(parts) == 2:
                labels[int(parts[0])] = parts[1]
    return labels


def capture_image(command, image_path, width, height):
    subprocess.run(
        [
            command,
            "-o", str(image_path),
            "--width", str(width),
            "--height", str(height),
            "--timeout", "1000",
            "--nopreview",
        ],
        check=True,
    )


def try_read_sensor():
    try:
        import bme280
        import smbus2
        from salmoncv.sensors import PORT, ADDRESS

        bus = smbus2.SMBus(PORT)
        calibration_params = bme280.load_calibration_params(bus, ADDRESS)
        data = bme280.sample(bus, ADDRESS, calibration_params)
        return {
            "temperature_c": round(data.temperature, 2),
            "humidity": round(data.humidity, 2),
            "pressure_hpa": round(data.pressure, 2),
        }
    except Exception:
        return {"temperature_c": "", "humidity": "", "pressure_hpa": ""}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None)
    parser.add_argument("--labels", default=None)
    parser.add_argument("--outdir", default="captures")
    parser.add_argument("--interval", type=float, default=3.0)
    parser.add_argument("--camera-command", default="rpicam-still")
    parser.add_argument("--width", type=int, default=4056)
    parser.add_argument("--height", type=int, default=3040)
    parser.add_argument("--top_k", type=int, default=3)
    parser.add_argument("--threshold", type=float, default=0.05)
    parser.add_argument(
        "--no-inference",
        action="store_true",
        help="Capture images only, skip Coral TPU inference",
    )
    args = parser.parse_args()

    run_inference = not args.no_inference
    if run_inference and not args.model:
        parser.error("--model is required unless --no-inference is set")

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # --- Capture log (always written) ---
    capture_log_path = outdir / "capture_log.csv"
    capture_fieldnames = [
        "timestamp",
        "image_path",
        "file_size_kb",
        "width",
        "height",
        "temperature_c",
        "humidity",
        "pressure_hpa",
    ]

    write_capture_header = (
        not capture_log_path.exists() or capture_log_path.stat().st_size == 0
    )
    capture_log = open(capture_log_path, "a", newline="", encoding="utf-8")
    capture_writer = csv.DictWriter(capture_log, fieldnames=capture_fieldnames)
    if write_capture_header:
        capture_writer.writeheader()

    # --- Inference log (only with model) ---
    interpreter = None
    model_size = None
    labels = {}
    inference_writer = None
    inference_log = None

    if run_inference:
        from PIL import Image
        from pycoral.adapters import classify, common
        from pycoral.utils.edgetpu import make_interpreter

        labels = load_labels(args.labels)
        inference_log_path = outdir / "inference_log.csv"

        interpreter = make_interpreter(args.model)
        interpreter.allocate_tensors()
        model_size = common.input_size(interpreter)

        inference_log = open(inference_log_path, "a", newline="", encoding="utf-8")
        inference_writer = csv.writer(inference_log)

        if inference_log_path.stat().st_size == 0:
            inference_writer.writerow([
                "timestamp",
                "image_path",
                "rank",
                "class_id",
                "label",
                "score",
            ])

    try:
        while True:
            start_time = time.time()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = outdir / f"capture_{file_timestamp}.jpg"

            capture_image(
                args.camera_command,
                image_path,
                args.width,
                args.height,
            )

            file_size_kb = round(image_path.stat().st_size / 1024, 1)
            env = try_read_sensor()

            capture_writer.writerow({
                "timestamp": timestamp,
                "image_path": image_path.name,
                "file_size_kb": file_size_kb,
                "width": args.width,
                "height": args.height,
                "temperature_c": env["temperature_c"],
                "humidity": env["humidity"],
                "pressure_hpa": env["pressure_hpa"],
            })
            capture_log.flush()

            env_str = ""
            if env["temperature_c"] != "":
                env_str = (
                    f"  {env['temperature_c']}°C"
                    f"  {env['humidity']}%"
                    f"  {env['pressure_hpa']}hPa"
                )

            print(f"{timestamp} | {image_path.name} | {file_size_kb}KB{env_str}")

            if run_inference:
                from PIL import Image
                from pycoral.adapters import classify, common

                image = Image.open(image_path).convert("RGB")
                image = image.resize(model_size, Image.LANCZOS)

                common.set_input(interpreter, image)
                interpreter.invoke()

                results = classify.get_classes(
                    interpreter,
                    top_k=args.top_k,
                    score_threshold=args.threshold,
                )

                for rank, result in enumerate(results, start=1):
                    label = labels.get(result.id, "unknown")
                    print(
                        f"  {rank}. id={result.id} "
                        f"label={label} score={result.score:.4f}"
                    )

                    inference_writer.writerow([
                        timestamp,
                        str(image_path),
                        rank,
                        result.id,
                        label,
                        result.score,
                    ])

                inference_log.flush()

            elapsed = time.time() - start_time
            time.sleep(max(0, args.interval - elapsed))

    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        capture_log.close()
        if inference_log:
            inference_log.close()


if __name__ == "__main__":
    main()
