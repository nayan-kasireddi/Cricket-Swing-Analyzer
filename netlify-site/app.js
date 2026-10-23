const EXPECTED = ["time", "ax", "ay", "az", "gx", "gy", "gz"];
const ALIASES = new Map([
  ["time_us", ["time", 1e-6]], ["time_ms", ["time", 1e-3]], ["time_s", ["time", 1]],
  ["ax_g", ["ax", 1]], ["ay_g", ["ay", 1]], ["az_g", ["az", 1]],
  ["gx_dps", ["gx", 1]], ["gy_dps", ["gy", 1]], ["gz_dps", ["gz", 1]],
]);
const FILES = [
  ["multi_swing.csv", "Three practice swings"],
  ["normal_swing.csv", "Single swing"],
  ["stationary.csv", "Stationary bat"],
  ["slow_swing.csv", "Gentle movement"],
];
const WINDOW = 5;
const HOLD = 0.2;
const COOLDOWN = 1;
const MIN_SWING = 0.05;
const MIN_GYRO = 150;
const ACCEL_COLOR = "#c5fa72";
const ROTATION_COLOR = "#65c9e8";
const TRIGGER_COLOR = "#ff805e";
const state = { rows: [], swings: [], threshold: 2.5, port: null, reader: null,
  running: false, demoTimer: null, demoIndex: 0, demoEpoch: 0, demoRows: [],
  fileName: "", csvParts: [], csvPending: [], tracker: null, sessionStart: null,
  lastPaint: 0, notice: "", reviewed: null };

const el = (id) => document.getElementById(id);
const escapeHtml = (value) => String(value).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

function setStatus(text, kind = "") {
  el("status-label").textContent = text;
  el("connection-status").className = `status${kind ? ` ${kind}` : ""}`;
}

function showError(message = "") {
  state.notice = message;
  const box = el("live-error");
  box.textContent = message;
  box.hidden = !message;
}

function thresholdValue(input, output, live = false) {
  state.threshold = Number(input.value);
  output.value = `${state.threshold.toFixed(1)} g`;
  output.textContent = output.value;
  if (live && state.reviewed) renderReview(state.reviewed.rows, state.reviewed.name);
  if (live && state.running) paintLive(true);
}

class SwingTracker {
  constructor() {
    this.active = false;
    this.armed = true;
    this.blockedUntil = -Infinity;
    this.start = 0;
    this.lastActive = 0;
    this.peakG = 0;
    this.peakDps = 0;
  }

  update(t, acceleration, rotation) {
    if (!this.active) {
      if (t >= this.blockedUntil) {
        if (acceleration > state.threshold && this.armed) {
          this.active = true;
          this.start = this.lastActive = t;
          this.peakG = acceleration;
          this.peakDps = rotation;
        } else if (acceleration < state.threshold * 0.8 && rotation < MIN_GYRO) {
          this.armed = true;
        }
      }
      return null;
    }

    this.peakG = Math.max(this.peakG, acceleration);
    this.peakDps = Math.max(this.peakDps, rotation);
    if (acceleration >= state.threshold * 0.8 || rotation >= MIN_GYRO) this.lastActive = t;
    if (t - this.lastActive >= HOLD || t - this.start >= 3) return this.finish();
    return null;
  }

  flush() {
    return this.active ? this.finish() : null;
  }

  finish() {
    this.active = false;
    this.armed = false;
    this.blockedUntil = this.lastActive + COOLDOWN;
    if (this.lastActive - this.start < MIN_SWING) return null;
    return { start: this.start, end: this.lastActive, duration: this.lastActive - this.start,
      peakG: this.peakG, peakDps: this.peakDps };
  }
}

