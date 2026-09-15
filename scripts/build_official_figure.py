from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PATHS = ROOT / "results" / "event_paths"
OUTPUT = ROOT / "results" / "figures" / "official_event_wealth.png"

v16 = pd.read_csv(PATHS / "v16.csv", parse_dates=["Exit_Date"])
v8 = pd.read_csv(PATHS / "v8.csv", parse_dates=["Exit_Date"])
tqqq = pd.read_csv(PATHS / "tqqq.csv", parse_dates=["Exit_Date"])

start_date = pd.Timestamp("2023-10-18")
v16_dates = [start_date, *list(v16["Exit_Date"])]
v16_wealth = [1.0, *list(v16["V16_Wealth"])]
v16_dates.append(v16_dates[-1])
v16_wealth.append(4.365779600738577)

v8_dates = [start_date, *list(v8["Exit_Date"])]
v8_wealth = [1.0, *list(v8["Wealth"])]
tqqq_dates = [start_date, *list(tqqq["Exit_Date"])]
tqqq_wealth = [1.0, *list(tqqq["End_Wealth"])]

plt.figure(figsize=(13, 7))
plt.plot(v16_dates, v16_wealth, marker="o", linewidth=2.4, label="V16 official")
plt.plot(v8_dates, v8_wealth, marker="o", linewidth=2.0, label="V8 corrected")
plt.plot(tqqq_dates, tqqq_wealth, linewidth=2.0, label="TQQQ benchmark")
plt.axhline(1.0, color="black", linestyle="--", linewidth=1, alpha=0.6)
plt.title("Official Common-Window Event Wealth")
plt.xlabel("Exit date")
plt.ylabel("Wealth multiple")
plt.grid(alpha=0.25)
plt.legend()
plt.figtext(
    0.5,
    0.01,
    "Historical research backcast; endpoints include the official accounting adjustments.",
    ha="center",
    fontsize=9,
)
plt.tight_layout(rect=(0, 0.03, 1, 1))
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(OUTPUT, dpi=180)
plt.close()
