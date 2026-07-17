[https://wikistats.streamlit.app/](https://wikistats.streamlit.app/)

# Wikimedia Campaign Suite

The **Wikimedia Campaign Suite** is an advanced analytics platform engineered to monitor, evaluate, and benchmark community participation across international Wikimedia photo competitions (such as *Wiki Loves Monuments*, *Wiki Loves Earth*, and *Wiki Loves Folklore*). By aggregating live log data from Wikimedia Toolforge, the application delivers actionable data visualizations and automated health assessments for community organizers and program evaluators.

---

## 🧭 Application Modules

### 1. Cross-Event Retention Analytics

This module maps how effectively campaigns retain historical contributors over multiple years or translate interest between different competition themes.

* **Heatmap View:** Generates a cross-tabulation matrix calculating the precise percentage directional migration and retention from a source campaign to a target campaign.
* **Comparative Table:** Aggregates multi-year performance parameters including mean, median, maximum, and standard deviation tracking metrics.
* **Choropleth Worldmap:** Renders global metrics using regional geographic layers to identify high-performing territories at a glance.

### 2. Campaign Health Evaluation Suite

Provides an automated diagnostic assessment scorecard by measuring a campaign's performance against historical configurations and localized geographic peer benchmarks.

---

## 📊 Methodology

The evaluation engine leverages a standardized composite weighting framework combined with dynamic cohort normalization to eliminate static geographic bias.

### Health Score Weight Distribution

The overall health score (scaled from 0 to 100) is calculated via a weighted index across four core metrics:

| Metric Pillar | Weight | Description |
| --- | --- | --- |
| **Retention** | **50%** | The proportion of contributors from the baseline campaign who returned to participate in the target campaign. |
| **Growth** | **20%** | The percentage of the active cohort consists of new, first-time participants. |
| **Quality** | **15%** | A calculated stability index evaluating upload survival rates and adherence to deletion guidelines. |
| **Diversity** | **15%** | An outreach equity index measuring the distribution of contributions across the user base to ensure the campaign is not reliant on isolated power-users. |

### Dynamic Regional Benchmarking

To maintain objective scoring, the suite avoids rigid static metrics. Instead, it utilizes an automated peer-grouping framework:

1. **Regional Grouping:** When an event is evaluated, the engine flags its geographic region (e.g., *South Asia*, *ESEAP*, *Northern & Western Europe*).
2. **Footprint Scans:** The platform queries data for all countries within that designated region for both the target and preceding campaign years.
3. **Top 2 Identification:** The engine isolates the **top two countries** within the region displaying the largest active participant footprints.
4. **Baseline Standardization:** The parameters (Retention, Growth, Quality, and Diversity) of these top two volume drivers are averaged. This merged baseline value represents the regional standard and is mapped precisely to a **3-Star (`★★★☆☆`) baseline score** (60 points). Performance above or below this baseline scales dynamically.

---

## 💡 Use Cases

### Program Evaluators & Grant Officers

* **Impact Verification:** Quantify the exact onboarding and legacy sustainability value of funding allocations across regional chapters.
* **Objective Comparative Analysis:** Compare an event's performance fairly by evaluating it directly against its nearest economic and demographic regional peers.

### Local Campaign Organizers

* **Churn Diagnostics:** Determine if an execution strategy suffers from low retention rates (veteran contributor drop-off) or weak growth pipelines (failure to attract newcomers).
* **Data-Backed Strategy Adjustments:** Use automated, contextual smart insights to adjust outreach models, implement community mentoring programs, or balance upload distributions.

---

## 🛠️ Installation and Setup

### Prerequisites

* Python 3.9 or higher
* Internet connectivity (to process live categories via Wikimedia Toolforge APIs)

### Local Deployment

1. Clone this repository to your environment:
```bash
git clone https://github.com/your-username/wikimedia-campaign-suite.git
cd wikimedia-campaign-suite

```


2. Install the necessary dependencies:
```bash
pip install streamlit requests numpy pandas matplotlib seaborn plotly

```


3. Launch the Streamlit server:
```bash
streamlit run app.py

```



### Event Code Syntax Guide

To query campaigns accurately inside the application, input standard text sequences following this structure: `[Event Code][Country Code][Year]`

* **wlm** (Wiki Loves Monuments), **wle** (Wiki Loves Earth), **wlf** (Wiki Loves Folklore), **wlb** (Wiki Loves Bangla)
* Example entries: `wlmbd24` (Wiki Loves Monuments Bangladesh 2024), `wlmde25` (Wiki Loves Monuments Germany 2025)
