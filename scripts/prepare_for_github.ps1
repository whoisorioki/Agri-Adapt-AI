# Git Preparation Script for Agri-Adapt AI (PowerShell)
# Run this script before pushing to GitHub

Write-Host "🚀 AGRI-ADAPT AI: GIT PREPARATION" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

# Check if we're in a git repository
if (-not (Test-Path .git)) {
    Write-Host "❌ Not a git repository. Initializing..." -ForegroundColor Red
    git init
    Write-Host "✅ Git repository initialized" -ForegroundColor Green
}

# Check current status
Write-Host "📊 Git status:" -ForegroundColor Cyan
git status --porcelain | Select-Object -First 10

# Add all documentation and code files
Write-Host "📝 Adding files to git..." -ForegroundColor Cyan
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

Write-Host "✅ Essential files added to git" -ForegroundColor Green

# Check what's been staged
Write-Host "📋 Staged files:" -ForegroundColor Cyan
git diff --cached --name-only | Select-Object -First 20

Write-Host ""
Write-Host "🎯 READY FOR COMMIT!" -ForegroundColor Yellow
Write-Host "Suggested commit message:" -ForegroundColor Cyan
Write-Host ""
Write-Host "feat: GitHub-ready Agri-Adapt AI with production-ready ML pipeline" -ForegroundColor White
Write-Host ""
Write-Host "- Random Forest model with R² = 0.894 (89.4% accuracy)" -ForegroundColor Gray
Write-Host "- Complete 47 counties coverage across Kenya" -ForegroundColor Gray
Write-Host "- Multi-crop intelligence (Maize, Beans, Sweet Potato)" -ForegroundColor Gray
Write-Host "- Professional data pipeline with 78.3% completeness" -ForegroundColor Gray
Write-Host "- CHIRPS satellite precipitation integration" -ForegroundColor Gray
Write-Host "- Comprehensive documentation and deployment guides" -ForegroundColor Gray
Write-Host "- FastAPI backend with Next.js frontend" -ForegroundColor Gray
Write-Host "- Production-ready architecture with quality validation" -ForegroundColor Gray
Write-Host ""
Write-Host "Run: git commit -m `"feat: GitHub-ready Agri-Adapt AI with production-ready ML pipeline`"" -ForegroundColor Yellow
Write-Host "Then: git push origin main" -ForegroundColor Yellow