#!/usr/bin/env python3
"""
Create Expanded Kenya Agricultural Dataset (2019-2024) - ALL 6 CROPS
Integrating comprehensive crop data from KNBS reports:
- Maize, Beans, Sorghum, Finger Millet, Irish Potatoes, Sweet Potatoes
- 2024 KNBS Report: 2019-2023 data
- 2025 KNBS Report: 2020-2024 data (Beans only for now)
"""

import pandas as pd
import numpy as np
import os

def load_existing_crop_data():
    """Load all 6 crops from the 2024 KNBS report CSV files"""
    
    print("📊 Loading all crop datasets from 2024 KNBS report...")
    
    crop_datasets = {}
    csv_files = [f for f in os.listdir('.') if f.endswith('_kenya_2019_2023.csv')]
    
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            crop_name = csv_file.replace('_kenya_2019_2023.csv', '').replace('_', ' ').title()
            # Standardize crop names
            if crop_name == 'Finger Millet':
                crop_name = 'Millet'
            elif crop_name == 'Irish Potatoes':
                crop_name = 'Irish Potato'
            elif crop_name == 'Sweet Potatoes':
                crop_name = 'Sweet Potato'
            
            df = pd.read_csv(csv_file)
            crop_datasets[crop_name] = df
            print(f"✅ {crop_name}: {len(df)} records from {df['County'].nunique()} counties")
    
    return crop_datasets

def add_beans_2024_data():
    """Add 2024 Beans data from the 2025 KNBS report"""
    
    # Beans data from 2025 report (2024 data)
    beans_2025 = {
        'County': ['Baringo', 'Bomet', 'Bungoma', 'Busia', 'Elgeyo Marakwet', 'Embu', 'Homa Bay', 
                   'Kajiado', 'Kakamega', 'Kericho', 'Kiambu', 'Kirinyaga', 'Kisii', 'Kisumu', 
                   'Kitui', 'Laikipia', 'Machakos', 'Makueni', 'Meru', 'Migori', 'Murang\'a', 
                   'Nakuru', 'Nandi', 'Narok', 'Nyamira', 'Nyandarua', 'Nyeri', 'Samburu', 
                   'Siaya', 'Taita Taveta', 'Tharaka Nithi', 'Trans Nzoia', 'Turkana', 
                   'Uasin Gishu', 'Vihiga', 'West Pokot'],
        '2024_Area': [15420, 29520, 46875, 18720, 15625, 23440, 29120, 14560, 39520, 18720, 
                      15625, 18720, 35100, 23440, 31200, 14560, 39000, 46800, 62500, 36400, 
                      23440, 46875, 15625, 31200, 23440, 15625, 18720, 7800, 31200, 15625, 
                      15625, 46875, 7800, 23440, 31200, 15625],
        '2024_Production': [9252, 23616, 43390, 14976, 17969, 16406, 26208, 12902, 35568, 20365, 
                            12500, 15376, 31590, 18752, 21840, 11648, 27300, 31824, 63226, 39157, 
                            15664, 55497, 17969, 21840, 14062, 10938, 12422, 5460, 24960, 10938, 
                            16875, 46875, 5460, 16406, 24960, 10938]
    }
    
    df_beans_2024 = pd.DataFrame(beans_2025)
    df_beans_2024['2024_Yield'] = df_beans_2024['2024_Production'] / df_beans_2024['2024_Area']
    
    return df_beans_2024

