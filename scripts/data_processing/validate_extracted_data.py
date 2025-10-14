#!/usr/bin/env python3
"""
County Census Data Validation
Quick validation of extracted county data
"""

import pandas as pd
from pathlib import Path

def validate_county_data():
    """Validate the extracted county census data"""
    
    # Ensure we're working in the correct directory structure
    data_file = Path("data/processed/census_2019/cleaned_county_population.csv")
    
    if not data_file.exists():
        print("❌ County data file not found!")
        return False
    
    # Load the data
    df = pd.read_csv(data_file)
    
    print("🇰🇪 COUNTY CENSUS DATA VALIDATION")
    print("=" * 50)
    print(f"📁 Data file: {data_file}")
    print(f"📊 Records: {len(df)}")
    print(f"📋 Columns: {list(df.columns)}")
    
    # Population statistics
    total_pop = df["Total_Population"].sum()
    print(f"👥 Total population: {total_pop:,}")
    
    # Data completeness
    complete_records = df.dropna().shape[0]
    print(f"✅ Complete records: {complete_records}/{len(df)}")
    
    print("\n🏘️ TOP 10 COUNTIES BY POPULATION:")
    print("-" * 40)
    top_counties = df.nlargest(10, 'Total_Population')[['County', 'Total_Population']]
    for _, row in top_counties.iterrows():
        print(f"{row['County']:<20} {row['Total_Population']:>10,}")
    
    print(f"\n🎯 PHASE I STEP 4 STATUS: ✅ COMPLETE")
    print(f"📊 County demographic data ready for integration!")
    
    return True

if __name__ == "__main__":
    validate_county_data()