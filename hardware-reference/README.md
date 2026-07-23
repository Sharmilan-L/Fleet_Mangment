# EvolveX ESP32 Embedded Integration Guide

This guide describes physical hardware integration guidelines, wiring schematics, WiFi connection settings, and telemetry payload constraints.

## 1. Hardware Pin Configurations

Recommended wiring mapping for the ESP32 development board, GPS receiver module, and MPU6050 6-Axis IMU Sensor:

```text
+-----------------------+-------------+----------------------+
| ESP32 GPIO Pin        | Sensor Pin  | Description          |
+-----------------------+-------------+----------------------+
| GPIO 21 (SDA)         | MPU6050 SDA | I2C Data Line        |
| GPIO 22 (SCL)         | MPU6050 SCL | I2C Clock Line       |
| GPIO 16 (RX2)         | NEO-6M TX   | GPS Serial Transmit  |
| GPIO 17 (TX2)         | NEO-6M RX   | GPS Serial Receive   |
| 3V3                   | VCC         | 3.3V Power Supply    |
| GND                   | GND         | Ground Reference     |
+-----------------------+-------------+----------------------+
```

## 2. Wifi Network & Connection Reconnection

To prevent connection drops during highway driving, use a robust WiFi connection loop inside the ESP32 setup code:

```cpp
#include <WiFi.h>

const char* ssid = "EvolveX-Fleet-WiFi";
const char* password = "evolvex-secure-wifi";

void connectToWiFi() {
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected!");
}
```

## 3. Telemetry API Expectations

Embedded firmware must send a HTTP POST request with authentication headers:

```http
POST /api/v1/device/telemetry HTTP/1.1
Host: local-server-ip:8000
Content-Type: application/json
X-Device-Code: SIM-DEVICE-001
X-Device-Key: demo-simulator-secret-key-2026
X-Telemetry-Schema-Version: 1.0
```