function noteSwing(swing) {
  if (!swing) return;
  state.swings.push({ number: state.swings.length + 1, ...swing });
  const peak = state.swings.reduce((best, item) => item.peakG > best.peakG ? item : best, state.swings[0]);
  const spin = state.swings.reduce((best, item) => item.peakDps > best.peakDps ? item : best, state.swings[0]);
  el("swing-count").textContent = String(state.swings.length);
  el("peak-acceleration").textContent = peak.peakG.toFixed(1);
  el("peak-rotation").textContent = String(Math.round(spin.peakDps));
  el("last-duration").textContent = swing.duration.toFixed(2);
}

function pushCsv(row) {
  state.csvPending.push(row.join(","));
  if (state.csvPending.length >= 100) {
    state.csvParts.push(state.csvPending.join("\n") + "\n");
    state.csvPending = [];
  }
}

function processRow(row) {
  if (state.sessionStart === null) state.sessionStart = row[0];
  const t = row[0] - state.sessionStart;
  const normalized = [t, ...row.slice(1)];
  const acceleration = Math.hypot(row[1], row[2], row[3]);
  const rotation = Math.hypot(row[4], row[5], row[6]);
  state.rows.push(normalized);
  if (state.rows.length > 3000) state.rows.splice(0, 1000);
  pushCsv(normalized);
  noteSwing(state.tracker.update(t, acceleration, rotation));
  const now = performance.now();
  if (now - state.lastPaint > 160) {
    state.lastPaint = now;
    paintLive();
  }
}

function setRunning(running) {
  state.running = running;
  el("stop-button").hidden = !running;
  el("connect-button").hidden = running;
  el("demo-button").hidden = running;
  el("threshold-slider").disabled = false;
}

function connectionDetails(port) {
  const info = port.getInfo?.() ?? {};
  const ids = [info.usbVendorId, info.usbProductId]
    .filter(value => value !== undefined).map(value => `0x${value.toString(16).padStart(4, "0")}`);
  return ids.length ? `Pico sensor · ${ids.join(":")}` : "Pico sensor connected";
}

async function connectSensor(port = null) {
  if (!window.isSecureContext || !("serial" in navigator)) {
    showError("Live USB sensor access needs Chrome or Edge on HTTPS (or localhost). You can still review recordings and try the demo.");
    return;
  }
  showError("");
  try {
    // requestPort must run in the click handler so the browser can grant USB access.
    port ??= await navigator.serial.requestPort();
    await port.open({ baudRate: 115200 });
    state.port = port;
    startSession("live", connectionDetails(port));
    await readSerial(port);
  } catch (error) {
    await closePort(port);
    if (error.name !== "NotFoundError") showError(`Could not connect: ${error.message}. Close Arduino Serial Monitor and try again.`);
    if (!state.running) setStatus("Ready when you are");
  }
}

async function readSerial(port) {
  let decoder = new TextDecoder();
  let pending = "";
  try {
    while (state.running && state.port === port && port.readable) {
      const reader = port.readable.getReader();
      state.reader = reader;
      try {
        while (state.running && state.port === port) {
          const { value, done } = await reader.read();
          if (done) break;
          pending += decoder.decode(value, { stream: true });
          const lines = pending.split(/\r?\n/);
          pending = lines.pop() ?? "";
          for (const line of lines) {
            const row = parseSerialLine(line);
            if (row) processRow(row);
          }
        }
      } finally {
        reader.releaseLock();
        if (state.reader === reader) state.reader = null;
      }
      break;
    }
    if (state.running && state.port === port) await endSession("Sensor disconnected. Your session is saved; reconnect to start another.");
  } catch (error) {
    if (state.running && state.port === port) await endSession(`Sensor stopped sending data. Your session is saved. ${error.message}`);
  }
}

function parseSerialLine(line) {
  if (!line || line.startsWith("#") || /^time/i.test(line)) return null;
  const parts = line.trim().split(",");
  if (parts.length !== 7 && parts.length !== 8) return null;
  const row = parts.slice(0, 7).map(Number);
  if (row.length !== 7 || !row.every(Number.isFinite)) return null;
  if (row[1] < -16 || row[1] > 16 || row[2] < -16 || row[2] > 16 || row[3] < -16 || row[3] > 16) return null;
  if (row.slice(4).some(value => Math.abs(value) > 2000)) return null;
  row[0] *= 1e-6;
  return row;
}

