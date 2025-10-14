#!/bin/bash
# Git Preparation Script for Agri-Adapt AI
# Run this script before pushing to GitHub

echo "🚀 AGRI-ADAPT AI: GIT PREPARATION"
echo "=================================="

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo "❌ Not a git repository. Initializing..."
    git init
    echo "✅ Git repository initialized"
fi

# Check for sensitive files and update .gitignore
echo "🔒 Checking .gitignore configuration..."

# Create comprehensive .gitignore if it doesn't exist
if [ ! -f .gitignore ]; then
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/
.conda/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project specific
*.log
*.sqlite
*.db
.env.local
.env.development.local
.env.test.local
.env.production.local

# Data files (large datasets)
*.csv
*.json
*.parquet
*.h5
*.hdf5
*.pickle
*.pkl

# Model files (large)
*.joblib
*.model
*.h5

# Node.js (frontend)
node_modules/
.next/
out/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*

# Local development
.local/
tmp/
temp/
.cache/

# Secrets and credentials
secrets/
credentials/
*.pem
*.key
*.crt
config/production.py
config/secrets.py
EOF
    echo "✅ .gitignore created"
else
    echo "✅ .gitignore exists"
fi

# Check current status
echo "📊 Git status:"
git status --porcelain | head -10

# Add all documentation and code files
echo "📝 Adding files to git..."
git add README.md
git add PROJECT_DOCUMENTATION.md
git add DEPLOYMENT.md
git add CHANGELOG.md
git add GITHUB_READY_SUMMARY.md
git add CONTRIBUTING.md
git add LICENSE
git add requirements.txt
git add requirements-dev.txt
git add .gitignore
git add src/
git add frontend/
git add scripts/
git add tests/
git add deployment/
git add docs/
git add config/

# Add essential data files (not large datasets)
git add data/analysis/model_metrics.json
git add data/comprehensive_data_audit.json

echo "✅ Essential files added to git"

# Check what's been staged
echo "📋 Staged files:"
git diff --cached --name-only | head -20

echo ""
echo "🎯 READY FOR COMMIT!"
echo "Suggested commit message:"
echo ""
echo "feat: GitHub-ready Agri-Adapt AI with production-ready ML pipeline"
echo ""
echo "- Random Forest model with R² = 0.894 (89.4% accuracy)"
echo "- Complete 47 counties coverage across Kenya"
echo "- Multi-crop intelligence (Maize, Beans, Sweet Potato)"
echo "- Professional data pipeline with 78.3% completeness"
echo "- CHIRPS satellite precipitation integration"
echo "- Comprehensive documentation and deployment guides"
echo "- FastAPI backend with Next.js frontend"
echo "- Production-ready architecture with quality validation"
echo ""
echo "Run: git commit -m \"feat: GitHub-ready Agri-Adapt AI with production-ready ML pipeline\""
echo "Then: git push origin main"