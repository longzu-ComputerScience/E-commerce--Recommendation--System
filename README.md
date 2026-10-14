# CS116 — E-Commerce Recommendation & Sales Forecasting

A full-stack e-commerce prototype and two machine learning experiments developed for **CS116: Python Programming for Machine Learning**. The app explores product discovery and recommendation, while the notebooks investigate personalized item recommendation and location-level sales forecasting.

## Components

| Module | What it does | Implementation |
| --- | --- | --- |
| Web application | Product catalog, search, related items, up-sell suggestions, forecast view | [frontend/](frontend/), [backend/](backend/) |
| Task 1 — Personalized Item Recommendation (PIR) | Ranks ten products for each customer from historical purchases and interactions | [Notebook](ml/task1-personalized-recommendation/task1.ipynb), [explanation](ml/task1-personalized-recommendation/explain.md) |
| Task 2 — Location Sales Forecasting (LSF) | Predicts monthly quantities for `(location, item_id)` pairs | [Notebook](ml/task2-sales-forecasting/lsf-latest-full-holiday.ipynb), [explanation](ml/task2-sales-forecasting/explain.md) |

**Stack:** Next.js 14, React 18, TypeScript, Tailwind CSS; Python, FastAPI, Polars; Jupyter, LightGBM, Optuna and scikit-learn.

## Repository layout

```text
backend/                              FastAPI endpoints and recommendation services
frontend/                             Next.js pages and UI components
scripts/preprocess.py                 Product and co-occurrence preprocessing
ml/
  task1-personalized-recommendation/
    task1.ipynb                       PIR notebook
    explain.md / report.md             Task explanation and presentation notes
    experiments/                       Optional PIR experiments (not required for the website)
  task2-sales-forecasting/
    lsf-latest-full-holiday.ipynb      LightGBM forecasting experiment
    explain.md / report.md             Task explanation and presentation notes
    requirements.txt                   Notebook dependencies
data/                                LOCAL ONLY: website runtime parquet
raw_data/                            LOCAL ONLY: source datasets
DATASETS.md                          Expected data and privacy notes
```

## Run locally

**Requirements:** Python 3.10+ and a Node.js version compatible with Next.js 14.

1. Place the datasets at the paths documented in [DATASETS.md](DATASETS.md). The public repository intentionally excludes datasets, models and submissions.
2. Install backend dependencies from the repository root:

   ```bash
   python -m pip install -r backend/requirements.txt
   ```

3. Start the API:

   ```bash
   python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
   ```

   API documentation: <http://localhost:8000/docs>.

4. In a separate terminal, install and start the frontend:

   ```bash
   cd frontend
   npm ci
   npm run dev
   ```

   Browse <http://localhost:3000>. The frontend uses `NEXT_PUBLIC_API_URL` if configured, otherwise `http://localhost:8000/api`.

### Useful commands

| Command | Purpose |
| --- | --- |
| `python scripts/preprocess.py` | Generate the local product and co-purchase parquet files from the appropriate raw datasets |
| `npm run backend` | Run the backend from the repository root after installing requirements |
| `npm run dev` | Run the frontend from the repository root |
| `cd frontend && npm run build` | Validate a production frontend build |

## ML experiments

**Task 1:** Personalized top-10 product recommendation, evaluated using Precision@10 as explained in [Task 1 report](ml/task1-personalized-recommendation/report.md). Supporting exploratory scripts are in the `experiments/` folder.

**Task 2:** Time-aware location/item quantity forecasting with LightGBM; the project reports discuss quantity MAPE. Use `pip install -r ml/task2-sales-forecasting/requirements.txt` for the notebook environment.

The committed notebooks contain editable code without saved execution outputs. Some source cells refer to the original research folder layout, so you may need to adjust paths before rerunning locally. Large outputs and pickled predictions remain in the local archive.

## Data privacy and deployment

- GitHub does **not** contain transaction/customer histories, raw interaction events, serialized customer recommendations, trained models or generated predictions.
- Follow [DATASETS.md](DATASETS.md) to restore local data. Do not redistribute the dataset without appropriate permissions.
- The FastAPI backend loads local parquet on startup. The web app needs the backend running separately; a standalone Next.js deployment does not automatically include this service.
- This is a course demonstration, **not** a production payment or e-commerce platform.

## Project history

The current `main` branch provides one curated version of the website and both tasks. Earlier experiments, duplicate notebooks, bulky model outputs and the previous divergent `ForeCast` worktree were preserved locally during the cleanup; they are not included in this public source snapshot.
