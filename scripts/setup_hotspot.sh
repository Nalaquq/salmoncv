#!/usr/bin/env bash
set -euo pipefail

SSID="${1:-SalmonCV}"
PASS="${2:-salmon2026}"
AP_IP="192.168.4.1"
DHCP_START="192.168.4.10"
DHCP_END="192.168.4.50"

echo "=== SalmonCV Hotspot Setup ==="
echo "SSID:     $SSID"
echo "Password: $PASS"
echo "AP IP:    $AP_IP"
echo ""

if [ "$EUID" -ne 0 ]; then
  echo "Error: run this script as root (sudo)."
  exit 1
fi

echo "Installing hostapd and dnsmasq..."
apt-get update -qq
apt-get install -y hostapd dnsmasq

systemctl stop hostapd 2>/dev/null || true
systemctl stop dnsmasq 2>/dev/null || true

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
echo "Reboot the Pi to activate the hotspot."
echo "After reboot:"
echo "  1. Connect your phone/tablet to Wi-Fi network: $SSID"
echo "  2. Open a browser to: http://$AP_IP"
echo ""
echo "To start the web dashboard:"
echo "  sudo salmoncv-web"
