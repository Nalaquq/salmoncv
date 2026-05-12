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

# ---- Header ----
echo "=== SalmonCV Hotspot Setup ==="
echo "SSID:     $SSID"
echo "Password: $PASS"
echo "AP IP:    $AP_IP"
echo "DHCP:     $DHCP_START – $DHCP_END"
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
echo "--- /etc/systemd/network/10-ap0.netdev ---"
cat <<EOF
[NetDev]
Name=ap0
Kind=vlan

[VLAN]
Id=1
EOF
echo ""

echo "--- /etc/network/interfaces.d/ap0 ---"
cat <<EOF
auto ap0
iface ap0 inet static
    address $AP_IP
    netmask 255.255.255.0
EOF
echo ""

echo "--- /etc/hostapd/hostapd.conf ---"
cat <<EOF
interface=ap0
driver=nl80211
ssid=$SSID
hw_mode=g
channel=7
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
        # Fallback: use a one-shot systemd timer
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

# ---- Write configs ----
echo "Creating virtual AP interface (ap0)..."
cat > /etc/systemd/network/10-ap0.netdev <<EOF
[NetDev]
Name=ap0
Kind=vlan

[VLAN]
Id=1
EOF

cat > /etc/network/interfaces.d/ap0 <<EOF
auto ap0
iface ap0 inet static
    address $AP_IP
    netmask 255.255.255.0
EOF

echo "Configuring hostapd..."
cat > /etc/hostapd/hostapd.conf <<EOF
interface=ap0
driver=nl80211
ssid=$SSID
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$PASS
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF

sed -i 's|^#DAEMON_CONF=.*|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd

echo "Configuring dnsmasq..."
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

echo ""
echo "=== Setup complete ==="
echo ""
echo "Reboot the Pi to activate the hotspot:"
echo "  sudo reboot"
echo ""
echo "After reboot:"
echo "  1. Connect your phone/tablet to Wi-Fi network: $SSID"
echo "  2. Open a browser to: http://$AP_IP"
echo ""

if $SAFE_MODE; then
    echo ">>> REMINDER: You have $SAFE_MINUTES minutes to verify the hotspot works."
    echo ">>> After rebooting and confirming SSH still works, cancel the revert:"
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
