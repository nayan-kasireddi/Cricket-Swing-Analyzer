# Cricket Bat Swing & Impact Analyzer

**Embedded Systems | Raspberry Pi Pico 2 W | MPU6050 | Arduino | Python | KiCad**

A motion-tracking system designed to capture, analyze, and visualize cricket bat swing dynamics using embedded hardware and software.

The Cricket Bat Swing & Impact Analyzer combines a Raspberry Pi Pico 2 W microcontroller with an MPU6050 inertial measurement unit (IMU) to collect real-time acceleration and angular velocity data. The project aims to transform raw sensor measurements into meaningful insights about swing speed, motion patterns, and potential bat impact events.

The system is being developed from initial breadboard prototyping through custom PCB design, signal processing, and data visualization.

## Features

### Current Capabilities

- **Real-Time Motion Tracking:** Collects 3-axis acceleration and 3-axis angular velocity data using the MPU6050.
- **500 Hz Target Sampling:** Firmware polls every 2000 microseconds; actual timing and skipped slots should be checked in recordings.
- **I²C Communication:** Interfaces the Raspberry Pi Pico 2 W with the MPU6050 at address `0x68`.
- **Serial Data Streaming:** Outputs timestamped sensor readings in CSV format at 115200 baud.
- **Embedded Firmware:** Arduino-compatible C++ firmware for sensor initialization, data acquisition, and streaming.
- **Hardware Prototyping:** Breadboard-based circuit with soldered sensor headers for reliable connections.

### Python Capabilities

- **Swing Detection:** Shared streaming and recorded-data detection using acceleration and rotation, with hysteresis, a quiet period, and cooldown.
- **Recording Review:** Streamlit dashboard with recording selection, charts, per-swing summaries, and detail views.
- **Live Capture:** USB serial dashboard and Matplotlib viewer, CSV recording, and a simulated source.
- **Data Validation:** Firmware CSV normalization, timestamp/sample-rate checks, and sensor-range checks.

### Planned Capabilities

- **Impact Detection:** Investigate sudden motion changes and acceleration peaks associated with bat-ball contact.
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

**Sampling frequency:** 500 Hz target (2000 microsecond polling interval)

**Serial baud rate:** 115200

### Firmware Capabilities

- MPU6050 initialization and register configuration
- I²C communication at 400 kHz
- Accelerometer and gyroscope data acquisition
- Raw sensor value conversion into physical units
- Microsecond timestamps, skipped-slot reporting, and CSV output
- Accelerometer range ±16 g; gyroscope range ±2000 degrees/second
- 400 kHz I²C with sensor configuration checks and comment-prefixed diagnostics
- Basic sensor communication error handling

### Firmware Location

`firmware/pico2w_mpu6050/pico2w_mpu6050.ino`

### Example Sensor Output

```csv
time_us,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps,skipped_slots
94754100,0.1135,-0.0537,1.0270,-0.5496,1.6947,0.7786,0
```

| Field | Description | Unit |
|---|---|---|
| time_us | Microcontroller clock | Microseconds |
| ax_g, ay_g, az_g | Acceleration along X, Y, Z | g |
| gx_dps, gy_dps, gz_dps | Angular velocity around X, Y, Z | Degrees/second |

`skipped_slots` reports missed scheduled polling slots. Lines beginning with `#` contain startup or error diagnostics. A 500 Hz target is not a guarantee that every sample arrives on time.

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

