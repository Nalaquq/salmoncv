import time
import smbus2
import bme280

PORT = 1
ADDRESS = 0x76  # change to 0x77 if needed

bus = smbus2.SMBus(PORT)
calibration_params = bme280.load_calibration_params(bus, ADDRESS)

print("Starting BME280 sensor read...\n")

while True:
    data = bme280.sample(bus, ADDRESS, calibration_params)

    temp_f = (data.temperature * 9/5) + 32

    print(f"Temp: {data.temperature:.2f} °C / {temp_f:.2f} °F")
    print(f"Humidity: {data.humidity:.2f} %")
    print(f"Pressure: {data.pressure:.2f} hPa")
    print("-" * 40)

    time.sleep(2)
