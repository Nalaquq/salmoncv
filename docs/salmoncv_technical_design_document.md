# SalmonCV Technical Design Document

**Project:** SalmonCV Automated Fish Counting System  
**Organization:** Nalaquq, LLC  
**Repository:** https://github.com/Nalaquq/salmoncv  
**Version:** 1.0  
**Generated:** 2026-05-11 22:26 UTC

---

# 1. Executive Summary

SalmonCV is a rugged, solar-powered, edge-computing platform designed to automatically detect and count salmon in remote river environments. The system uses a Raspberry Pi 5, high-resolution imaging, Google Coral Edge TPU acceleration, environmental sensors, and scheduled Starlink uploads to support near real-time fisheries monitoring and machine learning development.

The platform is intended for deployment in Quinhagak, Alaska, where it must operate autonomously in harsh environmental conditions with limited connectivity and constrained power budgets.

---

# 2. Project Objectives

- Capture high-frequency time-lapse imagery of salmon migration.
- Perform on-device inference using TensorFlow Lite models accelerated by a Coral Edge TPU.
- Record environmental metadata (temperature, humidity, pressure).
- Store images and results locally.
- Upload selected data daily via Starlink.
- Provide a browser-based configuration interface.
- Operate continuously using solar and battery power.
- Support future expansion to underwater cameras and sonar.

---

# 3. System Requirements

## Functional Requirements
- Adjustable capture intervals (1 second to several minutes).
- Local web interface accessible via Wi-Fi or Ethernet.
- Automated control of lights and Starlink power.
- Robust image storage and metadata logging.
- Scheduled uploads to a remote server.
- Automated startup after power restoration.

## Environmental Requirements
- Waterproof enclosure.
- Operation in Alaska coastal conditions.
- Resistance to rain, salt spray, and temperature extremes.

## Power Requirements
- Continuous operation of Raspberry Pi and sensors.
- Intermittent operation of lights and Starlink.
- Solar recharging with marine battery storage.

---

# 4. High-Level Architecture

```text
Solar Panel -> Charge Controller -> 12 V Battery -> Fuses/Bus Bars
                                              |
                                              +-> Buck Converter (5 V) -> Raspberry Pi 5
                                              |                           |
                                              |                           +-> Camera
                                              |                           +-> Coral TPU
                                              |                           +-> BME280
                                              |                           +-> Flask Web App
                                              |
                                              +-> Relay Board -> Automotive Relays
                                                                  |-> LED Lights
                                                                  |-> Starlink
```

---

# 5. Hardware Architecture

## Computing Subsystem
- Raspberry Pi 5
- Google Coral USB or M.2 Edge TPU
- 256 GB microSD (development)
- Optional 1 TB NVMe SSD

## Imaging Subsystem
- Raspberry Pi camera module
- Waterproof housing
- Polarizing filter
- 38 mm viewing port

## Illumination
- 12 V marine LED floodlights

## Communications
- Starlink terminal
- Wi-Fi hotspot
- Ethernet

## Sensors
- BME280 environmental sensor

## Power Components
- 100 W solar panel
- 30 A charge controller
- 12 V marine battery
- Fuse block
- Bus bars
- DC-DC buck converters
- Automotive relays

---

# 6. Power System Design

## Base Load
- Raspberry Pi 5: 5–10 W
- Coral TPU: 2–4 W
- Camera and sensors: <2 W

## Intermittent Loads
- LED lights: 20–100 W depending on configuration
- Starlink Mini or standard terminal: 20–100+ W

## Strategy
The Raspberry Pi remains active continuously. GPIO-controlled relays power lights and Starlink only when needed.

---

# 7. Optical System

The camera views the river through a waterproof port. A removable circular polarizing filter reduces glare from the water surface. Focus and exposure are tuned for fish located approximately 20 feet from the camera.

---

# 8. Software Architecture

## Operating System
- Raspberry Pi OS

## Python Environment
- Python 3.9 compatible virtual environment
- Optional Docker container for Coral runtime

## Major Libraries
- Flask
- OpenCV
- Pillow
- TensorFlow Lite
- pycoral
- APScheduler (planned)

---

# 9. Software Modules

```text
app/
  flask_app.py
camera/
  capture.py
coral/
  inference.py
sensors/
  bme280_logger.py
power/
  relay_control.py
uploads/
  starlink_upload.py
scheduler/
  task_scheduler.py
```

---

# 10. Flask Web Interface

The Flask application provides configuration and status monitoring.

## Planned Features
- Capture interval settings
- Camera exposure controls
- Lighting schedule
- Starlink upload schedule
- Storage status
- Live preview
- Manual trigger buttons

---

# 11. Image Capture Pipeline

1. Scheduler triggers image capture.
2. Camera acquires image.
3. Metadata are recorded.
4. Coral TPU performs inference.
5. Results are saved to disk.
6. Detection summaries are logged.

---

# 12. Machine Learning Pipeline

## Training Workflow
- Upload images to a central server.
- Annotate images.
- Train object detection models.
- Convert to TensorFlow Lite.
- Compile for Edge TPU.
- Deploy to field units.

---

# 13. Data Storage

## Local Storage
- Raw images
- Thumbnails
- Detection outputs
- Environmental logs
- Upload manifests

## Remote Storage
- Cloud or self-hosted server
- Dataset repository
- Model archive

---

# 14. Starlink Upload Workflow

1. GPIO enables relay powering Starlink.
2. Starlink establishes connection.
3. Upload script transfers data.
4. Upload manifest is updated.
5. Starlink is powered down.

---

# 15. Environmental Monitoring

The BME280 sensor records:
- Temperature
- Relative humidity
- Barometric pressure

These measurements are synchronized with each capture event.

---

# 16. Proposed Directory Structure

```text
salmoncv/
├── app/
├── camera/
├── coral/
├── sensors/
├── power/
├── scheduler/
├── uploads/
├── salmon_captures/
├── models/
├── logs/
├── sys/
├── docs/
├── requirements.txt
└── README.md
```

---

# 17. Security Considerations

- Local authentication for the Flask interface
- Firewall rules
- Secure SSH access
- Encrypted uploads when possible

---

# 18. Deployment Workflow

1. Assemble electronics.
2. Configure Raspberry Pi OS.
3. Install Python environment.
4. Deploy software.
5. Conduct bench testing.
6. Validate power system.
7. Field deploy in Quinhagak.
8. Monitor uploads and refine models.

---

# 19. Testing and Validation

## Bench Tests
- Camera focus and exposure
- Relay control
- Starlink uploads
- Sensor logging

## Field Tests
- Battery endurance
- Solar charging performance
- Detection accuracy

---

# 20. Maintenance

- Clean viewing port
- Inspect cables and seals
- Review logs
- Update models
- Replace worn batteries

---

# 21. Future Enhancements

- Underwater cameras
- Sonar integration
- Real-time dashboards
- Active learning
- Multi-camera deployments

---

# 22. Bill of Materials (Summary)

- Raspberry Pi 5
- Coral Edge TPU
- Camera module
- Waterproof enclosure
- BME280 sensor
- Starlink terminal
- Solar panel
- Charge controller
- Marine battery
- Relays and wiring

---

# 23. Research Applications

SalmonCV supports:
- Fisheries monitoring
- Community-based environmental observation
- Machine learning dataset generation
- Edge AI research
- Arctic field instrumentation

---

# 24. Immediate Next Steps

1. Finalize enclosure and optics.
2. Complete Flask application.
3. Integrate Coral inference.
4. Implement upload scheduler.
5. Conduct pilot deployment.

---

# End of Technical Design Document
