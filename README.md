# Cricket Bat Swing & Impact Analyzer

An embedded hardware and Python-based system for analyzing cricket bat swing and impact motion.

## Project Timeline

- Start: October 2, 2026
- End: December 10, 2026
- Optional Week 11: 3D-printed enclosure

## Project Overview

This project uses a Raspberry Pi Pico 2W and MPU6050 inertial measurement unit (IMU) to collect motion data from a cricket bat during swings.

The system will collect accelerometer and gyroscope data, process the data using Python, detect swings, and display useful swing-intensity metrics.

## Hardware

- Raspberry Pi Pico 2W Microcontroller
- MPU6050 accelerometer + gyroscope
- Breadboard
- Jumper wires
- USB cable
- PCB (stretch goal)
- Battery/power system
- Optional 3D-printed enclosure

## Software

- Arduino IDE
- C++
- Python
- NumPy
- Pandas
- Matplotlib
- SciPy
- KiCad

## Project Structure

```text
firmware/    Raspberry Pi Pico 2W firmware
python/      Python analysis
data/        Sensor CSV data
hardware/    Schematics, PCB, and enclosure files
images/      Project photos and graphs
docs/        Development documentation
