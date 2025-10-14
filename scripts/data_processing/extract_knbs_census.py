#!/usr/bin/env python3
"""
Automated KNBS 2019 Census Data Extraction
Downloads and parses PDF reports to extract structured data
"""

import requests
import pandas as pd
import PyPDF2
import pdfplumber
import re
from pathlib import Path
import logging
from urllib.parse import urlparse
import time

# Optional imports for additional PDF processing
try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False
    print("Camelot not available - skipping lattice table extraction")

try:
    import tabula
    TABULA_AVAILABLE = True
except ImportError:
    TABULA_AVAILABLE = False
    print("Tabula not available - skipping Java-based table extraction")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KNBSCensusExtractor:
    """Extract data from KNBS 2019 Census PDF reports"""
    
    def __init__(self):
        self.data_dir = Path("data/raw/census_2019")
        self.processed_dir = Path("data/processed/census_2019")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Census volume URLs
        self.census_urls = {
            "volume_1": "https://www.knbs.or.ke/wp-content/uploads/2023/09/2019-Kenya-population-and-Housing-Census-Volume-1-Population-By-County-And-Sub-County.pdf",
            "volume_2": "https://www.knbs.or.ke/wp-content/uploads/2023/09/2019-Kenya-population-and-Housing-Census-Volume-2-Distribution-of-Population-by-Administrative-Units.pdf", 
            "volume_3": "https://www.knbs.or.ke/wp-content/uploads/2023/09/2019-Kenya-population-and-Housing-Census-Volume-3-Distribution-of-Population-by-Age-and-Sex.pdf",
            "volume_4": "https://www.knbs.or.ke/wp-content/uploads/2023/09/2019-Kenya-population-and-Housing-Census-Volume-4-Distribution-of-Population-by-Socio-Economic-Characteristics.pdf"
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        # Disable SSL verification for government sites with certificate issues
        self.session.verify = False
        # Suppress SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def download_pdf(self, url, filename):
        """Download PDF file from URL"""
        filepath = self.data_dir / filename
        
        if filepath.exists():
            logger.info(f"File {filename} already exists, skipping download")
            return filepath
        
        logger.info(f"Downloading {filename} from {url}")
        try:
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Successfully downloaded {filename}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error downloading {filename}: {e}")
            return None
    
    def download_all_volumes(self):
        """Download all census volumes"""
        logger.info("Starting download of all census volumes...")
        
        downloaded_files = {}
        for volume, url in self.census_urls.items():
            filename = f"{volume}.pdf"
            filepath = self.download_pdf(url, filename)
            if filepath:
                downloaded_files[volume] = filepath
                time.sleep(2)  # Be respectful to the server
        
        return downloaded_files
    
    def extract_tables_with_camelot(self, pdf_path, pages=None):
        """Extract tables using camelot (best for structured tables)"""
        if not CAMELOT_AVAILABLE:
            logger.warning("Camelot not available, skipping lattice extraction")
            return None
            
        try:
            logger.info(f"Extracting tables from {pdf_path.name} using camelot...")
            tables = camelot.read_pdf(str(pdf_path), pages=pages or 'all', flavor='lattice')
            logger.info(f"Found {len(tables)} tables using camelot")
            return tables
        except Exception as e:
            logger.error(f"Camelot extraction failed: {e}")
            return None
    
    def extract_tables_with_tabula(self, pdf_path, pages=None):
        """Extract tables using tabula (good for mixed content)"""
        if not TABULA_AVAILABLE:
            logger.warning("Tabula not available, skipping Java-based extraction")
            return None
            
        try:
            logger.info(f"Extracting tables from {pdf_path.name} using tabula...")
            tables = tabula.read_pdf(str(pdf_path), pages=pages or 'all', multiple_tables=True)
            logger.info(f"Found {len(tables)} tables using tabula")
            return tables
        except Exception as e:
            logger.error(f"Tabula extraction failed: {e}")
            return None
    
    def extract_tables_with_pdfplumber(self, pdf_path, pages=None):
        """Extract tables using pdfplumber (most flexible)"""
        try:
            logger.info(f"Extracting tables from {pdf_path.name} using pdfplumber...")
            tables = []
            
            with pdfplumber.open(pdf_path) as pdf:
                page_range = pages or range(len(pdf.pages))
                if isinstance(page_range, str):
                    page_range = [int(p) - 1 for p in page_range.split(',')]
                
                for page_num in page_range:
                    if page_num < len(pdf.pages):
                        page = pdf.pages[page_num]
                        page_tables = page.extract_tables()
                        if page_tables:
                            for table in page_tables:
                                if table and len(table) > 1:  # Skip empty tables
                                    df = pd.DataFrame(table[1:], columns=table[0])
                                    tables.append({
                                        'page': page_num + 1,
                                        'dataframe': df
                                    })
            
            logger.info(f"Found {len(tables)} tables using pdfplumber")
            return tables
            
        except Exception as e:
            logger.error(f"PDFplumber extraction failed: {e}")
            return None
    
    def extract_volume_1_data(self, pdf_path):
        """Extract key data from Volume 1: Population by County and Sub-County"""
        logger.info("Extracting Volume 1: Population data...")
        
        extracted_data = {
            'county_population': None,
            'subcounty_population': [],
            'rural_urban_breakdown': []
        }
        
        # Try different extraction methods
        methods = [('pdfplumber', self.extract_tables_with_pdfplumber)]
        
        if CAMELOT_AVAILABLE:
            methods.append(('camelot', self.extract_tables_with_camelot))
        if TABULA_AVAILABLE:
            methods.append(('tabula', self.extract_tables_with_tabula))
        
        for method_name, method_func in methods:
            try:
                logger.info(f"Trying {method_name} extraction for Volume 1...")
                tables = method_func(pdf_path)
                
                if tables:
                    # Look for county population table (like Table 2.2)
                    county_table = self.find_county_population_table(tables, method_name)
                    if county_table is not None:
                        extracted_data['county_population'] = county_table
                        logger.info(f"Found county population table using {method_name}")
                    
                    # Look for sub-county tables
                    subcounty_tables = self.find_subcounty_population_tables(tables, method_name)
                    if subcounty_tables:
                        extracted_data['subcounty_population'].extend(subcounty_tables)
                        logger.info(f"Found {len(subcounty_tables)} sub-county tables using {method_name}")
                
                # If we found data, break
                if extracted_data['county_population'] is not None or extracted_data['subcounty_population']:
                    break
                    
            except Exception as e:
                logger.error(f"Error with {method_name}: {e}")
                continue
        
        return extracted_data
    
    def find_county_population_table(self, tables, method_name):
        """Find the county population table (Table 2.2 equivalent)"""
        county_keywords = ['county', 'male', 'female', 'total', 'population']
        
        if method_name == 'pdfplumber':
            for table_info in tables:
                df = table_info['dataframe']
                if self.is_county_population_table(df, county_keywords):
                    return self.clean_county_population_table(df)
        
        elif method_name in ['camelot', 'tabula']:
            for table in tables:
                if hasattr(table, 'df'):
                    df = table.df
                else:
                    df = table
                
                if self.is_county_population_table(df, county_keywords):
                    return self.clean_county_population_table(df)
        
        return None
    
    def is_county_population_table(self, df, keywords):
        """Check if dataframe is a county population table"""
        if df.empty or len(df.columns) < 4:
            return False
        
        # Convert to string and check for keywords
        text_content = ' '.join(df.astype(str).values.flatten()).lower()
        keyword_matches = sum(1 for keyword in keywords if keyword in text_content)
        
        # Check for county names
        kenyan_counties = ['nairobi', 'mombasa', 'nakuru', 'baringo', 'kiambu', 'machakos']
        county_matches = sum(1 for county in kenyan_counties if county in text_content)
        
        return keyword_matches >= 3 and county_matches >= 2
    
    def clean_county_population_table(self, df):
        """Clean and standardize county population table"""
        # Remove empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Look for standard columns
        columns_map = {}
        for col in df.columns:
            col_str = str(col).lower()
            if 'county' in col_str or 'area' in col_str:
                columns_map['county'] = col
            elif 'male' in col_str and 'female' not in col_str:
                columns_map['male'] = col
            elif 'female' in col_str:
                columns_map['female'] = col
            elif 'total' in col_str or 'population' in col_str:
                columns_map['total'] = col
        
        if len(columns_map) >= 3:  # At least county, one gender, total
            cleaned_df = pd.DataFrame()
            for new_col, old_col in columns_map.items():
                cleaned_df[new_col] = df[old_col]
            
            # Clean numeric columns
            for col in ['male', 'female', 'total']:
                if col in cleaned_df.columns:
                    cleaned_df[col] = pd.to_numeric(
                        cleaned_df[col].astype(str).str.replace(r'[^\d]', '', regex=True), 
                        errors='coerce'
                    )
            
            return cleaned_df
        
        return df  # Return as-is if can't clean
    
    def find_subcounty_population_tables(self, tables, method_name):
        """Find sub-county population tables"""
        subcounty_tables = []
        subcounty_keywords = ['sub', 'county', 'constituency', 'ward', 'population']
        
        if method_name == 'pdfplumber':
            for table_info in tables:
                df = table_info['dataframe']
                if self.is_subcounty_population_table(df, subcounty_keywords):
                    cleaned = self.clean_subcounty_population_table(df)
                    if cleaned is not None:
                        subcounty_tables.append({
                            'page': table_info['page'],
                            'data': cleaned
                        })
        
        elif method_name in ['camelot', 'tabula']:
            for i, table in enumerate(tables):
                if hasattr(table, 'df'):
                    df = table.df
                else:
                    df = table
                
                if self.is_subcounty_population_table(df, subcounty_keywords):
                    cleaned = self.clean_subcounty_population_table(df)
                    if cleaned is not None:
                        subcounty_tables.append({
                            'table_index': i,
                            'data': cleaned
                        })
        
        return subcounty_tables
    
    def is_subcounty_population_table(self, df, keywords):
        """Check if dataframe is a sub-county population table"""
        if df.empty or len(df.columns) < 3:
            return False
        
        text_content = ' '.join(df.astype(str).values.flatten()).lower()
        keyword_matches = sum(1 for keyword in keywords if keyword in text_content)
        
        # Check for sub-county indicators
        subcounty_indicators = ['central', 'north', 'south', 'east', 'west', 'town']
        indicator_matches = sum(1 for indicator in subcounty_indicators if indicator in text_content)
        
        return keyword_matches >= 2 and indicator_matches >= 1
    
    def clean_subcounty_population_table(self, df):
        """Clean sub-county population table"""
        # Similar cleaning logic as county table
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        if len(df) < 2:  # Need at least header and one data row
            return None
        
        # Basic cleaning - convert numeric columns
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to numeric if it looks like numbers
                numeric_series = pd.to_numeric(
                    df[col].astype(str).str.replace(r'[^\d]', '', regex=True), 
                    errors='coerce'
                )
                if not numeric_series.isna().all():
                    df[col] = numeric_series
        
        return df
    
    def extract_volume_4_data(self, pdf_path):
        """Extract socio-economic data from Volume 4"""
        logger.info("Extracting Volume 4: Socio-economic data...")
        
        extracted_data = {
            'education_data': [],
            'employment_data': [],
            'economic_indicators': []
        }
        
        # Try extraction methods
        methods = [('pdfplumber', self.extract_tables_with_pdfplumber)]
        
        if TABULA_AVAILABLE:
            methods.append(('tabula', self.extract_tables_with_tabula))
        if CAMELOT_AVAILABLE:
            methods.append(('camelot', self.extract_tables_with_camelot))
        
        for method_name, method_func in methods:
            try:
                logger.info(f"Trying {method_name} extraction for Volume 4...")
                tables = method_func(pdf_path)
                
                if tables:
                    # Look for education tables
                    education_tables = self.find_education_tables(tables, method_name)
                    if education_tables:
                        extracted_data['education_data'].extend(education_tables)
                        logger.info(f"Found {len(education_tables)} education tables using {method_name}")
                    
                    # Look for employment tables
                    employment_tables = self.find_employment_tables(tables, method_name)
                    if employment_tables:
                        extracted_data['employment_data'].extend(employment_tables)
                        logger.info(f"Found {len(employment_tables)} employment tables using {method_name}")
                
                # If we found significant data, break
                if len(extracted_data['education_data']) > 5 or len(extracted_data['employment_data']) > 5:
                    break
                    
            except Exception as e:
                logger.error(f"Error with {method_name}: {e}")
                continue
        
        return extracted_data
    
    def find_education_tables(self, tables, method_name):
        """Find education-related tables"""
        education_tables = []
        education_keywords = ['education', 'school', 'literacy', 'primary', 'secondary', 'university']
        
        if method_name == 'pdfplumber':
            for table_info in tables:
                df = table_info['dataframe']
                if self.contains_keywords(df, education_keywords, min_matches=2):
                    education_tables.append({
                        'page': table_info['page'],
                        'data': df,
                        'type': 'education'
                    })
        
        elif method_name in ['camelot', 'tabula']:
            for i, table in enumerate(tables):
                if hasattr(table, 'df'):
                    df = table.df
                else:
                    df = table
                
                if self.contains_keywords(df, education_keywords, min_matches=2):
                    education_tables.append({
                        'table_index': i,
                        'data': df,
                        'type': 'education'
                    })
        
        return education_tables
    
    def find_employment_tables(self, tables, method_name):
        """Find employment-related tables"""
        employment_tables = []
        employment_keywords = ['employment', 'occupation', 'work', 'agriculture', 'farming', 'business']
        
        if method_name == 'pdfplumber':
            for table_info in tables:
                df = table_info['dataframe']
                if self.contains_keywords(df, employment_keywords, min_matches=2):
                    employment_tables.append({
                        'page': table_info['page'],
                        'data': df,
                        'type': 'employment'
                    })
        
        elif method_name in ['camelot', 'tabula']:
            for i, table in enumerate(tables):
                if hasattr(table, 'df'):
                    df = table.df
                else:
                    df = table
                
                if self.contains_keywords(df, employment_keywords, min_matches=2):
                    employment_tables.append({
                        'table_index': i,
                        'data': df,
                        'type': 'employment'
                    })
        
        return employment_tables
    
    def contains_keywords(self, df, keywords, min_matches=1):
        """Check if dataframe contains specified keywords"""
        if df.empty:
            return False
        
        text_content = ' '.join(df.astype(str).values.flatten()).lower()
        matches = sum(1 for keyword in keywords if keyword in text_content)
        return matches >= min_matches
    
    def save_extracted_data(self, volume, data):
        """Save extracted data to CSV files"""
        volume_dir = self.processed_dir / volume
        volume_dir.mkdir(exist_ok=True)
        
        if volume == 'volume_1':
            # Save county population data
            if data.get('county_population') is not None:
                county_file = volume_dir / 'county_population.csv'
                data['county_population'].to_csv(county_file, index=False)
                logger.info(f"Saved county population data to {county_file}")
            
            # Save sub-county population data
            for i, subcounty_data in enumerate(data.get('subcounty_population', [])):
                subcounty_file = volume_dir / f'subcounty_population_{i+1}.csv'
                subcounty_data['data'].to_csv(subcounty_file, index=False)
                logger.info(f"Saved sub-county population data to {subcounty_file}")
        
        elif volume == 'volume_4':
            # Save education data
            for i, edu_data in enumerate(data.get('education_data', [])):
                edu_file = volume_dir / f'education_data_{i+1}.csv'
                edu_data['data'].to_csv(edu_file, index=False)
                logger.info(f"Saved education data to {edu_file}")
            
            # Save employment data
            for i, emp_data in enumerate(data.get('employment_data', [])):
                emp_file = volume_dir / f'employment_data_{i+1}.csv'
                emp_data['data'].to_csv(emp_file, index=False)
                logger.info(f"Saved employment data to {emp_file}")
    
    def run_extraction(self):
        """Main extraction workflow"""
        logger.info("Starting KNBS Census Data Extraction...")
        
        # Step 1: Download all volumes
        downloaded_files = self.download_all_volumes()
        
        if not downloaded_files:
            logger.error("No files downloaded successfully")
            return
        
        # Step 2: Extract data from priority volumes
        extraction_results = {}
        
        # Volume 1: Population data (highest priority)
        if 'volume_1' in downloaded_files:
            logger.info("=" * 60)
            logger.info("EXTRACTING VOLUME 1: POPULATION DATA")
            logger.info("=" * 60)
            vol1_data = self.extract_volume_1_data(downloaded_files['volume_1'])
            extraction_results['volume_1'] = vol1_data
            self.save_extracted_data('volume_1', vol1_data)
        
        # Volume 4: Socio-economic data (second priority)
        if 'volume_4' in downloaded_files:
            logger.info("=" * 60)
            logger.info("EXTRACTING VOLUME 4: SOCIO-ECONOMIC DATA")
            logger.info("=" * 60)
            vol4_data = self.extract_volume_4_data(downloaded_files['volume_4'])
            extraction_results['volume_4'] = vol4_data
            self.save_extracted_data('volume_4', vol4_data)
        
        # Step 3: Generate summary report
        self.generate_summary_report(extraction_results)
        
        logger.info("Census data extraction completed!")
        return extraction_results
    
    def generate_summary_report(self, results):
        """Generate a summary report of extracted data"""
        summary_file = self.processed_dir / 'extraction_summary.txt'
        
        with open(summary_file, 'w') as f:
            f.write("KNBS 2019 Census Data Extraction Summary\n")
            f.write("=" * 50 + "\n\n")
            
            for volume, data in results.items():
                f.write(f"Volume: {volume}\n")
                f.write("-" * 20 + "\n")
                
                if volume == 'volume_1':
                    f.write(f"County population table: {'Found' if data.get('county_population') is not None else 'Not found'}\n")
                    f.write(f"Sub-county tables: {len(data.get('subcounty_population', []))}\n")
                
                elif volume == 'volume_4':
                    f.write(f"Education tables: {len(data.get('education_data', []))}\n")
                    f.write(f"Employment tables: {len(data.get('employment_data', []))}\n")
                
                f.write("\n")
        
        logger.info(f"Summary report saved to {summary_file}")

def main():
    """Main execution function"""
    extractor = KNBSCensusExtractor()
    results = extractor.run_extraction()
    
    print("\n" + "=" * 80)
    print("EXTRACTION COMPLETE!")
    print("=" * 80)
    print(f"Check the 'data/processed/census_2019/' directory for extracted CSV files")
    print(f"Priority data for Phase I Step 4 implementation is now available!")

if __name__ == "__main__":
    main()