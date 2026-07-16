# CRIMECAST Tier-3 ops notes

## 1. District entity cleanup
Module: `district_entities.py`  
Used by news harvest (`normalize_district`) to map headlines → real TN districts and drop junk tokens.

## 2. Tamil NLP
Module: `nlp_pipeline.py`  
- Tamil-script headlines → Tamil crime lexicon (primary)  
- Mixed headlines → blend with English DistilBERT  
- English headlines → DistilBERT SST-2 as before  

## 3. Uncertainty bands (2026 rape)
`predict_2026_rape_all_districts.py` writes:
- `pred_low`, `predicted_2026_rape_incidents`, `pred_high`, `uncertainty_width`  
Shown on the **2026 Forecasts** dashboard page.

## 4. District compare
**District Scorecard** → pick two districts → side-by-side metrics + bar chart.

## 5. Weekly auto-refresh (Windows)

### Option A — double-click
`SCHEDULE_NEWS_REFRESH.bat` runs `acquire_news_signals.py --refresh-new`.

### Option B — Task Scheduler (weekly)
1. Open **Task Scheduler** → Create Basic Task  
2. Trigger: Weekly (e.g. Sunday 08:00)  
3. Action: Start a program  
   - Program:  
     `C:\Users\ya allah\python_visual_code\machine_learning\CRIMECAST\SCHEDULE_NEWS_REFRESH.bat`  
   - Start in:  
     `C:\Users\ya allah\python_visual_code\machine_learning\CRIMECAST`  
4. Finish → allow run whether user is logged on (optional)

### Option C — PowerShell one-liner (register once)

```powershell
$action = New-ScheduledTaskAction -Execute "C:\Users\ya allah\python_visual_code\machine_learning\CRIMECAST\SCHEDULE_NEWS_REFRESH.bat" -WorkingDirectory "C:\Users\ya allah\python_visual_code\machine_learning\CRIMECAST"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 8am
Register-ScheduledTask -TaskName "CRIMECAST_NewsRefresh" -Action $action -Trigger $trigger -Description "Incremental TN crime news harvest"
```

Only **new** headlines are merged; full bulk populate remains menu `n` mode 1.
