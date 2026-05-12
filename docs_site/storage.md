# Storage

SalmonCV uses a Samsung T9 SSD as primary storage with automatic fallback to the SD card.

## Storage Priority

| Priority | Drive | Mount Point | Capacity |
|----------|-------|-------------|----------|
| 1 | Samsung T9 SSD | `/media/nalaquq/T9` | 932 GB |
| 2 | SD Card | `~/salmoncv/captures` | ~230 GB |

In **Auto** mode (default), the system checks the T9 on every capture:

- Is it mounted?
- Does it have more than 100 MB free?
- Is it writable?

If all checks pass, images go to the T9. Otherwise, they fall back to the SD card.

## Storage Modes

| Mode | Behavior |
|------|----------|
| **Auto** | T9 first, fall back to SD card |
| **Samsung T9** | T9 only (falls back to SD if unavailable) |
| **SD Card** | SD card only, ignores T9 |

## Change Storage Mode

### From the Dashboard

The [Dashboard](web-dashboard.md) has a storage card with a dropdown to switch between Auto, Samsung T9, and SD Card. The change takes effect immediately and persists across reboots.

### From the CLI

The preference is stored in `~/salmoncv/data/storage_config.json`. The camera reads this on every capture.

## Where Images Are Stored

| Mode | Directory |
|------|-----------|
| T9 active | `/media/nalaquq/T9/salmoncv/captures/` |
| SD card | `~/salmoncv/captures/` |

Each capture is named `capture_YYYYMMDD_HHMMSS.jpg` with a corresponding `capture_log.csv` in the same directory.

## Checking Storage

### Dashboard

The [Settings page](web-dashboard.md#settings) shows usage bars for both the Samsung T9 and SD card, including total, used, and free space.

### CLI

```bash
df -h /media/nalaquq/T9
df -h ~
```

### Verify T9 Is Mounted

```bash
lsblk
```

Look for the T9 partition mounted at `/media/nalaquq/T9`.

## Troubleshooting

**T9 not detected**

- Check the USB cable connection
- Run `lsblk` to see if the drive appears at all
- Try a different USB port on the Pi

**Images going to SD card when T9 is plugged in**

- Check if T9 is mounted: `ls /media/nalaquq/T9`
- Check free space: `df -h /media/nalaquq/T9` (needs >100 MB free)
- Check write permission: `touch /media/nalaquq/T9/test && rm /media/nalaquq/T9/test`

**Switching back to Auto mode**

Delete the config file to reset to Auto:

```bash
rm ~/salmoncv/data/storage_config.json
```
