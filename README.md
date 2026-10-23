# Crease: Cricket Swing Analyzer

**Embedded Systems | Raspberry Pi Pico 2 W | MPU6050 | Arduino | Web | Python | KiCad**

**Live site: [creasecricketswing.netlify.app](https://creasecricketswing.netlify.app)**

A sensor on a cricket bat, and a website that turns its motion into swings you can see. A Raspberry Pi Pico 2 W reads an MPU6050 motion sensor 500 times a second. Plug it into your computer, open Crease in the browser, and watch each swing appear as you practice.

## What it does

- **Reads the sensor:** the firmware samples 3-axis acceleration and 3-axis rotation at a **500 Hz** target (±16 g, ±2000 deg/s) and streams them over USB.
- **Shows your practice live:** the Crease website connects to the sensor from the browser, draws your swing as it happens, and counts each swing.
- **Reviews every session:** a session chart with the detected swings shaded, a scorecard for each swing, and a summary you can download.
- **Works without a sensor:** a demo mode lets anyone try the site with sample data.
- **Keeps your data private:** your readings stay in your browser.

## Try it

1. Open **[creasecricketswing.netlify.app](https://creasecricketswing.netlify.app)**.
2. Click **Try a demo** to see how it works with sample data, no hardware needed.
3. To use the real sensor, plug the Pico into your computer with a data USB cable and click **Connect sensor**. Live sensor access works in **desktop Chrome and Edge**, and the browser remembers the sensor for next time.
4. Move the sensor. Each swing is counted and added to the scorecard. Use the **swing trigger** slider (2.5 g by default) to make detection more or less sensitive.

### What the numbers mean

| Reading | Meaning |
|---|---|
| Swings detected | How many swings the trigger picked out |
| Peak acceleration | The strongest push on the sensor, in g, including gravity (a sensor lying still reads about 1 g) |
| Peak rotation | How fast the bat turns, in degrees per second (360 deg/s is one full turn a second) |
| Last swing | How long the swing lasted, in seconds |

**About bat speed:** the sensor records acceleration and rotation, not the speed of the bat head in km/h. Crease does not estimate bat speed or compare you with named players, because that needs a validated bat-speed sensor and comparable published measurements. Detected swings are a practice aid, so tune the trigger for your sensor and movement.

## How it works

```text
 Pico 2 W (C++ firmware)                       Your computer
 ─────────────────────────                     ─────────────────────────────────────
 MPU6050 over I²C, every 2 ms
 prints one CSV line per sample ── USB ──►    Crease website (desktop Chrome or Edge)
                                               reads the sensor, finds the swings,
                                               and draws your session
```

The firmware and the website never call each other. They only agree on the text format of each line (see [Data format](#data-format)).

## Using the real sensor

1. **Wire the sensor** (see [Hardware](#hardware)) and **upload the firmware** `firmware/pico2w_mpu6050/pico2w_mpu6050.ino` with the Arduino IDE and the Arduino-Pico board package. Hold **BOOTSEL** while plugging the Pico in for the first upload.
2. **Plug the Pico into your computer** with a data USB cable. Close the Arduino Serial Monitor first, because it locks the port.
3. Open the site, click **Connect sensor**, and choose the Pico from the list.

If the Pico loses power or a wire comes loose while running, replug the Pico so the firmware sets the sensor up again.

## Hardware

| Component | Purpose |
|---|---|
| Raspberry Pi Pico 2 W | Main microcontroller |
| MPU6050 (GY-521) | 6-axis accelerometer and gyroscope |
| Breadboard and jumper wires | Prototyping |
| USB cable (data-capable) | Power, programming and serial data |
| Custom PCB (in progress) | Compact version for mounting on a bat |

| MPU6050 | Raspberry Pi Pico 2 W |
|---|---|
| VCC | 3V3 (Pin 36) |
| GND | GND (Pin 38) |
| SDA | GP4 (Pin 6) |
| SCL | GP5 (Pin 7) |

The sensor communicates over I²C at address `0x68`.

## Firmware

**Location:** `firmware/pico2w_mpu6050/pico2w_mpu6050.ino` (C++, Arduino)

- Configures the MPU6050 for ±16 g and ±2000 deg/s, and checks the sensor configuration at start-up
- Reads the sensor over I²C at 400 kHz and converts raw values to g and deg/s
- Polls on a fixed 2000 µs schedule (a 500 Hz target) and counts any missed slots in `skipped_slots`
- Streams one line per sample at 115200 baud, with start-up and error diagnostics as `#` comment lines

The other sketches in `firmware/` are earlier bring-up tests (LED and button checks).

## Data format

Each line the firmware sends:

```csv
time_us,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps,skipped_slots
94754100,0.1135,-0.0537,1.0270,-0.55,1.69,0.78,0
```

| Field | Description | Unit |
|---|---|---|
| time_us | Time since the board powered on | Microseconds |
| ax_g, ay_g, az_g | Acceleration along X, Y, Z | g |
| gx_dps, gy_dps, gz_dps | Rotation around X, Y, Z | Degrees/second |
| skipped_slots | Sample slots missed so far | Count |

Lines starting with `#` (a startup banner and sensor error notes) are not data. A 500 Hz target is not a guarantee that every sample arrives on time, so check `skipped_slots` and the sample rate in recordings.

## Python tools

The `python/` folder holds the analysis code used to build and test the project, and it still works on its own for offline checks of recordings.

| File | What it does |
|---|---|
| `python/ingest.py` | `load_csv()`: loads a recording, converts units, and checks it (columns, 500 Hz rate, gaps, increasing timestamps, plausible ranges) |
| `python/swings.py` | `SwingTracker`, `detect_swings()`, `summarize_swings()` |
| `python/analyze.py` | Acceleration and rotation magnitude, static plots from the command line |
| `python/live.py` | Reads the serial port, saves a CSV, and logs swings |
| `python/generate_test_data.py` | Makes synthetic recordings (stationary, slow, normal and multi-swing) |
| `python/dashboard.py`, `python/ui.py` | An earlier Streamlit dashboard, kept for reference |
| `python/core.py` | Placeholder for an alternative analysis implementation, not used |
| `python/tests/` | Automated tests |

```bash
git clone https://github.com/nayan-kasireddi/Cricket-Swing-Analyzer.git
cd Cricket-Swing-Analyzer
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m pytest -q                       # run the automated tests
python -m python.live --sim               # live graph with a fake sensor
python -m python.analyze data/synthetic/multi_swing.csv   # static plots from a recording
```

Developed on Python 3.14, and Python 3.12 has also been validated. Package versions are not pinned in `requirements.txt`, so a newer release of a library could behave differently.

### Why one swing counts once

A bat swing is one smooth sweep of rotation, but the acceleration has several spikes inside it: the hands speeding the bat up, a peak around contact, and the sudden stop in the follow-through, with dips in between. Counting every spike would count one swing three times.

The Python `SwingTracker` treats a swing as active while the force is high **or** the bat is still rotating faster than 150 deg/s. It ends the swing only after things stay calm for 0.2 s, and then ignores new swings for 1 s (a batter cannot swing again that fast).

## Current status and limits

This is a working prototype, and it has not yet seen real bat swings.

- **Tuned on synthetic data and hand movements.** The swing trigger and the other detection settings are provisional. They need retuning on recordings from a sensor mounted on a bat.
- **No bat speed, impact, or force in newtons.** The sensor measures acceleration and rotation only, and Crease reports exactly that.
- **Sensor range:** at ±16 g and ±2000 deg/s, a hard hit with the sensor far from the hands could exceed the accelerometer's range.
- **Browser support:** live sensor access needs desktop Chrome or Edge. Other browsers and phones can use the demo.
- **Not built yet:** impact (bat-ball contact) detection, swing-type classification, and wireless transmission. These need real swing data first.

## Development progress

| Milestone | Status |
|---|---|
| Repository setup and documentation | Complete |
| Pico 2 W firmware upload and LED testing | Complete |
| MPU6050 wiring and soldering | Complete |
| I²C sensor detection | Complete |
| Accelerometer and gyroscope streaming | Complete |
| 500 Hz firmware implementation | Complete |
| CSV loading and data validation | Complete |
| Swing detection (counted once per swing) | Complete |
| Crease website: live practice and session review | Complete |
| Automated tests (40+) | Complete |
| Controlled swing data collection on a bat | Upcoming |
| Threshold tuning on real swings | Upcoming |
| Impact detection | Planned |
| Swing-type classification | Planned |
| KiCad schematic and PCB layout | In progress |
| PCB fabrication and assembly | Planned |
| Final demonstration | Planned |

See [`docs/devlog.md`](docs/devlog.md) and [`docs/shayon_chakraborti_devlog.md`](docs/shayon_chakraborti_devlog.md) for detailed updates.

## Troubleshooting

| Issue | Suggested solution |
|---|---|
| Connect sensor does nothing, or the sensor is not listed | Use desktop Chrome or Edge, a data-capable USB cable, and replug the Pico |
| "Port busy" or cannot open the port | Close the Arduino Serial Monitor or any other program using the sensor |
| Readings stop or look wrong after a loose wire | Unplug and replug the Pico so the firmware sets the sensor up again |
| Too many or too few swings | Adjust the swing trigger slider |
| MPU6050 not detected | Check wiring, solder joints, and I²C address `0x68` |
| Firmware upload fails | Hold BOOTSEL while plugging in the Pico, and confirm the board selection |

## Authors

Crease was developed by both authors.

**Nayan Kasireddi** — hardware, firmware, and PCB design
Electrical and Computer Engineering, The University of Texas at Austin
GitHub: [@nayan-kasireddi](https://github.com/nayan-kasireddi)

**Shayon Chakraborti** — Python data pipeline, swing detection, and testing
Statistics and Data Science, The University of Texas at Austin
GitHub: [@Shayon2307](https://github.com/Shayon2307)

## Acknowledgments

Built with the Raspberry Pi Pico platform, the MPU6050 motion sensor, Arduino, Python (NumPy, pandas, Matplotlib, pySerial), and KiCad. Hardware prototyping and fabrication resources are available through Texas Inventionworks at The University of Texas at Austin.

## Project resources

- [Crease website](https://creasecricketswing.netlify.app)
- [GitHub repository](https://github.com/nayan-kasireddi/Cricket-Swing-Analyzer)
- [Firmware](firmware/pico2w_mpu6050/pico2w_mpu6050.ino)
- [Development logs](docs/)
- [Python code](python/)