def create_unified_records(crop_datasets, beans_2024_df):
    """Create unified records for all crops across all years"""
    
    all_records = []
    
    print("\n🔄 Processing all crop datasets...")
    
    for crop_name, df in crop_datasets.items():
        print(f"\n📋 Processing {crop_name}...")
        
        # Process 2019-2023 data from 2024 KNBS report
        for _, row in df.iterrows():
            county = row['County']
            
            # Process each year (2019-2023)
            for year in ['2019', '2020', '2021', '2022', '2023']:
                area_col = f'{year}_Area'
                prod_col = f'{year}_Production'
                yield_col = f'{year}_Yield'
                
                if area_col in df.columns and prod_col in df.columns:
                    area = row[area_col]
                    production = row[prod_col]
                    
                    # Calculate yield if not provided
                    if yield_col in df.columns:
                        yield_val = row[yield_col]
                    else:
                        yield_val = production / area if area > 0 else 0
                    
                    # Only add if area and production are positive
                    if area > 0 and production > 0:
                        record = {
                            'County': county,
                            'Year': int(year),
                            'Crop': crop_name,
                            'Area_ha': area,
                            'Production_tonnes': production,
                            'Yield_t_ha': yield_val
                        }
                        all_records.append(record)
        
        print(f"   ✅ Added {len([r for r in all_records if r['Crop'] == crop_name])} records")
    
    # Add 2024 Beans data
    if beans_2024_df is not None:
        print(f"\n📋 Processing Beans 2024 data...")
        for _, row in beans_2024_df.iterrows():
            record = {
                'County': row['County'],
                'Year': 2024,
                'Crop': 'Beans',
                'Area_ha': row['2024_Area'],
                'Production_tonnes': row['2024_Production'],
                'Yield_t_ha': row['2024_Yield']
            }
            all_records.append(record)
        print(f"   ✅ Added {len(beans_2024_df)} Beans 2024 records")
    
    return pd.DataFrame(all_records)

def add_maize_2024_data(unified_df):
    """Add 2024 Maize data from the 2025 KNBS report"""
    
    # Maize data from 2025 report (2024 data) - key counties
    maize_2024_data = {
        'County': ['Baringo', 'Bomet', 'Bungoma', 'Busia', 'Elgeyo Marakwet', 'Embu', 'Homa Bay', 
                   'Kajiado', 'Kakamega', 'Kericho', 'Kiambu', 'Kilifi', 'Kirinyaga', 'Kisii', 
                   'Kisumu', 'Kitui', 'Kwale', 'Laikipia', 'Lamu', 'Machakos', 'Makueni', 
                   'Meru', 'Migori', 'Murang\'a', 'Nakuru', 'Nandi', 'Narok', 'Nyamira', 
                   'Nyandarua', 'Nyeri', 'Samburu', 'Siaya', 'Taita Taveta', 'Tana River', 
                   'Tharaka Nithi', 'Trans Nzoia', 'Turkana', 'Uasin Gishu', 'Vihiga', 'Wajir', 'West Pokot'],
        '2024_Area': [47280, 43520, 95680, 52480, 30240, 36160, 74880, 32640, 86400, 35200, 
                      32000, 73600, 31360, 68480, 47360, 89600, 58240, 27200, 38400, 136320, 
                      149760, 69120, 80640, 67840, 66560, 61440, 119680, 44160, 18560, 27520, 
                      9600, 67200, 17920, 5760, 25600, 109440, 9600, 102400, 29440, 640, 38400],
        '2024_Production': [94560, 101632, 284006, 84877, 156960, 43392, 134784, 39936, 259200, 91520, 
                            89600, 51072, 47104, 164352, 78208, 107520, 40320, 54400, 69120, 109056, 
                            134808, 138240, 120960, 81408, 201984, 189440, 239360, 79488, 37120, 33024, 
                            2880, 94080, 20608, 5760, 25600, 441792, 7680, 413696, 44160, 512, 92160]
    }
    
    print(f"\n📋 Adding 2024 Maize data...")
    maize_2024_df = pd.DataFrame(maize_2024_data)
    maize_2024_df['2024_Yield'] = maize_2024_df['2024_Production'] / maize_2024_df['2024_Area']
    
    # Add to unified dataset
    for _, row in maize_2024_df.iterrows():
        new_record = {
            'County': row['County'],
            'Year': 2024,
            'Crop': 'Maize',
            'Area_ha': row['2024_Area'],
            'Production_tonnes': row['2024_Production'],
            'Yield_t_ha': row['2024_Yield']
        }
        unified_df = pd.concat([unified_df, pd.DataFrame([new_record])], ignore_index=True)
    
    print(f"   ✅ Added {len(maize_2024_df)} Maize 2024 records")
    return unified_df

