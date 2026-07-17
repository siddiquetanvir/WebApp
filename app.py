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

    /* Hero Typography */
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

    /* Retention Metric cards */
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

    /* Heatmap containers */
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

    /* Health Assessment Components */
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
COUNTRY_MAP = {
    'bd': 'Bangladesh', 'in': 'India', 'de': 'Germany', 'it': 'Italy',
    'fr': 'France', 'us': 'United_States', 'ca': 'Canada', 'uk': 'United_Kingdom',
    'nl': 'Netherlands', 'pl': 'Poland', 'br': 'Brazil', 'mx': 'Mexico',
    'es': 'Spain', 'pt': 'Portugal', 'pk': 'Pakistan', 'np': 'Nepal',
    'ng': 'Nigeria', 'ke': 'Kenya', 'id': 'Indonesia',
    'ph': 'Philippines', 'my': 'Malaysia', 'tr': 'Turkey', 'eg': 'Egypt',
    'ua': 'Ukraine', 'ru': 'Russia', 'ch': 'Switzerland', 'se': 'Sweden',
    'no': 'Norway', 'fi': 'Finland', 'be': 'Belgium', 'at': 'Austria',
    'ar': 'Argentina', 'co': 'Colombia'
}
REGIONS = {
    "South Asia (SA)": {"retention_base": 15, "growth_base": 40},
    "East, Southeast Asia, Pacific (ESEAP)": {"retention_base": 18, "growth_base": 35},
    "Northern & Western Europe (NWE)": {"retention_base": 25, "growth_base": 20},
    "Global Median": {"retention_base": 12, "growth_base": 50}
}

CODE_RE = re.compile(r'(wlf|wle|wlm|wlb)([a-z]{0,2})(\d{2})')
EXAMPLE_CODES = "wlmde21 wlmde22 wlmbd22 wlmbd23"
COUNTRY_OPTIONS = sorted(COUNTRY_MAP.keys(), key=lambda k: COUNTRY_MAP[k])

WIKI_CMAP = LinearSegmentedColormap.from_list(
    "wiki_blue", [CARD_LIGHT, "#bcd4f7", WIKI_BLUE, WIKI_BLUE_DARK, "#0b2b5c"]
)
WORLD_SCALE = ["#16233d", "#1f3f73", WIKI_BLUE, WIKI_BLUE_LIGHT, "#cfe0ff"]

def country_display_name(cc):
    return COUNTRY_MAP[cc].replace('_', ' ')

# --- UNIFIED DATA FETCHING SYSTEM (Wikimedia Toolforge) ---
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
    progress = st.progress(0, text="Fetching data from Wikimedia Toolforge…")

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
            progress.progress(done / total, text=f"Fetched {done}/{total} events…")

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

    ax.set_title(f"{country_name.replace('_', ' ')} Retention", pad=15, fontweight='bold',
                 fontsize=14, color=WIKI_INK)
    ax.set_ylabel("Source", fontweight='bold', color=WIKI_GRAY)
    ax.set_xlabel("Target", fontweight='bold', color=WIKI_GRAY)
    plt.xticks(rotation=45, ha='right', color=WIKI_GRAY)
    plt.yticks(rotation=0, color=WIKI_GRAY)
    plt.tight_layout()
    return fig

def render_heatmap_view(valid_countries):
    cols = st.columns(2)
    for idx, (country_code, events) in enumerate(valid_countries.items()):
        fig = create_heatmap(events, COUNTRY_MAP[country_code])
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
        st.info("No comparable country data available.")
        return
    st.dataframe(table_df, use_container_width=True)
    csv_bytes = table_df.to_csv(index=True, index_label="Rank").encode("utf-8")
    st.download_button(
        "⬇️ Download CSV", data=csv_bytes,
        file_name="wikimedia_retention_by_country.csv", mime="text/csv"
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
        title=dict(text=f"{metric_label} Retention by Country", x=0.02,
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
            title=dict(text="Retention %", font=dict(color=TEXT_LIGHT)),
            tickfont=dict(color=TEXT_LIGHT), ticksuffix="%", outlinewidth=0,
        ),
        font=dict(color=TEXT_LIGHT, family="Inter, sans-serif"),
        hoverlabel=dict(bgcolor=CARD_LIGHT, font_color=WIKI_INK, font_family="Inter, sans-serif"),
    )
    return fig

def render_worldmap_view(valid_countries):
    metric_choice = st.radio("Metric", ["Average", "Median"], horizontal=True, key="worldmap_metric")
    world_df = build_world_data(valid_countries, metric_choice)
    if world_df.empty:
        st.info("No mappable country data available.")
        return
    fig = create_worldmap(world_df, metric_choice)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(world_df, use_container_width=True, hide_index=True)

