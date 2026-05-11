#!/usr/bin/env python3

import argparse
import csv
import subprocess
import time
from datetime import datetime
from pathlib import Path

from PIL import Image

from pycoral.adapters import classify, common
from pycoral.utils.edgetpu import make_interpreter


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--labels", default=None)
    parser.add_argument("--outdir", default="captures")
    parser.add_argument("--interval", type=float, default=3.0)
    parser.add_argument("--camera-command", default="rpicam-still")
    parser.add_argument("--width", type=int, default=4056)
    parser.add_argument("--height", type=int, default=3040)
    parser.add_argument("--top_k", type=int, default=3)
    parser.add_argument("--threshold", type=float, default=0.05)
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    labels = load_labels(args.labels)
    csv_path = outdir / "inference_log.csv"

    interpreter = make_interpreter(args.model)
    interpreter.allocate_tensors()
    model_size = common.input_size(interpreter)

    with open(csv_path, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        if csv_path.stat().st_size == 0:
            writer.writerow([
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
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_path = outdir / f"capture_{timestamp}.jpg"

                capture_image(
                    args.camera_command,
                    image_path,
                    args.width,
                    args.height,
                )

                image = Image.open(image_path).convert("RGB")
                image = image.resize(model_size, Image.LANCZOS)

                common.set_input(interpreter, image)
                interpreter.invoke()

                results = classify.get_classes(
                    interpreter,
                    top_k=args.top_k,
                    score_threshold=args.threshold,
                )

                print(f"\n{timestamp} | {image_path}")

                for rank, result in enumerate(results, start=1):
                    label = labels.get(result.id, "unknown")
                    print(
                        f"  {rank}. id={result.id} "
                        f"label={label} score={result.score:.4f}"
                    )

                    writer.writerow([
                        timestamp,
                        str(image_path),
                        rank,
                        result.id,
                        label,
                        result.score,
                    ])

                csvfile.flush()

                elapsed = time.time() - start_time
                time.sleep(max(0, args.interval - elapsed))

        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
