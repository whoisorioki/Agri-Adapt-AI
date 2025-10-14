#!/usr/bin/env python3
import pandas as pd
import os
from datetime import datetime

print('IDENTIFYING THE REAL DATASET:')
print('='*50)

processed_folder = 'data/processed'
csv_files = [f for f in os.listdir(processed_folder) if f.endswith('.csv')]

print(f'Found {len(csv_files)} CSV files in processed folder:')
print()

for filename in csv_files:
    try:
        df = pd.read_csv(f'{processed_folder}/{filename}')
        file_size = os.path.getsize(f'{processed_folder}/{filename}')
        modified_time = datetime.fromtimestamp(os.path.getmtime(f'{processed_folder}/{filename}'))
        
        counties = df['County'].nunique() if 'County' in df.columns else 0
        years = df['Year'].nunique() if 'Year' in df.columns else 0
        crops = df['Crop'].nunique() if 'Crop' in df.columns else 0
        
        print(f'📁 {filename}:')
        print(f'   Records: {len(df):,}')
        print(f'   Counties: {counties}')
        print(f'   Years: {years}')
        print(f'   Crops: {crops}')
        print(f'   Modified: {modified_time.strftime("%Y-%m-%d %H:%M:%S")}')
        print(f'   Size: {file_size:,} bytes')
        
        # Check if this matches our 93/100 criteria
        if (len(df) == 1413 and counties == 47 and years == 6):
            print('   🎯 >>> THIS IS OUR REAL DATASET! (93/100 score) <<<')
        
        print()
        
    except Exception as e:
        print(f'❌ {filename}: Error - {e}')
        print()

print('SUMMARY:')
print('The real dataset should have:')
print('- 1,413 records')
print('- 47 counties (after standardization)')
print('- 6 years (2019-2024)')
print('- 6-7 crops')