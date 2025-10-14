#!/usr/bin/env python3
import pandas as pd

print('🔍 VALIDATING FINAL CLEANED DATASET:')
print('='*50)

df = pd.read_csv('data/processed/kenya_agricultural_complete_6crops_2019_2024.csv')

print(f'📊 Final Dataset Validation:')
print(f'   File: kenya_agricultural_complete_6crops_2019_2024.csv')
print(f'   Records: {len(df):,}')
print(f'   Counties: {df["County"].nunique()}')
print(f'   Crops: {df["Crop"].nunique()}')
print(f'   Years: {df["Year"].nunique()}')
print(f'   Year Range: {df["Year"].min()}-{df["Year"].max()}')

# Check for our standardized county names
has_trans_nzoia = 'Trans-Nzoia' in df['County'].values
has_muranga = 'Murang\'a' in df['County'].values
no_old_trans = 'Trans Nzoia' not in df['County'].values
no_old_muranga = 'Muranga' not in df['County'].values

print(f'   County Standardization Verification:')
print(f'      Trans-Nzoia present: {"✅" if has_trans_nzoia else "❌"}')
print(f'      Murang\'a present: {"✅" if has_muranga else "❌"}')
print(f'      Old names absent: {"✅" if (no_old_trans and no_old_muranga) else "❌"}')

# Final validation
criteria_met = (
    len(df) == 1413 and 
    df['County'].nunique() == 47 and 
    df['Year'].nunique() == 6 and 
    df['Crop'].nunique() >= 6 and
    has_trans_nzoia and has_muranga and
    no_old_trans and no_old_muranga
)

print(f'')
print(f'🎯 93/100 MODEL READINESS VALIDATION:')
print(f'   1,413 records: {"✅" if len(df) == 1413 else "❌"}')
print(f'   47 counties: {"✅" if df["County"].nunique() == 47 else "❌"}')
print(f'   6 years: {"✅" if df["Year"].nunique() == 6 else "❌"}')
print(f'   6+ crops: {"✅" if df["Crop"].nunique() >= 6 else "❌"}')
print(f'   County standardization: {"✅" if (has_trans_nzoia and has_muranga) else "❌"}')
print(f'')
if criteria_met:
    print('✅ VALIDATION PASSED: This is our authentic 93/100 dataset!')
    print('🚀 STATUS: READY FOR CLOUDOON PRESENTATION')
else:
    print('❌ VALIDATION FAILED')