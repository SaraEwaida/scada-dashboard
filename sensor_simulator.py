"""
Sensor Simulator
----------------
Simulates realistic industrial sensor readings for a SCADA system.
Each sensor has a target value, normal operating range, and small random noise
to mimic real-world process variation.

Tags (process variables) simulated:
    TT-101  Reactor Temperature (deg C)
    PT-201  Pump Discharge Pressure (bar)
    FT-301  Process Flow Rate (L/min)
    LT-401  Storage Tank Level (%)
    ST-501  Motor Speed (RPM)
"""

import random
from datetime import datetime


# Sensor configuration: each tag has a target, allowed range, warning range,
# critical range, unit, and current value (which drifts realistically over time).
SENSORS = {
    "TT-101": {
        "name": "Reactor Temperature",
        "unit": "C",
        "target": 75.0,
        "current": 75.0,
        "warning_low": 65, "warning_high": 85,
        "critical_low": 60, "critical_high": 90,
        "noise": 0.4,
    },
    "PT-201": {
        "name": "Pump Pressure",
        "unit": "bar",
        "target": 5.0,
        "current": 5.0,
        "warning_low": 4.0, "warning_high": 6.0,
        "critical_low": 3.0, "critical_high": 7.0,
        "noise": 0.08,
    },
    "FT-301": {
        "name": "Flow Rate",
        "unit": "L/min",
        "target": 100.0,
        "current": 100.0,
        "warning_low": 90, "warning_high": 110,
        "critical_low": 80, "critical_high": 120,
        "noise": 1.2,
    },
    "LT-401": {
        "name": "Tank Level",
        "unit": "%",
        "target": 60.0,
        "current": 60.0,
        "warning_low": 30, "warning_high": 85,
        "critical_low": 15, "critical_high": 95,
        "noise": 0.5,
    },
    "ST-501": {
        "name": "Motor Speed",
        "unit": "RPM",
        "target": 1500.0,
        "current": 1500.0,
        "warning_low": 1300, "warning_high": 1700,
        "critical_low": 1100, "critical_high": 1900,
        "noise": 8.0,
    },
}


def get_status(tag, value):
    """Return one of: NORMAL, WARNING, CRITICAL based on value vs. limits."""
    s = SENSORS[tag]
    if value <= s["critical_low"] or value >= s["critical_high"]:
        return "CRITICAL"
    if value <= s["warning_low"] or value >= s["warning_high"]:
        return "WARNING"
    return "NORMAL"


def read_sensor(tag):
    """Simulate one reading for the given tag and update its drift state."""
    s = SENSORS[tag]
    # Drift slightly back toward target (mean-reverting walk)
    drift = (s["target"] - s["current"]) * 0.05
    noise = random.gauss(0, s["noise"])
    s["current"] += drift + noise

    # Occasionally inject an "event" (process upset) for realism
    if random.random() < 0.01:
        s["current"] += random.choice([-1, 1]) * s["noise"] * 6

    value = round(s["current"], 2)
    return {
        "tag": tag,
        "name": s["name"],
        "unit": s["unit"],
        "value": value,
        "status": get_status(tag, value),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }


def read_all():
    """Return a reading from every configured sensor."""
    return [read_sensor(tag) for tag in SENSORS]


# Quick self-test: run `python sensor_simulator.py` to see 5 readings.
if __name__ == "__main__":
    print("Sensor Simulator self-test\n" + "-" * 60)
    for _ in range(5):
        for r in read_all():
            print(f"{r['timestamp']}  {r['tag']}  {r['name']:<22}"
                  f"  {r['value']:>8} {r['unit']:<5}  [{r['status']}]")
        print()
