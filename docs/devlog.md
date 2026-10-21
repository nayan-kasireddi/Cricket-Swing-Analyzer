# Development Log

## September 30, 2026
- Created the `Cricket-Swing-Analyzer` repository and established the development log.
- Project timeline: October 3, 2026 through December 10, 2026, with an optional Week 11 for the enclosure.
- Project scope includes ESP32 embedded hardware, I²C sensors, KiCad/PCB design, Python swing and impact analysis, and a dashboard.

## October 3–9, 2026
- Tested an ESP32 microcontroller and troubleshot upload and connection issues.
- Experimented with basic hardware setup and Arduino IDE test programs.
- Switched to the Raspberry Pi Pico 2 W after continued ESP32 problems.

## October 17, 2026
- Set up the Pico 2 W and tested its onboard LED with a blinking program.
- Uploaded code successfully and verified serial communication.
- Connected the GY-521 MPU6050 sensor using a breadboard and jumper wires.
- Tested I²C communication, but the sensor was not detected at address 0x68.
- Next steps: Fix the sensor connection, confirm I²C communication, and begin collecting motion data.

## October 18, 2026 – MPU6050 Sensor Setup and Troubleshooting**
- Connected the MPU6050 sensor to the Raspberry Pi Pico 2 W.
- Tested I²C communication using the Arduino IDE Serial Monitor.
- Observed intermittent sensor detection at address `0x68` and register selection errors.
- Investigated possible wiring and breadboard connection issues.
- Identified that the sensor's header pins are not soldered.
- Next step: Solder the header pins to establish reliable connections before continuing sensor testing.

## October 20, 2026 – MPU6050 Data Collection and GitHub Update
- Soldered the MPU6050 sensor's header pins to establish secure and reliable connections with the breadboard and Raspberry Pi Pico 2 W.
- Successfully established reliable I²C communication between the Pico 2 W and MPU6050 sensor at address `0x68`.
- Verified accelerometer and gyroscope readings through the Arduino IDE Serial Monitor.
- Configured the MPU6050 to collect 3-axis acceleration and 3-axis angular velocity data at approximately 100 Hz.
- Implemented CSV-formatted serial output containing `time,ax,ay,az,gx,gy,gz`.
- Created `firmware/pico2w_mpu6050/pico2w_mpu6050.ino` to store the sensor firmware.
- Committed and pushed the firmware to the GitHub repository, integrating the latest remote changes.
- Next steps: Test sensor readings during controlled movements, begin designing the circuit schematic in KiCad, and develop Python scripts for processing motion data.
