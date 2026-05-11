# Fish Counts Project Conversation History (Context Export)

**Generated:** 2026-05-11 22:22:22

> **Important Note:** This file is compiled from the project conversation summaries and recent conversation context currently available in this chat session. It is **not a complete verbatim export of every message** from all conversations in the project, because I do not have direct access to the full text of all historical chats unless they are loaded into the current context or stored as files.
>
> However, this document captures the key topics, timestamps, and message summaries that are currently available and should serve as a useful project archive and reference.

---

## Project Overview

This project centers on the development of a Raspberry Pi–based automated salmon counting system (`salmoncv`) for deployment in Quinhagak, Alaska. The system integrates:

- Raspberry Pi 5
- High-resolution camera for time-lapse image capture
- Google Coral Edge TPU for on-device inference
- Starlink for daily data uploads
- Solar charging and marine battery power
- Environmental sensors (e.g., BME280)
- Flask-based web interface for remote configuration
- Computer vision models for salmon detection and counting

---

# Recent Project Conversations

## 2026-05-11 — Livestream on Raspberry Pi
**User:** What command can I use to livestream video on my Pi?

---

## 2026-05-09 — Control Lights and Starlink from Raspberry Pi
Topics included:

- Initializing a Git repository for `salmoncv`
- Adding a GitHub remote
- Creating the first commit
- Pushing to GitHub
- Pulling the repository to a development machine using VS Code

Key commands discussed:

```bash
git clone https://github.com/Nalaquq/salmoncv.git
```

---

## 2026-05-11 — Photo File Size Estimate
Topics included:

- Estimating image sizes from the selected camera sensor
- Calculating Starlink upload requirements
- Planning daily data transfer schedules

---

## 2026-05-11 — Photocell Compatibility with DC Systems
Topics included:

- Using a TORK photocontrol on DC power
- Wire gauge selection
- Whether thicker wire is always better
- Using 14 AWG wire from Raspberry Pi relay to automotive relay

---

## 2026-05-08 — Raspberry Pi Control for Starlink and Lights
Topics included:

- GPIO relay control
- Required cables and connectors
- Relay placement outside the camera housing
- Fuse sizing and 12V wiring strategies
- Integrating buck converters and load control

---

## 2026-05-08 — Flask App for Raspberry Pi
Topics included:

- Creating a Flask-based configuration interface
- Accessing the Pi via Wi-Fi from a phone or computer
- Setting trigger settings for:
  - Camera
  - Lights
  - Starlink upload schedule
- Automatically launching the Flask app on boot
- Integrating with a Python virtual environment

---

## 2026-05-07 — PowerShell SSH and Wi-Fi Configuration
Topics included:

- Using `nmcli` to connect the Pi to Wi-Fi
- Resolving WPA security configuration issues
- Creating persistent NetworkManager connections

---

## 2026-05-06 — Camera and Lighting Hardware
Topics included:

- Marine LED spotlights for nighttime illumination
- Evaluating waterproof lighting options

---

## 2026-05-06 — Raspberry Pi Camera Web App Architecture
Topics included:

- Building a Flask application similar to the Parrot Sequoia interface
- Adjustable camera parameters
- Markdown documentation of system architecture
- Exporting system information and Python requirements

Example system inventory script:

```bash
mkdir -p ~/salmoncv/sys
pip freeze > ~/salmoncv/requirements.txt
uname -a > ~/salmoncv/sys/uname.txt
lsusb > ~/salmoncv/sys/lsusb.txt
lspci > ~/salmoncv/sys/lspci.txt
```

---

## 2026-05-03 — Solar Power and Charge Controller Design
Topics included:

- Selecting a 30A solar charge controller
- Estimating battery requirements for:
  - Raspberry Pi
  - Coral TPU
  - Starlink
- Wiring diagrams and fuse protection

---

## 2026-05-05 — Underwater Camera and Sonar Integration
Topics included:

- USB underwater camera options
- Blue Robotics imaging sonars
- Arctic deployment strategies

---

## 2026-05-05 — Raspberry Pi Storage Upgrades
Topics included:

- NVMe SSDs using PCIe HATs
- Samsung T9 external SSDs
- Storage options for high-frequency time-lapse imagery

---

## 2026-05-05 — Cloud Storage for Uploaded Images
Topics included:

- Low-cost server storage solutions
- Uploading images via Starlink
- Building labeled datasets for machine learning

---

## 2026-05-04 — Waterproof Filter Mounting
Topics included:

- Mounting polarizing filters over a 38 mm case opening
- Maintaining watertight seals
- Non-permanent mounting strategies

---

## 2026-05-02 — Solar Charging Design
Topics included:

- 100W solar panels
- 10A charge controllers
- Marine batteries
- Bus bars, fuses, and buck converters

---

## 2026-05-04 — BME280 Environmental Sensor
Topics included:

- Reading temperature, humidity, and pressure from a BME280 sensor
- Python scripts for data logging

---

## 2026-05-03 — Coral TPU and Python Environment
Topics included:

- Installing `pyenv`
- Python 3.9 compatibility for Coral libraries
- Docker-based Coral environments
- Camera focus issues and automatic exposure control

---

## 2026-05-02 — Image Storage Estimation
Topics included:

- Number of images that fit on a 256 GB microSD card
- Choosing time-lapse intervals
- Daily retrieval and upload planning

---

# System Architecture Summary

## Hardware Components

### Computing
- Raspberry Pi 5
- Google Coral Edge TPU
- 256 GB microSD or NVMe SSD

### Imaging
- 12 MP camera module
- Waterproof housing
- Polarizing filter

### Connectivity
- Starlink Mini or standard terminal
- Wi-Fi and Ethernet access

### Power
- 100W solar panel
- 30A charge controller
- 12V marine battery
- DC-DC buck converters
- Automotive relays

### Sensors
- BME280 environmental sensor
- Optional underwater camera or sonar

---

# Software Stack

## Operating System
- Raspberry Pi OS

## Python Environment
- Python 3.9 virtual environment
- Docker for Coral compatibility

## Application Framework
- Flask web interface

## Computer Vision
- TensorFlow Lite
- Coral Edge TPU runtime
- OpenCV
- Pillow

## Data Transfer
- GitHub for source control
- Starlink for image uploads

---

# Planned Workflow

1. User connects to Raspberry Pi via Wi-Fi or Ethernet.
2. Flask interface allows configuration of:
   - Capture interval
   - Camera settings
   - Lighting schedule
   - Starlink upload timing
3. Raspberry Pi captures images automatically.
4. Coral TPU performs on-device inference.
5. Images and metadata are stored locally.
6. Starlink powers on at scheduled times.
7. Data is uploaded to a remote server.
8. Server hosts labeled datasets for algorithm development.

---

# GitHub Repository

Repository:
https://github.com/Nalaquq/salmoncv

---

# Suggested Directory Structure

```text
salmoncv/
├── app/
│   ├── flask_app.py
│   ├── templates/
│   └── static/
├── camera/
├── coral/
├── uploads/
├── sys/
├── requirements.txt
└── README.md
```

---

# Key Objectives

- Autonomous salmon counting
- Remote field deployment in Alaska
- Solar-powered operation
- Near real-time data upload
- Continuous model improvement
- Open, reproducible workflow

---

# Future Development Goals

- Automated fish counting dashboard
- Environmental metadata integration
- Web-based annotation tools
- Active learning pipeline
- Edge-to-cloud model retraining
- Search and rescue and environmental monitoring extensions

---

# End of Context Export
