# SalmonCV Chronological Development Log

**Project:** SalmonCV Automated Fish Counting System  
**Organization:** Nalaquq, LLC  
**Repository:** https://github.com/Nalaquq/salmoncv  
**Generated:** 2026-05-11 22:24 UTC

---

## Project Vision

SalmonCV is a solar-powered, Raspberry Pi–based computer vision platform designed to autonomously monitor salmon movement in remote environments such as Quinhagak, Alaska. The system combines time-lapse imaging, on-device inference using a Coral Edge TPU, environmental sensing, and scheduled data uploads over Starlink.

Primary objectives include:

- Automated salmon detection and counting
- Low-power, field-hardened deployment
- Daily data synchronization via Starlink
- Continuous machine learning model improvement
- Support for fisheries research and community-based monitoring

---

# 1. Initial Concept Development

## Core Idea
The project began with the goal of building a rugged, inexpensive, and extensible camera trap capable of collecting high-frequency imagery for salmon counting.

## Early Design Principles

- Use commodity hardware
- Minimize power consumption
- Enable remote configuration
- Support edge AI inference
- Operate autonomously for extended periods

---

# 2. Hardware Platform Selection

## Computing Platform
- Raspberry Pi 5
- Google Coral USB or M.2 Edge TPU
- 256 GB microSD card initially, later expanded to NVMe SSD options

## Imaging
- Raspberry Pi camera module
- Waterproof enclosure
- Polarizing filter to reduce glare
- Marine LED floodlights for nighttime illumination

## Connectivity
- Starlink for satellite uploads
- Wi-Fi and Ethernet for local access

## Sensors
- BME280 environmental sensor
- Optional underwater cameras and sonar systems

---

# 3. Power System Engineering

## Power Components
- 100 W solar panel
- 30 A charge controller
- 12 V marine battery
- Fuses and bus bars
- Buck converters
- Automotive relays controlled by Raspberry Pi GPIO

## Controlled Loads
- Raspberry Pi and Coral TPU
- Camera
- Lighting
- Starlink terminal

## Design Goal
Provide enough stored energy to run the system continuously while powering Starlink only during scheduled upload windows.

---

# 4. Image Storage and Capture Planning

## Storage Estimates
Extensive discussion focused on estimating image sizes and determining how many images could fit on:

- 256 GB microSD cards
- 1 TB NVMe SSDs
- External USB SSDs such as the Samsung T9

## Time-Lapse Strategy
A three-second interval was selected as an initial operating mode for salmon monitoring.

---

# 5. Coral TPU Software Environment

## Python Compatibility
The Coral runtime required Python 3.9 compatibility, leading to evaluation of:

- pyenv
- Virtual environments
- Docker containers

## Dependencies
- TensorFlow Lite
- pycoral
- OpenCV
- Pillow

---

# 6. Camera Testing and Optical Calibration

## Challenges Encountered
- Blurry imagery
- Incorrect focus distance
- Exposure and autofocus tuning

## Desired Capability
Capture sharp images of salmon approximately 20 feet from the camera.

---

# 7. Flask Web Application Architecture

## Concept
A web interface accessible over Wi-Fi or Ethernet allows field users to configure and operate the system.

## Planned Settings
- Capture interval
- Camera parameters
- Lighting schedule
- Starlink upload schedule
- Trigger thresholds

## Deployment
The Flask application will launch automatically on boot and run within a Python virtual environment.

---

# 8. GitHub Repository Setup

## Repository
`Nalaquq/salmoncv`

## Initial Workflow
- Initialize local Git repository
- Add GitHub remote
- Commit source code
- Push to GitHub
- Clone to development machines using VS Code

---

# 9. Environmental Sensor Integration

## BME280
Added to collect:
- Temperature
- Humidity
- Barometric pressure

These data will be stored alongside imagery and detection results.

---

# 10. Starlink Upload Strategy

## Operational Model
Images and metadata are collected locally throughout the day. Starlink powers on during scheduled windows to transmit data to a remote server.

## Planned Server Uses
- Central image archive
- Annotation and labeling
- Model training
- Dashboard visualization

---

# 11. Underwater and Sonar Exploration

The project considered underwater imaging and sonar options, including systems from Blue Robotics, for future fish monitoring and habitat studies.

---

# 12. Waterproof Housing and Optics

Engineering discussions focused on:
- 38 mm viewing ports
- Replaceable polarizing filters
- Watertight, non-permanent mounting systems

---

# 13. Current Software Stack

## Operating System
- Raspberry Pi OS

## Core Libraries
- Flask
- OpenCV
- Pillow
- TensorFlow Lite
- pycoral

## Development Tools
- VS Code
- GitHub
- Docker

---

# 14. Proposed Directory Structure

```text
salmoncv/
├── app/
│   ├── flask_app.py
│   ├── templates/
│   └── static/
├── camera/
├── coral/
├── sensors/
├── uploads/
├── salmon_captures/
├── sys/
├── requirements.txt
└── README.md
```

---

# 15. Future Development Milestones

## Software
- Complete Flask interface
- Implement scheduler
- Add Starlink power control
- Integrate Coral inference pipeline

## Hardware
- Finalize enclosure
- Complete wiring harness
- Test solar charging system

## Data Pipeline
- Build upload scripts
- Establish cloud storage
- Create annotation workflow

## Research
- Train salmon detection models
- Compare counting approaches
- Publish methods and results

---

# 16. Long-Term Vision

SalmonCV serves as a modular environmental monitoring platform with applications beyond fish counting, including:

- Wildlife monitoring
- Coastal observation
- Search and rescue
- Cultural heritage documentation
- Community-based science

---

# 17. Immediate Next Steps

1. Finalize camera focus and exposure settings.
2. Build Flask configuration interface.
3. Integrate Coral TPU inference.
4. Implement relay control for lights and Starlink.
5. Conduct bench tests.
6. Deploy pilot unit in Quinhagak.
7. Begin dataset labeling and model refinement.

---

# End of Development Log
