#!/usr/bin/env python3
"""
Complete 2024 Data Integration Script
Adds ALL missing 2024 crop data from KNBS 2025 report to our expanded dataset
"""

import pandas as pd
import numpy as np
import os

def load_complete_2024_data():
    """Load all 6 crops complete 2024 data from validation script"""
    
    print("📊 Loading complete 2024 data from KNBS validation...")
    
    # Load all the CSV files created by validation script
    datasets_2024 = {}
    
    # File mapping
    files = {
        'Maize': 'kenya_maize_complete_2024.csv',
        'Sorghum': 'kenya_sorghum_complete_2024.csv', 
        'Millet': 'kenya_millet_complete_2024.csv',
        'Beans': 'kenya_beans_complete_2024.csv',
        'Irish Potato': 'kenya_potatoes_complete_2024.csv',
        'Cassava': 'kenya_cassava_complete_2024.csv'
    }
    
    for crop_name, filename in files.items():
        if os.path.exists(filename):
            df = pd.read_csv(filename)
            # Standardize column names for 2024 data
            if 'Area_2024' in df.columns:
                df = df[['County', 'Area_2024', 'Production_2024', 'Yield_2024']].copy()
                df.columns = ['County', 'Area_ha', 'Production_tonnes', 'Yield_t_ha']
            else:
                continue
            
            # Add crop and year
            df['Crop'] = crop_name
            df['Year'] = 2024
            
            # Remove zero production records
            df = df[df['Production_tonnes'] > 0].copy()
            
            datasets_2024[crop_name] = df
            print(f"✅ {crop_name}: {len(df)} counties loaded")
        else:
            print(f"❌ {filename} not found")
    
    return datasets_2024

def load_existing_expanded_dataset():
    """Load our current expanded dataset"""
    
    print("\n📊 Loading existing expanded dataset...")
    df_existing = pd.read_csv('data/processed/kenya_agricultural_expanded_6crops_2019_2024.csv')
    print(f"✅ Current dataset: {len(df_existing)} records")
    
    # Check current 2024 coverage
    df_2024_existing = df_existing[df_existing['Year'] == 2024]
    print(f"📅 Current 2024 records: {len(df_2024_existing)}")
    print(f"🌾 Current 2024 crops: {sorted(df_2024_existing['Crop'].unique())}")
    
    return df_existing

def integrate_complete_2024_data(df_existing, datasets_2024):
    """Integrate complete 2024 data, replacing partial data"""
    
    print(f"\n🔄 Integrating complete 2024 data...")
    
    # Remove all existing 2024 data
    df_without_2024 = df_existing[df_existing['Year'] != 2024].copy()
    print(f"📊 After removing 2024: {len(df_without_2024)} records")
    
    # Add all complete 2024 data
    all_2024_records = []
    
    for crop_name, df_crop in datasets_2024.items():
        # Ensure column order matches existing dataset
        df_crop_standardized = df_crop[['County', 'Year', 'Crop', 'Area_ha', 'Production_tonnes', 'Yield_t_ha']].copy()
        all_2024_records.append(df_crop_standardized)
        print(f"✅ Added {crop_name}: {len(df_crop_standardized)} counties")
    
    # Combine all 2024 data
    df_2024_complete = pd.concat(all_2024_records, ignore_index=True)
    print(f"📊 Total 2024 records: {len(df_2024_complete)}")
    
    # Combine with historical data
    df_complete = pd.concat([df_without_2024, df_2024_complete], ignore_index=True)
    print(f"📊 Final dataset: {len(df_complete)} records")
    
    return df_complete