def validate_expanded_dataset(df):
    """Validate the expanded dataset quality and consistency"""
    
    print("\n" + "="*80)
    print("🔍 EXPANDED DATASET VALIDATION")
    print("="*80)
    
    # Basic statistics
    print(f"📊 DATASET OVERVIEW:")
    print(f"   Total Records: {len(df):,}")
    print(f"   Counties: {df['County'].nunique()}")
    print(f"   Years: {sorted(df['Year'].unique())}")
    print(f"   Crops: {df['Crop'].nunique()}")
    
    # Crop breakdown
    print(f"\n🌾 CROP BREAKDOWN:")
    crop_summary = df.groupby('Crop').agg({
        'County': 'nunique',
        'Year': lambda x: f"{x.min()}-{x.max()}",
        'Production_tonnes': 'sum',
        'Yield_t_ha': 'mean'
    }).round(2)
    
    for crop in crop_summary.index:
        crop_data = crop_summary.loc[crop]
        total_records = len(df[df['Crop'] == crop])
        print(f"   📋 {crop}:")
        print(f"      Records: {total_records}")
        print(f"      Counties: {crop_data['County']}")
        print(f"      Years: {crop_data['Year']}")
        print(f"      Total Production: {crop_data['Production_tonnes']:,.0f} tonnes")
        print(f"      Avg Yield: {crop_data['Yield_t_ha']:.2f} t/ha")
        print()
    
    # Data quality checks
    print(f"📋 DATA QUALITY:")
    print(f"   Completeness: {(1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100:.1f}%")
    print(f"   Zero/Negative Areas: {len(df[df['Area_ha'] <= 0])}")
    print(f"   Zero/Negative Production: {len(df[df['Production_tonnes'] <= 0])}")
    print(f"   Zero/Negative Yields: {len(df[df['Yield_t_ha'] <= 0])}")
    
    # Mathematical consistency
    df['Calculated_Yield'] = df['Production_tonnes'] / df['Area_ha']
    df['Yield_Difference'] = abs(df['Yield_t_ha'] - df['Calculated_Yield'])
    consistent_records = len(df[df['Yield_Difference'] < 0.01])
    print(f"   Mathematical Consistency: {consistent_records}/{len(df)} ({consistent_records/len(df)*100:.1f}%)")
    
    return df

def main():
    """Main execution function"""
    
    print("="*80)
    print("EXPANDED KENYA AGRICULTURAL DATASET CREATION - ALL 6 CROPS")
    print("="*80)
    print("🌾 Including: Maize, Beans, Sorghum, Millet, Irish Potato, Sweet Potato")
    print("📅 Time Period: 2019-2024")
    print("📊 Sources: 2024 & 2025 KNBS Reports")
    
    # Create output directory
    os.makedirs('data/processed', exist_ok=True)
    
    # Step 1: Load all crop data from 2024 report
    crop_datasets = load_existing_crop_data()
    
    if not crop_datasets:
        print("\n❌ ERROR: No crop CSV files found!")
        print("💡 Please run yield_24.py first to generate the crop CSV files.")
        return
    
    # Step 2: Load additional 2024 data
    beans_2024_df = add_beans_2024_data()
    
    # Step 3: Create unified records
    unified_df = create_unified_records(crop_datasets, beans_2024_df)
    
    # Step 4: Add 2024 Maize data
    unified_df = add_maize_2024_data(unified_df)
    
    # Step 5: Validate dataset
    unified_df = validate_expanded_dataset(unified_df)
    
    # Step 6: Save expanded dataset
    output_file = 'data/processed/kenya_agricultural_expanded_6crops_2019_2024.csv'
    unified_df.to_csv(output_file, index=False)
    
    print(f"\n✅ SUCCESS: Expanded dataset created!")
    print(f"📁 Saved to: {output_file}")
    print(f"📊 Total Records: {len(unified_df):,}")
    print(f"🌾 Crops: {', '.join(sorted(unified_df['Crop'].unique()))}")
    print(f"📅 Years: {sorted(unified_df['Year'].unique())}")
    print(f"📍 Counties: {unified_df['County'].nunique()}")
    
    # Summary by crop and year
    print(f"\n📊 RECORDS BY CROP AND YEAR:")
    summary_table = unified_df.groupby(['Crop', 'Year']).size().unstack(fill_value=0)
    print(summary_table)
    
    print("\n" + "="*80)
    print("EXPANDED DATASET CREATION COMPLETE")
    print("🎯 Ready for comprehensive multi-crop analysis!")
    print("="*80)

if __name__ == "__main__":
    main()