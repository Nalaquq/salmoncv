#!/usr/bin/env bash
set -euo pipefail

# ---- Defaults ----
SSID="SalmonCV"
PASS="salmon2026"
AP_IP="192.168.4.1"
DHCP_START="192.168.4.10"
DHCP_END="192.168.4.50"
DRY_RUN=false
SAFE_MODE=false
SAFE_MINUTES=5
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ---- Usage ----
usage() {
    cat <<USAGE
Usage: sudo bash setup_hotspot.sh [OPTIONS] [SSID] [PASSWORD]

Options:
  --dry-run         Show what would be changed without modifying anything
  --safe [MINUTES]  Schedule automatic revert after MINUTES (default: 5)
                    If the hotspot breaks SSH, the Pi reverts on its own
  --revert          Undo all hotspot changes immediately
  -h, --help        Show this help

Examples:
  sudo bash setup_hotspot.sh --dry-run              # Preview changes
  sudo bash setup_hotspot.sh --safe                  # Install with 5-min safety net
  sudo bash setup_hotspot.sh --safe 10               # Install with 10-min safety net
  sudo bash setup_hotspot.sh                         # Install (no safety net)
  sudo bash setup_hotspot.sh "MySSID" "mypass"       # Custom SSID and password
  sudo bash setup_hotspot.sh --revert                # Undo everything
USAGE
    exit 0
}

# ---- Detect wlan0 channel for simultaneous AP+client ----
detect_channel() {
    local chan
    chan=$(iw dev wlan0 info 2>/dev/null | awk '/channel/ {print $2; exit}')
    if [ -z "$chan" ] || [ "$chan" = "0" ]; then
        echo "7"
        echo "g"
    else
        echo "$chan"
        if [ "$chan" -ge 36 ]; then
            echo "a"
        else
            echo "g"
        fi
    fi
}

# ---- Parse args ----
POSITIONAL=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --safe)
            SAFE_MODE=true
            shift
            if [[ $# -gt 0 && "$1" =~ ^[0-9]+$ ]]; then
                SAFE_MINUTES="$1"
                shift
            fi
            ;;
        --revert)
            if [ "$EUID" -ne 0 ]; then
                echo "Error: run with sudo."
                exit 1
            fi
            bash "$SCRIPT_DIR/revert_hotspot.sh"
            exit 0
            ;;
        -h|--help)
            usage
            ;;
        *)
            POSITIONAL+=("$1")
            shift
            ;;
    esac
done

