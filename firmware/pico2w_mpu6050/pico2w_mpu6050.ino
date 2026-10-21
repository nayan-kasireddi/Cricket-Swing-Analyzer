// Cricket Swing Analyzer: Raspberry Pi Pico 2 W + GY-521 MPU6050
// Four wires only: 3V3, GND, GP4/SDA, GP5/SCL. NO INT WIRE REQUIRED.
// 500 Hz target via micros()-timed polling, CSV output over USB Serial.
#include <Wire.h>

constexpr uint8_t MPU = 0x68;
constexpr uint32_t SAMPLE_INTERVAL_US = 2000;  // 500 Hz
uint32_t nextSampleUs = 0;

bool writeRegister(uint8_t reg, uint8_t value) {
  Wire.beginTransmission(MPU);
  Wire.write(reg);
  Wire.write(value);
  return Wire.endTransmission() == 0;
}

bool readRegister(uint8_t reg, uint8_t &value) {
  Wire.beginTransmission(MPU);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(MPU, (uint8_t)1, true) != 1) return false;
  value = (uint8_t)Wire.read();
  return true;
}

bool readMotion(int16_t raw[7]) {
  Wire.beginTransmission(MPU);
  Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(MPU, (uint8_t)14, true) != 14) return false;

  for (int i = 0; i < 7; ++i) {
    uint16_t high = (uint8_t)Wire.read();
    uint16_t low = (uint8_t)Wire.read();
    raw[i] = (int16_t)((high << 8) | low);
  }
  return true;
}

void fail(const char *message) {
  while (true) {
    if (Serial) {
      Serial.print("# ERROR: ");
      Serial.println(message);
    }
    delay(1000);
  }
}

void setup() {
  Serial.begin(115200);
  Wire.setSDA(4);
  Wire.setSCL(5);
  Wire.begin();
  Wire.setClock(400000);

  if (!writeRegister(0x6B, 0x80)) fail("MPU6050 reset failed");
  delay(100);
  if (!writeRegister(0x6B, 0x01)) fail("MPU6050 wake failed");
  delay(20);

  uint8_t value = 0;
  if (!readRegister(0x75, value) || value != 0x68)
    fail("MPU6050 not found at 0x68 (check four wires)");

  if (!writeRegister(0x1A, 0x01) ||   // low-pass: 184 Hz accel, 188 Hz gyro
      !writeRegister(0x19, 0x01) ||   // sensor output rate: 500 Hz
      !writeRegister(0x1B, 0x18) ||   // gyro range: +/-2000 deg/s
      !writeRegister(0x1C, 0x18) ||   // acceleration range: +/-16g
      !writeRegister(0x38, 0x00))     // disable hardware interrupt output
    fail("MPU6050 configuration failed");

  if (!readRegister(0x1A, value) || value != 0x01 ||
      !readRegister(0x19, value) || value != 0x01 ||
      !readRegister(0x1B, value) || (value & 0x18) != 0x18 ||
      !readRegister(0x1C, value) || (value & 0x18) != 0x18)
    fail("MPU6050 configuration readback failed");

  nextSampleUs = micros();
}

void loop() {
  static bool headerSent = false;
  static uint32_t skippedSlots = 0;
  static uint32_t readFailures = 0;

  if (!Serial) {
    headerSent = false;
    nextSampleUs = micros();
    return;
  }

  if (!headerSent) {
    Serial.println("# MPU6050 500 Hz target | polling | +/-16g | +/-2000dps");
    Serial.println("time_us,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps,skipped_slots");
    headerSent = true;
    nextSampleUs = micros();
  }

  uint32_t now = micros();
  if ((int32_t)(now - nextSampleUs) < 0) return;

  // Skip slots if USB output or I2C took longer than the 2 ms interval.
  uint32_t skipped = (now - nextSampleUs) / SAMPLE_INTERVAL_US;
  skippedSlots += skipped;
  nextSampleUs += (skipped + 1) * SAMPLE_INTERVAL_US;

  int16_t raw[7];
  if (!readMotion(raw)) {
    if (++readFailures % 100 == 1) Serial.println("# Sensor I2C read failed");
    return;
  }

  Serial.print(now);
  Serial.print(','); Serial.print(raw[0] / 2048.0f, 4);
  Serial.print(','); Serial.print(raw[1] / 2048.0f, 4);
  Serial.print(','); Serial.print(raw[2] / 2048.0f, 4);
  Serial.print(','); Serial.print(raw[4] / 16.4f, 2);
  Serial.print(','); Serial.print(raw[5] / 16.4f, 2);
  Serial.print(','); Serial.print(raw[6] / 16.4f, 2);
  Serial.print(','); Serial.println(skippedSlots);
}
