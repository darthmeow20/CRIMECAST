import pandas as pd
import os



complaint_df = pd.read_csv(r"dataset\tn_2023_complaints.csv")
crime_women_df = pd.read_csv(r"dataset\tn_2023_crimes_against_women.csv")
murder_df = pd.read_csv(r"dataset\tn_2023_muder_homicide.csv")

print(complaint_df.head())