# Positional args: SSID and PASSWORD
if [ ${#POSITIONAL[@]} -ge 1 ]; then
    SSID="${POSITIONAL[0]}"
fi
if [ ${#POSITIONAL[@]} -ge 2 ]; then
    PASS="${POSITIONAL[1]}"
fi

# Detect channel
read -r CHANNEL HW_MODE <<< "$(detect_channel | tr '\n' ' ')"

# ---- Header ----
echo "=== SalmonCV Hotspot Setup ==="
echo "SSID:     $SSID"
echo "Password: $PASS"
echo "AP IP:    $AP_IP"
echo "DHCP:     $DHCP_START – $DHCP_END"
echo "Channel:  $CHANNEL ($( [ "$HW_MODE" = "a" ] && echo "5 GHz" || echo "2.4 GHz" ))"
if $DRY_RUN; then
    echo "Mode:     DRY RUN (no changes will be made)"
fi
if $SAFE_MODE; then
    echo "Mode:     SAFE (auto-revert in $SAFE_MINUTES minutes if you don't cancel)"
fi
echo ""

# ---- Root check (skip for dry-run) ----
if ! $DRY_RUN && [ "$EUID" -ne 0 ]; then
    echo "Error: run this script as root (sudo)."
    echo "Tip: try --dry-run first to preview changes safely."
    exit 1
fi

# ---- Show what will be created ----
echo "--- /etc/NetworkManager/conf.d/unmanage-ap0.conf ---"
cat <<EOF
[keyfile]
unmanaged-devices=interface-name:ap0
EOF
echo ""

echo "--- /etc/systemd/system/ap0.service ---"
cat <<EOF
[Unit]
Description=Create ap0 virtual interface for SalmonCV hotspot
Before=hostapd.service
After=NetworkManager.service
Wants=NetworkManager.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStartPre=/bin/sleep 3
ExecStart=/sbin/iw dev wlan0 interface add ap0 type __ap
ExecStart=/sbin/ip addr add $AP_IP/24 dev ap0
ExecStart=/sbin/ip link set ap0 up
ExecStop=/sbin/iw dev ap0 del

[Install]
WantedBy=multi-user.target
EOF
echo ""

echo "--- /etc/hostapd/hostapd.conf ---"
cat <<EOF
interface=ap0
driver=nl80211
ssid=$SSID
hw_mode=$HW_MODE
channel=$CHANNEL
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$PASS
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF
echo ""

echo "--- /etc/dnsmasq.d/salmoncv.conf ---"
cat <<EOF
interface=ap0
dhcp-range=$DHCP_START,$DHCP_END,255.255.255.0,24h
domain=local
address=/salmoncv.local/$AP_IP
EOF
echo ""

# ---- Dry run stops here ----
if $DRY_RUN; then
    echo "=== Dry run complete ==="
    echo "No files were changed. Run without --dry-run to apply."
    echo ""
    echo "Recommended next step:"
    echo "  sudo bash $0 --safe $SSID $PASS"
    echo ""
    echo "This will apply the changes AND schedule an automatic revert"
    echo "in $SAFE_MINUTES minutes, so if SSH breaks, networking recovers on its own."
    exit 0
fi

# ---- Safe mode: schedule revert before making changes ----
if $SAFE_MODE; then
    echo "Scheduling automatic revert in $SAFE_MINUTES minutes..."
    REVERT_SCRIPT="$SCRIPT_DIR/revert_hotspot.sh"

    if [ ! -f "$REVERT_SCRIPT" ]; then
        echo "Error: revert script not found at $REVERT_SCRIPT"
        exit 1
    fi

    # Schedule the revert via at (preferred) or one-shot systemd timer
    if command -v at &>/dev/null; then
        echo "bash $REVERT_SCRIPT" | at "now + $SAFE_MINUTES minutes" 2>&1
        echo "Revert scheduled via 'at'. Job will run in $SAFE_MINUTES minutes."
    else
        cat > /etc/systemd/system/salmoncv-revert.service <<SVCEOF
[Unit]
Description=Revert SalmonCV hotspot (safety net)

[Service]
Type=oneshot
ExecStart=/bin/bash $REVERT_SCRIPT
SVCEOF
        cat > /etc/systemd/system/salmoncv-revert.timer <<TMREOF
[Unit]
Description=Auto-revert hotspot in $SAFE_MINUTES minutes

[Timer]
OnActiveSec=${SAFE_MINUTES}min
AccuracySec=10s

[Install]
WantedBy=timers.target
TMREOF
        systemctl daemon-reload
        systemctl start salmoncv-revert.timer
        echo "Revert scheduled via systemd timer. Will run in $SAFE_MINUTES minutes."
    fi

    echo ""
    echo ">>> IMPORTANT: After confirming the hotspot works, cancel the revert:"
    echo ""
    if command -v at &>/dev/null; then
        echo "    sudo atrm \$(atq | head -1 | awk '{print \$1}')"
    else
        echo "    sudo systemctl stop salmoncv-revert.timer"
        echo "    sudo systemctl disable salmoncv-revert.timer"
    fi
    echo ""
fi

# ---- Install packages ----
echo "Installing hostapd and dnsmasq..."
apt-get update -qq
apt-get install -y hostapd dnsmasq

systemctl stop hostapd 2>/dev/null || true
systemctl stop dnsmasq 2>/dev/null || true

# ---- Tell NetworkManager to leave ap0 alone ----
echo "Configuring NetworkManager to ignore ap0..."
mkdir -p /etc/NetworkManager/conf.d
cat > /etc/NetworkManager/conf.d/unmanage-ap0.conf <<EOF
[keyfile]
unmanaged-devices=interface-name:ap0
EOF

systemctl restart NetworkManager

# ---- Create ap0 interface via systemd service ----
echo "Creating ap0 systemd service..."
cat > /etc/systemd/system/ap0.service <<EOF
[Unit]
Description=Create ap0 virtual interface for SalmonCV hotspot
Before=hostapd.service
After=NetworkManager.service
Wants=NetworkManager.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStartPre=/bin/sleep 3
ExecStart=/sbin/iw dev wlan0 interface add ap0 type __ap
ExecStart=/sbin/ip addr add $AP_IP/24 dev ap0
ExecStart=/sbin/ip link set ap0 up
ExecStop=/sbin/iw dev ap0 del

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ap0.service

# ---- Write configs ----
echo "Configuring hostapd..."
mkdir -p /etc/hostapd
cat > /etc/hostapd/hostapd.conf <<EOF
interface=ap0
driver=nl80211
ssid=$SSID
hw_mode=$HW_MODE
channel=$CHANNEL
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$PASS
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF

if [ -f /etc/default/hostapd ]; then
    sed -i 's|^#DAEMON_CONF=.*|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd
fi

echo "Configuring dnsmasq..."
mkdir -p /etc/dnsmasq.d
cat > /etc/dnsmasq.d/salmoncv.conf <<EOF
interface=ap0
dhcp-range=$DHCP_START,$DHCP_END,255.255.255.0,24h
domain=local
address=/salmoncv.local/$AP_IP
EOF

echo "Enabling services..."
systemctl unmask hostapd
systemctl enable hostapd
systemctl enable dnsmasq

# ---- Bring up ap0 now if it doesn't exist ----
if ! ip link show ap0 &>/dev/null; then
    echo "Creating ap0 interface..."
    iw dev wlan0 interface add ap0 type __ap
    ip addr add $AP_IP/24 dev ap0
    ip link set ap0 up
fi

echo "Starting services..."
systemctl start dnsmasq
systemctl start hostapd

echo ""
echo "=== Setup complete ==="
echo ""
echo "The hotspot is active now. Test by connecting to: $SSID"
echo "Dashboard: http://$AP_IP"
echo ""
echo "The hotspot will persist across reboots."
echo ""

if $SAFE_MODE; then
    echo ">>> REMINDER: You have $SAFE_MINUTES minutes to verify the hotspot works."
    echo ">>> After confirming SSH still works, cancel the revert:"
    echo ""
    if command -v at &>/dev/null; then
        echo "    sudo atrm \$(atq | head -1 | awk '{print \$1}')"
    else
        echo "    sudo systemctl stop salmoncv-revert.timer"
        echo "    sudo systemctl disable salmoncv-revert.timer"
    fi
    echo ""
    echo ">>> If you lose SSH, just wait $SAFE_MINUTES minutes and networking will be restored."
fi
