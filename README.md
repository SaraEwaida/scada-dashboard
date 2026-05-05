
# SCADA Control Center

A live web-based **Supervisory Control and Data Acquisition (SCADA)** dashboard built in Python. It simulates a small industrial process, polls five sensors on a one-second scan cycle, stores every reading in a time-series historian, and visualises the live state of the plant in a browser-based HMI.

This project demonstrates the core building blocks of a real SCADA system on a small scale: the **field layer** (sensors), the **historian** (data persistence), and the **HMI** (operator interface), all communicating through a clean, decoupled architecture.

---

## Dashboard Preview

![SCADA Control Center - live process monitoring with KPI cards, alarm panel, and trend charts](screenshots/dashboard_overview.png)

---

## Features

- **Live process monitoring** — current values for every tag, refreshed every second.
- **Industrial alarm system** — each tag is classified as `NORMAL`, `WARNING`, or `CRITICAL` based on configurable hi/lo limits, with colour-coded indicators on the dashboard.
- **Active alarms panel** — only deviating tags are shown, the way real SCADA systems summarise plant health.
- **Time-series trends** — the last two minutes of data plotted for every tag, with reference lines for warning and critical limits.
- **Historian database** — every reading is logged to a SQLite database (`historian.db`) so historical data persists across restarts.
- **Realistic sensor simulation** — each tag uses a mean-reverting random walk plus occasional process upset events, so values move the way real instruments do.
- **Dark industrial HMI theme** — visual style modelled on real SCADA control room interfaces.

---

## Architecture
