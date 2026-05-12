#!/usr/bin/env bash
set -euo pipefail

# Reverts all changes made by setup_hotspot.sh.
# Can be run manually or scheduled by --safe mode as a network safety net.

echo "=== Reverting SalmonCV Hotspot ==="

systemctl stop hostapd 2>/dev/null || true
systemctl stop dnsmasq 2>/dev/null || true
systemctl disable hostapd 2>/dev/null || true
systemctl disable dnsmasq 2>/dev/null || true

rm -f /etc/hostapd/hostapd.conf
rm -f /etc/dnsmasq.d/salmoncv.conf
rm -f /etc/systemd/network/10-ap0.netdev
rm -f /etc/network/interfaces.d/ap0

# Restore default hostapd config
if [ -f /etc/default/hostapd ]; then
    sed -i 's|^DAEMON_CONF=.*|#DAEMON_CONF=""|' /etc/default/hostapd
fi

# Remove the safety cron if it exists
crontab -l 2>/dev/null | grep -v "revert_hotspot.sh" | crontab - 2>/dev/null || true

# Bring down ap0 if it exists
ip link set ap0 down 2>/dev/null || true
ip addr flush dev ap0 2>/dev/null || true

echo ""
echo "=== Hotspot reverted ==="
echo "Networking is back to default. You may want to reboot to be sure:"
echo "  sudo reboot"