The Python workflow is implemented for recorded data and live USB capture. Run commands from the repository root. Python 3.12 is validated in the cloud environment; the repository does not pin package versions.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pytest python/tests -q
python -m streamlit run python/dashboard.py
```

The dashboard has a responsive cricket practice interface with animated local artwork, a **Demo mode** for simulated live sessions, and interactive recording charts (hover for readings, scroll to zoom, drag to explore). Reduced-motion preferences are respected. Session CSVs and swing summaries can be downloaded.

The Live page scans serial ports every second, including when no sensor is connected. Plugging in or reconnecting the Pico updates the picker automatically; start a session when ready. Disconnects or five seconds without samples stop and preserve the session so you can reconnect and start a new one without refreshing the browser. Serial devices must be attached to the machine running Streamlit, not a separate browser device.

The dashboard opens on **Live**: select the Pico serial port, start capture, then **Stop and save** to finish the CSV. Close other serial monitors first. On **Review**, choose a recording (the default is `data/synthetic/multi_swing.csv`), adjust the trigger, and inspect detected swings, peak acceleration, peak rotation, and duration. Recorded timelines are relative to the first saved sample. Live recordings go to ignored `data/live/` files.

Without hardware, use Review with the bundled synthetic recordings or the simulated desktop viewer:

```bash
python -m python.live --sim
python -m python.live --list-ports
python -m python.live --port /dev/ttyACM0
python -m python.analyze data/synthetic/normal_swing.csv
```

Use the port reported on your machine (for example `/dev/cu.usbmodem...` on macOS or `COM3` on Windows). The live viewer requires a graphical desktop; close its plot window to save and stop. The analysis command prints statistics, saves a PNG under `images/`, and opens plots. For headless analysis, set `MPLBACKEND=Agg`.

`load_csv()` accepts firmware headers, ignores `#` diagnostics and `skipped_slots`, converts microseconds to seconds, and returns canonical `time,ax,ay,az,gx,gy,gz` columns. Synthetic files already use seconds. It rejects missing/non-numeric/non-finite values, unordered timestamps, large gaps, rates outside 500 Hz ±20%, and values outside ±16 g / ±2000 deg/s. Historical recordings with a different sample rate may be rejected; preserve the original data rather than relabeling it.

`acceleration_magnitude()` combines the three acceleration axes (including gravity); rotation magnitude combines the three gyroscope axes. `SwingTracker` is shared by live and batch detection: default trigger 2.5 g, release at 80% of trigger, rotation hold at 150 deg/s, 0.2 seconds quiet before finishing, 1 second cooldown, minimum duration 0.05 seconds, and a 3 second safety cap. The live dashboard starts at 1.5 g for gentle hand movements. These are heuristic parameters to tune against real bat recordings, not validated impact detection or bat speed estimates. Values in g measure acceleration, not force in newtons, even where the dashboard uses the plain-language label “force.”

NumPy, Pandas, and Matplotlib support analysis; PySerial supports USB capture; Streamlit provides the dashboard; pytest runs regression checks. SciPy is available for future signal processing. `python/core.py` remains an unused algorithm placeholder for ongoing work; the functioning magnitude calculation lives in `python/analyze.py`, and detection lives in `python/swings.py`.

The generator `python -m python.generate_test_data` intentionally regenerates the four files under `data/synthetic/`; it does not replace `data/stationary.csv`. Existing tests exercise ingestion, parsing, swing detection, recording, and UI helpers. Physical hardware and firmware upload require a local Pico/MPU6050 setup.

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
| 500 Hz target firmware implementation | Complete |
| Controlled swing data collection | Upcoming |
| Python CSV validation, magnitudes, and plotting | Complete |
| Live USB capture and recording dashboard | Complete |
| Heuristic swing detection and summaries | Complete |
| Impact classification and real-bat calibration | Planned |
| KiCad schematic and PCB layout | Planned |
| PCB fabrication and assembly | Planned |
| Final demonstration | Planned |

### Development Timeline

**October 2026 – December 2026**

Development began with microcontroller testing and hardware troubleshooting, followed by successful integration of the Raspberry Pi Pico 2 W and MPU6050.

The next phases focus on calibration with real bat recordings, impact classification, wireless recording, custom PCB design, and complete system integration.

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

**Nayan Kasireddi** and **Shayon Chakraborti** (Python analysis and dashboard)

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
