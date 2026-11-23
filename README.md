# Athens Air Observatory

Final project for **Programming for Data Science — ESILV**. We apply KDD to air quality and meteorological data from Athens.

**Team:** Guilhem LE DU, Anais KAMTCHOUANG NONO, Yutong CAO, Soukaina BAHAMI.

## Deliverables

- **[Interactive dashboard](Soukaina_Bahami_dashboard.html):** download the raw HTML and double-click it. All results and Plotly are embedded; no server, Internet or CSV is needed. GitHub's file viewer does not execute HTML.
- **[Slides PDF](Soukaina_Bahami_slides.pdf):** seven slides for a five-minute presentation.
- **[Integrated notebook](Soukaina_Bahami_notebook.ipynb):** exploration, documented queries, computation and dashboard display.
- **[Speaker notes](presentation/speaker_notes.md):** presentation timing and demonstration guide.
- **[Computed results](results/analysis.json):** indicators, source SHA-256 and computation timestamp.

The prefix identifies these deliverables; rename submission files if the designated group leader is another member. Instructor dataset approval is not evidenced here. Original team notebooks are preserved as development history.

## Dataset

[Air Quality Monitoring in European Cities — yekenot, Kaggle](https://www.kaggle.com/datasets/yekenot/air-quality-monitoring-in-european-cities). The Athens CSV contains **1,726,464 hourly observations × 19 columns**, **64 stations**, **1 May 2020–29 May 2023**.

Temporal dimension: `Date`. Spatial: `Latitude`, `Longitude`, `station_name`. Analytical: PM10, PM2.5, NO₂, O₃, wind, temperature, humidity and other environmental variables. No external enrichment dataset is used.

The original CSV (459 MB) is excluded from Git. Download it from Kaggle, then place it at `data/athens_data.csv`. Source SHA-256 for this delivery: `9acd164c24ea0adbf8decef35266c2ff3b7ec0d5790cf0138166d85f904a8a82`.

Public direct download, when available (returns a ZIP):

```bash
curl -L "https://www.kaggle.com/api/v1/datasets/download/yekenot/air-quality-monitoring-in-european-cities?file_name=athens_data.csv" -o athens.zip
```

Extract `athens_data.csv` into `data/`. A HEAD request may return 404 although the GET download succeeds.

## Reproduce

Use Python 3.11+ in a dedicated environment:

```bash
git clone https://github.com/guylemme/Data_Science_Athens.git
cd Data_Science_Athens
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python analysis_pipeline.py data/athens_data.csv --output results/analysis.json
python build_dashboard.py
python presentation/build_slides.py
python -m unittest discover -s tests -v
```

Alternatively, run `Soukaina_Bahami_notebook.ipynb` from the repository root with a Jupyter kernel containing the requirements. Jupyter is optional and installed separately. Its main block runs all four queries, builds the HTML and displays it in an iframe.

Bundled JSON and HTML let readers inspect results without downloading the CSV. Delivery package versions are recorded in `results/environment.json`; optimizer differences may slightly change forecast decimals.

## Four queries

| Query | Method | Interpretation |
|---|---|---|
| Station comparison | Station PM2.5 mean/max, NO₂ mean, hours with PM2.5 >25 µg/m³ | Full-period ranking; the hourly reference is exploratory, not a compliance test. |
| Weather associations | Station-day averages, quartile categories, Apriori support ≥5% and confidence ≥10% | Conditions associated with high PM2.5 (>Q3), without causal claims. |
| Temporal forecasting | Equal-weight daily station means; additive damped Holt-Winters with weekly seasonality; last 30 days held out | MAE/RMSE versus weekly seasonal naive, then refit for the next 30 days. |
| Spatial clustering | DBSCAN, haversine distance, 2 km radius, minimum neighborhood size 3 | Geographical groups; pollution is compared after grouping. |

The dashboard includes station metrics/ranking filters, rule lift/confidence filters, holdout/future views, cluster/noise selection, missingness, method explanations, JSON export and print-to-PDF. Controls filter precomputed results; they do not retrain models.

## Findings and limits

- Apriori: **90 itemsets, 300 rules, 10 high-PM2.5 target rules** over **71,585 complete station-days**. Low wind: confidence **44.88%**, lift **1.804**. High PM2.5 means above the daily third quartile, approximately **17.91 µg/m³**.
- Holt-Winters: holdout **MAE ≈4.04, RMSE ≈4.83 µg/m³**, compared with **4.34 and 5.41** for seasonal naive. This is one historical holdout. Forecasts start **30 May 2023**, not today; no prediction intervals are produced.
- DBSCAN: **5 geographical clusters, 32 noise stations**. Noise means spatial isolation, not erroneous measurements. Cluster IDs have no ordinal pollution meaning.
- Missing weather, station types and coverage affect representativeness. High positive outliers are retained. A network average is not a population exposure estimate. Associations are not causal effects.

## Implementation and validation

`analysis_pipeline.py` provides documented functions and a local Apriori implementation with downward-closure pruning. `build_dashboard.py` embeds results and Plotly into `dashboard/template.html`. `presentation/build_slides.py` creates the PDF and previews from computed results.

Original notebooks (`Data_Project.ipynb`, `query2/Query2_Frequent_Pattern_Mining.ipynb`, `Query34_Frequent_Pattern_Mining.ipynb`) remain available; use the integrated notebook for the completed workflow.

Tests cover itemset supports, absence of holdout leakage and DBSCAN kilometer units. See `VALIDATION.md` for browser, notebook and delivery checks.