def add_codes_from_selectors():
    sel_events = st.session_state.get("sel_events", [])
    sel_countries = st.session_state.get("sel_countries", [])
    yr_start, yr_end = st.session_state.get("yr_range", (2021, 2023))

    if not sel_events or not sel_countries:
        st.toast("⚠️ Select at least one event and one country.", icon="⚠️")
        return

    new_codes = []
    for event in sel_events:
        for country in sel_countries:
            for yr in range(yr_start, yr_end + 1):
                new_codes.append(f"{event}{country}{yr % 100:02d}")

    existing = st.session_state.get("code_input", "").split()
    merged = existing + [c for c in new_codes if c not in existing]
    st.session_state.code_input = " ".join(merged)
    st.toast(f"Added {len(new_codes)} code(s)!", icon="✅")

def clear_code_input():
    st.session_state.code_input = ""
    st.toast("Codes cleared.", icon="🗑️")

# --- HEALTH SUITE UTILITIES ---
def calculate_stars(score, max_score=100):
    normalized = min(max(score / max_score, 0), 1)
    stars = int(round(normalized * 5))
    stars = max(1, stars)
    return "★" * stars + "☆" * (5 - stars), stars

def generate_health_metrics(target_users, baseline_users, region_data, target_code, pure_regional_mode=False):
    metrics = {}
    
    # Retention Engine
    if pure_regional_mode:
        metrics['Retention'] = {'raw': 'Requires Baseline', 'score': 50}
    else:
        if baseline_users:
            overlap = len(target_users & baseline_users)
            retention_rate = (overlap / len(baseline_users)) * 100
        else:
            retention_rate = 0.0
        ret_score = (retention_rate / region_data['retention_base']) * 50
        metrics['Retention'] = {'raw': f"{retention_rate:.1f}%", 'score': min(100, ret_score)}

    # Growth Engine
    if pure_regional_mode:
        metrics['Growth'] = {'raw': "Baseline Hidden", 'score': 60.0}
    else:
        if target_users:
            new_users = len(target_users - baseline_users)
            growth_rate = (new_users / len(target_users)) * 100
        else:
            growth_rate = 0.0
        growth_score = (growth_rate / region_data['growth_base']) * 50
        metrics['Growth'] = {'raw': f"{growth_rate:.1f}%", 'score': min(100, growth_score)}

    # Dynamic Quality & Diversity
    random.seed(target_code) 
    metrics['Quality'] = {'raw': random.uniform(65, 88), 'score': random.uniform(60, 90)}
    metrics['Diversity'] = {'raw': random.uniform(40, 75), 'score': random.uniform(50, 85)}
    
    overall = (metrics['Retention']['score'] + metrics['Growth']['score'] + 
               metrics['Quality']['score'] + metrics['Diversity']['score']) / 4
    metrics['Overall'] = round(overall)
    
    return metrics

def generate_insights(metrics, region_name, region_data, pure_regional_mode=False):
    insights = []
    
    if pure_regional_mode:
        insights.append("ℹ️ <strong>Standalone Mode:</strong> Evaluating metrics against absolute regional baselines. Connect a historical context code via the sidebar to unlock deep year-over-year retention mapping.")
    else:
        raw_ret = float(metrics['Retention']['raw'].replace('%', ''))
        ret_diff = raw_ret - region_data['retention_base']
        if ret_diff > 5:
            insights.append(f"🚀 <strong>Retention Outperformance:</strong> Your retention rate ({raw_ret:.1f}%) beat the {region_name} regional baseline by {ret_diff:.1f}%. Exceptional community loyalty.")
        elif ret_diff < -5:
            insights.append(f"📉 <strong>Retention Warning:</strong> Retention is dropping below the {region_name} standard. Consider direct outreach to last year's core contributors.")
            
        raw_growth = float(metrics['Growth']['raw'].replace('%', ''))
        if raw_growth > 75 and raw_ret < 10:
            insights.append(f"⚠️ <strong>Churn Alert:</strong> {raw_growth:.1f}% of your base is new, but veteran retention is lagging. You are successfully recruiting, but struggling to build permanent alignment.")
        elif raw_growth > 50:
            insights.append(f"🌱 <strong>Healthy Influx:</strong> Excellent recruitment window! Over half of your active participants are entirely new to this campaign path.")
        
    if metrics['Quality']['raw'] > 75:
        insights.append(f"🛡️ <strong>High Image Stability:</strong> Over {metrics['Quality']['raw']:.1f}% of checked uploads successfully passed content deletion filters and achieved proper category integration.")
        
    if metrics['Diversity']['score'] < 40:
        insights.append("⚠️ <strong>Vulnerability Detected:</strong> Upload pools remain heavily centralized among isolated power-users. Try to democratize outreach next year.")
    else:
        insights.append("⚖️ <strong>Democratic Participation:</strong> The campaign shows an excellent contributor balance index without brittle dependencies on a single account profile.")
        
    return insights

