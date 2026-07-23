# EvolveX Hardware Integration Checklist

Use this checklist to verify physical IoT devices connecting to the EvolveX Telemetry Ingestion API:

- [ ] **Power Supply**: Verify ESP32 development board and GPS/IMU modules receive stable 3.3V power.
- [ ] **Sensors wiring**: Verify I2C interface pins (SDA/SCL) are correctly mapped for MPU6050, and UART pins (RX/TX) are correctly mapped for GPS module.
- [ ] **Wi-Fi Connectivity**: Ensure SSID and password are set correctly and include a robust reconnection loop.
- [ ] **Headers Configuration**: Include `X-Device-Code`, `X-Device-Key`, and `X-Telemetry-Schema-Version` headers in all REST API telemetry post requests.
- [ ] **Payload Structure**: Verify the JSON payload matches the exact schema contract (boot_id, sequence_number, speed_kmh, forward/lateral acceleration, yaw rate).
- [ ] **API Keys Security**: Verify plain secrets are not stored in log files or version control systems.
