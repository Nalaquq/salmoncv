# Camera

SalmonCV captures time-lapse images using the Raspberry Pi HQ Camera (IMX477) with `rpicam-still`.

## Quick Capture (CLI)

Take a single photo:

```bash
salmoncv-camera --no-inference --outdir ~/salmoncv/test_captures
```

## Time-Lapse Capture

Capture continuously at a set interval:

```bash
salmoncv-camera --no-inference --interval 5 --width 4056 --height 3040
```

Images are saved to the active storage drive (Samsung T9 if available, otherwise SD card). See [Storage](storage.md) for details.

## Camera Settings

### Auto Mode

By default, the camera uses automatic exposure, gain, and white balance. This works well in most daylight conditions.

### Manual Mode

For tricky lighting (underwater, low light, glare), override individual settings:

| Flag | Description | Range |
|------|-------------|-------|
| `--shutter` | Shutter speed in microseconds | 1 -- 200000000 (0 = auto) |
| `--gain` | Analogue gain (ISO) | 0 -- 16 (0 = auto) |
| `--awb` | White balance mode | auto, daylight, cloudy, tungsten, fluorescent, incandescent, indoor |
| `--ev` | Exposure compensation (stops) | -10 to +10 (0 = neutral) |

Example --- freeze fast-moving fish with a short shutter:

```bash
salmoncv-camera --no-inference --shutter 5000 --gain 4 --awb daylight
```

### Web Dashboard Controls

The [Camera page](web-dashboard.md#camera) provides a toggle between Auto and Manual mode. In manual mode you can adjust shutter, gain, white balance, and exposure compensation from the browser --- no SSH needed.

## With Coral TPU Inference

To run fish detection on each captured image:

```bash
salmoncv-camera --model ~/salmoncv/models/fish_model.tflite \
                --labels ~/salmoncv/models/fish_labels.txt \
                --top_k 3 --threshold 0.3
```

This requires the Coral TPU to be connected and the model files to exist. See [Coral TPU Setup](coral-tpu-setup.md).

## Capture Log

Every capture is logged to `capture_log.csv` in the output directory:

| Column | Description |
|--------|-------------|
| timestamp | When the image was taken |
| image_path | Filename |
| file_size_kb | File size in KB |
| width | Image width |
| height | Image height |
| temperature_c | BME280 temperature at capture time |
| humidity | Humidity at capture time |
| pressure_hpa | Pressure at capture time |

Sensor columns are blank if the BME280 is not connected.

## CLI Reference

```
salmoncv-camera [OPTIONS]

  --model PATH         TFLite model file (required unless --no-inference)
  --labels PATH        Labels file
  --outdir PATH        Output directory (default: active storage drive)
  --interval SECONDS   Time between captures (default: 3.0)
  --width PIXELS       Image width (default: 4056)
  --height PIXELS      Image height (default: 3040)
  --no-inference       Capture only, skip Coral TPU
  --shutter MICROSEC   Shutter speed (0 = auto)
  --gain FLOAT         Analogue gain (0 = auto)
  --awb MODE           White balance mode (default: auto)
  --ev FLOAT           Exposure compensation (default: 0)
  --top_k INT          Top K inference results (default: 3)
  --threshold FLOAT    Minimum confidence score (default: 0.05)
  --camera-command CMD rpicam-still command (default: rpicam-still)
```