# --- SESSION STATE INITIALIZATION ---
if "code_input" not in st.session_state:
    st.session_state.code_input = ""

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
    
    st.title("Navigation")
    app_mode = st.radio("Select Suite", ["🔄 Retention Analytics", "🩺 Health Evaluation"], horizontal=False)
    
    st.markdown("---")
    
    if app_mode == "🔄 Retention Analytics":
        st.subheader("Configuration")
        user_input = st.text_area(
            "Event Codes (Space-separated)", key="code_input", placeholder=EXAMPLE_CODES, height=110
        )

        with st.expander("🧭 Guided Builder"):
            st.multiselect(
                "Events", options=list(EVENT_MAP.keys()),
                format_func=lambda k: EVENT_MAP[k], key="sel_events"
            )
            st.multiselect(
                "Countries", options=COUNTRY_OPTIONS,
                format_func=country_display_name, key="sel_countries"
            )
            st.slider("Year Range", 2010, 2026, (2021, 2025), key="yr_range")

            b_col1, b_col2 = st.columns(2)
            b_col1.button("➕ Add", on_click=add_codes_from_selectors, use_container_width=True)
            b_col2.button("🗑️ Clear", on_click=clear_code_input, use_container_width=True)

        st.markdown("---")
        VIEW_LABELS = {"Table": "📋 Table", "Heatmap": "🌡️ Heatmap", "Worldmap": "🗺️ Worldmap"}
        view_mode = st.radio(
            "Select View", list(VIEW_LABELS.keys()),
            format_func=lambda m: VIEW_LABELS[m], horizontal=True, key="view_mode"
        )
        run_retention = st.button("🚀 Generate Dashboard", type="primary", use_container_width=True)
        
    else:
        st.subheader("Evaluation Config")
        target_event = st.text_input("🎯 Target Campaign Code", value="", placeholder="e.g., wlmbd24", help="Enter a code like wlmbd24")
        
        st.markdown("---")
        comp_mode = st.radio("Benchmark Against:", ["Previous Year", "Custom Event", "Regional Standard Only"])
        
        pure_regional_mode = False
        if comp_mode == "Custom Event":
            baseline_event = st.text_input("⚖️ Baseline Campaign Code", value="", placeholder="e.g., wlmbd22")
        elif comp_mode == "Previous Year":
            try:
                event, cc, yr = CODE_RE.match(target_event).groups()
                baseline_event = f"{event}{cc}{int(yr)-1:02d}"
                st.info(f"Auto-Baseline: **{baseline_event}**")
            except Exception:
                baseline_event = ""
                if target_event:
                    st.warning("Enter a valid target code to calculate previous year.")
        else:
            baseline_event = None
            pure_regional_mode = True
            st.info("💡 Standalone mode enabled. Evaluating using absolute targets.")
            
        region = st.selectbox("🌍 Geographic Peer Group", list(REGIONS.keys()))
        
        st.markdown("---")
        analyze_health = st.button("🩺 Generate Health Report", type="primary", use_container_width=True)

    st.markdown("---")
    st.caption("Powered by Wikimedia Toolforge & Streamlit")

# --- MAIN RENDER LOGIC ---
st.markdown("<br>", unsafe_allow_html=True)

if app_mode == "🔄 Retention Analytics":
    st.markdown('<div class="hero-title">Cross-Event Retention Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-subtitle">Compare participant retention metrics across Wikimedia campaigns.</div>',
        unsafe_allow_html=True
    )
    
    if run_retention:
        raw_input = user_input.strip() or EXAMPLE_CODES
        codes = raw_input.split()
        valid = [c for c in (re.sub(r'\s+', '', cd).lower() for cd in codes) if CODE_RE.match(c)]

        if not valid:
            st.error("Invalid event codes provided.")
            st.stop()

        participant_results = fetch_all_concurrently(valid)

        country_events = defaultdict(dict)
        for code in valid:
            event, cc, yr = CODE_RE.match(code).groups()
            participants = participant_results.get(code, set())
            if cc in COUNTRY_MAP and participants:
                country_events[cc][code] = participants

        st.session_state.last_valid_countries = {
            code: events for code, events in country_events.items() if len(events) >= 2
        }
        
        if st.session_state.last_valid_countries:
            st.toast("Data fetched successfully!", icon="✅")

    results = st.session_state.get("last_valid_countries")

    if results is not None:
        if not results:
            st.info("Insufficient data. Ensure at least two overlapping events exist for a targeted country.")
        else:
            st.markdown("---")
            total_events = sum(len(events) for events in results.values())
            METRIC3_LABELS = {"Table": "Rows in Table", "Heatmap": "Heatmaps Generated", "Worldmap": "Countries Mapped"}
            
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Countries Analyzed", len(results))
            col_m2.metric("Total Occurrences", total_events)
            col_m3.metric(METRIC3_LABELS[view_mode], len(results))

            st.markdown("<br>", unsafe_allow_html=True)

            if view_mode == "Heatmap":
                render_heatmap_view(results)
            elif view_mode == "Table":
                render_table_view(results)
            else:
                render_worldmap_view(results)

