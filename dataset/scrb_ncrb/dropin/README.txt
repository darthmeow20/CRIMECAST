Drop SCRB / NCRB official district CSVs here.

Naming (same as project raw tables):
  tn_2025_complaints.csv
  tn_2025_muder_homicide.csv
  tn_2025_crimes_against_women.csv
  tn_2026_complaints.csv
  tn_2026_muder_homicide.csv
  tn_2026_crimes_against_women.csv
  tn_2018_... etc.

Then run:
  python acquire_scrb_ncrb.py --apply --rebuild-ml
  python train_model.py

Or tag existing dataset files as official SCRB:
  python acquire_scrb_ncrb.py --tag-years 2025 2026 --apply --rebuild-ml
