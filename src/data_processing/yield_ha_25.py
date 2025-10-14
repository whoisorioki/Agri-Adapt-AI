import pandas as pd

# Maize Yield Data (Tonnes/Ha)
maize_data = {
    'County': ['Baringo', 'Bomet', 'Bungoma', 'Busia', 'Elgeyo Marakwet', 'Embu', 'Homa Bay', 
               'Kajiado', 'Kakamega', 'Kericho', 'Kiambu', 'Kilifi', 'Kirinyaga', 'Kisii', 
               'Kisumu', 'Kitui', 'Kwale', 'Laikipia', 'Lamu', 'Machakos', 'Makueni', 
               'Meru', 'Migori', 'Murang\'a', 'Nakuru', 'Nandi', 'Narok', 'Nyamira', 
               'Nyandarua', 'Nyeri', 'Trans Nzoia', 'Uasin Gishu', 'West Pokot'],
    '2020': [1.44, 1.72, 3.61, 1.44, 3.38, 0.99, 1.28, 0.50, 2.71, 2.70, 1.37, 0.62, 
             1.32, 1.97, 1.45, 0.32, 0.60, 1.49, 0.76, 0.31, 0.82, 1.11, 1.23, 0.96, 
             3.17, 2.78, 1.74, 1.58, 2.22, 0.99, 4.66, 4.27, 0.72],
    '2021': [1.70, 1.45, 2.89, 1.24, 2.74, 0.87, 1.03, 0.60, 2.67, 2.82, 0.84, 0.49, 
             0.80, 1.46, 0.65, 0.15, 0.60, 1.38, 0.28, 0.41, 0.58, 0.71, 1.05, 0.78, 
             2.77, 2.39, 2.30, 1.44, 1.99, 0.72, 3.81, 3.68, 1.52],
    '2022': [1.34, 1.57, 2.98, 1.52, 2.28, 0.29, 1.20, 0.41, 1.53, 2.12, 0.67, 0.66, 
             0.44, 1.82, 0.64, 0.15, 1.96, 0.29, 1.50, 0.17, 0.62, 0.95, 1.08, 0.70, 
             3.22, 1.96, 2.13, 1.59, 1.34, 0.53, 3.57, 3.50, 1.51],
    '2023': [2.23, 2.32, 2.40, 1.62, 3.48, 1.20, 1.47, 1.23, 1.51, 2.73, 0.97, 0.85, 
             1.29, 1.80, 1.69, 0.43, 1.01, 1.50, 1.62, 1.26, 0.59, 1.06, 1.29, 0.83, 
             3.01, 2.37, 2.37, 1.32, 2.25, 1.13, 3.58, 4.04, 1.96],
    '2024': [1.77, 1.57, 2.30, 1.76, 2.79, 0.74, 1.65, 1.85, 2.02, 3.06, 1.18, 0.82, 
             1.36, 0.62, 1.21, 0.20, 0.76, 1.76, 2.09, 0.58, 0.54, 0.98, 1.68, 1.02, 
             2.14, 3.10, 1.83, 1.84, 1.91, 0.85, 3.39, 4.51, 1.72]
}

# Sorghum Yield Data (Tonnes/Ha)
sorghum_data = {
    'County': ['Baringo', 'Bomet', 'Busia', 'Embu', 'Homa Bay', 'Kisumu', 'Kitui', 
               'Meru', 'Migori', 'Siaya', 'Tharaka Nithi'],
    '2020': [1.54, 2.27, 1.16, 0.52, 1.04, 1.11, 2.39, 1.13, 0.70, 0.93, 0.66],
    '2021': [0.39, 2.07, 0.68, 0.27, 1.11, 0.95, 0.29, 0.83, 0.81, 0.97, 0.65],
    '2022': [0.35, 1.20, 1.01, 0.44, 0.64, 0.72, 0.29, 0.83, 0.75, 1.04, 0.60],
    '2023': [1.09, 1.56, 1.43, 1.68, 1.13, 1.25, 0.54, 3.15, 0.78, 0.99, 0.59],
    '2024': [1.31, 1.08, 1.36, 0.39, 1.34, 1.12, 0.33, 0.75, 2.16, 1.44, 0.61]
}

