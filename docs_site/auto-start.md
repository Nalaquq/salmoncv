# Auto-Start on Boot

SalmonCV can start the web dashboard automatically when the Pi boots, so the system is ready as soon as it has power.

## Install the Service

Run the install script once:

```bash
sudo bash scripts/install_service.sh
```

This creates a systemd service that:

- Starts `salmoncv-web` on port 80 at boot
- Restarts automatically if it crashes
- Runs as root (required for port 80 and GPIO access)

## Verify

After installing (or after a reboot):

```bash
sudo systemctl status salmoncv-web
```

You should see `active (running)`.

## Manage the Service

| Command | Description |
|---------|-------------|
| `sudo systemctl status salmoncv-web` | Check if running |
| `sudo systemctl restart salmoncv-web` | Restart after code changes |
| `sudo systemctl stop salmoncv-web` | Stop the dashboard |
| `sudo systemctl start salmoncv-web` | Start it again |
| `sudo systemctl disable salmoncv-web` | Disable auto-start on boot |
| `sudo systemctl enable salmoncv-web` | Re-enable auto-start |

## View Logs

```bash
sudo journalctl -u salmoncv-web -f
```

This follows the log output in real time. Press `Ctrl+C` to stop.

To see recent logs:

```bash
sudo journalctl -u salmoncv-web --no-pager -n 50
```

## After Code Updates

When you pull new code and reinstall:

```bash
cd ~/salmoncv
source venv/bin/activate
git pull
pip install -e .
sudo systemctl restart salmoncv-web
```

## Custom Venv Path

If your virtual environment is in a non-default location:

```bash
sudo bash scripts/install_service.sh /path/to/your/venv
```

## What the Script Does

The install script (`scripts/install_service.sh`):

1. Verifies `salmoncv-web` exists in the venv
2. Creates `/etc/systemd/system/salmoncv-web.service`
3. Reloads systemd and enables the service
4. Starts the service immediately