function startSession(kind, label) {
  state.rows = [];
  state.swings = [];
  state.sessionStart = null;
  state.tracker = new SwingTracker();
  state.csvPending = [];
  state.csvParts = ["time,ax,ay,az,gx,gy,gz\n"];
  state.fileName = `${kind}_${new Date().toISOString().replace(/[:.]/g, "-")}.csv`;
  state.lastPaint = 0;
  state.reviewed = null;
  setRunning(true);
  setStatus(kind === "demo" ? "Demo session · simulated data" : label, "recording");
  el("sensor-name").textContent = label;
  showError("");
  el("sample-rate").textContent = "Warming up sensor…";
  el("live-log").className = "empty-log";
  el("live-log").textContent = "Your first completed swing will appear here.";
  el("download-live").hidden = false;
}

function paintLive(force = false) {
  const latest = state.rows.at(-1);
  if (!latest) return;
  const recent = state.rows.filter(row => row[0] >= latest[0] - WINDOW);
  const elapsed = recent.at(-1)[0] - recent[0][0];
  const rate = elapsed > 0 ? (recent.length - 1) / elapsed : 0;
  el("sample-rate").textContent = rate ? `${rate.toFixed(0)} Hz · ${state.rows.length.toLocaleString()} samples` : "Receiving readings…";
  drawCharts(el("live-charts"), recent, state.threshold, state.swings, true);
  renderLog(el("live-log"), state.swings, true);
}

async function endSession(message = "") {
  if (!state.running) return;
  state.running = false;
  clearInterval(state.demoTimer);
  state.demoTimer = null;
  noteSwing(state.tracker?.flush());
  if (state.csvPending.length) {
    state.csvParts.push(state.csvPending.join("\n") + "\n");
    state.csvPending = [];
  }
  if (!message && state.rows.length) download(state.fileName, state.csvParts);
  const port = state.port;
  state.port = null;
  const reader = state.reader;
  if (reader) await reader.cancel().catch(() => {});
  await closePort(port);
  setRunning(false);
  setStatus(message ? "Session saved · reconnect when ready" : "Session saved · nice work");
  if (message) showError(message);
  if (state.rows.length) {
    const duration = state.rows.at(-1)[0];
    el("sample-rate").textContent = `${state.rows.length.toLocaleString()} samples · ${duration.toFixed(1)} seconds`;
    paintLive(true);
  }
}

async function closePort(port) {
  if (!port) return;
  try { if (port.readable) await port.close(); } catch { /* A disconnected USB port may already be closed. */ }
}

async function startDemo() {
  if (!state.demoRows.length) {
    el("demo-button").disabled = true;
    el("demo-button").textContent = "Loading demo…";
    try {
      state.demoRows = (await loadRecording("multi_swing.csv")).rows;
    } catch (error) {
      showError(`Could not load the demo: ${error.message}`);
      el("demo-button").disabled = false;
      el("demo-button").textContent = "Try a demo";
      return;
    }
    el("demo-button").disabled = false;
    el("demo-button").textContent = "Try a demo";
  }
  startSession("demo", "DEMO · simulated readings");
  el("connection-help").textContent = "DEMO · Simulated sensor data for practice. Not a real swing or hardware reading.";
  state.demoIndex = 0;
  state.demoEpoch = 0;
  state.demoTimer = setInterval(() => {
    // Eight 500 Hz samples per 16 ms frame keeps the demo close to real time.
    for (let batch = 0; batch < 8; batch += 1) {
      const row = state.demoRows[state.demoIndex];
      processRow([row[0] + state.demoEpoch, ...row.slice(1)]);
      state.demoIndex += 1;
      if (state.demoIndex === state.demoRows.length) {
        state.demoIndex = 0;
        state.demoEpoch += state.demoRows.at(-1)[0] + 0.002;
      }
    }
  }, 16);
}