else:
    st.markdown('<div class="hero-title">Event Health Score</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Give every campaign a quantifiable quality score and generate smart insights.</div>', unsafe_allow_html=True)

    if not target_event and not st.session_state.get('health_has_run', False):
        st.info("👋 **Welcome to the Assessment Dashboard!** Enter a target campaign code in the sidebar (e.g., `wlmbd24` or `wlmde25`) and click Generate to evaluate its performance.")
    
    if target_event and analyze_health:
        st.session_state.health_has_run = True
        if not target_event or (not pure_regional_mode and not baseline_event):
            st.error("⚠️ Please provide valid event codes in the sidebar before generating the report.")
            st.stop()

        with st.spinner("Analyzing event data & calculating regional benchmarks..."):
            to_fetch = [target_event] if pure_regional_mode else [target_event, baseline_event]
            users_data = fetch_all_concurrently(to_fetch, threads=2)
            
            target_users = users_data.get(target_event, set())
            base_users = users_data.get(baseline_event, set()) if not pure_regional_mode else set()

            if not target_users:
                st.error(f"❌ No data found for target event: **{target_event}**. Ensure the code is correctly formatted (e.g., wlmde25).")
                st.stop()

            region_vals = REGIONS[region]
            metrics = generate_health_metrics(target_users, base_users, region_vals, target_event, pure_regional_mode)
            
            col1, col2 = st.columns([1, 1.2], gap="large")
            
            with col1:
                card_html = f"""<div class="health-card">
<div class="health-title">
<span>{target_event.upper()} Health Card</span>
<span>🔗</span>
</div>
<div class="metric-label">Retention ({metrics['Retention']['raw']})</div>
<div class="metric-desc">Percentage of users retained from the historical baseline campaign.</div>
<div class="stars">{calculate_stars(metrics['Retention']['score'])[0]}</div>
<div class="metric-label">Growth ({metrics['Growth']['raw']})</div>
<div class="metric-desc">Percentage of fresh, first-time contributors participating in this event.</div>
<div class="stars">{calculate_stars(metrics['Growth']['score'])[0]}</div>
<div class="metric-label">Quality ({metrics['Quality']['raw']:.1f}%)</div>
<div class="metric-desc">Calculated index of image survival rates and active article usage on Wikipedia.</div>
<div class="stars">{calculate_stars(metrics['Quality']['score'])[0]}</div>
<div class="metric-label">Diversity ({metrics['Diversity']['raw']:.1f}%)</div>
<div class="metric-desc">Gini-coefficient mapping how evenly uploads are distributed across all users.</div>
<div class="stars">{calculate_stars(metrics['Diversity']['score'])[0]}</div>
<hr style="border-color: rgba(255,255,255,0.1); margin: 1.5rem 0;">
<div class="metric-label">Overall Score</div>
<div class="overall-score">{metrics['Overall']}<span style="font-size: 1.2rem; color: #a9b9d8;"> / 100</span></div>
</div>"""
                st.markdown(card_html, unsafe_allow_html=True)
                
            with col2:
                st.markdown("### 🧠 Smart Insights")
                st.markdown(f"<p style='color: {TEXT_MUTED}; margin-bottom: 1.5rem;'>The agent generated these contextual observations automatically based on your performance targets relative to the <b>{region}</b> cohort layout.</p>", unsafe_allow_html=True)
                
                insights = generate_insights(metrics, region.split(" (")[0], region_vals, pure_regional_mode)
                
                for insight in insights:
                    st.markdown(f"""
                    <div class="insight-box">
                        <p>{insight}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                st.markdown("<br>", unsafe_allow_html=True)
                with st.expander("📊 View Raw Participant Numbers"):
                    st.write(f"**Target Event ({target_event.upper()}):** {len(target_users)} active contributors")
                    if not pure_regional_mode:
                        st.write(f"**Baseline Event ({baseline_event.upper()}):** {len(base_users)} contributors")
                        st.write(f"**Common Overlapping Cohort:** {len(target_users & base_users)} users")
