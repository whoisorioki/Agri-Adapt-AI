#!/usr/bin/env python3
"""
Complete Socioeconomic Data Extractor
Extracts education, poverty, age, and employment data from KNBS Census Volumes 2, 3, and 4
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

class CompleteSocioeconomicExtractor:
    """Extract complete socioeconomic data from all census volumes"""
    
    def __init__(self):
        self.data_dir = Path("data/raw/census_2019")
        self.processed_dir = Path("data/processed/census_2019")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Kenya counties for validation
        self.kenya_counties = [
            'Baringo', 'Bomet', 'Bungoma', 'Busia', 'Elgeyo-Marakwet', 'Embu', 'Garissa',
            'Homa Bay', 'Isiolo', 'Kajiado', 'Kakamega', 'Kericho', 'Kiambu', 'Kilifi',
            'Kirinyaga', 'Kisii', 'Kisumu', 'Kitui', 'Kwale', 'Laikipia', 'Lamu', 'Machakos',
            'Makueni', 'Mandera', 'Marsabit', 'Meru', 'Migori', 'Mombasa', 'Murang\'a',
            'Nairobi', 'Nakuru', 'Nandi', 'Narok', 'Nyamira', 'Nyandarua', 'Nyeri',
            'Samburu', 'Siaya', 'Taita-Taveta', 'Tana River', 'Tharaka-Nithi', 'Trans Nzoia',
            'Turkana', 'Uasin Gishu', 'Vihiga', 'Wajir', 'West Pokot'
        ]
        
        # Target socioeconomic indicators
        self.target_indicators = {
            'education': {
                'keywords': ['education', 'school', 'literacy', 'primary', 'secondary', 'university', 'tertiary'],
                'volume': 4,
                'priority': 'HIGH'
            },
            'poverty': {
                'keywords': ['poverty', 'income', 'household', 'economic', 'wealth', 'assets'],
                'volume': 4,
                'priority': 'HIGH'
            },
            'employment': {
                'keywords': ['employment', 'occupation', 'work', 'agriculture', 'farming', 'business', 'unemployed'],
                'volume': 4,
                'priority': 'HIGH'
            },
            'age_structure': {
                'keywords': ['age', 'years', 'children', 'youth', 'elderly', 'population'],
                'volume': 3,
                'priority': 'MEDIUM'
            },
            'household_size': {
                'keywords': ['household', 'family', 'size', 'members', 'composition'],
                'volume': 2,
                'priority': 'MEDIUM'
            }
        }
        
        # Census volumes
        self.census_urls = {
            "volume_2": "https://www.knbs.or.ke/wp-content/uploads/2023/09/2019-Kenya-population-and-Housing-Census-Volume-2-Distribution-of-Population-by-Administrative-Units.pdf",
            "volume_3": "https://www.knbs.or.ke/wp-content/uploads/2023/09/2019-Kenya-population-and-Housing-Census-Volume-3-Distribution-of-Population-by-Age-and-Sex.pdf",
            "volume_4": "https://www.knbs.or.ke/wp-content/uploads/2023/09/2019-Kenya-population-and-Housing-Census-Volume-4-Distribution-of-Population-by-Socio-Economic-Characteristics.pdf"
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.session.verify = False
    
    def download_volume(self, volume_key):
        """Download a specific census volume"""
        url = self.census_urls[volume_key]
        filename = f"{volume_key}.pdf"
        filepath = self.data_dir / filename
        
        if filepath.exists():
            logger.info(f"✅ {filename} already exists ({filepath.stat().st_size} bytes)")
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
                    logger.error(f"❌ Failed to download {filename}")
                    return None
    
    def analyze_volume_structure(self, pdf_path, target_keywords):
        """Analyze PDF structure to find relevant pages"""
        logger.info(f"🔍 Analyzing {pdf_path.name} structure...")
        
        relevant_pages = []
        
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            logger.info(f"📄 Total pages: {total_pages}")
            
            # Analyze first 60 pages (where summary tables are usually located)
            for page_num in range(min(60, total_pages)):
                page = pdf.pages[page_num]
                text = (page.extract_text() or "").lower()
                
                # Count keyword matches
                keyword_matches = sum(1 for keyword in target_keywords if keyword in text)
                
                # Count county mentions
                county_matches = sum(1 for county in self.kenya_counties[:10] 
                                   if county.lower() in text)
                
                # Check for tables
                tables = page.extract_tables()
                has_tables = len(tables) > 0
                
                # Check for numerical data
                has_numbers = bool(re.search(r'\d{1,3}[,\s]\d{3}', text))
                
                # Score the page
                relevance_score = (keyword_matches * 3) + (county_matches * 2) + (1 if has_tables else 0) + (1 if has_numbers else 0)
                
                if relevance_score >= 5:  # Threshold for relevance
                    relevant_pages.append({
                        'page': page_num + 1,
                        'score': relevance_score,
                        'keyword_matches': keyword_matches,
                        'county_matches': county_matches,
                        'has_tables': has_tables,
                        'has_numbers': has_numbers
                    })
        
        # Sort by relevance score
        relevant_pages.sort(key=lambda x: x['score'], reverse=True)
        
        logger.info(f"📊 Found {len(relevant_pages)} relevant pages")
        for page_info in relevant_pages[:5]:  # Show top 5
            logger.info(f"   Page {page_info['page']}: score={page_info['score']}, keywords={page_info['keyword_matches']}, counties={page_info['county_matches']}")
        
        return relevant_pages
    
    def extract_data_from_pages(self, pdf_path, relevant_pages, indicator_type):
        """Extract data from relevant pages"""
        logger.info(f"🎯 Extracting {indicator_type} data from {len(relevant_pages)} pages...")
        
        extracted_tables = []
        
        for page_info in relevant_pages[:10]:  # Process top 10 most relevant pages
            page_num = page_info['page'] - 1
            logger.info(f"📄 Processing page {page_info['page']} (score: {page_info['score']})")
            
            # Extract tables from this page
            page_tables = self.extract_tables_from_page(pdf_path, page_num)
            
            for table_info in page_tables:
                if self.validate_socioeconomic_table(table_info['data'], indicator_type):
                    table_info['source_page'] = page_info['page']
                    table_info['indicator_type'] = indicator_type
                    table_info['confidence'] = self.calculate_table_confidence(table_info['data'], indicator_type)
                    extracted_tables.append(table_info)
        
        # Sort by confidence
        extracted_tables.sort(key=lambda x: x['confidence'], reverse=True)
        
        if extracted_tables:
            logger.info(f"✅ Found {len(extracted_tables)} {indicator_type} tables")
            best_table = extracted_tables[0]
            logger.info(f"   Best table: page {best_table['source_page']}, confidence {best_table['confidence']}")
        else:
            logger.warning(f"⚠️  No {indicator_type} tables found")
        
        return extracted_tables
    
    def extract_tables_from_page(self, pdf_path, page_num):
        """Extract all tables from a specific page"""
        tables = []
        
        # Method 1: PDFPlumber
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page = pdf.pages[page_num]
                page_tables = page.extract_tables()
                
                for i, table in enumerate(page_tables):
                    if table and len(table) > 3:
                        df = pd.DataFrame(table[1:], columns=table[0])
                        if not df.empty and len(df) >= 3:
                            tables.append({
                                'data': df,
                                'method': 'PDFPlumber',
                                'table_index': i
                            })
        except Exception as e:
            logger.warning(f"PDFPlumber failed on page {page_num + 1}: {e}")
        
        # Method 2: Camelot Stream
        try:
            camelot_tables = camelot.read_pdf(str(pdf_path), pages=str(page_num + 1), flavor='stream')
            for i, table in enumerate(camelot_tables):
                if not table.df.empty and len(table.df) >= 3:
                    tables.append({
                        'data': table.df,
                        'method': 'Camelot-Stream',
                        'table_index': i
                    })
        except Exception as e:
            logger.warning(f"Camelot Stream failed on page {page_num + 1}: {e}")
        
        # Method 3: Tabula
        try:
            tabula_tables = tabula.read_pdf(str(pdf_path), pages=[page_num + 1], multiple_tables=True)
            for i, table in enumerate(tabula_tables):
                if not table.empty and len(table) >= 3:
                    tables.append({
                        'data': table,
                        'method': 'Tabula',
                        'table_index': i
                    })
        except Exception as e:
            logger.warning(f"Tabula failed on page {page_num + 1}: {e}")
        
        return tables
    
    def validate_socioeconomic_table(self, df, indicator_type):
        """Validate if table contains relevant socioeconomic data"""
        if df.empty or len(df) < 5:
            return False
        
        text_content = ' '.join(df.astype(str).values.flatten()).lower()
        
        # Check for indicator-specific keywords
        keywords = self.target_indicators[indicator_type]['keywords']
        keyword_matches = sum(1 for keyword in keywords if keyword in text_content)
        
        # Check for county data
        county_matches = sum(1 for county in self.kenya_counties[:10] 
                           if county.lower() in text_content)
        
        # Check for numerical data
        numeric_cols = 0
        for col in df.columns:
            try:
                numeric_values = pd.to_numeric(df[col], errors='coerce').dropna()
                if len(numeric_values) > len(df) * 0.3:
                    numeric_cols += 1
            except:
                continue
        
        # Must have keywords, some counties, and numeric data
        return keyword_matches >= 1 and county_matches >= 2 and numeric_cols >= 1
    
    def calculate_table_confidence(self, df, indicator_type):
        """Calculate confidence score for socioeconomic table"""
        score = 0
        
        text_content = ' '.join(df.astype(str).values.flatten()).lower()
        
        # Keyword relevance (0-30 points)
        keywords = self.target_indicators[indicator_type]['keywords']
        keyword_matches = sum(1 for keyword in keywords if keyword in text_content)
        score += min(30, keyword_matches * 5)
        
        # County coverage (0-25 points)
        county_matches = sum(1 for county in self.kenya_counties 
                           if county.lower() in text_content)
        score += min(25, county_matches * 2)
        
        # Table structure (0-25 points)
        if 10 <= len(df) <= 50:  # Good size for county data
            score += 15
        if 3 <= len(df.columns) <= 10:  # Reasonable column count
            score += 10
        
        # Data quality (0-20 points)
        numeric_cols = 0
        for col in df.columns:
            try:
                numeric_values = pd.to_numeric(df[col], errors='coerce').dropna()
                if len(numeric_values) > len(df) * 0.5:
                    numeric_cols += 1
            except:
                continue
        score += min(20, numeric_cols * 7)
        
        return score
    
    def clean_socioeconomic_data(self, table_info, indicator_type):
        """Clean extracted socioeconomic data"""
        df = table_info['data'].copy()
        
        # Remove empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Try to identify county column
        county_col = None
        for col in df.columns:
            col_str = str(col).lower()
            if any(keyword in col_str for keyword in ['county', 'area', 'name', 'region']):
                county_col = col
                break
        
        # If no obvious county column, check first column
        if county_col is None:
            first_col_text = ' '.join(df.iloc[:, 0].astype(str)).lower()
            county_matches = sum(1 for county in self.kenya_counties[:5] 
                               if county.lower() in first_col_text)
            if county_matches >= 2:
                county_col = df.columns[0]
        
        if county_col is not None:
            df = df.rename(columns={county_col: 'County'})
        
        # Clean county names
        if 'County' in df.columns:
            df['County'] = df['County'].apply(self.clean_county_name)
            # Filter to valid counties
            df = df[df['County'].notna()]
        
        # Clean numeric columns
        for col in df.columns:
            if col != 'County':
                df[col] = df[col].apply(self.clean_numeric_value)
        
        return df
    
    def clean_county_name(self, name_str):
        """Clean county name"""
        if pd.isna(name_str):
            return None
        
        name = str(name_str)
        name = re.sub(r'[.…]+', '', name)
        name = re.sub(r'\s+', ' ', name)
        name = name.strip()
        name = re.sub(r'^[^a-zA-Z]+|[^a-zA-Z]+$', '', name)
        
        # Special cases
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
        elif 'Nairobi' in name:
            return 'Nairobi'
        
        return name.title() if len(name) > 2 else None
    
    def clean_numeric_value(self, value_str):
        """Clean numeric values"""
        if pd.isna(value_str):
            return None
        
        value = str(value_str)
        cleaned = re.sub(r'[^\d.,]', '', value)
        
        try:
            return float(cleaned.replace(',', ''))
        except ValueError:
            return None
    
    def save_socioeconomic_data(self, extracted_data, indicator_type):
        """Save extracted socioeconomic data"""
        if not extracted_data:
            logger.warning(f"⚠️  No {indicator_type} data to save")
            return None
        
        best_table = extracted_data[0]
        cleaned_df = self.clean_socioeconomic_data(best_table, indicator_type)
        
        # Save to CSV
        output_file = self.processed_dir / f"county_{indicator_type}_data.csv"
        cleaned_df.to_csv(output_file, index=False)
        
        # Save metadata
        metadata_file = self.processed_dir / f"county_{indicator_type}_metadata.txt"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            f.write(f"County {indicator_type.title()} Data Extraction\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Source Page: {best_table['source_page']}\n")
            f.write(f"Extraction Method: {best_table['method']}\n")
            f.write(f"Confidence Score: {best_table['confidence']}\n")
            f.write(f"Records: {len(cleaned_df)}\n")
            f.write(f"Columns: {list(cleaned_df.columns)}\n\n")
        
        logger.info(f"✅ Saved {indicator_type} data to {output_file}")
        return output_file
    
    def extract_all_socioeconomic_indicators(self):
        """Main workflow to extract all socioeconomic indicators"""
        logger.info("🚀 Starting Complete Socioeconomic Data Extraction")
        logger.info("=" * 60)
        logger.info("🎯 Target: Education, Poverty, Employment, Age Structure, Household Data")
        logger.info("=" * 60)
        
        results = {}
        
        # Group indicators by volume
        volume_indicators = {}
        for indicator, info in self.target_indicators.items():
            volume = f"volume_{info['volume']}"
            if volume not in volume_indicators:
                volume_indicators[volume] = []
            volume_indicators[volume].append(indicator)
        
        # Process each volume
        for volume_key, indicators in volume_indicators.items():
            logger.info(f"\n📚 PROCESSING {volume_key.upper()}")
            logger.info("=" * 40)
            
            # Download volume
            pdf_path = self.download_volume(volume_key)
            if not pdf_path:
                logger.error(f"❌ Failed to download {volume_key}")
                continue
            
            # Process each indicator for this volume
            for indicator in indicators:
                logger.info(f"\n🔍 Extracting {indicator} data...")
                
                # Analyze structure
                keywords = self.target_indicators[indicator]['keywords']
                relevant_pages = self.analyze_volume_structure(pdf_path, keywords)
                
                if not relevant_pages:
                    logger.warning(f"⚠️  No relevant pages found for {indicator}")
                    continue
                
                # Extract data
                extracted_tables = self.extract_data_from_pages(pdf_path, relevant_pages, indicator)
                
                if extracted_tables:
                    # Save data
                    output_file = self.save_socioeconomic_data(extracted_tables, indicator)
                    results[indicator] = {
                        'status': 'SUCCESS',
                        'file': output_file,
                        'confidence': extracted_tables[0]['confidence'],
                        'source_page': extracted_tables[0]['source_page']
                    }
                else:
                    results[indicator] = {
                        'status': 'FAILED',
                        'file': None
                    }
        
        # Generate final summary
        self.generate_final_summary(results)
        
        return results
    
    def generate_final_summary(self, results):
        """Generate comprehensive summary of all extractions"""
        summary_file = self.processed_dir / "complete_socioeconomic_extraction_summary.txt"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("COMPLETE SOCIOECONOMIC DATA EXTRACTION SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("EXTRACTION RESULTS:\n")
            f.write("-" * 30 + "\n")
            
            successful = 0
            total = len(results)
            
            for indicator, result in results.items():
                status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
                f.write(f"{status_icon} {indicator.title()}: {result['status']}\n")
                if result['status'] == 'SUCCESS':
                    successful += 1
                    f.write(f"   File: {result['file']}\n")
                    f.write(f"   Confidence: {result['confidence']}\n")
                    f.write(f"   Source Page: {result['source_page']}\n")
                f.write("\n")
            
            f.write(f"SUCCESS RATE: {successful}/{total} ({successful/total*100:.0f}%)\n\n")
            
            f.write("PHASE I STEP 4 STATUS:\n")
            f.write("-" * 25 + "\n")
            if successful >= 3:  # Need at least education, poverty, employment
                f.write("✅ PHASE I STEP 4: COMPLETE\n")
                f.write("🚀 Socioeconomic layer ready for integration\n")
            else:
                f.write("⚠️  PHASE I STEP 4: PARTIAL\n")
                f.write(f"🔄 {3-successful} critical indicators still needed\n")
        
        logger.info(f"📋 Final summary saved to {summary_file}")

def main():
    """Main execution"""
    print("📊 COMPLETE SOCIOECONOMIC DATA EXTRACTOR")
    print("=" * 50)
    print("🎯 Extracting: Education, Poverty, Employment, Age, Household data")
    print("📚 Sources: KNBS Census Volumes 2, 3, and 4")
    print("=" * 50)
    
    extractor = CompleteSocioeconomicExtractor()
    results = extractor.extract_all_socioeconomic_indicators()
    
    # Count successes
    successful = sum(1 for r in results.values() if r['status'] == 'SUCCESS')
    total = len(results)
    
    print(f"\n{'='*60}")
    print("🎉 COMPLETE EXTRACTION FINISHED!")
    print("=" * 60)
    print(f"✅ Success rate: {successful}/{total} ({successful/total*100:.0f}%)")
    print("📁 Check data/processed/census_2019/ for extracted data")
    print("🚀 Phase I Step 4 socioeconomic layer enhanced!")

if __name__ == "__main__":
    main()