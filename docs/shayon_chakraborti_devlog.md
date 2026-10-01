## 2026-09-30
- Created PyCharm project with virtualenv (Python 3.14)
- Installed numpy, pandas, matplotlib, pytest, streamlit
- Created folder structure: python/, python/tests/, docs/, firmware/

## 2026-09-30 (session 2)
- Wrote python/generate_test_data.py: makes synthetic CSVs (stationary, slow_swing, normal_swing, multi_swing) in data/ so I can build and test before real sensor data exists
- Wrote python/ingest.py: load_csv() validates columns, non-numeric values, NaN/blank rows, timestamp order, sample rate, dropped-sample gaps, and out-of-range accel/gyro values. Raises DataValidationError with specific messages and CSV line numbers
- Wrote python/tests/test_ingest.py: 13 pytest tests, each breaks the data a different way. All 13 pass
- PLACEHOLDER CSV format (NOT yet agreed with Nayan): columns time,ax,ay,az,gx,gy,gz; time in seconds; accel in g; gyro in deg/s; 100 Hz target, +/-20% tolerance
- Config lives at the top of ingest.py (EXPECTED_COLUMNS, TARGET_SAMPLE_RATE_HZ, TIME_TO_SECONDS, etc.), so changing the format is a one-place edit

## 2026-10-01
- Wrote python/analyze.py: plot_acceleration(), plot_gyro(), summary_stats(), rotation_magnitude()
- acceleration_magnitude() is a local stand-in; analyze.py tries `from python.core import acceleration_magnitude` first, so Nayan's version takes over automatically once core.py exists
- Plots save to images/ as PNGs. Added a --show flag, because plt.show() blocks the terminal until the plot window is closed
- Plotted all synthetic files. Stationary magnitude sits at ~1 g (gravity). Swings peak at ~8.4 g and ~1000 deg/s. multi_swing.csv shows 3 clean bumps at 1.5 s, 4.0 s, 6.5 s, as generated
- Observation: a threshold around 2-3 g would cleanly separate swings from rest on the synthetic data. Real data will likely need retuning

## 2026-10-01 (session 2)
- Fixed ingest.py: load_csv() now converts the time column to seconds using TIME_TO_SECONDS (previously it was only used for the sample-rate check). Set it to 0.001 if Nayan's firmware logs millis()
- Added test_millisecond_timestamps_are_converted to test_ingest.py
- Known risks for real data: strict sample-rate/gap checks may reject the first real file; units may be raw counts instead of g and deg/s; MPU6050 default range (+/-2 g, +/-250 deg/s) will saturate on a real swing, so Nayan needs to raise it in firmware and my range limits in ingest.py must match

## 2026-10-01 (session 3)
- Wrote python/live.py: live scrolling graph + CSV recorder. Reads 'time,ax,ay,az,gx,gy,gz' lines over serial (pyserial, 115200 baud), parses on a background thread, saves raw lines to data/live/*.csv, shows accel/gyro magnitude with threshold line and a rough live swing counter
- Includes SimulatedSource (replays synthetic multi_swing) so the live view and recording path can be tested without hardware
- Wrote python/tests/test_live.py: parse_line tests (valid, header, truncated, boot garbage)
- Serial contract to confirm with Nayan: 115200 baud, one CSV line per sample, g and deg/s, millis() time, ~100 Hz, no extra Serial prints, sensor ranges +/-16 g and +/-2000 deg/s
- Not yet tested with real hardware: SerialSource, port naming on Mac (use /dev/cu.*)
- Open question: USB tether isn't practical for real swings; ask Nayan about on-board buffering/SD logging or Bluetooth/Wi-Fi

## 2026-10-01 (session 4)
- Cloned the shared repo (nayan-kasireddi/Cricket-Swing-Analyzer) in PyCharm and moved my Python code into python/: ingest.py, analyze.py, live.py, generate_test_data.py, tests/
- Synthetic data now writes to data/synthetic/ so it never overwrites Nayan's data/stationary.csv. Updated the output path in generate_test_data.py and the default path in analyze.py
- Left core.py untouched (Nayan's file, still empty). analyze.py falls back to my stand-in acceleration_magnitude() until core.py defines one
- Kept separate devlogs (mine vs Nayan's) to avoid edit conflicts; final README will draw on both
- Added pytest, streamlit, pyserial to requirements.txt alongside Nayan's numpy, pandas, matplotlib, scipy
- Added test_millisecond_timestamps_are_converted to test_ingest.py (it was written earlier but not yet in the test file)
- All 18 tests pass in the shared repo (14 ingest + 4 parser)
- Next: check .gitignore, make first commit and push, then message Nayan about the CSV format and core.py signatures

## Open items / TODO
- Text Nayan: propose CSV format (time in seconds, g, deg/s, 100 Hz) and core.py signatures: acceleration_magnitude(df) -> array, detect_swings(df, threshold) -> list of (start_time, end_time). Record the agreed final version here as a new dated entry
- Ask Nayan how Serial output becomes a CSV file (not assigned to either of us in the plan)
- Send Nayan my GitHub username (Shayon2307) and verify my GitHub email; clone the shared repo and copy files in once it exists
- Consider splitting data/ into data/synthetic/ and data/real/ before Nayan's recordings arrive
- Next: stand-in detect_swings(), multi-swing summary table, detection tests, then the Streamlit dashboard