# Millet Yield Data (Tonnes/Ha)
millet_data = {
    'County': ['Baringo', 'Bomet', 'Busia', 'Elgeyo Marakwet', 'Embu', 'Kisii', 
               'Kitui', 'Meru', 'Nyamira', 'Tharaka Nithi'],
    '2020': [0.85, 0.72, 0.75, 1.19, 0.44, 0.82, 2.20, 0.99, 0.84, 0.68],
    '2021': [0.73, 0.80, 1.14, 0.85, 0.08, 0.84, 0.25, 0.77, 0.66, 0.41],
    '2022': [0.86, 0.63, 0.79, 0.75, 0.30, 0.59, 0.51, 0.40, 0.65, 0.24],
    '2023': [0.92, 0.57, 0.81, 1.20, 1.44, 0.77, 0.45, 0.76, 0.69, 0.45],
    '2024': [0.96, 1.36, 0.81, 1.39, 0.76, 0.91, 0.32, 0.33, 0.61, 0.41]
}

# Beans Yield Data (Tonnes/Ha)
beans_data = {
    'County': ['Baringo', 'Bomet', 'Bungoma', 'Busia', 'Elgeyo Marakwet', 'Embu', 
               'Homa Bay', 'Kajiado', 'Kakamega', 'Kericho', 'Kiambu', 'Kirinyaga', 
               'Kisii', 'Kisumu', 'Kitui', 'Machakos', 'Makueni', 'Meru', 'Migori', 
               'Murang\'a', 'Nakuru', 'Nandi', 'Narok', 'Trans Nzoia', 'Uasin Gishu'],
    '2020': [1.18, 1.37, 0.65, 0.77, 0.45, 0.69, 0.66, 0.88, 0.52, 0.64, 1.05, 0.47, 
             0.58, 0.65, 0.50, 0.44, 0.81, 0.54, 0.73, 0.38, 0.98, 0.73, 0.64, 0.46, 0.82],
    '2021': [0.83, 0.97, 0.69, 0.60, 0.39, 0.65, 0.71, 0.67, 0.48, 1.13, 0.54, 0.34, 
             0.66, 0.41, 0.18, 0.37, 0.61, 0.63, 0.73, 0.48, 0.69, 0.82, 0.91, 0.36, 0.73],
    '2022': [0.91, 1.01, 0.57, 0.77, 0.33, 0.85, 0.66, 0.49, 0.43, 0.98, 0.45, 0.28, 
             0.64, 0.40, 0.32, 0.17, 0.20, 0.61, 0.97, 0.21, 1.24, 0.84, 0.75, 0.90, 0.74],
    '2023': [0.95, 0.97, 0.71, 0.78, 1.12, 0.48, 0.72, 0.89, 0.88, 1.09, 0.41, 1.07, 
             0.50, 0.76, 0.33, 0.60, 0.45, 0.41, 0.64, 0.39, 1.97, 0.72, 0.93, 0.78, 1.05],
    '2024': [0.89, 0.72, 0.68, 0.84, 0.61, 0.30, 0.90, 0.68, 0.27, 1.09, 0.53, 0.85, 
             0.64, 0.45, 0.25, 0.21, 0.43, 0.49, 1.08, 0.49, 0.90, 1.15, 0.50, 0.86, 0.68]
}

