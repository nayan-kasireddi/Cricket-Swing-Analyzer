# Cricket Bat Swing & Impact Analyzer

**Embedded Systems | Raspberry Pi Pico 2 W | MPU6050 | Arduino | Python | KiCad**

A motion-tracking system designed to capture, analyze, and visualize cricket bat swing dynamics using embedded hardware and software.

The Cricket Bat Swing & Impact Analyzer combines a Raspberry Pi Pico 2 W microcontroller with an MPU6050 inertial measurement unit (IMU) to collect real-time acceleration and angular velocity data. The project aims to transform raw sensor measurements into meaningful insights about swing speed, motion patterns, and potential bat impact events.

The system is being developed from initial breadboard prototyping through custom PCB design, signal processing, and data visualization.

## Features

### Current Capabilities

- **Real-Time Motion Tracking:** Collects 3-axis acceleration and 3-axis angular velocity data using the MPU6050.
- **100 Hz Sampling:** Firmware schedules sensor measurements at approximately 100 samples per second.
- **I²C Communication:** Interfaces the Raspberry Pi Pico 2 W with the MPU6050 at address `0x68`.
- **Serial Data Streaming:** Outputs timestamped sensor readings in CSV format at 115200 baud.
- **Embedded Firmware:** Arduino-compatible C++ firmware for sensor initialization, data acquisition, and streaming.
- **Hardware Prototyping:** Breadboard-based circuit with soldered sensor headers for reliable connections.

### Planned Capabilities

- **Swing Detection:** Identify individual cricket bat swings using acceleration and gyroscope measurements.
- **Impact Detection:** Investigate sudden motion changes and acceleration peaks associated with bat-ball contact.
- **Motion Analysis:** Calculate acceleration magnitude, angular velocity, and swing characteristics.
- **Data Visualization:** Generate plots and dashboards to examine recorded swings.
- **Custom PCB:** Design and assemble a compact circuit using KiCad.
- **Portable Integration:** Develop a hardware configuration suitable for mounting on a cricket bat.

## Hardware

### Components

| Component | Purpose |
|---|---|
| Raspberry Pi Pico 2 W | Main microcontroller |
| MPU6050 (GY-521) | 6-axis accelerometer and gyroscope |
| Breadboard | Initial circuit prototyping |
| Jumper wires | Electrical connections |
| USB cable | Power, programming, and serial communication |
| Custom PCB (planned) | Compact hardware integration |

### Wiring Configuration

| MPU6050 | Raspberry Pi Pico 2 W |
|---|---|
| VCC | 3V3 (Pin 36) |
| GND | GND (Pin 38) |
| SDA | GP4 (Pin 6) |
| SCL | GP5 (Pin 7) |

The MPU6050 communicates with the Pico 2 W over I²C using address `0x68`.

## Firmware

**Language:** C++ (Arduino)

**Microcontroller:** Raspberry Pi Pico 2 W

**Sensor:** MPU6050

**Sampling frequency:** Approximately 100 Hz

**Serial baud rate:** 115200

### Firmware Capabilities

- MPU6050 initialization and register configuration
- I²C communication at 400 kHz
- Accelerometer and gyroscope data acquisition
- Raw sensor value conversion into physical units
- Timestamped CSV serial output
- Basic sensor communication error handling

### Firmware Location

`firmware/pico2w_mpu6050/pico2w_mpu6050.ino`

### Example Sensor Output

```csv
time,ax,ay,az,gx,gy,gz
94.7541,0.1135,-0.0537,1.0270,-0.5496,1.6947,0.7786
```

| Field | Description | Unit |
|---|---|---|
| time | Elapsed microcontroller time | Seconds |
| ax, ay, az | Acceleration along X, Y, Z | g |
| gx, gy, gz | Angular velocity around X, Y, Z | Degrees/second |

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/nayan-kasireddi/Cricket-Swing-Analyzer.git
cd Cricket-Swing-Analyzer
```

### 2. Set Up Arduino IDE

Install the Arduino IDE and configure support for the Raspberry Pi Pico 2 W using the Arduino-Pico RP2040/RP2350 board package.

Select the appropriate Pico 2 W board and serial port.

### 3. Connect the Hardware

Wire the MPU6050 to the Pico 2 W using the pin configuration above.

Ensure the sensor's header pins are securely soldered and the connections are stable.

### 4. Upload the Firmware

Open:

`firmware/pico2w_mpu6050/pico2w_mpu6050.ino`

Compile and upload the sketch to the Raspberry Pi Pico 2 W.

### 5. View Live Sensor Data

Open the Arduino IDE Serial Monitor and configure the baud rate to `115200`.

The microcontroller should continuously stream timestamped acceleration and angular velocity readings.

## Python Analysis

**Status: Planned / In Development**

The Python portion of the project will process recorded IMU measurements and extract meaningful motion characteristics.

### Planned Libraries

- **NumPy:** Numerical calculations and vector operations
- **Pandas:** CSV loading and data organization
- **Matplotlib:** Sensor data visualization
- **SciPy:** Signal processing and peak detection

### Planned Processing Pipeline

1. Record acceleration and gyroscope data from the MPU6050.
2. Load timestamped measurements into Python.
3. Calculate acceleration magnitude.
4. Filter unwanted noise and sensor fluctuations.
5. Detect potential swing and impact events.
6. Visualize and compare motion characteristics.

### Acceleration Magnitude

The total acceleration magnitude can be calculated using:

\[
a_{\text{mag}}=\sqrt{a_x^2+a_y^2+a_z^2}
\]

This combines acceleration along all three axes into a single measurement that can be analyzed for motion peaks.

### Example Python Calculation

```python
import numpy as np
import pandas as pd

