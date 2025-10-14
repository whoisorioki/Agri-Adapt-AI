# Copilot Instructions for Agri-Adapt AI Hackathon

## Project Overview
Agri-Adapt AI is a web-based platform delivering a "Maize Drought Resilience Score" for Kenyan counties. The MVP combines a Next.js/React frontend, a FastAPI Python backend, and a Random Forest model trained on historical climate, soil, and weather data. The goal is actionable decision-support for farmers, policymakers, and agronomists.

## Architecture & Data Flow
- **Frontend (`frontend/`)**: Next.js (TypeScript) app for dashboard UI. Communicates with backend via REST API.
- **Backend (`src/api/`, `deployment/`)**: FastAPI service exposes endpoints for resilience scoring. Handles requests from frontend, loads ML models from `models/`, and processes data.
- **ML Model (`models/`, `src/models/`)**: Random Forest model (joblib/pkl) predicts maize yield and resilience score. Input features: rainfall, soil pH, organic carbon, temperature, evapotranspiration, water stress, irrigation volume, and county encoding.
- **Data (`data/`)**: Contains raw, processed, and integrated datasets. Key file: `master_water_scarcity_dataset.csv`.
- **Config (`config/settings.py`)**: Centralized settings for environment, paths, and external integrations.

## Developer Workflows
- **Build/Run Backend**: Use Docker (`deployment/Dockerfile`, `docker-compose.yml`) or run FastAPI locally. Example: `python src/api/main.py` or `docker-compose up`.
- **Build/Run Frontend**: In `frontend/`, use `npm install` then `npm run dev`.
- **Testing**: Python tests in `tests/unit/` and `tests/integration/`. Run with `pytest`.
- **Model Training**: Scripts in `scripts/` (e.g., `retrain_with_enhanced_data.py`).
- **Logs**: Backend logs in `logs/backend.log`.

## Conventions & Patterns
- **Branching**: Use feature branches (e.g., `feature/backend-api`, `feature/ui-design`).
- **Pull Requests**: All changes via PR, reviewed by at least one team member.
- **Data Processing**: Use Polars for fast dataframe operations (see `requirements.txt`).
- **API Response**: Target <1s latency for scoring endpoint.
- **User-Centric Design**: UI optimized for low-literacy, mobile-first users.

## Integration Points
- **External Data**: Integrates OpenWeatherMap, KNBS/KMD for weather and agricultural data.
- **Model Loading**: Backend loads models from `models/` at startup.
- **Frontend-Backend**: REST API endpoints documented in `src/api/`.

## Key Files & Directories
- `README.md`: High-level project summary and architecture diagram.
- `config/settings.py`: Environment and integration settings.
- `src/api/`: FastAPI backend code.
- `frontend/`: Next.js dashboard code.
- `models/`: ML model artifacts.
- `data/`: Datasets for training and scoring.
- `scripts/`: Data processing and model training scripts.
- `tests/`: Unit and integration tests.

## Example Patterns
- **Resilience Score Calculation**: See `README.md` for formula and feature list.
- **Model Inference**: Backend loads `.joblib`/`.pkl` model, receives feature vector, returns score.
- **Data Updates**: New data types (temperature, evapotranspiration) added per PRD updates.

---
For unclear or missing conventions, consult `PROJECT_DOCUMENTATION.md`, `README.md`, or the PRD in `.cursor/rules/project-prd.mdc`.