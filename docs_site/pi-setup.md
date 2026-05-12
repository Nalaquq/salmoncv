# Pi Setup

How to flash and configure a Raspberry Pi 5 for SalmonCV from scratch.

## Requirements

- Raspberry Pi 5
- microSD card (32 GB minimum, 256 GB recommended)
- Another computer with the Raspberry Pi Imager
- Monitor and keyboard (for initial setup)

## Flash the OS

1. Download and install [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Select **Raspberry Pi OS (64-bit)** --- Bookworm or later
3. Click the gear icon to configure:
    - **Hostname**: `nalaquqpi`
    - **Username**: `nalaquq`
    - **Password**: set your password
    - **Wi-Fi**: configure if connecting to an existing network
    - **SSH**: enable
4. Flash the SD card

## First Boot

Insert the SD card and power on. Wait 2--3 minutes for first-boot setup.

### Connect via SSH

```bash
ssh nalaquq@nalaquqpi.local
```

### Update the System

```bash
sudo apt update && sudo apt upgrade -y
```

### Enable I2C

Required for the BME280 sensor:

```bash
sudo raspi-config
```

Navigate to **Interface Options > I2C** and enable it. Reboot if prompted.

### Install System Dependencies

```bash
sudo apt install -y git python3-pip i2c-tools
```

## Clone the Repository

```bash
cd ~
git clone https://github.com/Nalaquq/salmoncv.git
cd salmoncv
```

## Next Steps

- [Coral TPU Setup](coral-tpu-setup.md) --- install Python 3.9 and Coral libraries
- [Getting Started](getting-started.md) --- install SalmonCV and test the hardware
