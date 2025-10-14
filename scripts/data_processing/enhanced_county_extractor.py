#!/usr/bin/env python3
"""
Enhanced County Census Data Extractor
Uses multiple strategies to locate and extract county-level data from KNBS PDFs
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

class EnhancedCountyExtractor:
    """Enhanced extractor with PDF exploration capabilities"""
    
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
    
    def explore_pdf_structure(self, pdf_path):
        """Explore PDF to understand its structure and locate county data"""
        logger.info("🔍 Exploring PDF structure to locate county data...")
        
        analysis = {
            'total_pages': 0,
            'pages_with_county_text': [],
            'pages_with_tables': [],
            'potential_data_pages': [],
            'table_of_contents_pages': []
        }
        
        with pdfplumber.open(pdf_path) as pdf:
            analysis['total_pages'] = len(pdf.pages)
            logger.info(f"📄 PDF has {analysis['total_pages']} pages")
            
            # Analyze first 50 pages in detail
            for page_num in range(min(50, len(pdf.pages))):
                page = pdf.pages[page_num]
                text = page.extract_text() or ""
                
                # Check for county mentions
                county_mentions = sum(1 for county in self.kenya_counties[:10] 
                                    if county.lower() in text.lower())
                
                if county_mentions >= 3:
                    analysis['pages_with_county_text'].append({
                        'page': page_num + 1,
                        'county_count': county_mentions,
                        'has_numbers': bool(re.search(r'\d{1,3}[,\s]\d{3}', text)),
                        'preview': text[:300]
                    })
                
                # Check for tables
                tables = page.extract_tables()
                if tables:
                    analysis['pages_with_tables'].append({
                        'page': page_num + 1,
                        'table_count': len(tables),
                        'largest_table_rows': max(len(table) for table in tables) if tables else 0
                    })
                
                # Check for table of contents
                if any(keyword in text.lower() for keyword in ['contents', 'table', 'chapter', 'summary']):
                    if page_num < 10:  # TOC usually in first few pages
                        analysis['table_of_contents_pages'].append({
                            'page': page_num + 1,
                            'preview': text[:500]
                        })
        
        # Identify most promising pages
        for page_info in analysis['pages_with_county_text']:
            if page_info['county_count'] >= 5 and page_info['has_numbers']:
                analysis['potential_data_pages'].append(page_info)
        
        return analysis
    
    def extract_data_from_promising_pages(self, pdf_path, promising_pages):
        """Extract data from the most promising pages"""
        logger.info(f"🎯 Extracting data from {len(promising_pages)} promising pages...")
        
        extracted_tables = []
        
        for page_info in promising_pages:
            page_num = page_info['page'] - 1  # Convert to 0-based
            logger.info(f"📄 Processing page {page_info['page']} (county mentions: {page_info['county_count']})")
            
            # Try multiple extraction methods for this specific page
            page_tables = self.extract_from_single_page(pdf_path, page_num)
            
            for table_info in page_tables:
                if self.validate_county_table(table_info['data']):
                    table_info['source_page'] = page_info['page']
                    table_info['confidence'] = self.calculate_confidence(table_info['data'])
                    extracted_tables.append(table_info)
        
        # Sort by confidence and return best
        extracted_tables.sort(key=lambda x: x['confidence'], reverse=True)
        return extracted_tables
    
    def extract_from_single_page(self, pdf_path, page_num):
        """Extract tables from a specific page using multiple methods"""
        tables = []
        
        # Method 1: PDFPlumber
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page = pdf.pages[page_num]
                page_tables = page.extract_tables()
                
                for i, table in enumerate(page_tables):
                    if table and len(table) > 5:
                        df = pd.DataFrame(table[1:], columns=table[0])
                        tables.append({
                            'data': df,
                            'method': 'PDFPlumber',
                            'table_index': i
                        })
        except Exception as e:
            logger.warning(f"PDFPlumber failed on page {page_num + 1}: {e}")
        
        # Method 2: Camelot Lattice for specific page
        try:
            camelot_tables = camelot.read_pdf(str(pdf_path), pages=str(page_num + 1), flavor='lattice')
            for i, table in enumerate(camelot_tables):
                if not table.df.empty and len(table.df) > 5:
                    tables.append({
                        'data': table.df,
                        'method': 'Camelot-Lattice',
                        'table_index': i
                    })
        except Exception as e:
            logger.warning(f"Camelot Lattice failed on page {page_num + 1}: {e}")
        
        # Method 3: Camelot Stream for specific page
        try:
            camelot_tables = camelot.read_pdf(str(pdf_path), pages=str(page_num + 1), flavor='stream')
            for i, table in enumerate(camelot_tables):
                if not table.df.empty and len(table.df) > 5:
                    tables.append({
                        'data': table.df,
                        'method': 'Camelot-Stream',
                        'table_index': i
                    })
        except Exception as e:
            logger.warning(f"Camelot Stream failed on page {page_num + 1}: {e}")
        
        # Method 4: Tabula for specific page
        try:
            tabula_tables = tabula.read_pdf(str(pdf_path), pages=[page_num + 1], multiple_tables=True)
            for i, table in enumerate(tabula_tables):
                if not table.empty and len(table) > 5:
                    tables.append({
                        'data': table,
                        'method': 'Tabula',
                        'table_index': i
                    })
        except Exception as e:
            logger.warning(f"Tabula failed on page {page_num + 1}: {e}")
        
        return tables
    
    def validate_county_table(self, df):
        """Validate if dataframe contains county data"""
        if df.empty or len(df) < 10:
            return False
        
        # Convert to string for analysis
        text_content = ' '.join(df.astype(str).values.flatten()).lower()
        
        # Count county mentions
        county_count = sum(1 for county in self.kenya_counties 
                          if county.lower() in text_content)
        
        # Count numeric columns
        numeric_cols = 0
        for col in df.columns:
            try:
                numeric_values = pd.to_numeric(df[col], errors='coerce').dropna()
                if len(numeric_values) > len(df) * 0.5:  # More than 50% numeric
                    numeric_cols += 1
            except:
                continue
        
        # Must have at least 5 counties and 1 numeric column
        return county_count >= 5 and numeric_cols >= 1
    
    def calculate_confidence(self, df):
        """Calculate confidence score for extracted table"""
        score = 0
        
        # County name coverage (0-40 points)
        text_content = ' '.join(df.astype(str).values.flatten()).lower()
        county_matches = sum(1 for county in self.kenya_counties 
                           if county.lower() in text_content)
        score += min(40, county_matches * 2)
        
        # Numeric columns (0-30 points)
        numeric_cols = 0
        for col in df.columns:
            try:
                numeric_values = pd.to_numeric(df[col], errors='coerce').dropna()
                if len(numeric_values) > len(df) * 0.7:
                    numeric_cols += 1
            except:
                continue
        score += min(30, numeric_cols * 10)
        
        # Table size (0-20 points)
        if 30 <= len(df) <= 50:  # Good range for county data
            score += 20
        elif 20 <= len(df) <= 60:
            score += 15
        elif 10 <= len(df) <= 70:
            score += 10
        
        # Population-like numbers (0-10 points)
        for col in df.columns:
            try:
                numeric_values = pd.to_numeric(df[col], errors='coerce').dropna()
                if len(numeric_values) > 0:
                    total_sum = numeric_values.sum()
                    if 30000000 <= total_sum <= 60000000:  # Kenya population range
                        score += 10
                        break
                    elif 1000000 <= total_sum <= 100000000:
                        score += 5
                        break
            except:
                continue
        
        return score
    
    def clean_best_table(self, table_info):
        """Clean the best extracted table"""
        df = table_info['data'].copy()
        
        # Remove completely empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Try to identify and rename columns
        new_columns = {}
        for col in df.columns:
            col_str = str(col).lower()
            if any(keyword in col_str for keyword in ['county', 'name', 'area']):
                new_columns[col] = 'County'
            elif 'male' in col_str and 'female' not in col_str:
                new_columns[col] = 'Male'
            elif 'female' in col_str:
                new_columns[col] = 'Female'
            elif any(keyword in col_str for keyword in ['total', 'population', 'both']):
                new_columns[col] = 'Total'
        
        df = df.rename(columns=new_columns)
        
        # Clean numeric columns
        for col in ['Male', 'Female', 'Total']:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(r'[^\d]', '', regex=True),
                    errors='coerce'
                )
        
        # Filter to rows that look like counties
        if 'County' in df.columns:
            county_mask = df['County'].astype(str).str.len() > 3
            df = df[county_mask]
        
        return df
    
    def run_enhanced_extraction(self):
        """Enhanced extraction workflow"""
        logger.info("🚀 Starting Enhanced County Census Data Extraction")
        logger.info("=" * 60)
        
        # Get the downloaded PDF
        pdf_path = self.data_dir / "volume_1_population.pdf"
        
        if not pdf_path.exists():
            logger.error("❌ PDF file not found. Run the basic extractor first.")
            return None
        
        # Step 1: Explore PDF structure
        logger.info("🔍 STEP 1: EXPLORING PDF STRUCTURE")
        analysis = self.explore_pdf_structure(pdf_path)
        
        logger.info(f"📊 Analysis Results:")
        logger.info(f"   📄 Total pages: {analysis['total_pages']}")
        logger.info(f"   📝 Pages with county text: {len(analysis['pages_with_county_text'])}")
        logger.info(f"   📋 Pages with tables: {len(analysis['pages_with_tables'])}")
        logger.info(f"   🎯 Potential data pages: {len(analysis['potential_data_pages'])}")
        
        # Step 2: Extract from most promising pages
        if analysis['potential_data_pages']:
            logger.info("\n🎯 STEP 2: EXTRACTING FROM PROMISING PAGES")
            extracted_tables = self.extract_data_from_promising_pages(pdf_path, analysis['potential_data_pages'])
            
            if extracted_tables:
                best_table = extracted_tables[0]
                logger.info(f"✅ Best table found with confidence: {best_table['confidence']}")
                logger.info(f"   📄 Source page: {best_table['source_page']}")
                logger.info(f"   🔧 Method: {best_table['method']}")
                logger.info(f"   📊 Rows: {len(best_table['data'])}")
                
                # Step 3: Clean and save
                logger.info("\n🧹 STEP 3: CLEANING AND SAVING DATA")
                cleaned_df = self.clean_best_table(best_table)
                
                # Save the data
                output_file = self.processed_dir / "county_population_extracted.csv"
                cleaned_df.to_csv(output_file, index=False)
                
                # Save analysis report
                self.save_analysis_report(analysis, best_table, cleaned_df)
                
                logger.info(f"✅ County data saved to {output_file}")
                logger.info(f"📊 Extracted {len(cleaned_df)} county records")
                
                return cleaned_df
            
            else:
                logger.warning("⚠️  No valid tables found in promising pages")
        
        else:
            logger.warning("⚠️  No promising pages identified")
        
        # Step 3: Fallback - manual page-by-page search
        logger.info("\n🔄 STEP 3: FALLBACK - SYSTEMATIC PAGE SEARCH")
        return self.systematic_page_search(pdf_path)
    
    def systematic_page_search(self, pdf_path):
        """Search through pages systematically for county data"""
        logger.info("🔍 Searching pages systematically for county data...")
        
        best_table = None
        best_confidence = 0
        
        # Search pages 10-40 (where summary tables are typically located)
        for page_num in range(9, min(40, self.get_page_count(pdf_path))):
            logger.info(f"🔍 Checking page {page_num + 1}")
            
            page_tables = self.extract_from_single_page(pdf_path, page_num)
            
            for table_info in page_tables:
                if self.validate_county_table(table_info['data']):
                    confidence = self.calculate_confidence(table_info['data'])
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_table = table_info
                        best_table['source_page'] = page_num + 1
                        best_table['confidence'] = confidence
                        
                        logger.info(f"✅ New best table found on page {page_num + 1} (confidence: {confidence})")
        
        if best_table and best_confidence > 30:  # Minimum confidence threshold
            cleaned_df = self.clean_best_table(best_table)
            
            output_file = self.processed_dir / "county_population_systematic.csv"
            cleaned_df.to_csv(output_file, index=False)
            
            logger.info(f"✅ Systematic search successful!")
            logger.info(f"📄 Best table from page {best_table['source_page']}")
            logger.info(f"🎯 Confidence: {best_confidence}")
            logger.info(f"💾 Saved to {output_file}")
            
            return cleaned_df
        
        else:
            logger.error("❌ Systematic search failed to find valid county data")
            return None
    
    def get_page_count(self, pdf_path):
        """Get total page count of PDF"""
        with pdfplumber.open(pdf_path) as pdf:
            return len(pdf.pages)
    
    def save_analysis_report(self, analysis, best_table, cleaned_df):
        """Save detailed analysis report"""
        report_file = self.processed_dir / "extraction_analysis_report.txt"
        
        with open(report_file, 'w') as f:
            f.write("ENHANCED COUNTY CENSUS EXTRACTION ANALYSIS\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("PDF STRUCTURE ANALYSIS:\n")
            f.write(f"Total pages: {analysis['total_pages']}\n")
            f.write(f"Pages with county text: {len(analysis['pages_with_county_text'])}\n")
            f.write(f"Pages with tables: {len(analysis['pages_with_tables'])}\n\n")
            
            if analysis['potential_data_pages']:
                f.write("MOST PROMISING PAGES:\n")
                for page_info in analysis['potential_data_pages']:
                    f.write(f"Page {page_info['page']}: {page_info['county_count']} counties mentioned\n")
                f.write("\n")
            
            f.write("BEST EXTRACTION RESULT:\n")
            f.write(f"Source page: {best_table['source_page']}\n")
            f.write(f"Extraction method: {best_table['method']}\n")
            f.write(f"Confidence score: {best_table['confidence']}\n")
            f.write(f"Final records: {len(cleaned_df)}\n")
            f.write(f"Columns: {list(cleaned_df.columns)}\n\n")
            
            if 'Total' in cleaned_df.columns:
                f.write(f"Total population: {cleaned_df['Total'].sum():,}\n")
        
        logger.info(f"📋 Analysis report saved to {report_file}")

def main():
    """Main execution"""
    print("🔬 Enhanced County Census Data Extractor")
    print("=" * 50)
    print("🎯 Advanced PDF analysis and data extraction")
    print("📊 Multiple extraction strategies")
    print("=" * 50)
    
    extractor = EnhancedCountyExtractor()
    result = extractor.run_enhanced_extraction()
    
    if result is not None:
        print("\n" + "=" * 60)
        print("🎉 ENHANCED EXTRACTION SUCCESSFUL!")
        print("=" * 60)
        print(f"✅ Extracted {len(result)} county records")
        print("📁 Check data/processed/census_2019/ for results")
        print("📋 See extraction_analysis_report.txt for details")
    else:
        print("\n" + "=" * 60)
        print("❌ ENHANCED EXTRACTION FAILED")
        print("=" * 60)
        print("💡 The PDF may require manual inspection")

if __name__ == "__main__":
    main()