# 2026 Rape Crime Prediction - All Tamil Nadu Districts

## Overview

This feature generates **2026 rape crime predictions** (Section 376 IPC) for Tamil Nadu districts/areas. Using historical trends, it provides:

- Individual predictions for each district
- Risk categorization (High/Medium/Low)
- Comparative analysis
- Comprehensive visualizations
- Detailed reports and recommendations

**Engine:** `predict_2026_rape_all_districts.py` (FIXED-NO-SKLEARN-v4)

---

## Quick Start

### Option 1: Interactive Menu
```bash
python app.py
# Select option 7: 2026 rape crime prediction
```

### Option 2: Command-Line
```bash
python app.py --rape-2026
```

### Option 3: Direct script
```bash
python predict_2026_rape_all_districts.py
# or RUN_OPTION7.bat
```

### Option 4: Python API
```python
from predict_2026_rape_all_districts import predict_2026_rape_all_districts, generate_rape_report
from visualize_rape_2026 import main as visualize_rape_2026

predictions = predict_2026_rape_all_districts()
generate_rape_report(predictions)
visualize_rape_2026()
```

---

## Output Files

### Generated Files
```
model_outputs/
├── rape_predictions_2026_all_districts.csv
├── rape_predictions_2026_report.txt
└── figures/
    ├── rape_2026_top_districts.png
    ├── rape_2026_distribution.png
    ├── rape_2026_risk_categories.png
    ├── rape_2026_all_districts.png
    └── rape_2026_top20_table.png
```

---

## Understanding the Predictions

### Risk Classification

| Category | Range | Meaning |
|----------|-------|---------|
| **HIGH RISK** | >= 1.5x average | Requires enhanced prevention measures |
| **MEDIUM RISK** | 0.5-1.5x average | Standard protocols sufficient |
| **LOW RISK** | < 0.5x average | Maintenance of existing systems |

### Prediction Output
```
CSV Columns (typical):
  rank                           - District ranking
  district                       - District name
  predicted_2026_rape_incidents  - 2026 forecast (incidents)
  rape_risk_index                - Risk score
  risk_level                     - High/Medium/Low
  method                         - Forecast method used
```

---

## How to Use for Planning

1. **Resource Allocation**: Direct more resources to High Risk districts
2. **Awareness**: Increase campaigns in Medium/High Risk areas
3. **Prevention**: Strengthen women safety initiatives
4. **Monitoring**: Track actual vs. predicted quarterly

---

## Data Requirements

- Historical crime data in `dataset/` (women crimes / rape columns)
- Optional: cleaned ML-ready tables under `dataset/cleaned/`

Run the full pipeline first if data is missing:
```bash
python app.py --full
```

---

## Limitations & Considerations

### Data Limitations
- Based on limited historical years (primarily 2022–2023 + proxies)
- Assumes future patterns follow past trends
- Cannot predict unprecedented events

### Recommendations
- Review quarterly for accuracy
- Adjust based on actual outcomes
- Combine with other analysis methods
- Use for trend identification, not absolute forecasting

---

## Troubleshooting

### Issue: "Module not found"
**Solution**: Install dependencies: `pip install -r requirements.txt`

### Issue: Missing districts in output
**Solution**: Some districts may not have sufficient historical data. Check the report for details.

### Issue: Import / engine errors
**Solution**: Run `python tests/test_option7_fix.py` and `python predict_2026_rape_all_districts.py` from the project root.

---

## Support

1. Check `docs/QUICK_START.md` for common problems
2. Review `docs/PROJECT_GUIDE.md` for project overview
3. See `docs/RAPE_2026_IMPLEMENTATION.md` for implementation notes

---

**Crime Data Source**: Tamil Nadu Police Department (2022-2023 + media proxies)  
**Status**: Production Ready  
**Version**: engine FIXED-NO-SKLEARN-v4