df = pd.read_csv("data/sensor_readings.csv")

df["accel_magnitude"] = np.sqrt(
    df["ax"]**2 +
    df["ay"]**2 +
    df["az"]**2
)

print(df[["time", "accel_magnitude"]].head())
```

This is an illustrative example of the planned analysis workflow, not a completed swing-detection algorithm.

## PCB Design

**Status: Planned**

A custom printed circuit board will be developed using KiCad to improve the system's size, reliability, and portability.

### Design Goals

- Integrate the microcontroller and IMU connections.
- Reduce reliance on breadboards and jumper wires.
- Provide stable power and I²C communication.
- Create a compact layout suitable for a cricket bat attachment.
- Develop and validate schematic and PCB layouts before fabrication.

## Project Structure

```text
Cricket-Swing-Analyzer/
├── firmware/
│   └── pico2w_mpu6050/
│       └── pico2w_mpu6050.ino
├── hardware/
├── python/
├── data/
├── docs/
│   └── devlog.md
├── images/
├── README.md
├── requirements.txt
└── .gitignore
```

## Development Progress

| Milestone | Status |
|---|---|
| Repository setup and documentation | Complete |
| Pico 2 W firmware upload and LED testing | Complete |
| MPU6050 wiring and soldering | Complete |
| I²C sensor detection | Complete |
| Accelerometer and gyroscope data streaming | Complete |
| 100 Hz firmware implementation | Complete |
| Controlled swing data collection | Upcoming |
| Python signal processing | Planned |
| Swing and impact detection | Planned |
| KiCad schematic and PCB layout | Planned |
| PCB fabrication and assembly | Planned |
| Final demonstration | Planned |

### Development Timeline

**October 2026 – December 2026**

Development began with microcontroller testing and hardware troubleshooting, followed by successful integration of the Raspberry Pi Pico 2 W and MPU6050.

The next phases focus on motion data analysis, custom PCB design, and complete system integration.

See [`docs/devlog.md`](docs/devlog.md) for detailed development updates.

## Troubleshooting

| Issue | Suggested Solution |
|---|---|
| MPU6050 not detected | Verify wiring, solder joints, and I²C address `0x68` |
| No serial output | Check USB connection, selected port, and 115200 baud rate |
| Firmware upload fails | Confirm board selection and bootloader connection |
| Unstable sensor readings | Check electrical connections and secure the sensor |
| Unexpected acceleration readings | Verify sensor orientation, calibration, and measurement units |

## Future Improvements

- Improve swing and impact event classification.
- Investigate gyroscope-based swing speed estimation.
- Implement noise filtering and sensor calibration.
- Compare multiple swings using graphical visualizations.
- Design a protective enclosure for the electronics.
- Evaluate sensor placement and mounting methods.

## Contributing

Contributions, suggestions, and feedback are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Push the branch to GitHub.
5. Open a pull request.

## Authors

**Nayan Kasireddi**

Electrical and Computer Engineering — The University of Texas at Austin

GitHub: [@nayan-kasireddi](https://github.com/nayan-kasireddi)

Developed as a hands-on exploration of embedded systems, hardware prototyping, circuit design, and motion analysis.

## Acknowledgments

Developed using the Raspberry Pi Pico platform, MPU6050 inertial sensing technology, Arduino, Python, and KiCad.

Hardware prototyping and fabrication resources are available through Texas Inventionworks at The University of Texas at Austin.

## Project Resources

- [GitHub Repository](https://github.com/nayan-kasireddi/Cricket-Swing-Analyzer)
- [Firmware](firmware/pico2w_mpu6050/pico2w_mpu6050.ino)
- [Development Log](docs/devlog.md)
- [Hardware Files](hardware/)
- [Python Analysis](python/)
- [Project Images](images/)
