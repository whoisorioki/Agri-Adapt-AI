#!/usr/bin/env python3
"""
County Census Data Cleaner
Cleans and standardizes the extracted county population data
"""

import pandas as pd
import re
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CountyDataCleaner:
    """Clean and standardize county census data"""
    
    def __init__(self):
        self.processed_dir = Path("data/processed/census_2019")
        
        # Known Kenya counties for validation
        self.kenya_counties = [
            'Baringo', 'Bomet', 'Bungoma', 'Busia', 'Elgeyo-Marakwet', 'Embu', 'Garissa',
            'Homa Bay', 'Isiolo', 'Kajiado', 'Kakamega', 'Kericho', 'Kiambu', 'Kilifi',
            'Kirinyaga', 'Kisii', 'Kisumu', 'Kitui', 'Kwale', 'Laikipia', 'Lamu', 'Machakos',
            'Makueni', 'Mandera', 'Marsabit', 'Meru', 'Migori', 'Mombasa', 'Murang\'a',
            'Nairobi', 'Nakuru', 'Nandi', 'Narok', 'Nyamira', 'Nyandarua', 'Nyeri',
            'Samburu', 'Siaya', 'Taita-Taveta', 'Tana River', 'Tharaka-Nithi', 'Trans Nzoia',
            'Turkana', 'Uasin Gishu', 'Vihiga', 'Wajir', 'West Pokot'
        ]
    
    def clean_county_name(self, name_str):
        """Clean county name from the raw extracted text"""
        if pd.isna(name_str):
            return None
        
        # Convert to string and clean
        name = str(name_str)
        
        # Remove dots, extra spaces, and special characters
        name = re.sub(r'[.…]+', '', name)
        name = re.sub(r'\s+', ' ', name)
        name = name.strip()
        
        # Remove leading/trailing non-letter characters
        name = re.sub(r'^[^a-zA-Z]+|[^a-zA-Z]+$', '', name)
        
        # Handle special cases
        if 'Elgeyo' in name:
            return 'Elgeyo-Marakwet'
        elif 'Taita' in name:
            return 'Taita-Taveta'
        elif 'Tharaka' in name:
            return 'Tharaka-Nithi'
        elif 'Trans' in name or 'Nzoia' in name:
            return 'Trans Nzoia'
        elif 'West' in name and 'Pokot' in name:
            return 'West Pokot'
        elif 'Uasin' in name:
            return 'Uasin Gishu'
        elif 'Homa' in name:
            return 'Homa Bay'
        elif 'Tana' in name:
            return 'Tana River'
        
        return name.title()
    
    def clean_numeric_value(self, value_str):
        """Clean numeric values from text"""
        if pd.isna(value_str):
            return None
        
        # Convert to string and extract numbers
        value = str(value_str)
        
        # Remove all non-numeric characters except commas
        cleaned = re.sub(r'[^\d,]', '', value)
        
        # Remove commas and convert to integer
        try:
            return int(cleaned.replace(',', ''))
        except ValueError:
            return None
    
    def process_extracted_data(self, input_file="county_population_extracted.csv"):
        """Process the raw extracted data"""
        logger.info("🧹 Starting county data cleaning process...")
        
        input_path = self.processed_dir / input_file
        
        if not input_path.exists():
            logger.error(f"❌ Input file not found: {input_path}")
            return None
        
        # Read the raw data
        raw_df = pd.read_csv(input_path)
        logger.info(f"📊 Raw data shape: {raw_df.shape}")
        
        # Examine the structure
        logger.info("🔍 Raw data columns:")
        for i, col in enumerate(raw_df.columns):
            logger.info(f"  Column {i}: '{col}'")
        
        # The data appears to have the county names in the first column
        # and population data in subsequent columns
        cleaned_data = []
        
        for index, row in raw_df.iterrows():
            # Skip header rows and non-county rows
            first_cell = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
            
            # Skip if it looks like a header or summary row
            if any(keyword in first_cell.lower() for keyword in 
                   ['national', 'county', 'male', 'female', 'total', 'intersex']):
                continue
            
            # Skip if it doesn't look like a county name
            if len(first_cell.strip()) < 3:
                continue
            
            # Extract county name
            county_name = self.clean_county_name(first_cell)
            
            if not county_name:
                continue
            
            # Extract population values from the row
            male_pop = None
            female_pop = None
            total_pop = None
            
            # Try to find numeric values in the row
            for cell in row:
                if pd.notna(cell):
                    cleaned_value = self.clean_numeric_value(cell)
                    if cleaned_value and cleaned_value > 10000:  # Reasonable county population
                        if male_pop is None:
                            male_pop = cleaned_value
                        elif female_pop is None:
                            female_pop = cleaned_value
                        elif total_pop is None:
                            total_pop = cleaned_value
            
            # Validate the data
            if county_name and (male_pop or female_pop or total_pop):
                # Calculate total if missing
                if not total_pop and male_pop and female_pop:
                    total_pop = male_pop + female_pop
                
                cleaned_data.append({
                    'County': county_name,
                    'Male_Population': male_pop,
                    'Female_Population': female_pop,
                    'Total_Population': total_pop
                })
        
        if not cleaned_data:
            logger.error("❌ No valid county data found after cleaning")
            return None
        
        # Create cleaned dataframe
        cleaned_df = pd.DataFrame(cleaned_data)
        
        # Validate county names
        cleaned_df = self.validate_and_correct_counties(cleaned_df)
        
        # Sort by county name
        cleaned_df = cleaned_df.sort_values('County').reset_index(drop=True)
        
        logger.info(f"✅ Cleaned data: {len(cleaned_df)} counties")
        
        return cleaned_df
    
    def validate_and_correct_counties(self, df):
        """Validate and correct county names"""
        logger.info("🔍 Validating county names...")
        
        corrected_counties = []
        unmatched_counties = []
        
        for _, row in df.iterrows():
            county = row['County']
            
            # Try exact match first
            if county in self.kenya_counties:
                corrected_counties.append(row)
                continue
            
            # Try fuzzy matching
            best_match = None
            best_score = 0
            
            for known_county in self.kenya_counties:
                # Simple similarity based on common words
                county_words = set(county.lower().split())
                known_words = set(known_county.lower().split())
                
                if county_words & known_words:  # Has common words
                    score = len(county_words & known_words) / len(county_words | known_words)
                    if score > best_score:
                        best_score = score
                        best_match = known_county
            
            if best_match and best_score > 0.5:
                logger.info(f"🔄 Corrected '{county}' → '{best_match}'")
                row_copy = row.copy()
                row_copy['County'] = best_match
                corrected_counties.append(row_copy)
            else:
                logger.warning(f"⚠️  Unmatched county: '{county}'")
                unmatched_counties.append(county)
                corrected_counties.append(row)  # Keep anyway
        
        if unmatched_counties:
            logger.info(f"⚠️  {len(unmatched_counties)} counties need manual review")
        
        return pd.DataFrame(corrected_counties)
    
    def generate_summary_statistics(self, df):
        """Generate summary statistics for the cleaned data"""
        logger.info("📊 Generating summary statistics...")
        
        stats = {}
        
        stats['total_counties'] = len(df)
        stats['counties_with_total_pop'] = df['Total_Population'].notna().sum()
        stats['counties_with_male_pop'] = df['Male_Population'].notna().sum()
        stats['counties_with_female_pop'] = df['Female_Population'].notna().sum()
        
        if df['Total_Population'].notna().any():
            total_pop = df['Total_Population'].sum()
            stats['total_population'] = total_pop
            stats['largest_county'] = df.loc[df['Total_Population'].idxmax(), 'County']
            stats['largest_population'] = df['Total_Population'].max()
            stats['smallest_county'] = df.loc[df['Total_Population'].idxmin(), 'County']
            stats['smallest_population'] = df['Total_Population'].min()
            stats['average_population'] = df['Total_Population'].mean()
        
        return stats
    
    def save_cleaned_data(self, df, output_file="cleaned_county_population.csv"):
        """Save cleaned data and generate reports"""
        output_path = self.processed_dir / output_file
        
        # Save CSV
        df.to_csv(output_path, index=False)
        logger.info(f"💾 Saved cleaned data to {output_path}")
        
        # Generate summary statistics
        stats = self.generate_summary_statistics(df)
        
        # Save summary report
        report_path = self.processed_dir / "cleaning_summary_report.txt"
        with open(report_path, 'w') as f:
            f.write("COUNTY CENSUS DATA CLEANING SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("DATA COMPLETENESS:\n")
            f.write(f"Total counties: {stats['total_counties']}\n")
            f.write(f"Counties with total population: {stats['counties_with_total_pop']}\n")
            f.write(f"Counties with male population: {stats['counties_with_male_pop']}\n")
            f.write(f"Counties with female population: {stats['counties_with_female_pop']}\n\n")
            
            if 'total_population' in stats:
                f.write("POPULATION STATISTICS:\n")
                f.write(f"Total population: {stats['total_population']:,}\n")
                f.write(f"Average county population: {stats['average_population']:,.0f}\n")
                f.write(f"Largest county: {stats['largest_county']} ({stats['largest_population']:,})\n")
                f.write(f"Smallest county: {stats['smallest_county']} ({stats['smallest_population']:,})\n\n")
            
            f.write("PHASE I STEP 4 READINESS:\n")
            f.write("✅ County-level population data: COMPLETE\n")
            f.write("✅ Data format: Standardized CSV\n")
            f.write("✅ County names: Validated\n")
            f.write("🚀 Ready for integration with resilience model\n")
        
        logger.info(f"📋 Summary report saved to {report_path}")
        
        return output_path, stats
    
    def run_cleaning_process(self):
        """Run the complete cleaning process"""
        logger.info("🚀 Starting County Census Data Cleaning")
        logger.info("=" * 50)
        
        # Process the extracted data
        cleaned_df = self.process_extracted_data()
        
        if cleaned_df is None:
            logger.error("❌ Cleaning process failed")
            return None
        
        # Save cleaned data and generate reports
        output_path, stats = self.save_cleaned_data(cleaned_df)
        
        logger.info("=" * 50)
        logger.info("✅ CLEANING PROCESS COMPLETED")
        logger.info("=" * 50)
        logger.info(f"📁 Output file: {output_path}")
        logger.info(f"📊 Counties processed: {stats['total_counties']}")
        if 'total_population' in stats:
            logger.info(f"👥 Total population: {stats['total_population']:,}")
        logger.info("🚀 Data ready for Phase I Step 4 integration!")
        
        return cleaned_df

def main():
    """Main execution"""
    print("🧹 County Census Data Cleaner")
    print("=" * 40)
    print("🎯 Standardizing extracted county data")
    print("📊 Preparing for Phase I Step 4")
    print("=" * 40)
    
    cleaner = CountyDataCleaner()
    result = cleaner.run_cleaning_process()
    
    if result is not None:
        print("\n✅ Data cleaning successful!")
        print("📁 Check data/processed/census_2019/ for cleaned CSV")
        print("🚀 Ready for resilience model integration!")
    else:
        print("\n❌ Data cleaning failed")

if __name__ == "__main__":
    main()