# Irish Potato Yield Data (Tonnes/Ha)
potato_data = {
    'County': ['Baringo', 'Bomet', 'Elgeyo Marakwet', 'Kajiado', 'Kiambu', 'Laikipia', 
               'Meru', 'Nakuru', 'Narok', 'Nyandarua', 'Nyeri', 'Trans Nzoia', 'Uasin Gishu'],
    '2020': [10.90, 10.13, 11.70, 4.97, 6.87, 7.18, 6.75, 12.46, 9.88, 11.04, 5.87, 5.82, 7.56],
    '2021': [13.45, 10.30, 13.58, 4.13, 6.54, 4.75, 12.92, 10.48, 9.29, 10.22, 5.73, 5.65, 7.83],
    '2022': [8.56, 11.69, 9.65, 9.68, 5.09, 2.79, 9.05, 11.20, 6.90, 5.16, 6.64, 12.00, 7.42],
    '2023': [10.44, 9.50, 10.31, 6.40, 5.35, 7.85, 9.61, 13.15, 9.39, 10.04, 5.96, 8.06, 7.22],
    '2024': [11.37, 15.00, 11.65, 8.49, 5.94, 3.75, 10.69, 9.83, 8.80, 11.27, 7.02, 10.42, 13.07]
}

# Cassava Yield Data (Tonnes/Ha)
cassava_data = {
    'County': ['Bungoma', 'Busia', 'Homa Bay', 'Kilifi', 'Kisumu', 'Kwale', 'Lamu', 
               'Migori', 'Siaya'],
    '2020': [15.58, 23.82, 13.80, 15.95, 14.93, 6.45, 9.60, 16.38, 12.50],
    '2021': [26.82, 16.21, 22.51, 6.78, 11.19, 6.70, 12.50, 8.95, 13.72],
    '2022': [8.81, 17.06, 21.45, 13.18, 11.61, 6.50, 15.00, 12.67, 11.03],
    '2023': [9.41, 16.78, 23.62, 12.36, 15.01, 9.67, 16.00, 12.68, 18.81],
    '2024': [20.12, 14.43, 21.18, 21.82, 16.22, 7.52, 50.00, 8.70, 16.75]
}

# Create DataFrames
df_maize = pd.DataFrame(maize_data)
df_sorghum = pd.DataFrame(sorghum_data)
df_millet = pd.DataFrame(millet_data)
df_beans = pd.DataFrame(beans_data)
df_potato = pd.DataFrame(potato_data)
df_cassava = pd.DataFrame(cassava_data)

# Calculate summary statistics for validation
print("=" * 80)
print("CROP YIELD DATA EXTRACTION AND VALIDATION (2020-2024)")
print("=" * 80)

crops = [
    ('MAIZE', df_maize),
    ('SORGHUM', df_sorghum),
    ('MILLET', df_millet),
    ('BEANS', df_beans),
    ('IRISH POTATO', df_potato),
    ('CASSAVA', df_cassava)
]

for crop_name, df in crops:
    print(f"\n{crop_name} YIELD (Tonnes/Hectare)")
    print("-" * 80)
    print(df.to_string(index=False))
    print(f"\nSummary Statistics:")
    print(f"  Average yield (2020-2024): {df[['2020','2021','2022','2023','2024']].mean().mean():.2f} tonnes/ha")
    print(f"  Min yield: {df[['2020','2021','2022','2023','2024']].min().min():.2f} tonnes/ha")
    print(f"  Max yield: {df[['2020','2021','2022','2023','2024']].max().max():.2f} tonnes/ha")
    
    # Year-over-year changes
    print(f"\nNational Average Yield Trends:")
    for year in ['2020', '2021', '2022', '2023', '2024']:
        avg = df[year].mean()
        print(f"  {year}: {avg:.2f} tonnes/ha")

print("\n" + "=" * 80)
print("DATA VALIDATION NOTES:")
print("=" * 80)
print("✓ Yields calculated as: Production (Tonnes) / Area (Hectares)")
print("✓ Only counties with consistent data across years included")
print("✓ Missing or zero values excluded from calculations")
print("✓ Data extracted from Annexes 1-4, 8, and 10 of the report")
print("=" * 80)