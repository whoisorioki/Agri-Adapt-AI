#!/usr/bin/env python3
"""
Incorporate Missing 2024 Data from yield_25.py
Add the missing crops and counties to our expanded dataset
"""

import pandas as pd
import os

def load_yield_25_data():
    """Load data from yield_25.py generated CSV files"""
    
    print("📊 Loading 2024 data from yield_25.py CSV files...")
    
    # Check if CSV files exist
    csv_files = {
        'Maize': 'kenya_maize_data_2024.csv',
        'Beans': 'kenya_beans_data_2024.csv', 
        'Irish Potato': 'kenya_potatoes_data_2024.csv',
        'Cassava': 'kenya_cassava_data_2024.csv',
        'Sorghum': 'kenya_sorghum_data_2024.csv',
        'Millet': 'kenya_millet_data_2024.csv'
    }
    
    yield_25_data = {}
    
    for crop, filename in csv_files.items():
        if os.path.exists(filename):
            df = pd.read_csv(filename)
            # Standardize to our format
            df_clean = pd.DataFrame({
                'County': df['County'],
                'Year': 2024,
                'Crop': crop,
                'Area_ha': df['Area_2024'],
                'Production_tonnes': df['Production_2024'],
                'Yield_t_ha': df['Yield_2024']
            })
            
            yield_25_data[crop] = df_clean
            print(f"✅ {crop}: {len(df_clean)} counties")
        else:
            print(f"❌ {filename} not found")
    
    return yield_25_data

def incorporate_missing_data():
    """Incorporate missing 2024 data into our expanded dataset"""
    
    print("\n🔄 Incorporating missing 2024 data...")
    
    # Load our current dataset
    current_df = pd.read_csv('data/processed/kenya_agricultural_expanded_6crops_2019_2024.csv')
    print(f"📊 Current dataset: {len(current_df)} records")
    
    # Load yield_25 data
    yield_25_data = load_yield_25_data()
    
    # Get current 2024 data
    current_2024 = current_df[current_df['Year'] == 2024].copy()
    print(f"📅 Current 2024 records: {len(current_2024)}")
    
    # Remove current 2024 data (we'll replace with complete data)
    df_without_2024 = current_df[current_df['Year'] != 2024].copy()
    print(f"📊 Without 2024: {len(df_without_2024)} records")
    
    # Add all 2024 data from yield_25
    all_2024_records = []
    
    for crop, df_crop in yield_25_data.items():
        all_2024_records.append(df_crop)
        print(f"✅ Adding {crop}: {len(df_crop)} counties")
    
    # Combine all 2024 data
    if all_2024_records:
        df_2024_complete = pd.concat(all_2024_records, ignore_index=True)
        print(f"📊 Total 2024 records: {len(df_2024_complete)}")
        
        # Combine with historical data
        df_final = pd.concat([df_without_2024, df_2024_complete], ignore_index=True)
        print(f"📊 Final dataset: {len(df_final)} records")
        
        return df_final
    else:
        print("❌ No yield_25 data found!")
        return current_df

def validate_incorporation(df_final, df_original):
    """Validate the incorporation results"""
    
    print(f"\n🔍 VALIDATION RESULTS")
    print("="*60)
    
    # Compare before/after
    original_2024 = df_original[df_original['Year'] == 2024]
    final_2024 = df_final[df_final['Year'] == 2024]
    
    print(f"BEFORE INCORPORATION:")
    print(f"  Total Records: {len(df_original)}")
    print(f"  2024 Records: {len(original_2024)}")
    print(f"  2024 Crops: {sorted(original_2024['Crop'].unique())}")
    
    print(f"\nAFTER INCORPORATION:")
    print(f"  Total Records: {len(df_final)}")
    print(f"  2024 Records: {len(final_2024)}")
    print(f"  2024 Crops: {sorted(final_2024['Crop'].unique())}")
    
    # 2024 breakdown
    print(f"\n2024 CROP BREAKDOWN:")
    crop_summary = final_2024.groupby('Crop').agg({
        'County': 'nunique',
        'Production_tonnes': 'sum'
    })
    
    for crop in sorted(crop_summary.index):
        counties = crop_summary.loc[crop, 'County']
        production = crop_summary.loc[crop, 'Production_tonnes']
        print(f"  {crop}: {counties} counties, {production:,.0f} tonnes")
    
    # Validation against expected
    expected_2024 = {
        'Maize': 37, 'Beans': 26, 'Irish Potato': 17, 
        'Cassava': 16, 'Sorghum': 11, 'Millet': 10
    }
    
    print(f"\nVALIDATION vs YIELD_25 DATA:")
    for crop, expected_counties in expected_2024.items():
        if crop in crop_summary.index:
            actual_counties = crop_summary.loc[crop, 'County']
            status = "✅ COMPLETE" if actual_counties >= expected_counties else f"⚠️ PARTIAL ({actual_counties}/{expected_counties})"
            print(f"  {crop}: {status}")
        else:
            print(f"  {crop}: ❌ MISSING")
    
    return df_final

def main():
    """Main execution function"""
    
    print("="*80)
    print("INCORPORATE MISSING 2024 DATA FROM YIELD_25.PY")
    print("="*80)
    print("🎯 Goal: Add missing 2024 crops and complete county coverage")
    
    # Load original dataset
    original_df = pd.read_csv('data/processed/kenya_agricultural_expanded_6crops_2019_2024.csv')
    
    # Incorporate missing data
    final_df = incorporate_missing_data()
    
    # Validate results
    final_df = validate_incorporation(final_df, original_df)
    
    # Save updated dataset
    output_file = 'data/processed/kenya_agricultural_complete_6crops_2019_2024.csv'
    final_df.to_csv(output_file, index=False)
    
    print(f"\n✅ SUCCESS: Updated dataset saved!")
    print(f"📁 File: {output_file}")
    print(f"📊 Records: {len(original_df)} → {len(final_df)} (+{len(final_df) - len(original_df)})")
    
    # Show improvement summary
    original_2024 = original_df[original_df['Year'] == 2024]
    final_2024 = final_df[final_df['Year'] == 2024]
    
    print(f"\n🎯 2024 DATA IMPROVEMENT:")
    print(f"   Records: {len(original_2024)} → {len(final_2024)} (+{len(final_2024) - len(original_2024)})")
    print(f"   Crops: {len(original_2024['Crop'].unique())} → {len(final_2024['Crop'].unique())} (+{len(final_2024['Crop'].unique()) - len(original_2024['Crop'].unique())})")
    
    added_crops = set(final_2024['Crop'].unique()) - set(original_2024['Crop'].unique())
    if added_crops:
        print(f"   Added Crops: {list(added_crops)}")
    
    print("\n" + "="*80)
    print("DATA INCORPORATION COMPLETE")
    print("✅ All available 2024 data from yield_25.py incorporated!")
    print("="*80)

if __name__ == "__main__":
    main()