async function loadRecording(filename) {
  const response = await fetch(`recordings/${encodeURIComponent(filename)}`);
  if (!response.ok) throw new Error(`Recording unavailable (${response.status}).`);
  return { name: FILES.find(([file]) => file === filename)?.[1] ?? filename,
    rows: parseCsv(await response.text()) };
}

function parseCsv(text) {
  const lines = text.replace(/^\uFEFF/, "").split(/\r?\n/).filter(line => line.trim() && !line.trimStart().startsWith("#"));
  if (lines.length < 3) throw new Error("Need a CSV header and at least two sensor readings.");
  const columns = lines[0].split(",").map(name => name.trim().toLowerCase());
  const indexes = new Map();
  let timeScale = 1;
  columns.forEach((name, index) => {
    const [canonical, scale] = ALIASES.get(name) ?? [name, 1];
    if (canonical === "time" && name !== "time") timeScale = scale;
    if (!indexes.has(canonical)) indexes.set(canonical, index);
  });
  const absent = EXPECTED.filter(name => !indexes.has(name));
  if (absent.length) throw new Error(`Missing required columns: ${absent.join(", ")}.`);
  const rows = [];
  for (let lineIndex = 1; lineIndex < lines.length; lineIndex += 1) {
    const cells = lines[lineIndex].split(",");
    if (cells.length < columns.length) throw new Error(`Incomplete CSV row ${lineIndex + 1}.`);
    const row = EXPECTED.map(name => Number(cells[indexes.get(name)])).map((value, index) => index === 0 ? value * timeScale : value);
    if (!row.every(Number.isFinite)) throw new Error(`Non-numeric reading at CSV row ${lineIndex + 1}.`);
    if (row.slice(1, 4).some(value => Math.abs(value) > 16) || row.slice(4).some(value => Math.abs(value) > 2000)) {
      throw new Error(`Reading outside the sensor range at CSV row ${lineIndex + 1}.`);
    }
    rows.push(row);
  }
  if (rows.length < 2) throw new Error("Need at least two sensor readings.");
  const intervals = [];
  for (let index = 1; index < rows.length; index += 1) {
    const dt = rows[index][0] - rows[index - 1][0];
    if (dt <= 0) throw new Error(`Timestamps must increase (CSV row ${index + 1}).`);
    intervals.push(dt);
  }
  const sorted = [...intervals].sort((a, b) => a - b);
  const median = sorted[Math.floor(sorted.length / 2)];
  const rate = 1 / median;
  if (Math.abs(rate - 500) / 500 > 0.2) throw new Error(`This recording is ${rate.toFixed(0)} Hz. The analyzer expects 500 Hz (±20%).`);
  for (let index = 0; index < intervals.length; index += 1) {
    if (intervals[index] > median * 3) throw new Error(`A large gap appears near CSV row ${index + 2}.`);
  }
  const origin = rows[0][0];
  return rows.map(([t, ...values]) => [t - origin, ...values]);
}

function analyze(rows, threshold) {
  const tracker = new SwingTracker();
  state.threshold = threshold;
  const swings = [];
  rows.forEach(row => {
    const sample = row;
    const result = tracker.update(sample[0], Math.hypot(...sample.slice(1, 4)), Math.hypot(...sample.slice(4, 7)));
    if (result) swings.push({ number: swings.length + 1, ...result });
  });
  const final = tracker.flush();
  if (final) swings.push({ number: swings.length + 1, ...final });
  return swings;
}

function drawCharts(container, rows, threshold, swings, live) {
  if (!rows.length) return;
  container.replaceChildren(
    makeChart(rows, 1, "Acceleration · g", ACCEL_COLOR, live ? threshold : null, swings, live),
    makeChart(rows, 4, "Rotation · degrees per second", ROTATION_COLOR, null, swings, live),
  );
}

