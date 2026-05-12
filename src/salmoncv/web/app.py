#!/usr/bin/env python3

import argparse
import csv
import json
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

from salmoncv.storage import get_capture_dir, get_storage_info, set_storage_pref, DATA_DIR

THUMB_DIR = DATA_DIR / "thumbs"
PID_FILE = DATA_DIR / ".camera_pid"
LIGHTS_PID = DATA_DIR / ".lights_pid"
STARLINK_PID = DATA_DIR / ".starlink_pid"
SENSORS_PID = DATA_DIR / ".sensors_pid"
LIGHTS_CONF = DATA_DIR / "lights_config.json"
STARLINK_CONF = DATA_DIR / "starlink_config.json"
SYSTEM_CONF = DATA_DIR / "system_config.json"
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
        capture_dir = get_capture_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = capture_dir / f"capture_{timestamp}.jpg"
        data = request.get_json(silent=True) or {}
        shutter = data.get("shutter", 0)
        gain = data.get("gain", 0)
        awb = data.get("awb", "auto")
        ev = data.get("ev", 0)
        try:
            cmd = [
                "rpicam-still", "-o", str(image_path),
                "--width", "2028", "--height", "1520",
                "--timeout", "1000", "--nopreview",
                "--awb", str(awb),
            ]
            if shutter > 0:
                cmd.extend(["--shutter", str(shutter)])
            if gain > 0:
                cmd.extend(["--gain", str(gain)])
            if ev != 0:
                cmd.extend(["--ev", str(ev)])
            subprocess.run(cmd, check=True, capture_output=True, timeout=15)
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
        shutter = data.get("shutter", 0)
        gain = data.get("gain", 0)
        awb = data.get("awb", "auto")
        ev = data.get("ev", 0)

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        cmd = [
            "salmoncv-camera", "--no-inference",
            "--outdir", str(get_capture_dir()),
            "--interval", str(interval),
            "--width", str(width),
            "--height", str(height),
            "--awb", str(awb),
        ]
        if shutter > 0:
            cmd.extend(["--shutter", str(shutter)])
        if gain > 0:
            cmd.extend(["--gain", str(gain)])
        if ev != 0:
            cmd.extend(["--ev", str(ev)])
        proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        PID_FILE.write_text(str(proc.pid))
        _log_request("/api/camera/start", "start_timelapse",
                      f"interval={interval} {width}x{height} shutter={shutter} gain={gain} awb={awb} ev={ev} pid={proc.pid}")
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

        capture_dir = get_capture_dir()
        images = sorted(capture_dir.glob("*.jpg")) if capture_dir.exists() else []
        today = datetime.now().strftime("%Y%m%d")
        today_count = sum(1 for img in images if today in img.name)

        last_capture = ""
        if images:
            last_capture = images[-1].name

        info = get_storage_info()
        return jsonify({
            "running": running,
            "total_images": len(images),
            "today_images": today_count,
            "last_capture": last_capture,
            "storage_drive": info["drive"],
        })

    # --- Gallery API ---

    @app.route("/api/gallery")
    def api_gallery():
        page = request.args.get("page", 1, type=int)
        per_page = 50

        capture_dir = get_capture_dir()
        images = sorted(
            capture_dir.glob("*.jpg"), reverse=True
        ) if capture_dir.exists() else []

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
        return send_from_directory(str(get_capture_dir()), filename)

    @app.route("/api/gallery/thumb/<filename>")
    def api_gallery_thumb(filename):
        THUMB_DIR.mkdir(parents=True, exist_ok=True)
        thumb_path = THUMB_DIR / filename

        if not thumb_path.exists():
            capture_dir = get_capture_dir()
            source = capture_dir / filename
            if not source.exists():
                return "Not found", 404
            try:
                from PIL import Image
                img = Image.open(source)
                img.thumbnail((300, 300))
                img.save(thumb_path, "JPEG", quality=70)
            except Exception:
                return send_from_directory(str(capture_dir), filename)

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
        except Exception as e:
            return jsonify({"ok": False, "error": f"Sensor not available: {e}"})

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
            new = get_new_images(get_capture_dir(), DEFAULT_MANIFEST)
            total_mb = sum(img.stat().st_size for img in new) / (1024 * 1024)
            return jsonify({
                "ok": True,
                "pending_images": len(new),
                "pending_mb": round(total_mb, 1),
            })
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)})

    # --- Scheduler API ---

    def _pid_running(pid_file):
        if not pid_file.exists():
            return False, 0
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)
            return True, pid
        except (OSError, ValueError):
            pid_file.unlink(missing_ok=True)
            return False, 0

    @app.route("/api/scheduler/lights/config")
    def api_lights_config():
        conf = {"mode": "auto", "on_time": "", "off_time": ""}
        if LIGHTS_CONF.exists():
            try:
                conf.update(json.loads(LIGHTS_CONF.read_text()))
            except (json.JSONDecodeError, ValueError):
                pass
        running, pid = _pid_running(LIGHTS_PID)
        conf["running"] = running
        conf["pid"] = pid
        return jsonify(conf)

    @app.route("/api/scheduler/lights/start", methods=["POST"])
    def api_lights_start():
        running, _ = _pid_running(LIGHTS_PID)
        if running:
            return jsonify({"ok": False, "error": "Lights scheduler already running"})

        data = request.get_json(silent=True) or {}
        mode = data.get("mode", "auto")
        on_time = data.get("on_time", "")
        off_time = data.get("off_time", "")

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        LIGHTS_CONF.write_text(json.dumps({
            "mode": mode, "on_time": on_time, "off_time": off_time,
        }))

        cmd = ["salmoncv-lights"]
        if mode == "manual" and on_time:
            cmd.extend(["--on-time", on_time])
        if mode == "manual" and off_time:
            cmd.extend(["--off-time", off_time])

        proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        LIGHTS_PID.write_text(str(proc.pid))
        _log_request("/api/scheduler/lights/start", "lights_scheduler_start",
                      f"mode={mode} on={on_time} off={off_time} pid={proc.pid}")
        return jsonify({"ok": True, "pid": proc.pid})

    @app.route("/api/scheduler/lights/stop", methods=["POST"])
    def api_lights_stop():
        running, pid = _pid_running(LIGHTS_PID)
        if not running:
            return jsonify({"ok": False, "error": "Lights scheduler not running"})
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
        LIGHTS_PID.unlink(missing_ok=True)
        _log_request("/api/scheduler/lights/stop", "lights_scheduler_stop")
        return jsonify({"ok": True})

    @app.route("/api/scheduler/starlink/config")
    def api_starlink_config():
        conf = {
            "mode": "auto", "on_time": "", "upload_time": "",
            "admin_time": "12:00", "admin_duration": 15,
            "upload_speed": 5.0,
        }
        if STARLINK_CONF.exists():
            try:
                conf.update(json.loads(STARLINK_CONF.read_text()))
            except (json.JSONDecodeError, ValueError):
                pass
        running, pid = _pid_running(STARLINK_PID)
        conf["running"] = running
        conf["pid"] = pid
        return jsonify(conf)

    @app.route("/api/scheduler/starlink/start", methods=["POST"])
    def api_starlink_start():
        running, _ = _pid_running(STARLINK_PID)
        if running:
            return jsonify({"ok": False, "error": "Starlink scheduler already running"})

        data = request.get_json(silent=True) or {}
        mode = data.get("mode", "auto")
        on_time = data.get("on_time", "")
        upload_time = data.get("upload_time", "")
        admin_time = data.get("admin_time", "12:00")
        admin_duration = data.get("admin_duration", 15)
        upload_speed = data.get("upload_speed", 5.0)

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        STARLINK_CONF.write_text(json.dumps({
            "mode": mode, "on_time": on_time, "upload_time": upload_time,
            "admin_time": admin_time, "admin_duration": admin_duration,
            "upload_speed": upload_speed,
        }))

        cmd = ["salmoncv-starlink",
               "--upload-speed", str(upload_speed),
               "--admin-duration", str(admin_duration)]
        if mode == "manual" and on_time:
            cmd.extend(["--on-time", on_time])
        if upload_time:
            cmd.extend(["--upload-time", str(upload_time)])
        if admin_time and admin_time != "off":
            cmd.extend(["--admin-time", admin_time])
        elif admin_time == "off":
            cmd.extend(["--admin-time", "off"])

        proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        STARLINK_PID.write_text(str(proc.pid))
        _log_request("/api/scheduler/starlink/start", "starlink_scheduler_start",
                      f"mode={mode} on={on_time} upload={upload_time} admin={admin_time} pid={proc.pid}")
        return jsonify({"ok": True, "pid": proc.pid})

    @app.route("/api/scheduler/starlink/stop", methods=["POST"])
    def api_starlink_stop():
        running, pid = _pid_running(STARLINK_PID)
        if not running:
            return jsonify({"ok": False, "error": "Starlink scheduler not running"})
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
        STARLINK_PID.unlink(missing_ok=True)
        _log_request("/api/scheduler/starlink/stop", "starlink_scheduler_stop")
        return jsonify({"ok": True})

    # --- System Start/Stop ---

    def _stop_pid(pid_file):
        running, pid = _pid_running(pid_file)
        if running:
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
        pid_file.unlink(missing_ok=True)
        return running

    @app.route("/api/system/start", methods=["POST"])
    def api_system_start():
        data = request.get_json(silent=True) or {}
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        results = {}

        # Camera
        cam_running, _ = _pid_running(PID_FILE)
        if not cam_running:
            cam_interval = data.get("camera_interval", 3)
            cam_width = data.get("camera_width", 4056)
            cam_height = data.get("camera_height", 3040)
            proc = subprocess.Popen(
                ["salmoncv-camera", "--no-inference",
                 "--outdir", str(get_capture_dir()),
                 "--interval", str(cam_interval),
                 "--width", str(cam_width),
                 "--height", str(cam_height)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            PID_FILE.write_text(str(proc.pid))
            results["camera"] = {"started": True, "pid": proc.pid}
        else:
            results["camera"] = {"started": False, "reason": "already running"}

        # Sensors
        sens_running, _ = _pid_running(SENSORS_PID)
        if not sens_running:
            sens_interval = data.get("sensor_interval", 30)
            proc = subprocess.Popen(
                ["salmoncv-sensors", "--interval", str(sens_interval)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            SENSORS_PID.write_text(str(proc.pid))
            results["sensors"] = {"started": True, "pid": proc.pid}
        else:
            results["sensors"] = {"started": False, "reason": "already running"}

        # Lights scheduler
        ls_running, _ = _pid_running(LIGHTS_PID)
        if not ls_running:
            ls_conf = {"mode": "auto", "on_time": "", "off_time": ""}
            if LIGHTS_CONF.exists():
                try:
                    ls_conf.update(json.loads(LIGHTS_CONF.read_text()))
                except (json.JSONDecodeError, ValueError):
                    pass
            cmd = ["salmoncv-lights"]
            if ls_conf["mode"] == "manual":
                if ls_conf.get("on_time"):
                    cmd.extend(["--on-time", ls_conf["on_time"]])
                if ls_conf.get("off_time"):
                    cmd.extend(["--off-time", ls_conf["off_time"]])
            proc = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            LIGHTS_PID.write_text(str(proc.pid))
            results["lights"] = {"started": True, "pid": proc.pid}
        else:
            results["lights"] = {"started": False, "reason": "already running"}

        # Starlink scheduler
        sl_running, _ = _pid_running(STARLINK_PID)
        if not sl_running:
            sl_conf = {
                "mode": "auto", "on_time": "", "upload_time": "",
                "admin_time": "12:00", "admin_duration": 15,
                "upload_speed": 5.0,
            }
            if STARLINK_CONF.exists():
                try:
                    sl_conf.update(json.loads(STARLINK_CONF.read_text()))
                except (json.JSONDecodeError, ValueError):
                    pass
            cmd = ["salmoncv-starlink",
                   "--upload-speed", str(sl_conf["upload_speed"]),
                   "--admin-duration", str(sl_conf["admin_duration"])]
            if sl_conf["mode"] == "manual" and sl_conf.get("on_time"):
                cmd.extend(["--on-time", sl_conf["on_time"]])
            if sl_conf.get("upload_time"):
                cmd.extend(["--upload-time", str(sl_conf["upload_time"])])
            admin = sl_conf.get("admin_time", "12:00")
            if admin and admin != "off":
                cmd.extend(["--admin-time", admin])
            elif admin == "off":
                cmd.extend(["--admin-time", "off"])
            proc = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            STARLINK_PID.write_text(str(proc.pid))
            results["starlink"] = {"started": True, "pid": proc.pid}
        else:
            results["starlink"] = {"started": False, "reason": "already running"}

        SYSTEM_CONF.write_text(json.dumps({
            "started_at": datetime.now().isoformat(),
            "camera_interval": data.get("camera_interval", 3),
            "sensor_interval": data.get("sensor_interval", 30),
        }))
        _log_request("/api/system/start", "system_start", json.dumps(results))
        return jsonify({"ok": True, "results": results})

    @app.route("/api/system/stop", methods=["POST"])
    def api_system_stop():
        results = {}
        results["camera"] = _stop_pid(PID_FILE)
        results["sensors"] = _stop_pid(SENSORS_PID)
        results["lights"] = _stop_pid(LIGHTS_PID)
        results["starlink"] = _stop_pid(STARLINK_PID)
        if SYSTEM_CONF.exists():
            SYSTEM_CONF.unlink()
        _log_request("/api/system/stop", "system_stop")
        return jsonify({"ok": True, "stopped": results})

    @app.route("/api/system/running")
    def api_system_running():
        cam, _ = _pid_running(PID_FILE)
        sens, _ = _pid_running(SENSORS_PID)
        lights, _ = _pid_running(LIGHTS_PID)
        starlink, _ = _pid_running(STARLINK_PID)
        all_running = cam and sens and lights and starlink
        any_running = cam or sens or lights or starlink
        return jsonify({
            "all_running": all_running,
            "any_running": any_running,
            "camera": cam,
            "sensors": sens,
            "lights": lights,
            "starlink": starlink,
        })

    # --- Storage API ---

    @app.route("/api/storage")
    def api_storage():
        return jsonify(get_storage_info())

    @app.route("/api/storage/set", methods=["POST"])
    def api_storage_set():
        data = request.get_json(silent=True) or {}
        mode = data.get("mode", "auto")
        if mode not in ("auto", "t9", "sd"):
            return jsonify({"ok": False, "error": "Invalid mode"}), 400
        set_storage_pref(mode)
        info = get_storage_info()
        _log_request("/api/storage/set", "storage_mode", mode)
        return jsonify({"ok": True, **info})

    # --- System API ---

    @app.route("/api/system")
    def api_system():
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

        capture_dir = get_capture_dir()
        image_count = len(list(capture_dir.glob("*.jpg"))) if capture_dir.exists() else 0

        return jsonify({
            "hostname": platform.node(),
            "uptime": uptime,
            "cpu_temp_c": cpu_temp,
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
            log_path = get_capture_dir() / logname
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
