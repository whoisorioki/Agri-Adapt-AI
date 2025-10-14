#!/usr/bin/env python3
"""
Targeted County-Level Census Data Extraction
Focuses on extracting specific county-level demographic and socioeconomic data 
needed for Phase I Step 4 of Agri-Adapt AI
"""

import requests
import pandas as pd
import pdfplumber
import camelot
import tabula
import re
from pathlib import Path
import logging
import time
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CountyCensusExtractor:
    """Extract county-level data from KNBS 2019 Census reports"""
    
    def __init__(self):
        self.data_dir = Path("data/raw/census_2019")
        self.processed_dir = Path("data/processed/census_2019")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Target counties (47 counties in Kenya)
        self.target_counties = [
            'Baringo', 'Bomet', 'Bungoma', 'Busia', 'Elgeyo-Marakwet', 'Embu', 'Garissa',
            'Homa Bay', 'Isiolo', 'Kajiado', 'Kakamega', 'Kericho', 'Kiambu', 'Kilifi',
            'Kirinyaga', 'Kisii', 'Kisumu', 'Kitui', 'Kwale', 'Laikipia', 'Lamu', 'Machakos',
            'Makueni', 'Mandera', 'Marsabit', 'Meru', 'Migori', 'Mombasa', 'Murang\'a',
            'Nairobi', 'Nakuru', 'Nandi', 'Narok', 'Nyamira', 'Nyandarua', 'Nyeri',
            'Samburu', 'Siaya', 'Taita-Taveta', 'Tana River', 'Tharaka-Nithi', 'Trans Nzoia',
            'Turkana', 'Uasin Gishu', 'Vihiga', 'Wajir', 'West Pokot'
        ]
        
        # Target data fields for Phase I Step 4
        self.target_fields = {
            'population': ['Total Population', 'Male', 'Female', 'Population Density'],
            'education': ['Primary Education', 'Secondary Education', 'University', 'Literacy Rate'],
            'employment': ['Agriculture', 'Employed', 'Unemployed', 'Self Employed'],
            'economic': ['Poverty Level', 'Income', 'Household Size', 'Rural Population', 'Urban Population']
        }
        
        # Census volumes with priorities
        self.census_urls = {
            "volume_1": {
                "url": "https://www.knbs.or.ke/wp-content/uploads/2023/09/2019-Kenya-population-and-Housing-Census-Volume-1-Population-By-County-And-Sub-County.pdf",
                "priority": 1,
                "target_data": ['population']
            },
            "volume_4": {
                "url": "https://www.knbs.or.ke/wp-content/uploads/2023/09/2019-Kenya-population-and-Housing-Census-Volume-4-Distribution-of-Population-by-Socio-Economic-Characteristics.pdf",
                "priority": 2,
                "target_data": ['education', 'employment', 'economic']
            }
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.session.verify = False  # Handle SSL certificate issues
    
    def download_pdf(self, url, filename):
        """Download PDF file with retry logic"""
        filepath = self.data_dir / filename
        
        if filepath.exists():
            logger.info(f"✅ File {filename} already exists ({filepath.stat().st_size} bytes)")
            return filepath
        
        logger.info(f"📥 Downloading {filename}...")
        
        for attempt in range(3):
            try:
                response = self.session.get(url, stream=True, timeout=60)
                response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"✅ Downloaded {filename} ({filepath.stat().st_size} bytes)")
                return filepath
                
            except Exception as e:
                logger.warning(f"⚠️  Attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(5)
                else:
                    logger.error(f"❌ Failed to download {filename} after 3 attempts")
                    return None
    
    def extract_county_population_data(self, pdf_path):
        """Extract county population summary table (highest priority)"""
        logger.info("🎯 Extracting county population data from Volume 1...")
        
        county_data = None
        extraction_methods = [
            ("Camelot Lattice", lambda: camelot.read_pdf(str(pdf_path), pages='all', flavor='lattice')),
            ("Camelot Stream", lambda: camelot.read_pdf(str(pdf_path), pages='all', flavor='stream')),
            ("Tabula", lambda: tabula.read_pdf(str(pdf_path), pages='all', multiple_tables=True)),
            ("PDFPlumber", lambda: self.extract_with_pdfplumber(pdf_path))
        ]
        
        for method_name, extract_func in extraction_methods:
            try:
                logger.info(f"🔍 Trying {method_name}...")
                tables = extract_func()
                
                if tables:
                    county_table = self.find_county_summary_table(tables, method_name)
                    if county_table is not None:
                        logger.info(f"✅ Found county data using {method_name}")
                        county_data = county_table
                        break
                
            except Exception as e:
                logger.warning(f"⚠️  {method_name} failed: {e}")
                continue
        
        return county_data
    
    def extract_with_pdfplumber(self, pdf_path):
        """Extract tables using pdfplumber with better page targeting"""
        tables = []
        
        with pdfplumber.open(pdf_path) as pdf:
            # Focus on early pages where summary tables are likely located
            target_pages = list(range(min(30, len(pdf.pages))))  # First 30 pages
            
            for page_num in target_pages:
                page = pdf.pages[page_num]
                
                # Look for text indicating county data
                text = page.extract_text() or ""
                if any(keyword in text.lower() for keyword in ['county', 'population', 'total', 'male', 'female']):
                    
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table in page_tables:
                            if table and len(table) > 3:  # Must have header + at least 3 data rows
                                df = pd.DataFrame(table[1:], columns=table[0])
                                tables.append({
                                    'page': page_num + 1,
                                    'dataframe': df,
                                    'text_context': text[:500]  # First 500 chars for context
                                })
        
        return tables
    
    def find_county_summary_table(self, tables, method_name):
        """Find the main county population summary table"""
        
        if method_name == "PDFPlumber":
            for table_info in tables:
                df = table_info['dataframe']
                if self.is_county_summary_table(df):
                    cleaned_df = self.clean_county_data(df)
                    if cleaned_df is not None:
                        return {
                            'data': cleaned_df,
                            'page': table_info['page'],
                            'method': method_name,
                            'context': table_info.get('text_context', '')
                        }
        
        else:  # Camelot or Tabula
            for i, table in enumerate(tables):
                if hasattr(table, 'df'):
                    df = table.df
                else:
                    df = table
                
                if self.is_county_summary_table(df):
                    cleaned_df = self.clean_county_data(df)
                    if cleaned_df is not None:
                        return {
                            'data': cleaned_df,
                            'table_index': i,
                            'method': method_name
                        }
        
        return None
    
    def is_county_summary_table(self, df):
        """Check if dataframe contains county population summary"""
        if df.empty or len(df) < 10:  # Need at least 10 rows for county data
            return False
        
        # Convert all data to string for analysis
        text_content = ' '.join(df.astype(str).values.flatten()).lower()
        
        # Check for county indicators
        county_indicators = sum(1 for county in self.target_counties[:10] 
                               if county.lower() in text_content)
        
        # Check for population indicators
        pop_indicators = ['total', 'male', 'female', 'population']
        pop_matches = sum(1 for indicator in pop_indicators if indicator in text_content)
        
        # Check for numeric data in multiple columns
        numeric_columns = 0
        for col in df.columns:
            try:
                pd.to_numeric(df[col], errors='raise')
                numeric_columns += 1
            except:
                continue
        
        # Must have at least 3 counties mentioned, 2 population indicators, and 2+ numeric columns
        return county_indicators >= 3 and pop_matches >= 2 and numeric_columns >= 2
    
    def clean_county_data(self, df):
        """Clean and standardize county data"""
        try:
            # Remove completely empty rows and columns
            df = df.dropna(how='all').dropna(axis=1, how='all')
            
            if len(df) < 5:  # Need meaningful data
                return None
            
            # Try to identify columns
            columns_mapping = {}
            
            for col in df.columns:
                col_str = str(col).lower()
                if any(keyword in col_str for keyword in ['county', 'area', 'name']):
                    columns_mapping['county'] = col
                elif 'male' in col_str and 'female' not in col_str:
                    columns_mapping['male'] = col
                elif 'female' in col_str:
                    columns_mapping['female'] = col
                elif any(keyword in col_str for keyword in ['total', 'population', 'both']):
                    columns_mapping['total'] = col
            
            # Create cleaned dataframe
            cleaned_df = pd.DataFrame()
            
            # Copy mapped columns
            for new_col, old_col in columns_mapping.items():
                cleaned_df[new_col] = df[old_col]
            
            # Clean numeric columns
            for col in ['male', 'female', 'total']:
                if col in cleaned_df.columns:
                    cleaned_df[col] = pd.to_numeric(
                        cleaned_df[col].astype(str).str.replace(r'[^\d]', '', regex=True),
                        errors='coerce'
                    )
            
            # Filter rows that look like county data
            if 'county' in cleaned_df.columns:
                county_mask = cleaned_df['county'].astype(str).str.len() > 3  # Filter out short entries
                cleaned_df = cleaned_df[county_mask]
            
            # Verify we have actual data
            if len(cleaned_df) >= 5 and 'total' in cleaned_df.columns:
                total_values = cleaned_df['total'].dropna()
                if len(total_values) >= 5 and total_values.sum() > 1000000:  # Reasonable population numbers
                    return cleaned_df
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️  Error cleaning county data: {e}")
            return None
    
    def validate_county_data(self, county_data):
        """Validate extracted county data"""
        if not county_data or 'data' not in county_data:
            return False
        
        df = county_data['data']
        
        # Check we have reasonable number of counties
        if len(df) < 30:  # Kenya has 47 counties, allow for some missing
            logger.warning(f"⚠️  Only {len(df)} counties found, expected ~47")
        
        # Check total population is reasonable
        if 'total' in df.columns:
            total_pop = df['total'].sum()
            if 40000000 <= total_pop <= 60000000:  # Kenya's population range
                logger.info(f"✅ Total population: {total_pop:,} (reasonable)")
                return True
            else:
                logger.warning(f"⚠️  Total population: {total_pop:,} (seems unusual)")
        
        return len(df) >= 20  # Accept if we have at least 20 counties
    
    def save_county_data(self, county_data, filename="county_population_summary.csv"):
        """Save county data to CSV"""
        if not county_data:
            logger.warning("⚠️  No county data to save")
            return None
        
        filepath = self.processed_dir / filename
        county_data['data'].to_csv(filepath, index=False)
        
        # Save metadata
        metadata_file = self.processed_dir / f"{filename.replace('.csv', '_metadata.txt')}"
        with open(metadata_file, 'w') as f:
            f.write(f"County Census Data Extraction Metadata\n")
            f.write(f"={'='*50}\n\n")
            f.write(f"Extraction Method: {county_data.get('method', 'Unknown')}\n")
            f.write(f"Source Page: {county_data.get('page', 'Unknown')}\n")
            f.write(f"Records Count: {len(county_data['data'])}\n")
            f.write(f"Columns: {list(county_data['data'].columns)}\n")
            if 'total' in county_data['data'].columns:
                f.write(f"Total Population: {county_data['data']['total'].sum():,}\n")
            
            if 'context' in county_data:
                f.write(f"\nPage Context:\n{county_data['context']}\n")
        
        logger.info(f"✅ Saved county data to {filepath}")
        logger.info(f"📄 Saved metadata to {metadata_file}")
        
        return filepath
    
    def run_targeted_extraction(self):
        """Main extraction workflow - focused on county-level data"""
        logger.info("🚀 Starting Targeted County Census Data Extraction")
        logger.info("=" * 60)
        
        # Step 1: Download Volume 1 (Population data - highest priority)
        volume_1_info = self.census_urls["volume_1"]
        logger.info(f"📥 Downloading Volume 1: Population Data")
        
        pdf_path = self.download_pdf(volume_1_info["url"], "volume_1_population.pdf")
        
        if not pdf_path:
            logger.error("❌ Could not download Volume 1. Cannot proceed.")
            return None
        
        # Step 2: Extract county population data
        logger.info("=" * 60)
        logger.info("🎯 EXTRACTING COUNTY POPULATION DATA")
        logger.info("=" * 60)
        
        county_data = self.extract_county_population_data(pdf_path)
        
        # Step 3: Validate and save
        if county_data and self.validate_county_data(county_data):
            logger.info("✅ County data extraction successful!")
            
            saved_file = self.save_county_data(county_data)
            
            # Generate summary
            self.generate_extraction_summary(county_data, saved_file)
            
            return county_data
        
        else:
            logger.error("❌ Failed to extract valid county data")
            return None
    
    def generate_extraction_summary(self, county_data, saved_file):
        """Generate extraction summary report"""
        summary_file = self.processed_dir / "county_extraction_summary.txt"
        
        df = county_data['data']
        
        with open(summary_file, 'w') as f:
            f.write("COUNTY CENSUS DATA EXTRACTION SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"✅ Status: SUCCESS\n")
            f.write(f"📁 Data File: {saved_file}\n")
            f.write(f"🔢 Counties Extracted: {len(df)}\n")
            f.write(f"📊 Columns: {list(df.columns)}\n\n")
            
            if 'total' in df.columns:
                f.write(f"👥 Total Population: {df['total'].sum():,}\n")
                f.write(f"📈 Largest County: {df.loc[df['total'].idxmax(), 'county'] if 'county' in df.columns else 'Unknown'} ({df['total'].max():,})\n")
                f.write(f"📉 Smallest County: {df.loc[df['total'].idxmin(), 'county'] if 'county' in df.columns else 'Unknown'} ({df['total'].min():,})\n\n")
            
            f.write("🎯 PHASE I STEP 4 READINESS:\n")
            f.write("✅ County-level population data: AVAILABLE\n")
            f.write("🔄 Next: Extract socioeconomic data from Volume 4\n")
            f.write("🚀 Phase I Step 4 implementation: READY TO PROCEED\n")
        
        logger.info(f"📋 Summary report saved to {summary_file}")

def main():
    """Main execution"""
    print("🇰🇪 KNBS 2019 County Census Data Extractor")
    print("=" * 50)
    print("🎯 Target: County-level demographic data for Phase I Step 4")
    print("📊 Focus: Population data from 47 Kenyan counties")
    print("=" * 50)
    
    extractor = CountyCensusExtractor()
    result = extractor.run_targeted_extraction()
    
    if result:
        print("\n" + "=" * 60)
        print("🎉 EXTRACTION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("✅ County population data extracted and validated")
        print("📁 Check data/processed/census_2019/ for CSV files")
        print("🚀 Phase I Step 4 data is now available!")
        print("📋 See county_extraction_summary.txt for details")
    else:
        print("\n" + "=" * 60)
        print("❌ EXTRACTION FAILED")
        print("=" * 60)
        print("💡 The PDF structure may be different than expected")
        print("🔍 Check logs above for specific error details")

if __name__ == "__main__":
    main()