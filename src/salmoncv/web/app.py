#!/usr/bin/env python3

import argparse
import csv
import os
import shutil
import signal
import subprocess
import platform
from datetime import datetime
from io import BytesIO
from pathlib import Path

from flask import (
    Flask, render_template, jsonify, request, send_file, send_from_directory,
)

CAPTURE_DIR = Path.home() / "salmoncv" / "captures"
DATA_DIR = Path.home() / "salmoncv" / "data"
THUMB_DIR = DATA_DIR / "thumbs"
PID_FILE = DATA_DIR / ".camera_pid"
WEB_LOG = DATA_DIR / "web_log.csv"


def _log_request(endpoint, action="", detail=""):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    write_header = not WEB_LOG.exists()
    with open(WEB_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["timestamp", "method", "endpoint", "action",
                         "detail", "remote_addr"])
        w.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            request.method,
            endpoint,
            action,
            detail,
            request.remote_addr,
        ])


def create_app():
    app = Flask(__name__)

    # --- Page routes ---

    @app.route("/")
    def dashboard():
        return render_template("dashboard.html")

    @app.route("/camera")
    def camera():
        return render_template("camera.html")

    @app.route("/gallery")
    def gallery():
        return render_template("gallery.html")

    @app.route("/sensors")
    def sensors():
        return render_template("sensors.html")

    @app.route("/power")
    def power():
        return render_template("power.html")

    @app.route("/settings")
    def settings():
        return render_template("settings.html")

    # --- Camera API ---

    @app.route("/api/camera/capture", methods=["POST"])
    def api_camera_capture():
        CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = CAPTURE_DIR / f"capture_{timestamp}.jpg"
        try:
            subprocess.run(
                [
                    "rpicam-still", "-o", str(image_path),
                    "--width", "2028", "--height", "1520",
                    "--timeout", "1000", "--nopreview",
                ],
                check=True, capture_output=True, timeout=15,
            )
            _log_request("/api/camera/capture", "capture", image_path.name)
            return jsonify({"ok": True, "filename": image_path.name})
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            _log_request("/api/camera/capture", "capture_failed", str(e))
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/api/camera/start", methods=["POST"])
    def api_camera_start():
        if PID_FILE.exists():
            pid = int(PID_FILE.read_text().strip())
            try:
                os.kill(pid, 0)
                return jsonify({"ok": False, "error": "Camera already running"})
            except OSError:
                PID_FILE.unlink()

        data = request.get_json(silent=True) or {}
        interval = data.get("interval", 3)
        width = data.get("width", 4056)
        height = data.get("height", 3040)

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        proc = subprocess.Popen(
            [
                "salmoncv-camera", "--no-inference",
                "--outdir", str(CAPTURE_DIR),
                "--interval", str(interval),
                "--width", str(width),
                "--height", str(height),
            ],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        PID_FILE.write_text(str(proc.pid))
        _log_request("/api/camera/start", "start_timelapse",
                      f"interval={interval} {width}x{height} pid={proc.pid}")
        return jsonify({"ok": True, "pid": proc.pid})

    @app.route("/api/camera/stop", methods=["POST"])
    def api_camera_stop():
        if not PID_FILE.exists():
            return jsonify({"ok": False, "error": "Camera not running"})
        pid = int(PID_FILE.read_text().strip())
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
        PID_FILE.unlink(missing_ok=True)
        _log_request("/api/camera/stop", "stop_timelapse")
        return jsonify({"ok": True})

    @app.route("/api/camera/status")
    def api_camera_status():
        running = False
        if PID_FILE.exists():
            try:
                pid = int(PID_FILE.read_text().strip())
                os.kill(pid, 0)
                running = True
            except (OSError, ValueError):
                PID_FILE.unlink(missing_ok=True)

        images = sorted(CAPTURE_DIR.glob("*.jpg")) if CAPTURE_DIR.exists() else []
        today = datetime.now().strftime("%Y%m%d")
        today_count = sum(1 for img in images if today in img.name)

        last_capture = ""
        if images:
            last_capture = images[-1].name

        return jsonify({
            "running": running,
            "total_images": len(images),
            "today_images": today_count,
            "last_capture": last_capture,
        })

    # --- Gallery API ---

    @app.route("/api/gallery")
    def api_gallery():
        page = request.args.get("page", 1, type=int)
        per_page = 50

        images = sorted(
            CAPTURE_DIR.glob("*.jpg"), reverse=True
        ) if CAPTURE_DIR.exists() else []

        total = len(images)
        start = (page - 1) * per_page
        end = start + per_page
        page_images = images[start:end]

        items = []
        for img in page_images:
            items.append({
                "filename": img.name,
                "size_kb": round(img.stat().st_size / 1024, 1),
                "timestamp": img.stat().st_mtime,
            })

        return jsonify({
            "images": items,
            "total": total,
            "page": page,
            "pages": (total + per_page - 1) // per_page,
        })

    @app.route("/api/gallery/<filename>")
    def api_gallery_image(filename):
        return send_from_directory(str(CAPTURE_DIR), filename)

    @app.route("/api/gallery/thumb/<filename>")
    def api_gallery_thumb(filename):
        THUMB_DIR.mkdir(parents=True, exist_ok=True)
        thumb_path = THUMB_DIR / filename

        if not thumb_path.exists():
            source = CAPTURE_DIR / filename
            if not source.exists():
                return "Not found", 404
            try:
                from PIL import Image
                img = Image.open(source)
                img.thumbnail((300, 300))
                img.save(thumb_path, "JPEG", quality=70)
            except Exception:
                return send_from_directory(str(CAPTURE_DIR), filename)

        return send_from_directory(str(THUMB_DIR), filename)

    # --- Sensors API ---

    @app.route("/api/sensors/current")
    def api_sensors_current():
        try:
            import bme280
            import smbus2
            bus = smbus2.SMBus(1)
            cal = bme280.load_calibration_params(bus, 0x76)
            data = bme280.sample(bus, 0x76, cal)
            return jsonify({
                "ok": True,
                "temperature_c": round(data.temperature, 2),
                "temperature_f": round(data.temperature * 9 / 5 + 32, 2),
                "humidity": round(data.humidity, 2),
                "pressure_hpa": round(data.pressure, 2),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
        except Exception:
            return jsonify({"ok": False, "error": "Sensor not available"})

    @app.route("/api/sensors/history")
    def api_sensors_history():
        limit = request.args.get("limit", 50, type=int)
        log_path = DATA_DIR / "sensor_log.csv"
        rows = []
        if log_path.exists():
            with open(log_path, "r", encoding="utf-8") as f:
                reader = list(csv.DictReader(f))
                rows = reader[-limit:]
                rows.reverse()
        return jsonify({"rows": rows})

    # --- Power API ---

    @app.route("/api/power/lights", methods=["POST"])
    def api_power_lights():
        data = request.get_json(silent=True) or {}
        action = data.get("action", "")
        try:
            from salmoncv.power import lights_on, lights_off
            if action == "on":
                lights_on()
            elif action == "off":
                lights_off()
            else:
                return jsonify({"ok": False, "error": "Invalid action"}), 400
            _log_request("/api/power/lights", f"lights_{action}")
            return jsonify({"ok": True, "action": action})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/api/power/starlink", methods=["POST"])
    def api_power_starlink():
        data = request.get_json(silent=True) or {}
        action = data.get("action", "")
        try:
            from salmoncv.power import starlink_on, starlink_off
            if action == "on":
                starlink_on()
            elif action == "off":
                starlink_off()
            else:
                return jsonify({"ok": False, "error": "Invalid action"}), 400
            _log_request("/api/power/starlink", f"starlink_{action}")
            return jsonify({"ok": True, "action": action})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/api/power/status")
    def api_power_status():
        from salmoncv.power import LIGHTS_STATE, STARLINK_STATE

        def relay_info(state_file):
            if state_file.exists():
                try:
                    on_since = datetime.fromisoformat(
                        state_file.read_text().strip()
                    )
                    elapsed = (datetime.now() - on_since).total_seconds()
                    return {"on": True, "since": on_since.isoformat(),
                            "elapsed_min": round(elapsed / 60, 1)}
                except (ValueError, OSError):
                    pass
            return {"on": False, "since": None, "elapsed_min": 0}

        return jsonify({
            "lights": relay_info(LIGHTS_STATE),
            "starlink": relay_info(STARLINK_STATE),
        })

    @app.route("/api/schedule/lights")
    def api_schedule_lights():
        try:
            from salmoncv.lights import get_civil_twilight
            dawn, dusk = get_civil_twilight(59.748, -161.922, "America/Anchorage")
            return jsonify({
                "ok": True,
                "dawn": dawn.strftime("%H:%M"),
                "dusk": dusk.strftime("%H:%M"),
            })
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)})

    @app.route("/api/schedule/starlink")
    def api_schedule_starlink():
        try:
            from salmoncv.starlink import get_new_images, DEFAULT_MANIFEST
            new = get_new_images(CAPTURE_DIR, DEFAULT_MANIFEST)
            total_mb = sum(img.stat().st_size for img in new) / (1024 * 1024)
            return jsonify({
                "ok": True,
                "pending_images": len(new),
                "pending_mb": round(total_mb, 1),
            })
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)})

    # --- System API ---

    @app.route("/api/system")
    def api_system():
        disk = shutil.disk_usage(str(Path.home()))
        uptime = ""
        cpu_temp = ""
        try:
            uptime = Path("/proc/uptime").read_text().split()[0]
            uptime = f"{float(uptime) / 3600:.1f} hours"
        except Exception:
            pass
        try:
            temp = Path("/sys/class/thermal/thermal_zone0/temp").read_text().strip()
            cpu_temp = f"{int(temp) / 1000:.1f}"
        except Exception:
            pass

        image_count = len(list(CAPTURE_DIR.glob("*.jpg"))) if CAPTURE_DIR.exists() else 0

        return jsonify({
            "hostname": platform.node(),
            "uptime": uptime,
            "cpu_temp_c": cpu_temp,
            "disk_total_gb": round(disk.total / (1024 ** 3), 1),
            "disk_used_gb": round(disk.used / (1024 ** 3), 1),
            "disk_free_gb": round(disk.free / (1024 ** 3), 1),
            "disk_percent": round(disk.used / disk.total * 100, 1),
            "image_count": image_count,
        })

    @app.route("/api/logs/<logname>")
    def api_logs(logname):
        allowed = [
            "sensor_log.csv", "lights_log.csv", "starlink_log.csv",
            "watchdog_log.csv", "capture_log.csv", "web_log.csv",
        ]
        if logname not in allowed:
            return "Not found", 404
        log_path = DATA_DIR / logname
        if logname == "capture_log.csv":
            log_path = CAPTURE_DIR / logname
        if not log_path.exists():
            return "Not found", 404
        return send_file(str(log_path), mimetype="text/csv",
                         as_attachment=True, download_name=logname)

    return app


def main():
    parser = argparse.ArgumentParser(description="SalmonCV web dashboard")
    parser.add_argument("--port", type=int, default=80)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    app = create_app()
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
