# Crease: Cricket Swing Analyzer

**Embedded Systems | Raspberry Pi Pico 2 W | MPU6050 | Arduino | Web | Python | KiCad**

**Live site: [creasecricketswing.netlify.app](https://creasecricketswing.netlify.app)**

A sensor on a cricket bat, and a website that turns its motion into swings you can see. A Raspberry Pi Pico 2 W reads an MPU6050 motion sensor 500 times a second. Plug it into your computer, open Crease in the browser, and watch each swing appear as you practice.

## What it does

- **Reads the sensor:** the firmware samples 3-axis acceleration and 3-axis rotation at a **500 Hz** target (±16 g, ±2000 deg/s) and streams them over USB.
- **Shows your practice live:** the Crease website connects to the sensor from the browser, draws your swing as it happens, and counts each swing.
- **Reviews every session:** a session chart with the detected swings shaded, a scorecard for each swing, and a summary you can download.
- **Works without a sensor:** a demo mode lets anyone try the site with sample data, and saved recordings can be reviewed in any modern desktop browser.
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
|