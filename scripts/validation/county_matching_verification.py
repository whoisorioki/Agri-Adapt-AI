#!/usr/bin/env python3
"""
County Matching Verification
Verify that our agricultural dataset counties match the Atlas boundary counties
"""

import pandas as pd
import numpy as np
from pathlib import Path

def verify_county_matching():
    """Verify county names match between agricultural data and boundary data"""
    
    print("🔍 VERIFYING COUNTY MATCHING BETWEEN DATASETS...")
    
    # Load agricultural dataset counties
    agri_file = Path("data/processed/kenya_agricultural_complete_6crops_2019_2024.csv")
    agri_data = pd.read_csv(agri_file)
    agri_counties = set(agri_data['County'].unique())
    
    print(f"   📊 Agricultural dataset counties: {len(agri_counties)}")
    print(f"   📝 Counties: {sorted(list(agri_counties))}")
    
    # Load boundary dataset counties  
    boundary_file = Path("data/analysis/kenya_administrative_units_catalog.csv")
    boundary_data = pd.read_csv(boundary_file)
    
    # Filter for admin1 (county level)
    admin1_data = boundary_data[boundary_data['Administrative_Level'] == 'admin1']
    boundary_counties = set(admin1_data['Name_admin1_name'].unique())
    
    print(f"\n   🗺️ Boundary dataset counties: {len(boundary_counties)}")
    print(f"   📝 Counties: {sorted(list(boundary_counties))}")
    
    # Check matches
    exact_matches = agri_counties.intersection(boundary_counties)
    agri_only = agri_counties - boundary_counties
    boundary_only = boundary_counties - agri_counties
    
    print(f"\n   ✅ Exact matches: {len(exact_matches)}")
    if exact_matches:
        print(f"      {sorted(list(exact_matches))}")
    
    print(f"\n   ⚠️ Agricultural only: {len(agri_only)}")
    if agri_only:
        print(f"      {sorted(list(agri_only))}")
    
    print(f"\n   ⚠️ Boundary only: {len(boundary_only)}")
    if boundary_only:
        print(f"      {sorted(list(boundary_only))}")
    
    # Calculate match percentage
    match_percentage = len(exact_matches) / len(agri_counties) * 100
    print(f"\n   📊 Match percentage: {match_percentage:.1f}%")
    
    # Try fuzzy matching for mismatches
    if agri_only or boundary_only:
        print(f"\n🔧 ATTEMPTING FUZZY MATCHING...")
        
        potential_matches = []
        for agri_county in agri_only:
            for boundary_county in boundary_only:
                # Simple fuzzy matching
                if agri_county.lower() in boundary_county.lower() or boundary_county.lower() in agri_county.lower():
                    potential_matches.append((agri_county, boundary_county))
                # Check for common variations
                elif agri_county.replace('-', ' ').lower() == boundary_county.replace('-', ' ').lower():
                    potential_matches.append((agri_county, boundary_county))
        
        if potential_matches:
            print(f"   🎯 Potential matches found:")
            for agri, boundary in potential_matches:
                print(f"      '{agri}' ↔ '{boundary}'")
        else:
            print(f"   ❌ No obvious fuzzy matches found")
    
    return {
        'agri_counties': agri_counties,
        'boundary_counties': boundary_counties,
        'exact_matches': exact_matches,
        'agri_only': agri_only,
        'boundary_only': boundary_only,
        'match_percentage': match_percentage
    }

def main():
    print("🇰🇪 COUNTY MATCHING VERIFICATION")
    print("=" * 50)
    
    results = verify_county_matching()
    
    print("\n" + "=" * 50)
    print("VERIFICATION COMPLETE")
    print("=" * 50)
    print(f"✅ Counties matched: {len(results['exact_matches'])}/{len(results['agri_counties'])}")
    print(f"📊 Match rate: {results['match_percentage']:.1f}%")
    
    if results['match_percentage'] >= 90:
        print("🎯 EXCELLENT: High county matching rate")
    elif results['match_percentage'] >= 75:
        print("✅ GOOD: Acceptable county matching rate")
    else:
        print("⚠️ NEEDS ATTENTION: Low county matching rate")

if __name__ == "__main__":
    main()