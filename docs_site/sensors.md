# Sensors

SalmonCV logs environmental data from a BME280 sensor connected via I2C. The sensor is mounted inside the camera case to monitor conditions that could affect image quality or hardware health.

## What It Measures

| Reading | Unit | Purpose |
|---------|------|---------|
| Temperature | °C / °F | Detect overheating inside the case |
| Humidity | % | Detect moisture ingress or seal failure |
| Pressure | hPa | Weather tracking, altitude reference |

## Quick Reading (CLI)

Start continuous logging:

```bash
salmoncv-sensors
```

This prints readings to the terminal and logs to CSV every 2 seconds.

### Custom Interval

```bash
salmoncv-sensors --interval 10
```

### Custom Log File

```bash
salmoncv-sensors --logfile ~/salmoncv/data/my_sensor_log.csv
```

## Sensor Log

Readings are saved to `~/salmoncv/data/sensor_log.csv`:

| Column | Description |
|--------|-------------|
| timestamp | Reading time |
| temperature_c | Temperature in Celsius |
| temperature_f | Temperature in Fahrenheit |
| humidity | Relative humidity (%) |
| pressure_hpa | Barometric pressure (hPa) |

## Web Dashboard

The [Sensors page](web-dashboard.md#sensors) shows:

- Live readings that auto-refresh every 5 seconds
- Recent history table from sensor_log.csv
- CSV download button

The [Monitor page](web-dashboard.md#monitor) shows:

- Temperature, humidity, and pressure charts over time
- Case health comparison (CPU temp vs. case temp/humidity)
- Threshold lines for overheating and moisture warnings

## Hardware Setup

The BME280 connects to the Pi's I2C bus:

| BME280 Pin | Pi Pin |
|------------|--------|
| VIN | 3.3V (pin 1) |
| GND | Ground (pin 6) |
| SCL | GPIO 3 / SCL (pin 5) |
| SDA | GPIO 2 / SDA (pin 3) |

The sensor uses I2C bus 1 at address `0x76`.

### Verify Connection

```bash
sudo i2cdetect -y 1
```

You should see `76` in the output grid. If the grid is empty, check wiring.

## Troubleshooting

**"Sensor not available" in the dashboard**

- Check wiring --- the most common cause is a loose connection
- Run `sudo i2cdetect -y 1` to verify the sensor is detected
- Make sure I2C is enabled: `sudo raspi-config` > Interface Options > I2C

**[Errno 121] Remote I/O error**

The sensor is not responding on the I2C bus. This is almost always a wiring issue:

1. Power off the Pi
2. Reseat all four wires (VIN, GND, SCL, SDA)
3. Power back on
4. Run `sudo i2cdetect -y 1` to verify `76` appears

## CLI Reference

```
salmoncv-sensors [OPTIONS]

  --logfile PATH       CSV log file path (default: ~/salmoncv/data/sensor_log.csv)
  --interval SECONDS   Time between readings (default: 2.0)
```
