# Scientific Review of the Wikimedia Campaign Suite Web Application

## Abstract
The Wikimedia Campaign Suite is a Streamlit-based analytical web application that evaluates participation dynamics across Wikimedia photo campaigns. It combines event-level contributor extraction from Toolforge with retention analytics and a campaign health scoring framework. This review examines its technical architecture, analytical methods, strengths, and methodological constraints.

## 1. Study Scope and Objective
The application is designed to support organizers and evaluators of Wikimedia campaigns (e.g., Wiki Loves Monuments, Wiki Loves Earth, Wiki Loves Folklore, Wiki Loves Bangla) by answering two core questions:
- How participants move across campaigns and years (retention and migration behavior).
- How healthy a campaign appears relative to regional peer standards.

## 2. System Architecture
The system is composed of:
- **Frontend/UI Layer (`app.py`)**: Streamlit interface with two operational modes (Retention Analytics and Health Evaluation), session-state persistence, and presentation components.
- **Analytics Layer (`analytics.py`)**: Data retrieval, cohort overlap computation, benchmark construction, scoring logic, and visualization generation.
- **Styling Layer (`styles.css`)**: Custom theme integration applied at runtime.
- **Dependency Stack**: `streamlit`, `requests`, `numpy`, `pandas`, `matplotlib`, `seaborn`, `plotly`.

## 3. Data Pipeline and Processing
### 3.1 Input Normalization
Campaign codes are parsed using a regex pattern:
- Event type (`wlf`, `wle`, `wlm`, `wlb`)
- Optional country code
- Two-digit year

Invalid patterns are filtered before analysis.

### 3.2 Data Acquisition
Contributor sets are fetched from Toolforge (`uploadersincat.php`) by constructing category names from event metadata. For structural campaign metrics, file-level metadata is additionally queried from Wikimedia Commons API category members. Fetching is parallelized with `ThreadPoolExecutor` to reduce latency for multi-code analysis.

### 3.3 Caching Strategy
The `get_participants` function uses Streamlit cache (`ttl=3600`), reducing repeated requests and improving responsiveness for recurring queries.

## 4. Analytical Methodology
### 4.1 Retention Analytics Module
Retention between campaign cohorts is computed directionally as:
\[
Retention(Source \rightarrow Target) = \frac{|Source \cap Target|}{|Source|} \times 100
\]

Outputs include:
- Heatmap matrix of directional retention percentages.
- Country-level summary table (mean, median, max, standard deviation).
- Choropleth map for geographic comparison.

### 4.2 Health Evaluation Module
The module computes a weighted composite score (0–100) from four dimensions:
- Retention (50%)
- Growth (20%)
- Quality: deletion-rate signal (15%)
- Diversity: upload concentration, measured as upload share from the top 10% uploaders (15%)

Regional baseline benchmarking is dynamically estimated by:
1. Selecting countries in a chosen region.
2. Identifying top three countries by participant footprint.
3. Averaging their metric values to define the 3-star baseline anchor.

The app then scales campaign metrics relative to this baseline and converts them into star ratings and explanatory insights.

## 5. Scientific Strengths
- **Reproducible computational core** for retention and overlap metrics.
- **Region-aware normalization** instead of fixed global thresholds.
- **Scalable retrieval workflow** via concurrent API calls and caching.
- **Multimodal interpretation support** through tables, heatmaps, and maps.

## 6. Methodological Limitations
- **External dependency risk**: data availability and format are tied to Toolforge endpoint behavior.
- **Regex-constrained input model**: only predefined event code patterns are accepted.
- **Proxy nature of quality signal**: deletion-risk categorization is an operational proxy and may not fully capture long-term media quality.
- **Concentration simplification**: top-10% uploader share captures contributor concentration but not thematic, geographic, or temporal diversity dimensions.
- **Potential baseline volatility**: top-three peer selection may shift with participant count changes.
- **No explicit uncertainty intervals** around reported metrics.

## 7. Validity and Reliability Considerations
- Retention and growth estimates are directly derived from observed participant sets and are computationally traceable.
- Deletion-rate and uploader-concentration metrics are derived from observed campaign file/user records and improve empirical grounding of the health model.
- Health score interpretation should still be treated as a comparative heuristic due to adaptive baseline calibration and proxy-based structural indicators.

## 8. Recommendations for Next Iteration
- Extend structural indicators with additional empirical dimensions (e.g., 30/90-day survival rates, in-use rates, concentration inequality indices such as Gini/Herfindahl).
- Add statistical confidence reporting and sensitivity analysis for benchmark selection.
- Introduce audit logs for fetched campaign snapshots to support reproducibility over time.
- Expand validation with ground-truth evaluations from historical campaign outcomes.

## 9. Conclusion
The Wikimedia Campaign Suite provides a practical and technically coherent analytical platform for campaign monitoring, especially for retention and regional comparative evaluation. Its retention engine is methodologically clear, and the health module now incorporates observable structural indicators (deletion-rate and uploader concentration) benchmarked against top regional performers. With broader structural indicators and uncertainty-aware benchmarking, it can evolve into a stronger scientific-grade evaluation framework.