function makeChart(rows, offset, title, color, trigger, swings, live) {
  const outer = document.createElement("div");
  outer.className = "chart-box";
  const heading = document.createElement("div");
  heading.className = "chart-title";
  heading.textContent = title;
  const tooltip = document.createElement("div");
  tooltip.className = "chart-tooltip";
  tooltip.hidden = true;
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("class", "chart-svg");
  svg.setAttribute("viewBox", "0 0 1000 190");
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", `${title} graph`);
  const allValues = rows.map(row => Math.hypot(row[offset], row[offset + 1], row[offset + 2]));
  const maxValue = Math.max(1, trigger ?? 0, allValues.reduce((maximum, value) => Math.max(maximum, value), 0)) * 1.12;
  const left = 52, right = 986, top = 11, bottom = 159;
  const start = rows[0][0], end = rows.at(-1)[0];
  const duration = Math.max(end - start, 0.001);
  const x = t => left + (t - start) / duration * (right - left);
  const y = value => bottom - value / maxValue * (bottom - top);
  const make = (name, attrs) => {
    const node = document.createElementNS("http://www.w3.org/2000/svg", name);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, String(value)));
    svg.append(node);
    return node;
  };
  [0, .25, .5, .75, 1].forEach(fraction => {
    const yy = bottom - fraction * (bottom - top);
    make("line", { x1: left, x2: right, y1: yy, y2: yy, class: "grid" });
    const label = make("text", { x: left - 9, y: yy + 3, "text-anchor": "end" });
    label.textContent = (fraction * maxValue).toFixed(maxValue < 12 ? 1 : 0);
  });
  const ticks = 4;
  for (let tick = 0; tick <= ticks; tick += 1) {
    const xx = left + tick / ticks * (right - left);
    make("line", { x1: xx, x2: xx, y1: bottom, y2: bottom + 4, class: "grid" });
    const label = make("text", { x: xx, y: bottom + 18, "text-anchor": tick === 0 ? "start" : tick === ticks ? "end" : "middle" });
    label.textContent = `${(start + duration * tick / ticks).toFixed(1)}s`;
  }
  swings.forEach(swing => {
    if (swing.end < start || swing.start > end) return;
    make("rect", { x: Math.max(left, x(swing.start)), y: top,
      width: Math.max(1, Math.min(right, x(swing.end)) - Math.max(left, x(swing.start))),
      height: bottom - top, class: "swing-band" });
  });
  if (trigger !== null) make("line", { x1: left, x2: right, y1: y(trigger), y2: y(trigger), class: "trigger" });
  const values = allValues.map((value, index) => `${index ? "L" : "M"} ${x(rows[index][0]).toFixed(2)} ${y(value).toFixed(2)}`).join(" ");
  make("path", { d: `${values} L ${x(end)} ${bottom} L ${x(start)} ${bottom} Z`, class: "area", fill: color });
  make("path", { d: values, class: "series", stroke: color });
  const hover = make("line", { x1: left, x2: left, y1: top, y2: bottom, class: "hoverline", hidden: "" });
  const dot = make("circle", { cx: left, cy: top, r: 4.5, fill: color, class: "hoverdot", hidden: "" });
  const pointer = make("rect", { x: left, y: top, width: right - left, height: bottom - top, class: "pointer" });
  pointer.addEventListener("pointermove", event => {
    const bounds = svg.getBoundingClientRect();
    const relativeX = (event.clientX - bounds.left) / bounds.width * 1000;
    const index = Math.max(0, Math.min(rows.length - 1, Math.round((relativeX - left) / (right - left) * (rows.length - 1))));
    const value = allValues[index];
    hover.removeAttribute("hidden"); dot.removeAttribute("hidden");
    hover.setAttribute("x1", x(rows[index][0])); hover.setAttribute("x2", x(rows[index][0]));
    dot.setAttribute("cx", x(rows[index][0])); dot.setAttribute("cy", y(value));
    tooltip.hidden = false;
    tooltip.textContent = `${rows[index][0].toFixed(3)} s  ·  ${value.toFixed(2)} ${offset === 1 ? "g" : "°/s"}`;
  });
  pointer.addEventListener("pointerleave", () => {
    hover.setAttribute("hidden", ""); dot.setAttribute("hidden", ""); tooltip.hidden = true;
  });
  outer.append(heading, tooltip, svg);
  if (live && trigger !== null) {
    const hint = document.createElement("span");
    hint.className = "chart-note";
    hint.textContent = `Trigger ${trigger.toFixed(1)} g`;
    outer.append(hint);
  }
  return outer;
}