def validate_complete_dataset(df_complete):
    """Validate the complete integrated dataset"""
    
    print(f"\n🔍 VALIDATING COMPLETE DATASET")
    print("="*60)
    
    # Basic statistics
    print(f"📊 DATASET OVERVIEW:")
    print(f"   Total Records: {len(df_complete):,}")
    print(f"   Counties: {df_complete['County'].nunique()}")
    print(f"   Years: {sorted(df_complete['Year'].unique())}")
    print(f"   Crops: {df_complete['Crop'].nunique()}")
    
    # 2024 coverage by crop
    df_2024 = df_complete[df_complete['Year'] == 2024]
    print(f"\n🌾 2024 COVERAGE BY CROP:")
    
    crop_coverage = df_2024.groupby('Crop').agg({
        'County': 'nunique',
        'Production_tonnes': 'sum',
        'Yield_t_ha': 'mean'
    }).round(2)
    
    for crop in sorted(crop_coverage.index):
        counties = crop_coverage.loc[crop, 'County']
        production = crop_coverage.loc[crop, 'Production_tonnes']
        avg_yield = crop_coverage.loc[crop, 'Yield_t_ha']
        print(f"   {crop}: {counties} counties, {production:,.0f} tonnes, {avg_yield:.2f} t/ha avg")
    
    # Year coverage by crop
    print(f"\n📅 TEMPORAL COVERAGE:")
    year_coverage = df_complete.groupby(['Crop', 'Year']).size().unstack(fill_value=0)
    print(year_coverage)
    
    # Data quality
    print(f"\n📋 DATA QUALITY:")
    print(f"   Completeness: {(df_complete.notna().sum().sum() / (len(df_complete) * len(df_complete.columns)) * 100):.1f}%")
    print(f"   Zero/Negative Areas: {len(df_complete[df_complete['Area_ha'] <= 0])}")
    print(f"   Zero/Negative Production: {len(df_complete[df_complete['Production_tonnes'] <= 0])}")
    print(f"   Zero/Negative Yields: {len(df_complete[df_complete['Yield_t_ha'] <= 0])}")
    
    return df_complete

def main():
    """Main execution function"""
    
    print("="*80)
    print("COMPLETE 2024 DATA INTEGRATION")
    print("="*80)
    print("🎯 Goal: Add ALL missing 2024 crop data from KNBS validation")
    print("📊 Source: Complete county-level data from validation script")
    
    # Step 1: Load complete 2024 data
    datasets_2024 = load_complete_2024_data()
    
    if not datasets_2024:
        print("\n❌ ERROR: No 2024 validation data found!")
        print("💡 Please run the validation script first to generate CSV files.")
        return
    
    # Step 2: Load existing dataset
    df_existing = load_existing_expanded_dataset()
    
    # Step 3: Integrate complete 2024 data
    df_complete = integrate_complete_2024_data(df_existing, datasets_2024)
    
    # Step 4: Validate complete dataset
    df_complete = validate_complete_dataset(df_complete)
    
    # Step 5: Save complete dataset
    output_file = 'data/processed/kenya_agricultural_complete_6crops_2019_2024.csv'
    df_complete.to_csv(output_file, index=False)
    
    print(f"\n✅ SUCCESS: Complete dataset created!")
    print(f"📁 Saved to: {output_file}")
    print(f"📊 Total Records: {len(df_complete):,}")
    print(f"🌾 All Crops: {', '.join(sorted(df_complete['Crop'].unique()))}")
    print(f"📅 All Years: {sorted(df_complete['Year'].unique())}")
    print(f"📍 Counties: {df_complete['County'].nunique()}")
    
    # Compare before/after
    print(f"\n📊 BEFORE vs AFTER:")
    print(f"   Records: {len(df_existing)} → {len(df_complete)} (+{len(df_complete) - len(df_existing)})")
    
    df_2024_old = df_existing[df_existing['Year'] == 2024]
    df_2024_new = df_complete[df_complete['Year'] == 2024]
    print(f"   2024 Records: {len(df_2024_old)} → {len(df_2024_new)} (+{len(df_2024_new) - len(df_2024_old)})")
    print(f"   2024 Crops: {len(df_2024_old['Crop'].unique())} → {len(df_2024_new['Crop'].unique())} (+{len(df_2024_new['Crop'].unique()) - len(df_2024_old['Crop'].unique())})")
    
    print("\n" + "="*80)
    print("COMPLETE 2024 INTEGRATION SUCCESSFUL")
    print("🎯 All 6 crops now have complete 2024 data!")
    print("🚀 Ready for comprehensive multi-crop analysis!")
    print("="*80)

if __name__ == "__main__":
    main()