# Five-minute presentation notes

The slides are in English to match the course brief and project notebooks. Timing below totals approximately five minutes. Every group member should be able to present all sections and operate the dashboard.

## Slide 1 — Research question (25 seconds)

We study air quality in Athens. Our goal is to compare monitoring locations, identify weather conditions associated with fine particles, forecast daily concentrations and organize stations geographically. Introduce the four team members without assigning unverified individual contributions.

## Slide 2 — Dataset and KDD (40 seconds)

The Athens CSV comes from the Air Quality Monitoring in European Cities dataset on Kaggle. It contains 1,726,464 hourly records, 19 columns and 64 monitoring stations, covering May 2020 to May 2023. Time, coordinates and environmental measurements give us the three dimensions required by the project. We explore missing values and extreme observations before aggregation and analysis. Some measurements are labelled CAMS in the source: avoid claiming every value is a direct physical sensor measurement.

## Slide 3 — Station aggregation (35 seconds)

We group hourly records by station. We calculate mean and maximum PM2.5, mean NO₂ and a count of observations above 25 micrograms per cubic metre. ATH-ENVICARE-0 and ATHINAS share the highest mean PM2.5, about 23.03 micrograms per cubic metre. ATHINAS has 8,333 hourly records above the cutoff. These indicators answer where typical or extreme concentrations are higher. The cutoff is an analytical choice applied to hourly measurements: do not call this a legal or health compliance calculation. A station with more observed hours may have a higher raw exceedance count, so coverage matters.

## Slide 4 — Apriori (45 seconds)

We first aggregate each station's measurements by day. Each environmental variable is split into low, medium and high using its first and third quartiles. We create Boolean transactions and apply Apriori with minimum support 5%, then generate association rules with minimum confidence 10%. In the recalculated results there are 90 frequent itemsets, 300 rules and 10 rules targeting high PM2.5. Low wind is the strongest positive association: lift 1.804 and confidence 44.88%. Confidence is the proportion of low-wind observations that also have high PM2.5; lift compares that confidence with the overall high-PM2.5 frequency. This is not a causal finding, and “high” is a relative category, not a regulatory threshold.

## Slide 5 — Forecasting (45 seconds)

We calculate a daily network mean, giving each available station equal weight. The final 30 days form a test period, excluded from model fitting. Holt-Winters uses an additive damped trend and seven-day seasonality. We compare it with a baseline that repeats the final observed training week. Recalculated test MAE is 4.039497 for Holt-Winters versus 4.339170 for the baseline; RMSE is 4.834095 versus 5.412688. The improvement is modest and only demonstrated on this holdout period. After evaluation, the model is fitted on the full history to produce a 30-day forecast after the dataset ends, in May 2023. This is not a prediction for the current date. Small differences from the original notebook's saved metrics reflect numerical optimization/environment differences; the displayed two-decimal metrics are unchanged.

## Slide 6 — Spatial clustering (40 seconds)

We retain one location per station and run DBSCAN on latitude and longitude using haversine distance. Epsilon is 2 kilometres and minimum samples is three, including the station itself. Recalculated results identify five groups, with 32 stations labelled noise. Those stations are geographically isolated under these settings, not necessarily faulty. Pollution is not an input to the clustering. We compute mean daily PM2.5 by station and summarize it within each geographical group afterwards. Different density settings may change the groups.

## Slide 7 — Dashboard and transition to demo (30 seconds)

The offline HTML dashboard brings the four perspectives together using Plotly. Show a station comparison, inspect a rule, compare forecast observations and predictions, then show the spatial groups. Conclude that low wind accompanies higher PM2.5 in this dataset, the forecasting model improves slightly on a simple baseline in the recalculated test, and geographical grouping helps compare monitoring locations. Mention missing values, extreme observations, parameter sensitivity and limited model validation.

## Demo checklist

- Open the dashboard before the presentation and verify all four views.
- Explain that all dashboard values were recalculated from the original CSV; this is a historical dataset, not a live air-quality feed.
- Keep a static HTML/PDF dashboard export available as supporting evidence.
- Do not rerun package installation cells live.
- The Kaggle CSV is not stored in this repository because of its size.
- Confirm instructor dataset approval and the final submission leader separately; neither is established by the repository.

## Evidence and reproduction

- Numerical findings and regenerated forecast/spatial images come from `results/analysis.json`, recalculated by `analysis_pipeline.py` from the original CSV. Source SHA-256: `9acd164c24ea0adbf8decef35266c2ff3b7ec0d5790cf0138166d85f904a8a82`.
- Query methods follow `Data_Project.ipynb` and `Query34_Frequent_Pattern_Mining.ipynb`.
- Team names and the dataset description come from `README.md`.
- Regenerate with `python presentation/build_slides.py` using an environment with Matplotlib. The script reads the recomputed JSON and regenerates the plots; it does not rerun the dataset analysis.
- The PDF contains seven 16:9 slides. `presentation/previews/` contains matching PNG previews; `presentation/assets/` contains the regenerated temporal and spatial plots.
