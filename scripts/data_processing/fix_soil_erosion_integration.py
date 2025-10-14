#!/usr/bin/env python3
"""
Quick Fix: Soil Erosion Data Integration
=====================================
Fix the county name mismatch and properly integrate GLOSEM 1.3 soil erosion data
"""

import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import numpy as np
from pathlib import Path

def fix_soil_erosion_integration():
    """Fix the soil erosion integration issue"""
    print("🔧 FIXING SOIL EROSION INTEGRATION")
    print("="*50)
    
    # Load master dataset
    master_df = pd.read_csv("data/integrated/kenya_master_agricultural_dataset_v2.csv")
    print(f"✅ Loaded master dataset: {master_df.shape[0]} records")
    
    # Load boundaries with correct column mapping
    counties_gdf = gpd.read_file("data/processed/geo/kenya/kenya_admin1_boundaries.json")
    print(f"✅ Loaded county boundaries: {len(counties_gdf)} counties")
    
    # Create county name mapping for boundaries
    boundary_mapping = {
        'Elgeyo-Marakwet': 'Elgeyo Marakwet',
        'Murang\'a': 'Murang\'a',  # Handle apostrophe
        'Taita-Taveta': 'Taita Taveta'
    }
    
    # Process GLOSEM data
    glosem_path = "data/raw/geo/kenya_soil_erosion_2019.tif"
    county_erosion = []
    
    print("🌍 Processing GLOSEM 1.3 soil erosion data...")
    
    with rasterio.open(glosem_path) as src:
        for idx, county in counties_gdf.iterrows():
            try:
                # Get county name and standardize it
                boundary_county_name = county['admin1_name']
                standardized_name = boundary_mapping.get(boundary_county_name, boundary_county_name)
                
                # Extract county geometry
                geom = [county.geometry.__geo_interface__]
                
                # Mask raster to county boundary
                out_image, out_transform = mask(src, geom, crop=True, nodata=src.nodata)
                
                # Calculate statistics (excluding nodata)
                county_data = out_image[0]
                valid_data = county_data[county_data != src.nodata]
                
                if len(valid_data) > 0:
                    erosion_stats = {
                        'County': standardized_name,
                        'soil_erosion_mean': float(np.mean(valid_data)),
                        'soil_erosion_median': float(np.median(valid_data)),
                        'soil_erosion_std': float(np.std(valid_data)),
                        'erosion_risk_category': classify_erosion_risk(float(np.mean(valid_data)))
                    }
                    county_erosion.append(erosion_stats)
                    print(f"   ✅ {standardized_name}: {np.mean(valid_data):.2f} Mg/ha/yr")
                    
            except Exception as e:
                print(f"   ⚠️ Error processing {boundary_county_name}: {e}")
                
    # Create erosion dataframe
    erosion_df = pd.DataFrame(county_erosion)
    print(f"✅ Processed {len(erosion_df)} counties for soil erosion")
    
    # Merge with master dataset (drop existing empty soil columns first)
    master_df = master_df.drop(columns=['soil_erosion_mean', 'soil_erosion_median'], errors='ignore')
    
    # Merge erosion data
    master_df = master_df.merge(
        erosion_df[['County', 'soil_erosion_mean', 'soil_erosion_median', 'erosion_risk_category']], 
        on='County', 
        how='left'
    )
    
    # Check merge success
    erosion_coverage = master_df['soil_erosion_mean'].notna().sum()
    print(f"✅ Soil erosion data merged: {erosion_coverage}/{len(master_df)} records")
    
    # Save corrected dataset
    output_path = "data/integrated/kenya_master_agricultural_dataset_v2_corrected.csv"
    master_df.to_csv(output_path, index=False)
    print(f"✅ Corrected dataset saved: {output_path}")
    
    # Generate summary
    print(f"\n📊 SOIL EROSION SUMMARY:")
    print(f"   Counties processed: {len(erosion_df)}/47")
    print(f"   Mean erosion range: {erosion_df['soil_erosion_mean'].min():.2f} - {erosion_df['soil_erosion_mean'].max():.2f} Mg/ha/yr")
    print(f"   High risk counties: {(erosion_df['erosion_risk_category'] == 'High').sum()}")
    print(f"   Medium risk counties: {(erosion_df['erosion_risk_category'] == 'Medium').sum()}")
    print(f"   Low risk counties: {(erosion_df['erosion_risk_category'] == 'Low').sum()}")
    
    return master_df, erosion_df

def classify_erosion_risk(erosion_rate):
    """Classify erosion risk based on GLOSEM values"""
    if erosion_rate > 50:
        return 'High'
    elif erosion_rate > 20:
        return 'Medium'
    else:
        return 'Low'

if __name__ == "__main__":
    master_df, erosion_df = fix_soil_erosion_integration()
    print("\n🎯 SOIL EROSION INTEGRATION FIXED!")