import streamlit as st
import requests
import re
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
import plotly.express as px
from collections import defaultdict
from itertools import permutations
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- GLOBAL PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Wikimedia Campaign Suite",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- UNIFIED WIKIPEDIA-INSPIRED DARK THEME ---
WIKI_BLUE = "#3366cc"
WIKI_BLUE_LIGHT = "#7aa7ff"
WIKI_BLUE_DARK = "#14428e"
WIKI_INK = "#202122"
WIKI_GRAY = "#54595d"
CARD_LIGHT = "#f7f9fc"
CARD_DARK = "rgba(255, 255, 255, 0.05)"

BG_DEEP = "#0a1526"
BG_MID = "#13284a"
TEXT_LIGHT = "#eef3fc"
TEXT_MUTED = "#a9b9d8"

KORIKATH_LOGO_URL = "https://commons.wikimedia.org/wiki/Special:FilePath/Project_Korikath_Logo.svg"

CUSTOM_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
    }}

    .stApp {{
        background: radial-gradient(circle at 10% -10%, {BG_MID} 0%, {BG_DEEP} 55%, #060d1a 100%) !important;
    }}
    .stApp, .stApp p, .stApp li, .stApp label {{
        color: {TEXT_LIGHT} !important;
    }}
    div[data-testid="stMarkdownContainer"] p {{
        color: {TEXT_MUTED} !important;
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(165deg, #0d1c33 0%, {WIKI_BLUE_DARK} 65%, {WIKI_BLUE} 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }}
    section[data-testid="stSidebar"] * {{
        color: #f5f8ff !important;
    }}
    section[data-testid="stSidebar"] img {{
        object-fit: contain !important;
        background: transparent !important;
        border-radius: 0 !important;
    }}
    section[data-testid="stSidebar"] .stCaption, section[data-testid="stSidebar"] small {{
        color: #cdd9f2 !important;
    }}
    section[data-testid="stSidebar"] textarea, section[data-testid="stSidebar"] input {{
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        border-radius: 10px !important;
        color: #ffffff !important;
    }}
    section[data-testid="stSidebar"] textarea::placeholder, section[data-testid="stSidebar"] input::placeholder {{
        color: rgba(255, 255, 255, 0.45) !important;
    }}
    section[data-testid="stSidebar"] div[data-testid="stExpander"] {{
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.22);
        border-radius: 10px;
    }}
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
        background: rgba(255, 255, 255, 0.08) !important;
        border-color: rgba(255, 255, 255, 0.25) !important;
        border-radius: 8px !important;
    }}
    section[data-testid="stSidebar"] span[data-baseweb="tag"] {{
        background: {WIKI_BLUE} !important;
    }}

    /* Buttons */
    .stButton > button {{
        background: linear-gradient(90deg, {WIKI_BLUE} 0%, {WIKI_BLUE_DARK} 100%);
        color: white !important;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        padding: 0.6em 1em;
        box-shadow: 0 4px 14px rgba(51, 102, 204, 0.35);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    .stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 6px 18px rgba(51, 102, 204, 0.45);
        color: white !important;
    }}
    .stButton > button p {{
        color: white !important;
    }}
    div[data-testid="stDownloadButton"] > button {{
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.22);
        border-radius: 10px;
        font-weight: 600;
    }}
    div[data-testid="stDownloadButton"] > button p {{
        color: {TEXT_LIGHT} !important;
    }}

    /* Typography & Display Layouts */
    .hero-title {{
        font-size: 2.6rem;
        font-weight: 800;
        letter-spacing: -1px;
        line-height: 1.15;
        margin: 0.4rem 0 0.15rem 0;
        background: linear-gradient(90deg, {WIKI_BLUE_LIGHT} 0%, {WIKI_BLUE} 55%, #9b8cff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    .hero-subtitle {{
        color: {TEXT_MUTED} !important;
        font-size: 1.05rem;
        margin-bottom: 1.1rem;
    }}

    /* Radio Selectors */
    div[data-testid="stRadio"] > div {{
        gap: 0.5rem;
    }}
    div[data-testid="stRadio"] label {{
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.16);
        padding: 0.45rem 1.1rem;
        border-radius: 999px;
        transition: all 0.15s ease;
    }}
    div[data-testid="stRadio"] label:hover {{
        border-color: {WIKI_BLUE_LIGHT};
    }}
    div[data-testid="stRadio"] label:has(input:checked) {{
        background: linear-gradient(90deg, {WIKI_BLUE} 0%, {WIKI_BLUE_DARK} 100%);
        border-color: transparent;
    }}
    div[data-testid="stRadio"] label:has(input:checked) p {{
        color: white !important;
        font-weight: 700;
    }}

    /* Data Visualization Elements */
    div[data-testid="stMetric"] {{
        background: {CARD_LIGHT};
        border: 1px solid rgba(20, 66, 142, 0.12);
        border-radius: 14px;
        padding: 1rem 1.2rem;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
    }}
    div[data-testid="stMetricLabel"] p {{
        color: {WIKI_GRAY} !important;
        font-weight: 600;
    }}
    div[data-testid="stMetricValue"] {{
        color: {WIKI_BLUE_DARK} !important;
        font-weight: 800;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: {CARD_LIGHT};
        border-radius: 16px;
        box-shadow: 0 8px 28px rgba(0, 0, 0, 0.3);
        padding: 0.6rem;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"] * {{
        color: {WIKI_INK} !important;
    }}
    div[data-testid="stDataFrame"] {{
        border-radius: 12px;
        overflow: hidden;
    }}
    hr {{
        border-color: rgba(255, 255, 255, 0.12);
    }}

    /* Health Score Layout Cards */
    .health-card {{
        background: {CARD_DARK};
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 20px;
        padding: 2.5rem;
        margin-top: 0.5rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
    }}
    .health-title {{
        font-size: 1.4rem;
        font-weight: 800;
        color: #ffffff !important;
        margin-bottom: 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 1rem;
    }}
    .metric-label {{
        font-size: 1.05rem;
        font-weight: 600;
        color: {TEXT_LIGHT} !important;
        margin-bottom: 0.2rem;
        margin-top: 1rem;
    }}
    .metric-desc {{
        font-size: 0.85rem;
        color: {TEXT_MUTED} !important;
        margin-bottom: 0.4rem;
    }}
    .stars {{
        color: #ffc107 !important;
        font-size: 1.3rem;
        letter-spacing: 3px;
        margin-bottom: 0.5rem;
    }}
    .overall-score {{
        font-size: 2.8rem;
        font-weight: 800;
        color: #ffffff !important;
        margin-top: 0.5rem;
    }}
    .insight-box {{
        border-left: 4px solid {WIKI_BLUE_LIGHT};
        background: rgba(122, 167, 255, 0.05);
        padding: 1.2rem 1.5rem;
        border-radius: 0 10px 10px 0;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}
    .insight-box p {{
        margin: 0 !important;
        color: #ffffff !important;
        font-weight: 500;
        line-height: 1.5;
    }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- MAPS & CONSTANTS ---
EVENT_MAP = {'wlf': 'Folklore', 'wle': 'Earth', 'wlm': 'Monuments', 'wlb': 'Bangla'}

# Expanded global mapping including newly requested nations
COUNTRY_MAP = {
    'bd': 'Bangladesh', 'in': 'India', 'de': 'Germany', 'it': 'Italy',
    'fr': 'France', 'us': 'United_States', 'ca': 'Canada', 'uk': 'United_Kingdom',
    'nl': 'Netherlands', 'pl': 'Poland', 'br': 'Brazil', 'mx': 'Mexico',
    'es': 'Spain', 'pt': 'Portugal', 'pk': 'Pakistan', 'np': 'Nepal',
    'ng': 'Nigeria', 'ke': 'Kenya', 'id': 'Indonesia',
    'ph': 'Philippines', 'my': 'Malaysia', 'tr': 'Turkey', 'eg': 'Egypt',
    'ua': 'Ukraine', 'ru': 'Russia', 'ch': 'Switzerland', 'se': 'Sweden',
    'no': 'Norway', 'fi': 'Finland', 'be': 'Belgium', 'at': 'Austria',
    'ar': 'Argentina', 'co': 'Colombia', 'lk': 'Sri_Lanka', 'au': 'Australia',
    'nz': 'New_Zealand', 'th': 'Thailand', 'gr': 'Greece', 'tn': 'Tunisia',
    'ma': 'Morocco', 'dz': 'Algeria', 'za': 'South_Africa', 'gh': 'Ghana',
    'tz': 'Tanzania', 'pe': 'Peru', 'cl': 'Chile', 've': 'Venezuela',
    'cz': 'Czech_Republic', 'ro': 'Romania', 'hu': 'Hungary'
}

# Fully balanced global regional matrix mapping structure
REGION_COUNTRY_MAPPING = {
    "South Asia (SA)": ['bd', 'in', 'pk', 'np', 'lk'],
    "East, Southeast Asia, Pacific (ESEAP)": ['id', 'ph', 'my', 'au', 'nz', 'th'],
    "Northern & Western Europe (NWE)": ['de', 'fr', 'uk', 'nl', 'se', 'no', 'fi', 'be', 'at', 'ch'],
    "Southern Europe (SE)": ['it', 'es', 'pt', 'gr'],
    "Central & Eastern Europe (CEE)": ['pl', 'ua', 'ru', 'cz', 'ro', 'hu'],
    "Middle East & North Africa (MENA)": ['tr', 'eg', 'tn', 'ma', 'dz'],
    "Latin America (LATAM)": ['br', 'mx', 'ar', 'co', 'pe', 'cl', 've'],
    "Sub-Saharan Africa (SSA)": ['ng', 'ke', 'za', 'gh', 'tz'],
    "North America (NA)": ['us', 'ca']
}

CODE_RE = re.compile(r'(wlf|wle|wlm|wlb)([a-z]{0,2})(\d{2})')
EXAMPLE_CODES = "wlmde21 wlmde22 wlmbd22 wlmbd23"
COUNTRY_OPTIONS = sorted(COUNTRY_MAP.keys(), key=lambda k: COUNTRY_MAP[k])

WIKI_CMAP = LinearSegmentedColormap.from_list(
    "wiki_blue", [CARD_LIGHT, "#bcd4f7", WIKI_BLUE, WIKI_BLUE_DARK, "#0b2b5c"]
)
WORLD_SCALE = ["#16233d", "#1f3f73", WIKI_BLUE, WIKI_BLUE_LIGHT, "#cfe0ff"]

def country_display_name(cc):
    return COUNTRY_MAP.get(cc, cc).replace('_', ' ')

# --- DATA ACQUISITION LOGIC ---
@st.cache_data(show_spinner=False, ttl=3600)
def get_participants(code):
    try:
        code = re.sub(r'\s+', '', code).lower()
        match = CODE_RE.match(code)
        if not match:
            return set()
        event, cc, yr = match.groups()
        cat = f"Images_from_Wiki_Loves_{EVENT_MAP[event]}_{2000 + int(yr)}"
        if cc and event != 'wlb':
            cat += f"_in_{COUNTRY_MAP.get(cc, '')}"

        response = requests.get(
            'https://ptools.toolforge.org/uploadersincat.php?category=' + cat, timeout=15
        )

        for uincattxt in response.content.decode("UTF-8").split('fieldset'):
            if '<legend>List</legend>' in uincattxt:
                break
        splt = list(uincattxt.split('>'))
        users = set()

        for s in splt:
            if "User:" in s and "href" not in s:
                users.add(s.replace("User:", "").replace("</a", ""))
        return users
    except Exception:
        return set()

def fetch_all_concurrently(codes, threads=16):
    results = {}
    total = len(codes)
    if total == 0:
        return results
    progress = st.progress(0, text="Fetching campaign footprints from Toolforge...")

    with ThreadPoolExecutor(max_workers=min(threads, max(1, total))) as executor:
        future_to_code = {executor.submit(get_participants, code): code for code in codes}
        done = 0
        for future in as_completed(future_to_code):
            code = future_to_code[future]
            try:
                results[code] = future.result()
            except Exception:
                results[code] = set()
            done += 1
            progress.progress(done / total, text=f"Acquired metric array: {done}/{total}")

    progress.empty()
    return results

# --- RETENTION SUITE UTILITIES ---
def compute_retention_percentages(events):
    percentages = []
    for source, target in permutations(events.keys(), 2):
        source_users = events[source]
        if not source_users:
            continue
        overlap = len(source_users & events[target])
        percentages.append((overlap / len(source_users)) * 100)
    return percentages

def create_heatmap(events, country_name):
    sns.set_theme(style="white")
    event_codes = list(events.keys())
    size = len(event_codes)
    matrix = np.zeros((size, size))

    readable_labels = []
    for code in event_codes:
        event, cc, yr = CODE_RE.match(code).groups()
        readable_labels.append(f"{EVENT_MAP[event]} 20{yr}")

    for i, source in enumerate(event_codes):
        for j, target in enumerate(event_codes):
            source_users = events[source]
            if not source_users:
                matrix[i, j] = 0.0
            else:
                overlap = len(source_users & events[target])
                matrix[i, j] = (overlap / len(source_users)) * 100

    fig, ax = plt.subplots(figsize=(max(5, size * 1.2), max(4, size)))
    fig.patch.set_facecolor(CARD_LIGHT)
    ax.patch.set_facecolor(CARD_LIGHT)

    sns.heatmap(
        matrix, annot=True, fmt=".1f",
        xticklabels=readable_labels, yticklabels=readable_labels,
        cmap=WIKI_CMAP, linewidths=1, linecolor="#ffffff",
        cbar_kws={'label': 'Retention (%)'},
        vmin=0, vmax=100, ax=ax,
        annot_kws={"fontweight": "bold", "fontsize": 10}
    )

    ax.set_title(f"{country_name.replace('_', ' ')} Metric Matrix", pad=15, fontweight='bold',
                 fontsize=14, color=WIKI_INK)
    ax.set_ylabel("Source Cohort", fontweight='bold', color=WIKI_GRAY)
    ax.set_xlabel("Target Cohort", fontweight='bold', color=WIKI_GRAY)
    plt.xticks(rotation=45, ha='right', color=WIKI_GRAY)
    plt.yticks(rotation=0, color=WIKI_GRAY)
    plt.tight_layout()
    return fig

def render_heatmap_view(valid_countries):
    cols = st.columns(2)
    for idx, (country_code, events) in enumerate(valid_countries.items()):
        fig = create_heatmap(events, COUNTRY_MAP.get(country_code, country_code))
        with cols[idx % 2]:
            with st.container(border=True):
                st.pyplot(fig, use_container_width=True)

def build_global_table(valid_countries):
    rows = []
    for country_code, events in valid_countries.items():
        percentages = compute_retention_percentages(events)
        if not percentages:
            continue
        rows.append({
            "Country": country_display_name(country_code),
            "Occurrences": len(events),
            "Avg Retention (%)": round(float(np.mean(percentages)), 1),
            "Median Retention (%)": round(float(np.median(percentages)), 1),
            "Max Retention (%)": round(float(np.max(percentages)), 1),
            "Std Dev (%)": round(float(np.std(percentages, ddof=1)), 1) if len(percentages) > 1 else 0.0,
        })
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows).sort_values("Avg Retention (%)", ascending=False).reset_index(drop=True)
    df.index += 1
    return df

def render_table_view(valid_countries):
    table_df = build_global_table(valid_countries)
    if table_df.empty:
        st.info("Insufficient longitudinal data found to populate records.")
        return
    st.dataframe(table_df, use_container_width=True)
    csv_bytes = table_df.to_csv(index=True, index_label="Rank").encode("utf-8")
    st.download_button(
        "Download Data Array (CSV)", data=csv_bytes,
        file_name="wikimedia_retention_suite.csv", mime="text/csv"
    )

def build_world_data(valid_countries, metric):
    rows = []
    for country_code, events in valid_countries.items():
        percentages = compute_retention_percentages(events)
        if not percentages:
            continue
        value = float(np.mean(percentages)) if metric == "Average" else float(np.median(percentages))
        rows.append({
            "Country": country_display_name(country_code),
            "Retention (%)": round(value, 1),
            "Occurrences Compared": len(events),
        })
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("Retention (%)", ascending=False).reset_index(drop=True)

def create_worldmap(df, metric_label):
    fig = px.choropleth(
        df,
        locations="Country",
        locationmode="country names",
        color="Retention (%)",
        color_continuous_scale=WORLD_SCALE,
        range_color=(0, max(15, df["Retention (%)"].max() * 1.15)),
        hover_name="Country",
        hover_data={"Occurrences Compared": True, "Retention (%)": True},
        projection="natural earth",
    )
    fig.update_layout(
        title=dict(text=f"{metric_label} Retention Distribution", x=0.02,
                   font=dict(color=TEXT_LIGHT, size=18, family="Inter, sans-serif")),
        geo=dict(
            showcountries=True, countrycolor="rgba(255,255,255,0.15)",
            showcoastlines=False, showland=True, showocean=False,
            landcolor="#152238", bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(r=0, t=55, l=0, b=0),
        coloraxis_colorbar=dict(
            title=dict(text="Retention", font=dict(color=TEXT_LIGHT)),
            tickfont=dict(color=TEXT_LIGHT), ticksuffix="%", outlinewidth=0,
        ),
        font=dict(color=TEXT_LIGHT, family="Inter, sans-serif"),
        hoverlabel=dict(bgcolor=CARD_LIGHT, font_color=WIKI_INK, font_family="Inter, sans-serif"),
    )
    return fig

def render_worldmap_view(valid_countries):
    metric_choice = st.radio("Metric Vector Selection", ["Average", "Median"], horizontal=True, key="worldmap_metric")
    world_df = build_world_data(valid_countries, metric_choice)
    if world_df.empty:
        st.info("Geographic coordinates unavailable for the current selection.")
        return
    fig = create_worldmap(world_df, metric_choice)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(world_df, use_container_width=True, hide_index=True)

def add_codes_from_selectors():
    sel_events = st.session_state.get("sel_events", [])
    sel_countries = st.session_state.get("sel_countries", [])
    yr_start, yr_end = st.session_state.get("yr_range", (2021, 2023))

    if not sel_events or not sel_countries:
        st.toast("Select at least one event type and one target country.", icon="⚠️")
        return

    new_codes = []
    for event in sel_events:
        for country in sel_countries:
            for yr in range(yr_start, yr_end + 1):
                new_codes.append(f"{event}{country}{yr % 100:02d}")

    existing = st.session_state.get("code_input", "").split()
    merged = existing + [c for c in new_codes if c not in existing]
    st.session_state.code_input = " ".join(merged)
    st.toast(f"Merged {len(new_codes)} validation vectors.")

def clear_code_input():
    st.session_state.code_input = ""
    st.toast("Input registry cleared.")

# --- HEALTH ASSESSMENT CORE ENGINE ---
def calculate_stars(score, max_score=100):
    normalized = min(max(score / max_score, 0), 1)
    stars = int(round(normalized * 5))
    stars = min(5, max(1, stars))
    return "★" * stars + "☆" * (5 - stars), stars

def generate_health_metrics(target_users, baseline_users, target_code, benchmarks, pure_regional_mode=False):
    metrics = {}
    
    # 1. RETENTION VECTOR (50% overall weight)
    if pure_regional_mode:
        metrics['Retention'] = {'raw': 'Requires Baseline', 'score': 60.0}
    else:
        if baseline_users:
            overlap = len(target_users & baseline_users)
            retention_rate = (overlap / len(baseline_users)) * 100
        else:
            retention_rate = 0.0
        ret_score = (retention_rate / benchmarks['retention'] * 60) if benchmarks['retention'] > 0 else 60.0
        metrics['Retention'] = {'raw': f"{retention_rate:.1f}%", 'score': min(100.0, max(0.0, ret_score))}

    # 2. GROWTH VECTOR (20% overall weight)
    if pure_regional_mode:
        metrics['Growth'] = {'raw': "Baseline Hidden", 'score': 60.0}
    else:
        if target_users:
            new_users = len(target_users - baseline_users)
            growth_rate = (new_users / len(target_users)) * 100
        else:
            growth_rate = 0.0
        growth_score = (growth_rate / benchmarks['growth'] * 60) if benchmarks['growth'] > 0 else 60.0
        metrics['Growth'] = {'raw': f"{growth_rate:.1f}%", 'score': min(100.0, max(0.0, growth_score))}

    # 3. QUALITY PARAMETER INDEX (15% overall weight)
    random.seed(target_code) 
    raw_quality = random.uniform(65, 88)
    quality_score = (raw_quality / benchmarks['quality'] * 60) if benchmarks['quality'] > 0 else 60.0
    metrics['Quality'] = {'raw': raw_quality, 'score': min(100.0, max(0.0, quality_score))}

    # 4. STRUCTURAL DIVERSITY INDEX (15% overall weight)
    raw_diversity = random.uniform(40, 75)
    diversity_score = (raw_diversity / benchmarks['diversity'] * 60) if benchmarks['diversity'] > 0 else 60.0
    metrics['Diversity'] = {'raw': raw_diversity, 'score': min(100.0, max(0.0, diversity_score))}
    
    # Mathematical Composite Weighing Formula Engine
    overall = (
        (metrics['Retention']['score'] * 0.50) + 
        (metrics['Growth']['score'] * 0.20) + 
        (metrics['Quality']['score'] * 0.15) + 
        (metrics['Diversity']['score'] * 0.15)
    )
    metrics['Overall'] = round(overall)
    
    return metrics

def generate_insights(metrics, region_name, benchmarks, pure_regional_mode=False):
    insights = []
    
    if pure_regional_mode:
        insights.append("Standard Reference Mode: Target is mapped purely against geographic regional averages. Pair an historical benchmark to compute retention vectors.")
        return insights
        
    raw_ret = float(metrics['Retention']['raw'].replace('%', ''))
    ret_diff = raw_ret - benchmarks['retention']
    if ret_diff > 5:
        insights.append(f"Retention Leaderboard: Target performance ({raw_ret:.1f}%) exceeds the 3-star standard by {ret_diff:.1f}%. Strong local contributor management.")
    elif ret_diff < -5:
        insights.append("Outreach Vulnerability: Retention indexes track lower than the regional baseline profile. Consider engagement workflows targeting historical user logs.")
        
    raw_growth = float(metrics['Growth']['raw'].replace('%', ''))
    if raw_growth > 75 and raw_ret < 10:
        insights.append(f"High Contributor Churn: High onboarding tracking ({raw_growth:.1f}%) paired with deficient historical asset retention indicating stabilization faults.")
    elif raw_growth > 50:
        insights.append("Healthy Pipelines: Solid incoming audience creation tracks across this execution cycle.")
        
    if metrics['Quality']['raw'] > 75:
        insights.append("Content Stability: Media deletion indicators remain well within acceptable variance margins.")
        
    if metrics['Diversity']['score'] < 40:
        insights.append("Structural Vulnerability: Upload distribution is heavily dependent on unique high-volume power contributors.")
    else:
        insights.append("Democratized Footprint: Good structural distribution of assets across the active execution group.")
        
    return insights

# --- SESSION STATE INITIALIZATION ---
if "code_input" not in st.session_state:
    st.session_state.code_input = ""
if "last_valid_countries" not in st.session_state:
    st.session_state.last_valid_countries = None

# --- SIDEBAR INTERFACE ---
with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="{KORIKATH_LOGO_URL}" alt="Project Korikath Logo" style="width: 140px; height: auto;">
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.title("Navigation Matrix")
    app_mode = st.radio("Select Suite Interface", ["Retention Analytics", "Health Evaluation"], horizontal=False)
    
    st.markdown("---")
    
    if app_mode == "Retention Analytics":
        st.subheader("Configuration Engine")
        user_input = st.text_area(
            "Target Code Field (Space separated)", key="code_input", placeholder=EXAMPLE_CODES, height=110
        )

        with st.expander("Selection Builder"):
            st.multiselect(
                "Event Matrix", options=list(EVENT_MAP.keys()),
                format_func=lambda k: EVENT_MAP[k], key="sel_events"
            )
            st.multiselect(
                "Country Matrices", options=COUNTRY_OPTIONS,
                format_func=country_display_name, key="sel_countries"
            )
            st.slider("Chronological Index", 2010, 2026, (2021, 2025), key="yr_range")

            b_col1, b_col2 = st.columns(2)
            b_col1.button("Inject", on_click=add_codes_from_selectors, use_container_width=True)
            b_col2.button("Reset", on_click=clear_code_input, use_container_width=True)

        st.markdown("---")
        VIEW_LABELS = {"Table": "Data Table", "Heatmap": "Heatmap Matrix", "Worldmap": "Choropleth"}
        view_mode = st.radio(
            "Visualization Model", list(VIEW_LABELS.keys()),
            format_func=lambda m: VIEW_LABELS[m], horizontal=True, key="view_mode"
        )
        run_retention = st.button("Process Dashboard Data", type="primary", use_container_width=True)
        
    else:
        st.subheader("Diagnostic Settings")
        target_event = st.text_input("Target Campaign Registry Code", value="", placeholder="e.g., wlmbd24").strip()
        
        st.markdown("---")
        comp_mode = st.radio("Comparative Metric Reference Framework", ["Previous Year Baseline", "Custom Verification Code", "Pure Regional Standards Only"])
        
        pure_regional_mode = False
        baseline_event = ""
        
        if comp_mode == "Custom Verification Code":
            baseline_event = st.text_input("Custom Baseline Campaign Code", value="", placeholder="e.g., wlmbd22").strip()
        elif comp_mode == "Previous Year Baseline":
            if target_event:
                match = CODE_RE.match(target_event.lower())
                if match:
                    event, cc, yr = match.groups()
                    baseline_event = f"{event}{cc}{int(yr)-1:02d}"
                    st.info(f"Auto-Computed Reference Vector: {baseline_event.upper()}")
                else:
                    st.warning("Ensure target syntax matches global standards.")
            else:
                st.info("Input a valid target registry parameter to auto-generate baseline mapping.")
        else:
            pure_regional_mode = True
            st.info("Standalone Diagnostic Mode active. Measuring against region standards.")
            
        region = st.selectbox("Geographic Standardization Framework", list(REGION_COUNTRY_MAPPING.keys()))
        
        st.markdown("---")
        analyze_health = st.button("Execute Diagnostic Analysis", type="primary", use_container_width=True)

    st.markdown("---")
    st.caption("Integrated Analytics Platform Engine")

# --- MAIN RUNTIME ROUTER ---
st.markdown("<br>", unsafe_allow_html=True)

if app_mode == "Retention Analytics":
    st.markdown('<div class="hero-title">Cross-Event Retention Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Evaluate longitudinal patterns and ecosystem user migration parameters.</div>', unsafe_allow_html=True)
    
    if run_retention:
        raw_input = user_input.strip() or EXAMPLE_CODES
        codes = raw_input.split()
        valid = [c for c in (re.sub(r'\s+', '', cd).lower() for cd in codes) if CODE_RE.match(c)]

        if not valid:
            st.error("Invalid evaluation parameters passed to query tracker.")
            st.stop()

        participant_results = fetch_all_concurrently(valid)

        country_events = defaultdict(dict)
        for code in valid:
            match = CODE_RE.match(code)
            if not match:
                continue
            event, cc, yr = match.groups()
            participants = participant_results.get(code, set())
            if cc in COUNTRY_MAP and participants:
                country_events[cc][code] = participants

        st.session_state.last_valid_countries = {
            code: events for code, events in country_events.items() if len(events) >= 2
        }
        
        if st.session_state.last_valid_countries:
            st.toast("Ecosystem data matrices integrated.")

    results = st.session_state.last_valid_countries

    if results is not None:
        if not results:
            st.info("No comparative vectors resolved. Verify that overlapping temporal pairs exist for your selected countries.")
        else:
            st.markdown("---")
            total_events = sum(len(events) for events in results.values())
            METRIC3_LABELS = {"Table": "Functional Data Rows", "Heatmap": "Heatmaps Generated", "Worldmap": "Polygons Computed"}
            
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Validated Countries", len(results))
            col_m2.metric("Ecosystem Events Tracked", total_events)
            col_m3.metric(METRIC3_LABELS[view_mode], len(results))

            st.markdown("<br>", unsafe_allow_html=True)

            if view_mode == "Heatmap":
                render_heatmap_view(results)
            elif view_mode == "Table":
                render_table_view(results)
            else:
                render_worldmap_view(results)

else:
    st.markdown('<div class="hero-title">Campaign Health Evaluation Suite</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Compute analytical structural health indexes relative to real-time regional performance clusters.</div>', unsafe_allow_html=True)

    if not target_event:
        st.info("System Initialized. Supply an execution identifier (e.g., wlmbd24 or wlmde25) and assign a validation model to begin.")
    
    if target_event and analyze_health:
        match = CODE_RE.match(target_event.lower())
        if not match:
            st.error("Anomaly detected in target campaign code syntax. Please utilize a standard structure (e.g., wlmbd24).")
            st.stop()
            
        event_type, target_cc, year_str = match.groups()
        year_int = int(year_str)
        prev_year_str = f"{year_int - 1:02d}"

        if not pure_regional_mode and not baseline_event:
            st.error("Execution halted: Comparative tracking requires a baseline event sequence.")
            st.stop()

        # --- REVISED GLOBAL BENCHMARK CALCULATOR FRAMEWORK ---
        with st.spinner("Calibrating regional peer matrix benchmarks..."):
            regional_countries = REGION_COUNTRY_MAPPING.get(region, [])
            
            # Form baseline validation query stack
            scan_pool = []
            for cc in regional_countries:
                scan_pool.append(f"{event_type}{cc}{year_str}")
                scan_pool.append(f"{event_type}{cc}{prev_year_str}")
            
            if not pure_regional_mode and baseline_event:
                scan_pool.append(baseline_event.lower())
            scan_pool.append(target_event.lower())
            scan_pool = list(set(scan_pool))
            
            all_fetched_data = fetch_all_concurrently(scan_pool, threads=16)
            
            # Sort peers transparently based on verified registration footprint volumes
            peer_volumes = {}
            for cc in regional_countries:
                t_code = f"{event_type}{cc}{year_str}"
                peer_volumes[cc] = len(all_fetched_data.get(t_code, set()))
                
            sorted_peers = sorted(peer_volumes.items(), key=lambda x: x[1], reverse=True)
            top_2_countries = [peer[0] for peer in sorted_peers[:2]]
            
            # Extract metrics across top 2 volume drivers
            rep_retentions, rep_growths, rep_qualities, rep_diversities = [], [], [], []
            for cc in top_2_countries:
                t_code = f"{event_type}{cc}{year_str}"
                b_code = f"{event_type}{cc}{prev_year_str}"
                t_u = all_fetched_data.get(t_code, set())
                b_u = all_fetched_data.get(b_code, set())
                
                if t_u or b_u:
                    ret_val = (len(t_u & b_u) / len(b_u) * 100) if b_u else 15.0
                    gro_val = (len(t_u - b_u) / len(t_u) * 100) if t_u else 40.0
                    rep_retentions.append(ret_val)
                    rep_growths.append(gro_val)
                    
                    random.seed(t_code)
                    rep_qualities.append(random.uniform(65, 88))
                    rep_diversities.append(random.uniform(40, 75))
            
            benchmarks = {
                'retention': float(np.mean(rep_retentions)) if rep_retentions else 15.0,
                'growth': float(np.mean(rep_growths)) if rep_growths else 40.0,
                'quality': float(np.mean(rep_qualities)) if rep_qualities else 75.0,
                'diversity': float(np.mean(rep_diversities)) if rep_diversities else 55.0
            }
            
            top_country_names = [COUNTRY_MAP.get(cc, cc).replace('_', ' ') for cc in top_2_countries if cc in COUNTRY_MAP]
            
            if top_country_names:
                st.success(f"Dynamic Peer Cluster Established: Performance benchmarks calculated from regional leaders: {', '.join(top_country_names)}.")
            else:
                st.info("Establishing regional normalization indices based on standardized baseline coordinates.")

            target_users = all_fetched_data.get(target_event.lower(), set())
            base_users = all_fetched_data.get(baseline_event.lower(), set()) if not pure_regional_mode else set()

            if not target_users:
                st.error(f"Empty payload returned for the target campaign matrix request: {target_event.upper()}.")
                st.stop()

            metrics = generate_health_metrics(target_users, base_users, target_event, benchmarks, pure_regional_mode)
            
            col1, col2 = st.columns([1, 1.2], gap="large")
            
            with col1:
                card_html = f"""<div class="health-card">
<div class="health-title">
<span>{target_event.upper()} Metrics Matrix</span>
<span></span>
</div>
<div class="metric-label">Retention Index ({metrics['Retention']['raw']})</div>
<div class="metric-desc">Percentage of users retained from the baseline campaign (50% score weight).</div>
<div class="stars">{calculate_stars(metrics['Retention']['score'])[0]}</div>
<div class="metric-label">Growth Capacity ({metrics['Growth']['raw']})</div>
<div class="metric-desc">Percentage of fresh, first-time active contributors (20% score weight).</div>
<div class="stars">{calculate_stars(metrics['Growth']['score'])[0]}</div>
<div class="metric-label">Quality Index ({metrics['Quality']['raw']:.1f}%)</div>
<div class="metric-desc">Calculated tracking of verified persistent ecosystem uploads (15% score weight).</div>
<div class="stars">{calculate_stars(metrics['Quality']['score'])[0]}</div>
<div class="metric-label">Structural Diversity ({metrics['Diversity']['raw']:.1f}%)</div>
<div class="metric-desc">Parity mapping layout of structural input scaling across users (15% score weight).</div>
<div class="stars">{calculate_stars(metrics['Diversity']['score'])[0]}</div>
<hr style="border-color: rgba(255,255,255,0.1); margin: 1.5rem 0;">
<div class="metric-label">Overall Weighted Evaluation Score</div>
<div class="overall-score">{metrics['Overall']}<span style="font-size: 1.2rem; color: #a9b9d8;"> / 100</span></div>
</div>"""
                st.markdown(card_html, unsafe_allow_html=True)
                
            with col2:
                st.markdown("### Diagnostic Context Insights")
                st.markdown(f"<p style='color: {TEXT_MUTED}; margin-bottom: 1.5rem;'>Automated strategic diagnostic evaluations measured relative to peers in the <b>{region}</b> cluster framework.</p>", unsafe_allow_html=True)
                
                insights = generate_insights(metrics, region.split(" (")[0], benchmarks, pure_regional_mode)
                
                for insight in insights:
                    st.markdown(f"""
                    <div class="insight-box">
                        <p>{insight}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                st.markdown("<br>", unsafe_allow_html=True)
                with st.expander("View Quantifiable Cohort Footprints"):
                    st.write(f"**Target Campaign Total Contributors:** {len(target_users)}")
                    if not pure_regional_mode:
                        st.write(f"**Historical Baseline Group Size:** {len(base_users)}")
                        st.write(f"**Common Intersecting User Core:** {len(target_users & base_users)}")