function renderLog(container, swings, isLive = false) {
  if (!swings.length) {
    container.className = "empty-log";
    container.textContent = isLive ? "Your first completed swing will appear here." : "No swings found at this trigger. Try lowering the trigger.";
    return;
  }
  const strongest = Math.max(1, ...swings.map(swing => swing.peakG));
  const rows = swings.map(swing => `<tr><td class="swing-number">${swing.number.toString().padStart(2, "0")}</td><td>${swing.start.toFixed(2)} s</td><td>${swing.duration.toFixed(2)} s</td><td class="peak-cell">${swing.peakG.toFixed(2)} g<span class="bar"><i style="width:${Math.max(4, swing.peakG / strongest * 100)}%"></i></span></td><td>${Math.round(swing.peakDps)} °/s</td></tr>`).join("");
  container.className = "score-table-wrap";
  container.innerHTML = `<table class="scorecard"><thead><tr><th>SWING</th><th>STARTED</th><th>DURATION</th><th>PEAK ACCELERATION</th><th>PEAK ROTATION</th></tr></thead><tbody>${rows}</tbody></table>`;
}

async function renderReview(rows, name) {
  state.reviewed = { rows, name };
  const swings = analyze(rows, state.threshold);
  const highestAcceleration = Math.max(0, ...swings.map(swing => swing.peakG));
  const highestRotation = Math.max(0, ...swings.map(swing => swing.peakDps));
  const averageDuration = swings.length ? swings.reduce((sum, swing) => sum + swing.duration, 0) / swings.length : 0;
  el("review-swing-count").textContent = swings.length;
  el("review-peak-acceleration").textContent = swings.length ? highestAcceleration.toFixed(1) : "—";
  el("review-peak-rotation").textContent = swings.length ? Math.round(highestRotation) : "—";
  el("review-average-duration").textContent = swings.length ? averageDuration.toFixed(2) : "—";
  el("recording-caption").textContent = `${name} · ${rows.length.toLocaleString()} samples · ${(rows.at(-1)[0] - rows[0][0]).toFixed(1)} seconds`;
  drawCharts(el("review-charts"), rows, state.threshold, swings, false);
  renderLog(el("review-log"), swings);
  el("review-source").textContent = `${swings.length} swing${swings.length === 1 ? "" : "s"}`;
  el("download-summary").disabled = swings.length === 0;
}

function download(filename, parts, mime = "text/csv") {
  const url = URL.createObjectURL(new Blob(parts, { type: `${mime};charset=utf-8` }));
  const link = document.createElement("a");
  link.href = url; link.download = filename;
  document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}

function swingSummaryCsv() {
  const rows = analyze(state.reviewed.rows, state.threshold);
  return ["swing,start_s,end_s,duration_s,peak_accel_g,peak_rotation_dps",
    ...rows.map(row => [row.number, row.start.toFixed(3), row.end.toFixed(3), row.duration.toFixed(3), row.peakG.toFixed(2), row.peakDps.toFixed(1)].join(","))].join("\n") + "\n";
}

