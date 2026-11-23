# Delivery validation — 23 November 2026

## Data and computation

- Downloaded the original Athens CSV through the Kaggle public GET endpoint, extracted only `athens_data.csv` and excluded it from Git.
- Source SHA-256: `9acd164c24ea0adbf8decef35266c2ff3b7ec0d5790cf0138166d85f904a8a82`.
- Recomputed all four analyses on 1,726,464 rows, 19 columns and 64 stations. No synthetic observations are used in delivered indicators.
- Executed all 10 cells of `Soukaina_Bahami_notebook.ipynb` with an actual Python kernel. The original team notebooks are unchanged.
- Apriori: 90 frequent itemsets, 300 rules, 10 high-PM2.5 rules, 71,585 complete station-days. Low-wind lift 1.804260 and confidence 0.448790 reproduce the saved team results.
- DBSCAN: 5 clusters and 32 noise stations reproduce the saved results.
- Recalculated Holt-Winters MAE 4.039497 and RMSE 4.834095, compared with baseline 4.339170 and 5.412688. Small differences from the original notebook's forecast optimizer are retained honestly. Slides and dashboard use recalculated results.
- Three unit tests pass: joint itemset support/pruning, exclusion of test values from training and imputation, haversine kilometer radius with isolated noise.

## Dashboard checks

- Desktop Chromium viewport 1440×1100: charts render without console errors.
- Station ranking switches between 15 and all 64 stations; container height adapts to avoid clipping. Metrics include mean/max PM2.5, mean NO₂ and exceedance observations.
- Rules: 10 initially shown; confidence ≥40% reduces the selection to 2; resetting restores 10. Wrapped compound labels visually checked.
- Forecast: 3 holdout traces; future view contains 30 predicted days.
- Spatial display: all 64 stations, 32 noise stations and 5 cluster summaries; noise selection behaves correctly.
- JSON download: captured the generated Blob and verified its parseable content and original row count.
- Print action: intercepted browser print call and verified all 6 chart containers render before invocation. Actual printer output is not validated; the standalone HTML is the dashboard evidence artifact.
- Opened the HTML directly through `file://`, emulated offline networking, and checked all five tabs at a 390×844 mobile viewport: no document horizontal overflow or dashboard error messages.
- Captures of the initial repository, dashboard views, offline mobile view and slide preview were saved separately in the user's requested Desktop folder. They are not repository source files.

## Slides and submission limits

- PDF generated from computed JSON: seven 16:9 slides, searchable text, rendered PNG previews visually inspected.
- Editable Python source and timed speaker notes included.
- Dashboard and slides are in English, consistent with the supplied course brief.
- Instructor approval, group leader designation and actual oral presentation are not established by these checks. All members still need to rehearse the demonstration and questions.
- No GitHub Pages or other hosting deployment is required: download and open the self-contained HTML. No third-party account connection is needed by the dashboard.
