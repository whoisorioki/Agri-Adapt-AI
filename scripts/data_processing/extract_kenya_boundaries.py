#!/usr/bin/env python3
"""
Extract Kenya-specific boundaries from Atlas boundaries and create separate JSON files
"""

import json
import os
from pathlib import Path

def extract_kenya_boundaries():
    """Extract Kenya boundaries from the Atlas admin files"""
    
    print("=" * 60)
    print("EXTRACTING KENYA BOUNDARIES")
    print("=" * 60)
    
    # Define paths
    geo_dir = Path("data/raw/geo")
    output_dir = Path("data/processed/geo/kenya")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Admin levels to process
    admin_levels = ["admin0", "admin1", "admin2"]
    
    for level in admin_levels:
        input_file = geo_dir / f"Atlas-boundaries_{level}.json"
        
        if not input_file.exists():
            print(f"⚠️  {input_file} not found, skipping...")
            continue
            
        print(f"\n📍 Processing {level.upper()} boundaries...")
        
        # Load the data
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract Kenya features
        kenya_features = []
        
        if isinstance(data, dict) and 'features' in data:
            # GeoJSON format
            for feature in data['features']:
                if isinstance(feature, dict) and 'properties' in feature:
                    props = feature['properties']
                    
                    # Check for Kenya in various property fields
                    kenya_indicators = [
                        props.get('admin0_name', '').lower() == 'kenya',
                        props.get('admin_name', '').lower() == 'kenya',
                        props.get('country', '').lower() == 'kenya',
                        props.get('iso3', '').upper() == 'KEN',
                        'kenya' in str(props).lower()
                    ]
                    
                    if any(kenya_indicators):
                        kenya_features.append(feature)
                        
                        # Print feature info
                        admin_name = props.get('admin_name', 'N/A')
                        if level == 'admin0':
                            print(f"  ✅ Found Kenya country boundary")
                        elif level == 'admin1':
                            print(f"  ✅ Found county: {admin_name}")
                        elif level == 'admin2':
                            print(f"  ✅ Found sub-county: {admin_name}")
        
        elif isinstance(data, list):
            # Array of features
            for feature in data:
                if isinstance(feature, dict) and 'properties' in feature:
                    props = feature['properties']
                    
                    kenya_indicators = [
                        props.get('admin0_name', '').lower() == 'kenya',
                        props.get('admin_name', '').lower() == 'kenya',
                        props.get('country', '').lower() == 'kenya',
                        props.get('iso3', '').upper() == 'KEN',
                        'kenya' in str(props).lower()
                    ]
                    
                    if any(kenya_indicators):
                        kenya_features.append(feature)
        
        # Create Kenya-specific GeoJSON
        if kenya_features:
            kenya_geojson = {
                "type": "FeatureCollection",
                "features": kenya_features
            }
            
            # Save Kenya boundaries
            output_file = output_dir / f"kenya_{level}_boundaries.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(kenya_geojson, f, indent=2, ensure_ascii=False)
            
            print(f"  💾 Saved {len(kenya_features)} features to {output_file}")
            
            # Generate summary
            if level == 'admin0':
                print(f"  📊 Summary: Kenya country boundary extracted")
            elif level == 'admin1':
                print(f"  📊 Summary: {len(kenya_features)} counties extracted")
            elif level == 'admin2':
                print(f"  📊 Summary: {len(kenya_features)} sub-counties extracted")
                
        else:
            print(f"  ❌ No Kenya features found in {level}")
    
    # Create a combined summary file
    summary_file = output_dir / "extraction_summary.json"
    summary = {
        "extraction_date": "2025-10-09",
        "source_files": [
            "Atlas-boundaries_admin0.json",
            "Atlas-boundaries_admin1.json", 
            "Atlas-boundaries_admin2.json"
        ],
        "output_files": [
            "kenya_admin0_boundaries.json",
            "kenya_admin1_boundaries.json",
            "kenya_admin2_boundaries.json"
        ],
        "description": "Kenya-specific administrative boundaries extracted from Atlas datasets"
    }
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📋 Summary saved to {summary_file}")
    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)

def inspect_boundary_structure():
    """Inspect the structure of boundary files to understand the format"""
    
    print("\n" + "=" * 60)
    print("INSPECTING BOUNDARY STRUCTURE")
    print("=" * 60)
    
    geo_dir = Path("data/raw/geo")
    
    for admin_file in ["admin0", "admin1", "admin2"]:
        file_path = geo_dir / f"Atlas-boundaries_{admin_file}.json"
        
        if not file_path.exists():
            continue
            
        print(f"\n📄 Analyzing {admin_file.upper()} structure...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and 'features' in data:
            features = data['features']
            print(f"  • Type: GeoJSON FeatureCollection")
            print(f"  • Total features: {len(features)}")
            
            # Inspect first feature
            if features:
                first_feature = features[0]
                if 'properties' in first_feature:
                    props = first_feature['properties']
                    print(f"  • Sample properties: {list(props.keys())}")
                    
                    # Look for Kenya
                    kenya_count = 0
                    sample_kenya = None
                    for feature in features[:10]:  # Check first 10
                        props = feature.get('properties', {})
                        if any([
                            'kenya' in str(props).lower(),
                            props.get('iso3', '').upper() == 'KEN'
                        ]):
                            kenya_count += 1
                            if not sample_kenya:
                                sample_kenya = props
                    
                    if sample_kenya:
                        print(f"  • Kenya found! Sample properties: {sample_kenya}")
                    else:
                        print(f"  • Kenya check: Not found in first 10 features")
        
        elif isinstance(data, list):
            print(f"  • Type: Array of features")
            print(f"  • Total features: {len(data)}")
        else:
            print(f"  • Type: Unknown structure")

if __name__ == "__main__":
    # First inspect the structure
    inspect_boundary_structure()
    
    # Then extract Kenya boundaries
    extract_kenya_boundaries()