#!/usr/bin/env python3
"""
Setup and run KNBS census extraction
Installs dependencies and runs the extraction process
"""

import subprocess
import sys
import os
from pathlib import Path

def install_pdf_requirements():
    """Install PDF processing requirements"""
    print("Installing PDF processing libraries...")
    
    requirements = [
        "PyPDF2==3.0.1",
        "pdfplumber==0.9.0", 
        "camelot-py[cv]==0.10.1",
        "tabula-py==2.5.1",
        "opencv-python==4.8.1.78",
        "requests==2.31.0"
    ]
    
    for requirement in requirements:
        try:
            print(f"Installing {requirement}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", requirement])
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to install {requirement}: {e}")
            print("You may need to install it manually")
    
    print("PDF processing libraries installation completed!")

def check_java():
    """Check if Java is available (required for tabula)"""
    try:
        result = subprocess.run(['java', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Java is available for tabula-py")
            return True
        else:
            print("⚠️  Java not found. Tabula-py may not work properly.")
            print("   Install Java from https://www.java.com/download/")
            return False
    except FileNotFoundError:
        print("⚠️  Java not found. Tabula-py may not work properly.")
        print("   Install Java from https://www.java.com/download/")
        return False

def run_extraction():
    """Run the census data extraction"""
    print("\n" + "="*60)
    print("STARTING KNBS CENSUS DATA EXTRACTION")
    print("="*60)
    
    script_path = Path(__file__).parent / "extract_knbs_census.py"
    
    try:
        # Import and run the extractor
        sys.path.append(str(Path(__file__).parent))
        from extract_knbs_census import KNBSCensusExtractor
        
        extractor = KNBSCensusExtractor()
        results = extractor.run_extraction()
        
        print("\n" + "="*60)
        print("🎉 EXTRACTION COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("📁 Check data/processed/census_2019/ for extracted CSV files")
        print("🚀 Phase I Step 4 data is now ready for integration!")
        
        return results
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        print("Check the logs above for details")
        return None

def main():
    """Main setup and extraction workflow"""
    print("KNBS Census Data Extraction Setup")
    print("="*40)
    
    # Step 1: Install dependencies
    print("\n1️⃣ Installing dependencies...")
    install_pdf_requirements()
    
    # Step 2: Check Java availability
    print("\n2️⃣ Checking Java availability...")
    java_ok = check_java()
    
    # Step 3: Run extraction
    print("\n3️⃣ Running extraction...")
    results = run_extraction()
    
    if results:
        print("\n✅ Setup and extraction completed successfully!")
        print("🎯 You now have the census data needed for Phase I Step 4!")
    else:
        print("\n❌ Setup completed but extraction had issues.")
        print("💡 Try running the extraction script directly for more details.")

if __name__ == "__main__":
    main()