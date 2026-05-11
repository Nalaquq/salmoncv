#!/bin/bash

# Main project/home directory
BASE_DIR="$HOME/salmoncv"

# Snapshot directories
SNAPSHOT_DIR="$BASE_DIR/salmoncam_snapshot"
SYS_DIR="$SNAPSHOT_DIR/sys"

# Create base directory if it does not exist
if [ ! -d "$BASE_DIR" ]; then
    mkdir -p "$BASE_DIR"
    echo "Created $BASE_DIR"
fi

# Create snapshot directory if it does not exist
if [ ! -d "$SNAPSHOT_DIR" ]; then
    mkdir -p "$SNAPSHOT_DIR"
    echo "Created $SNAPSHOT_DIR"
fi

# Create sys directory only if it does not exist
if [ ! -d "$SYS_DIR" ]; then
    mkdir -p "$SYS_DIR"
    echo "Created $SYS_DIR"
else
    echo "Using existing $SYS_DIR"
fi

# Move into snapshot directory
cd "$SNAPSHOT_DIR" || exit

# Save Python requirements in snapshot root
pip freeze > requirements.txt

# Save OS/system info
uname -a > "$SYS_DIR/system_info.txt"
cat /etc/os-release >> "$SYS_DIR/system_info.txt"

# Hardware info
lscpu > "$SYS_DIR/cpu_info.txt"
free -h > "$SYS_DIR/memory_info.txt"
lsblk > "$SYS_DIR/disk_info.txt"

# Raspberry Pi hardware info
cat /proc/cpuinfo > "$SYS_DIR/pi_cpuinfo.txt"

# Camera stack info
libcamera-hello --version > "$SYS_DIR/camera_stack.txt" 2>&1

python3 -c "import picamera2; print(picamera2.__version__)" \
>> "$SYS_DIR/camera_stack.txt" 2>/dev/null

python3 -c "import pycoral; print('pycoral installed')" \
>> "$SYS_DIR/camera_stack.txt" 2>/dev/null

# Installed apt packages
dpkg --get-selections > "$SYS_DIR/apt_packages.txt"

# Network configuration
ip addr > "$SYS_DIR/network_info.txt"
iwconfig >> "$SYS_DIR/network_info.txt" 2>&1

# Docker info (if installed)
docker images > "$SYS_DIR/docker_images.txt" 2>/dev/null
docker ps -a > "$SYS_DIR/docker_containers.txt" 2>/dev/null

echo ""
echo "Snapshot complete."
echo "Saved to: $SNAPSHOT_DIR"