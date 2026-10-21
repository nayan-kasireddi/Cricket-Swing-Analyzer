#include <Wire.h>

const uint8_t MPU = 0x68;
const uint32_t SAMPLE_INTERVAL_US = 10000;

uint32_t nextSample = 0;

bool writeRegister(uint8_t reg, uint8_t value) {
  Wire.beginTransmission(MPU);
  Wire.write(reg);
  Wire.write(value);
  return Wire.endTransmission() == 0;
}

bool readMotion(int16_t data[7]) {
  Wire.beginTransmission(MPU);
  Wire.write(0x3B);

  if (Wire.endTransmission(false) != 0) {
    return false;
  }

  if (Wire.requestFrom(MPU, (uint8_t)14, true) != 14) {
    return false;
  }

  for (int i = 0; i < 7; i++) {
    uint16_t high = Wire.read();
    uint16_t low = Wire.read();
    data[i] = (int16_t)((high << 8) | low);
  }

  return true;
}

void setup() {
  Serial.begin(115200);

  Wire.setSDA(4);
  Wire.setSCL(5);
  Wire.begin();
  Wire.setClock(400000);

  delay(1000);

  bool ok = true;

  ok &= writeRegister(0x6B, 0x01);
  ok &= writeRegister(0x1C, 0x00);
  ok &= writeRegister(0x1B, 0x00);
  ok &= writeRegister(0x1A, 0x03);

  if (!ok) {
    Serial.println("# MPU6050 initialization failed");
    while (true) {
      delay(1000);
    }
  }

  Serial.println("time,ax,ay,az,gx,gy,gz");

  nextSample = micros();
}

void loop() {
  uint32_t now = micros();

  if ((int32_t)(now - nextSample) < 0) {
    return;
  }

  nextSample += SAMPLE_INTERVAL_US;

  if ((int32_t)(micros() - nextSample) >= 0) {
    nextSample = micros() + SAMPLE_INTERVAL_US;
  }

  int16_t raw[7];

  if (!readMotion(raw)) {
    Serial.println("# Sensor read failed");
    return;
  }

  float ax = raw[0] / 16384.0;
  float ay = raw[1] / 16384.0;
  float az = raw[2] / 16384.0;

  float gx = raw[4] / 131.0;
  float gy = raw[5] / 131.0;
  float gz = raw[6] / 131.0;

  Serial.print(now / 1000000.0, 4);
  Serial.print(",");
  Serial.print(ax, 4);
  Serial.print(",");
  Serial.print(ay, 4);
  Serial.print(",");
  Serial.print(az, 4);
  Serial.print(",");
  Serial.print(gx, 4);
  Serial.print(",");
  Serial.print(gy, 4);
  Serial.print(",");
  Serial.println(gz, 4);
}
