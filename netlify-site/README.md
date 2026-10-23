# Crease — cricket swing analyzer

This is the ready-to-deploy static website. It has no build step, server, API, keys, or runtime dependencies. Example analysis, serial sensor readings, uploaded recordings, and downloaded CSVs stay in your browser.

## Put it on Netlify

Open [Netlify Drop](https://app.netlify.com/drop) and drag the **`netlify-site` folder** onto it. Netlify serves `index.html` directly. No build command or configuration is required for a folder drop.

If you connect this GitHub repository to Netlify, the root `netlify.toml` automatically builds and publishes this folder. Choose `feature/netlify-static-site` to try this version before it reaches `main`; choose `main` after the pull request is merged.

## Try it on your computer

From the repository root:

```sh
python3 -m http.server 8000 --directory netlify-site
```

Visit `http://localhost:8000`. Don’t open `index.html` as a `file://` URL: browsers block the bundled recording fetch and Web Serial requires HTTPS or localhost.

## Connect a Pico

Use a current desktop version of Chrome or Edge. On the Practice page, click **Connect sensor** and choose the Raspberry Pi Pico’s USB serial port. This first click grants the browser permission it requires. The firmware streams at 115200 baud; the website recognizes its microsecond timestamps, g/degree-per-second columns, and extra `skipped_slots` field. Close Arduino Serial Monitor first so the website can use the port.

After you grant access once, an unplugged and reconnected Pico reconnects automatically while the page is open. Some browsers or operating systems require you to click **Connect sensor** again to grant access. Disconnects preserve the session so it can be downloaded. The **Try a demo** button works without hardware or a browser serial API.

The Pico must be physically attached to the same computer running the browser. The website cannot use a sensor connected to a different computer or to the server that hosts the Netlify files.

## Review or add recordings

Choose one of the four bundled 500 Hz examples on Review, or upload a firmware CSV. The analyzer accepts `time_us`/`time_ms`/`time_s` or `time`, accelerometer columns with optional `_g`, gyro columns with optional `_dps`, `#` comments, and the extra firmware `skipped_slots` column. It checks sample spacing and sensor ranges. It reports acceleration in g and rotation in degrees per second; swing detection is an adjustable practice estimate.
