# Wikimedia Campaign Suite

A Streamlit-based analytics platform for evaluating Wikimedia campaign participation, contributor retention, and campaign health across regional peer benchmarks.

## Overview

The Wikimedia Campaign Suite supports organizers, evaluators, and stakeholders working with Wikimedia campaigns such as Wiki Loves Monuments, Wiki Loves Earth, Wiki Loves Folklore, and Wiki Loves Bangla. It combines live Wikimedia metadata with cohort-based analytics to answer two core questions:

- How contributors move across campaigns and years.
- How healthy a campaign appears relative to regional peer performance.

The application has two main operating modes:

1. Retention Analytics
   - Compare contributor overlap across years and campaigns.
   - View retention matrices, summary tables, and world maps.
2. Health Evaluation
   - Score a campaign using weighted metrics against regional benchmark clusters.
   - Surface diagnostics and actionable insights for program strategy.

## Key Features

- Contributor extraction from Wikimedia campaign categories via Toolforge.
- Regional peer benchmarking by country cluster.
- Weighted health scoring for retention, growth, quality image share, and diversity.
- Retention heatmaps, summary tables, and choropleth map views.
- Downloadable heatmap image exports.
- Streamlit UI tuned for rapid campaign review and reporting.

## Architecture

The project is structured as:

- `app.py` — Streamlit application and UI.
- `analytics.py` — data collection, metric logic, scoring, insights, and visualizations.
- `styles.css` — theme and UI styling.
- `SCIENTIFIC_REVIEW.md` — original methodological review and caveats.

## Methodology

### Retention analytics

Directional campaign retention is calculated as:

Retention(Source -> Target) = (|Source ∩ Target| / |Source|) × 100

This supports cross-year and cross-event movement analysis for contributors.

### Health evaluation

The health score is computed on a 0–100 scale using a weighted composite framework:

- Retention: 40%
- Growth capacity: 25%
- Quality Image: 20%
- Diversity: 15%

The quality image metric uses the Commons category structure and counts files whose category path includes official quality categories such as `Category:Quality images` and `Category:Featured pictures`.

### Regional benchmarking

The campaign is compared against the strongest peer countries in the same geographic group. The app:

1. selects the region for the target campaign,
2. identifies peer countries in that region,
3. computes benchmark values from the top regional performer cluster,
4. normalizes the target campaign against those values.

This reduces unfair comparisons caused by static global thresholds and better reflects regional campaign conditions.

## Scientific review summary

The core analytical design is technically coherent and practically useful for Wikimedia campaign monitoring.

Strengths:

- Reproducible computational workflow for retention and overlap analysis.
- Region-aware normalization instead of rigid global thresholds.
- Parallelized data collection and caching for responsiveness.
- Multi-view reporting through heatmaps, tables, and geographic maps.

Methodological limitations and caveats:

- The project depends on external Wikimedia API and Toolforge behaviors.
- Input is restricted to recognized event patterns and campaign code syntax.
- Quality image status is a practical Commons quality-category proxy rather than a full editorial assessment.
- Concentration-based diversity is informative but does not fully capture thematic or geographic spread.
- Regional benchmarking is comparative and heuristic, not a formal causal model.

## Installation

### Prerequisites

- Python 3.9+
- Internet access for Wikimedia API requests

### Install dependencies

```bash
pip install streamlit requests numpy pandas matplotlib seaborn plotly
```

### Run the app

```bash
streamlit run app.py
```

## Usage

### Campaign syntax

Use campaign identifiers in this form:

`[event][country][year]`

Examples:

- `wlmbd24` — Wiki Loves Monuments Bangladesh 2024
- `wlmde25` — Wiki Loves Monuments Germany 2025
- `wlein22` — Wiki Loves Earth India 2022

### Retention Analytics workflow

1. Choose the suite mode.
2. Enter campaign codes or use the selection builder.
3. Run the dashboard to compute retention matrices and summary tables.
4. Download heatmap images for reporting.

### Health Evaluation workflow

1. Enter the target campaign code.
2. Select the reference model (previous year baseline or custom reference campaign).
3. Choose the geographic region.
4. Run the diagnostic analysis.
5. Review the weighted scorecard and supporting insights.

## Data and quality notes

The scoring model is designed as a comparative evaluation tool instead of a definitive measure of campaign quality. It is best used for trend monitoring, regional comparison, and strategic review.

## License

This project is intended for research and operational analysis use in Wikimedia campaign monitoring. Please review repository policy and licensing terms before redistribution or deployment in production environments.

## Contributing

Contributions are welcome. Improvements that strengthen benchmark calibration, performance, or reliability are especially valuable.
