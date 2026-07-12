# stdlib-only generator — write 2026 rape CSV from fitted_predictions
import csv, math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FITTED = ROOT / "model_outputs" / "fitted_predictions.csv"
OUT = ROOT / "model_outputs" / "rape_predictions_2026_all_districts.csv"
REPORT = ROOT / "model_outputs" / "rape_predictions_2026_report.txt"
TARGET = "women_crimes_rape_sec_376_i"
TY = 2026


def forecast(years, vals):
    pts = [(float(y), float(v)) for y, v in zip(years, vals)
           if math.isfinite(float(y)) and math.isfinite(float(v))]
    if not pts:
        return 0.0
    if len(pts) == 1:
        return max(0.0, pts[0][1])
    ys = [p[0] for p in pts]
    vs = [p[1] for p in pts]
    my, mv = sum(ys) / len(ys), sum(vs) / len(vs)
    num = sum((y - my) * (v - mv) for y, v in zip(ys, vs))
    den = sum((y - my) ** 2 for y in ys)
    slope = num / den if den else 0.0
    last_y, last_v = max(pts, key=lambda p: p[0])
    return max(0.0, last_v + slope * (TY - last_y))


hist = defaultdict(list)
with FITTED.open(encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f):
        if row.get("target") != TARGET:
            continue
        d = (row.get("district_city") or "").strip()
        if not d:
            continue
        try:
            y = float(row["year"])
            a = float(row["actual"] if row.get("actual") not in (None, "") else row["predicted"])
        except Exception:
            continue
        hist[d].append((y, a))

rows = []
for d, pts in hist.items():
    pts.sort()
    pred = forecast([p[0] for p in pts], [p[1] for p in pts])
    risk = round(min(1.0, 0.7 * min(pred / 25.0, 1.0)), 3)
    rows.append({
        "district": d,
        "predicted_2026_rape_incidents": round(pred, 2),
        "model": "trend_extrapolation",
        "confidence": "High" if len(pts) >= 2 else "Medium",
        "data_points_available": len(pts),
        "base_year": TY,
        "is_fallback": False,
        "method": "Trend (fitted-actual)",
        "rape_risk_index": risk,
        "risk_level": "HIGH" if risk > 0.65 else ("MEDIUM" if risk > 0.35 else "LOW"),
    })

rows.sort(key=lambda r: r["predicted_2026_rape_incidents"], reverse=True)
for i, r in enumerate(rows, 1):
    r["rank"] = i

fields = list(rows[0].keys())
with OUT.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

total = sum(r["predicted_2026_rape_incidents"] for r in rows)
avg = total / len(rows) if rows else 0
lines = [
    "=" * 70,
    "2026 RAPE CRIME PREDICTION REPORT - TAMIL NADU",
    "Engine: FORCE-TREND-v3 (pre-generated, no sklearn)",
    "=" * 70,
    f"Total Districts: {len(rows)}",
    f"Total Predicted: {total:.0f}",
    f"Average: {avg:.1f}",
    f"Highest: {rows[0]['district']} ({rows[0]['predicted_2026_rape_incidents']})",
    f"Lowest: {rows[-1]['district']} ({rows[-1]['predicted_2026_rape_incidents']})",
    "",
    "TOP 10:",
]
for r in rows[:10]:
    lines.append(f"  {r['rank']:2d}. {r['district']:<25} {r['predicted_2026_rape_incidents']:>8.1f}")
lines.append("=" * 70)
REPORT.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {len(rows)} rows to {OUT}")
