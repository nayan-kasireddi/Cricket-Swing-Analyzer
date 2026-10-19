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