function switchPage(page) {
  const review = page === "review";
  el("live-page").hidden = review;
  el("review-page").hidden = !review;
  document.querySelectorAll(".nav-button").forEach(button => button.classList.toggle("active", button.dataset.page === page));
  el("hero-title").innerHTML = review ? "Find your rhythm.<br>Own your next innings." : "Every swing.<br>A little better.";
  el("hero-subtitle").textContent = review ? "Go beyond the score. Explore your recordings and get to know the shape of your swing." : "Your practice, in focus. Take a swing and turn movement into insight.";
  location.hash = page;
}

async function openRecording(name, rows) {
  const recording = rows ? { name, rows } : await loadRecording(name);
  await renderReview(recording.rows, recording.name);
}

async function init() {
  for (const [file, label] of FILES) {
    const option = document.createElement("option");
    option.value = file; option.textContent = label;
    el("recording-select").append(option);
  }
  el("recording-select").value = FILES[0][0];
  try { await openRecording(FILES[0][0]); }
  catch (error) { el("review-log").textContent = `Could not load the bundled example: ${error.message}`; }

  document.querySelectorAll(".nav-button").forEach(button => button.addEventListener("click", () => switchPage(button.dataset.page)));
  el("connect-button").addEventListener("click", () => connectSensor());
  el("demo-button").addEventListener("click", startDemo);
  el("stop-button").addEventListener("click", () => endSession());
  el("threshold-slider").addEventListener("input", () => thresholdValue(el("threshold-slider"), el("threshold-value"), true));
  el("review-threshold").addEventListener("input", () => {
    const input = el("review-threshold");
    state.threshold = Number(input.value);
    el("review-threshold-value").value = `${state.threshold.toFixed(1)} g`;
    el("review-threshold-value").textContent = el("review-threshold-value").value;
    if (state.reviewed) renderReview(state.reviewed.rows, state.reviewed.name);
  });
  el("recording-select").addEventListener("change", async event => {
    try { await openRecording(event.target.value); }
    catch (error) { el("review-log").textContent = `Could not open recording: ${error.message}`; }
  });
  el("file-input").addEventListener("change", async event => {
    const file = event.target.files[0];
    if (!file) return;
    try {
      const rows = parseCsv(await file.text());
      const option = document.createElement("option");
      option.value = `upload:${file.name}`; option.textContent = file.name;
      option.dataset.uploaded = "true";
      el("recording-select").add(option);
      el("recording-select").value = option.value;
      await openRecording(file.name, rows);
      switchPage("review");
    } catch (error) { el("review-log").textContent = `Could not open recording: ${error.message}`; }
    event.target.value = "";
  });
  el("download-live").addEventListener("click", () => {
    if (state.csvPending.length) {
      state.csvParts.push(state.csvPending.join("\n") + "\n");
      state.csvPending = [];
    }
    download(state.fileName || "cricket-session.csv", state.csvParts);
  });
  el("download-summary").addEventListener("click", () => {
    if (state.reviewed) download("swing-summary.csv", [swingSummaryCsv()]);
  });

  if (!window.isSecureContext || !("serial" in navigator)) {
    el("connect-button").disabled = true;
    el("sensor-name").textContent = "Browser USB access unavailable";
    el("connection-help").textContent = "For live sensor access, use Chrome or Edge at your Netlify HTTPS address (or localhost). Demo and recording review work in other browsers too.";
  } else {
    navigator.serial.addEventListener("connect", async event => {
      if (!state.running) await connectSensor(event.target);
    });
    navigator.serial.addEventListener("disconnect", event => {
      if (state.running && state.port === event.target) endSession("Sensor disconnected. Your session is saved; reconnect to start another.");
    });
    const remembered = await navigator.serial.getPorts().catch(() => []);
    if (remembered.length) el("connection-help").textContent = "Previously approved Pico ports reconnect automatically. Use Connect sensor to choose or authorize a sensor.";
  }
  document.documentElement.dataset.ready = "true";
}

document.addEventListener("DOMContentLoaded", init);
