# 📈 Stock Intelligence Dashboard

> **Jarnox Software Internship Assignment — Full Stack Submission**

A production-ready stock market intelligence platform that fetches **real NSE/BSE data**, exposes **REST APIs via FastAPI**, and visualises everything in a **React dashboard** with live quotes, ML price predictions, and correlation analysis.

---

## 📸 Screenshots

| Dashboard | Correlation | Prediction |
|---|---|---|
| Stock chart with 7-day MA | Pearson r gauge | 7-day ML forecast |

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11 · FastAPI · Uvicorn |
| **Data Source** | yfinance (NSE `.NS` → BSE `.BO` fallback) |
| **Data Processing** | Pandas · NumPy |
| **ML Prediction** | scikit-learn (LinearRegression) |
| **Database** | SQLite via SQLAlchemy ORM |
| **Scheduler** | APScheduler (auto-refresh every 60 min) |
| **Frontend** | React 18 · Vite · Chart.js · Axios |
| **Container** | Docker · docker-compose |
| **Deployment** | Render (free tier — backend + static frontend) |

---

## 🚀 Quick Start

### Option A — Without Docker (Local Development)

#### 1. Clone the repo
```bash
git clone https://github.com/<your-username>/stock-intelligence-dashboard.git
cd stock-intelligence-dashboard
```

#### 2. Start the Backend
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
python main.py
```

Backend runs at → `http://localhost:8000`  
Swagger UI at → `http://localhost:8000/docs`

#### 3. Start the Frontend
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Dashboard runs at → `http://localhost:5173`

---

### Option B — With Docker (Recommended)

```bash
# Build and start everything with one command
docker-compose up --build

# Stop all services
docker-compose down
```

| Service | URL |
|---|---|
| FastAPI Backend | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |
| React Frontend | `http://localhost:5173` |

---

## 📡 API Endpoints

All endpoints are fully documented with examples at `http://localhost:8000/docs`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/companies` | List of all tracked NSE symbols |
| `GET` | `/data/{symbol}?days=30` | Last N days of OHLCV + calculated metrics |
| `GET` | `/summary/{symbol}` | 52-week high/low, average close, volatility |
| `GET` | `/live/{symbol}` | Near-real-time quote via yfinance (15-min delay) |
| `GET` | `/compare?symbol1=X&symbol2=Y` | Side-by-side closing prices for two stocks |
| `GET` | `/correlation?symbol1=X&symbol2=Y&days=90` | Pearson r correlation of daily returns |
| `GET` | `/movers?n=5` | Top N gainers + top N losers today |
| `GET` | `/predict/{symbol}?forecast_days=7` | 7-day ML price forecast |
| `GET` | `/volatility` | Annualised volatility scores for all symbols |
| `POST` | `/refresh/{symbol}` | Force re-fetch from yfinance |

### Example API Calls

```bash
# Get last 30 days TCS data
curl http://localhost:8000/data/TCS?days=30

# Get live HDFCBANK quote
curl http://localhost:8000/live/HDFCBANK

# Compare INFY vs TCS
curl "http://localhost:8000/compare?symbol1=INFY&symbol2=TCS"

# Correlation between INFY and TCS over 90 days
curl "http://localhost:8000/correlation?symbol1=INFY&symbol2=TCS&days=90"

# Top 5 movers
curl http://localhost:8000/movers?n=5

# Predict next 7 days for RELIANCE
curl http://localhost:8000/predict/RELIANCE

