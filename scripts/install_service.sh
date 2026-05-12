#!/usr/bin/env bash
set -euo pipefail

VENV_PATH="${1:-/home/nalaquq/salmoncv/venv}"

echo "=== SalmonCV Service Installer ==="

if [ "$EUID" -ne 0 ]; then
  echo "Error: run this script as root (sudo)."
  exit 1
fi

if [ ! -f "$VENV_PATH/bin/salmoncv-web" ]; then
  echo "Error: salmoncv-web not found at $VENV_PATH/bin/salmoncv-web"
  echo "Make sure you've run: pip install -e ."
  exit 1
fi

echo "Creating systemd service..."
cat > /etc/systemd/system/salmoncv-web.service <<EOF
[Unit]
Description=SalmonCV Web Dashboard
After=network.target

[Service]
Type=simple
User=root
ExecStart=$VENV_PATH/bin/salmoncv-web
Restart=always
RestartSec=5
Environment=HOME=/home/nalaquq

[Install]
WantedBy=multi-user.target
EOF

echo "Enabling and starting service..."
systemctl daemon-reload
systemctl enable salmoncv-web
systemctl start salmoncv-web

echo ""
echo "=== Done ==="
echo "salmoncv-web will now start automatically on boot (port 80)."
echo ""
echo "Useful commands:"
echo "  sudo systemctl status salmoncv-web    # check status"
echo "  sudo systemctl restart salmoncv-web   # restart"
echo "  sudo systemctl stop salmoncv-web      # stop"
echo "  sudo journalctl -u salmoncv-web -f    # view logs"
echo "  sudo systemctl disable salmoncv-web   # disable auto-start"
