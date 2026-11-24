# EduShield AI — PS164
**AI-Powered Student Risk Detection and Early Intervention System**

## Stack
- **Backend**: FastAPI + Python (risk engine + NVIDIA NIM)
- **Frontend**: React (single HTML file, no build step required)

## Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate synthetic data
```bash
python generate_data.py
```

### 3. (Optional) Add an NVIDIA NIM API key
Create a `.env` file:
```
NVIDIA_API_KEY=your_key_here
# Optional: defaults to nvidia/nemotron-3-nano-30b-a3b
NVIDIA_NIM_MODEL=nvidia/nemotron-3-nano-30b-a3b
```
Create a key at https://build.nvidia.com
Without a key, the app uses high-quality mock reports automatically.

### 4. Start the FastAPI backend
```bash
uvicorn backend.main:app --reload --port 8000
```

### 5. Open the frontend
Open `frontend/index.html` in your browser.
*(Or serve it: `python -m http.server 3000 --directory frontend`)*

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/metrics` | Cohort-level summary metrics |
| GET | `/api/cohort?tier=High` | All students, optional tier filter |
| GET | `/api/student/{id}` | Single student full profile |
| POST | `/api/report` | Generate AI risk report |
| GET | `/api/report/download/{id}` | Download report as .txt |
| GET | `/api/report/batch-zip` | Download all High risk reports as .zip |

## Project Structure
```
edushield-ai/
├── backend/
│   └── main.py          ← FastAPI app + all API routes
├── frontend/
│   └── index.html       ← React SPA (no build step)
├── data/                ← Generated synthetic datasets
├── data_loader.py       ← Data ingestion + feature computation
├── risk_engine.py       ← Weighted risk scoring
├── llm_client.py        ← NVIDIA NIM API integration
├── generate_data.py     ← Synthetic data generator
└── requirements.txt
```