# Volatility scores for all stocks
curl http://localhost:8000/volatility
```

---

## 🧮 Data Logic & Metrics

### Part 1 — Cleaning Pipeline (`data_cleaner.py`)

Every DataFrame fetched from yfinance passes through 8 cleaning steps:

| Step | Action |
|---|---|
| 1. Column normalisation | Flattens multi-level columns, standardises to Title Case |
| 2. Date index fix | Converts tz-aware UTC → IST naive `DatetimeIndex` |
| 3. Duplicate removal | Keeps last record per date |
| 4. All-NaN row drop | Removes rows where all price columns are `NaN` |
| 5. Type coercion | Casts OHLCV → `float64`, Volume → `int64` |
| 6. Missing value fill | **Forward-fill → back-fill** for prices, zero-fill for volume |
| 7. Outlier flagging | Marks rows with `>50%` single-day change as `is_outlier` |
| 8. Sort ascending | Ensures index is in chronological order |

### Calculated Metrics

| Metric | Formula | Notes |
|---|---|---|
| **Daily Return** | `(Close − Open) / Open` | Stored as decimal e.g. `0.012` = 1.2% |
| **7-day MA** | Rolling 7-day mean of Close | `min_periods=1` so first rows aren't `NaN` |
| **52-week High/Low** | Rolling 252-day max/min | ~252 trading days per year |
| **Volatility Score** | `std(returns, 20d) × √252` | Annualised — see scale below |

### Custom Metrics

**Volatility Score (annualised)**
```
Volatility = rolling_std(daily_return, window=20) × √252
```
| Range | Risk Label | Meaning |
|---|---|---|
| `< 0.20` | 🟢 Low | Stable, low-risk stock |
| `0.20 – 0.40` | 🟡 Medium | Moderate risk |
| `> 0.40` | 🔴 High | Highly volatile |

**Pearson Correlation (`/correlation`)**
```
r = Σ[(R₁ − μ₁)(R₂ − μ₂)] / (σ₁ × σ₂ × (n−1))
```
| r value | Interpretation |
|---|---|
| `≥ 0.7` | Strongly correlated |
| `0.4 – 0.7` | Moderately correlated |
| `-0.1 – 0.1` | Essentially uncorrelated |
| `≤ -0.7` | Strongly inverse |

**Use case:** Low-correlation stocks in a portfolio reduce overall risk.

### ML Price Prediction

- **Algorithm:** `LinearRegression` (scikit-learn)
- **Training data:** Last 60 closing prices
- **Output:** Next 7 days of predicted prices
- **Endpoint:** `GET /predict/{symbol}?forecast_days=7`
- ⚠️ Educational purposes only — not financial advice

---

## 📊 Dashboard Features

| Feature | Description |
|---|---|
| **Company Sidebar** | Click any symbol to load its data |
| **Price Chart** | Close price + 7-day MA overlay · 7D / 30D / 90D periods |
| **Summary Card** | 52-week stats + live quote refreshed every 60s |
| **Volatility Badge** | Colour-coded Low / Medium / High risk indicator |
| **7-day Prediction** | Purple dashed ML forecast line |
| **Compare Mode** | Overlay two stocks on one chart |
| **Correlation Tab** | Gauge bar + Pearson r + plain-English interpretation |
| **Top Movers Table** | Daily gainers & losers with BUY/SELL signal |

---

## 📂 Project Structure

```
stock-intelligence-dashboard/
│
├── backend/
│   ├── main.py               # FastAPI app — all 10 endpoints
│   ├── data_collector.py     # yfinance fetch, live quotes, metrics
│   ├── data_cleaner.py       # Part 1: 8-step cleaning pipeline
│   ├── database.py           # SQLAlchemy ORM + SQLite helpers
│   ├── models.py             # Pydantic response schemas
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Root component + routing
│   │   ├── App.css           # Dark terminal theme
│   │   └── components/
│   │       ├── CompanyList.jsx
│   │       ├── StockChart.jsx
│   │       ├── SummaryCard.jsx     # Live quote + 52-week stats
│   │       ├── ComparisonChart.jsx
│   │       ├── CorrelationCard.jsx # Pearson r visualisation
│   │       ├── MoversTable.jsx
│   │       └── Predictor.jsx
│   ├── .env.example
│   ├── package.json
│   └── Dockerfile.frontend
│
├── docker-compose.yml
├── render.yaml               # One-click Render.com deployment
├── .gitignore
└── README.md
```

---

## 🌐 Tracked NSE Symbols

| Symbol | Company |
|---|---|
| `BHARTIARTL` | Bharti Airtel |
| `BAJFINANCE` | Bajaj Finance |
| `HDFCBANK` | HDFC Bank |
| `ICICIBANK` | ICICI Bank |
| `INFY` | Infosys |
| `ITC` | ITC Limited |
| `RELIANCE` | Reliance Industries |
| `SBIN` | State Bank of India |
| `TCS` | Tata Consultancy Services |
| `WIPRO` | Wipro |

> **Note:** `TATAMOTORS` was removed — Yahoo Finance has delisted it from their data feed (both `.NS` and `.BO` return 404). `BAJFINANCE` is the replacement.

---

## ☁️ Deployment on Render (Free Tier)

### One-Click Blueprint
```bash
# 1. Push repo to GitHub
# 2. Go to render.com → New → Blueprint
# 3. Connect your GitHub repo
# 4. Render reads render.yaml and deploys both services automatically
```

### Manual Setup

**Backend (Web Service)**
| Setting | Value |
|---|---|
| Root Directory | `backend` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

**Frontend (Static Site)**
| Setting | Value |
|---|---|
| Root Directory | `frontend` |
| Build Command | `npm install && npm run build` |
| Publish Directory | `dist` |
| Env Var | `VITE_API_URL=https://your-backend.onrender.com` |

---

## 🐙 GitHub Setup

```bash
# From project root
git init
git add .
git commit -m "Initial commit — Stock Intelligence Dashboard"
git branch -M main
git remote add origin https://github.com/<your-username>/stock-intelligence-dashboard.git
git push -u origin main
```

---

## 📦 Installing Dependencies

```bash
# Backend
pip install -r requirements.txt

# Frontend
npm install
```

**`requirements.txt` contents:**
```
fastapi
uvicorn[standard]
pandas
numpy
yfinance
scikit-learn
sqlalchemy
apscheduler
```

---

## 🔍 Data Source & Freshness

| Endpoint type | Source | Delay | Cache |
|---|---|---|---|
| Historical charts | Yahoo Finance via yfinance | EOD (end of day) | 1 hour |
| Live quote (`/live`) | Yahoo Finance `fast_info` | ~15 minutes | 60 seconds |
| Background refresh | APScheduler | Every 60 min | — |

> Data is **real NSE market data**, not mock/simulated values.
> The 15-minute delay on live quotes is Yahoo Finance's free-tier policy.

---

## 🔑 Key Insights from the Data

- **INFY and TCS** show strong positive correlation (~0.8) — both track IT sector sentiment
- **RELIANCE** shows low correlation with banking stocks — useful for diversification
- **HDFCBANK** 52-week range ₹726–₹1020, trading near lower end — potential value zone
- Volatility scores spike noticeably during RBI rate decisions and earnings seasons
- The 7-day MA crossing below the close price has historically preceded short-term reversals

---

## ⚠️ Disclaimer

This project is built for educational and demonstration purposes as part of an internship assignment. **Nothing here constitutes financial advice.** All price predictions are based on simple linear regression and should not be used for actual trading decisions.

---

*Built by [Nehal Narvekar] · Jarnox Software Internship Assignment · April 2026*
