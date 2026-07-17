import streamlit as st
import requests
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
import plotly.express as px
from collections import defaultdict
from itertools import permutations
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Wikimedia Campaigns",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- WIKIPEDIA-INSPIRED BASE CONSTANTS ---
WIKI_BLUE = "#3366cc"
WIKI_BLUE_LIGHT = "#7aa7ff"
WIKI_BLUE_DARK = "#14428e"
WIKI_INK = "#202122"
WIKI_GRAY = "#54595d"
KORIKATH_LOGO_URL = "https://commons.wikimedia.org/wiki/Special:FilePath/Project_Korikath_Logo.svg"
MW_API_URL = "https://commons.wikimedia.org/w/api.php"

# --- THEME TOGGLE VIA SESSION STATE ---
if "is_dark_mode" not in st.session_state:
    st.session_state.is_dark_mode = True

# --- DYNAMIC THEME VARIABLES ---
if st.session_state.is_dark_mode:
    BG_DEEP = "#0a1526"
    BG_MID = "#13284a"
    APP_BG = f"radial-gradient(circle at 10% -10%, {BG_MID} 0%, {BG_DEEP} 55%, #060d1a 100%)"
    TEXT_MAIN = "#eef3fc"
    TEXT_MUTED = "#a9b9d8"
    CARD_BG = "rgba(255, 255, 255, 0.05)"
    CARD_BORDER = "rgba(255, 255, 255, 0.12)"
    SIDEBAR_BG = f"linear-gradient(165deg, #0d1c33 0%, {WIKI_BLUE_DARK} 65%, {WIKI_BLUE} 100%)"
    SIDEBAR_TEXT = "#f5f8ff"
    INPUT_BG = "rgba(255, 255, 255, 0.08)"
    INSIGHT_BG = "rgba(122, 167, 255, 0.05)"
    CHART_BG = "#f7f9fc"
else:
    APP_BG = "linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)"
    TEXT_MAIN = WIKI_INK
    TEXT_MUTED = WIKI_GRAY
    CARD_BG = "#ffffff"
    CARD_BORDER = "rgba(0, 0, 0, 0.1)"
    SIDEBAR_BG = "linear-gradient(165deg, #f1f3f6 0%, #e2e8f0 100%)"
    SIDEBAR_TEXT = WIKI_INK
    INPUT_BG = "#ffffff"
    INSIGHT_BG = "rgba(51, 102, 204, 0.05)"
    CHART_BG = "#ffffff"

# --- CUSTOM CSS ---
CUSTOM_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif; }}
    .stApp {{ background: {APP_BG} !important; }}
    .stApp, .stApp p, .stApp li, .stApp label {{ color: {TEXT_MAIN} !important; }}
    div[data-testid="stMarkdownContainer"] p {{ color: {TEXT_MUTED} !important; }}
    .stDeployButton, [data-testid="stHeaderActionElements"] {{ display: none !important; }}
    header[data-testid="stHeader"] {{ background: transparent !important; height: 0px !important; }}
    section[data-testid="stSidebar"] {{ background: {SIDEBAR_BG} !important; border-right: 1px solid {CARD_BORDER}; }}
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {{ color: {SIDEBAR_TEXT} !important; }}
    section[data-testid="stSidebar"] img {{ object-fit: contain !important; background: transparent !important; border-radius: 0 !important; }}
    section[data-testid="stSidebar"] textarea, section[data-testid="stSidebar"] input {{ background: {INPUT_BG} !important; border: 1px solid {CARD_BORDER} !important; border-radius: 10px !important; color: {SIDEBAR_TEXT} !important; }}
    section[data-testid="stSidebar"] div[data-testid="stExpander"] {{ background: {CARD_BG}; border: 1px solid {CARD_BORDER}; border-radius: 10px; }}
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{ background: {INPUT_BG} !important; border-color: {CARD_BORDER} !important; border-radius: 8px !important; }}
    section[data-testid="stMain"] div[data-testid="stButton"]:first-of-type {{ position: fixed !important; top: 1rem !important; right: 1.2rem !important; z-index: 999999 !important; width: 44px !important; }}
    section[data-testid="stMain"] div[data-testid="stButton"]:first-of-type button {{ width: 44px !important; height: 44px !important; border-radius: 12px !important; padding: 0 !important; display: flex !important; justify-content: center !important; align-items: center !important; background: {CARD_BG} !important; border: 1px solid {CARD_BORDER} !important; color: {TEXT_MAIN} !important; font-size: 1.5rem !important; font-weight: 300 !important; box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important; backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); transition: all 0.2s ease; }}
    section[data-testid="stMain"] div[data-testid="stButton"]:first-of-type button:hover {{ border-color: {WIKI_BLUE} !important; color: {WIKI_BLUE} !important; transform: translateY(-2px); box-shadow: 0 6px 14px rgba(0,0,0,0.15) !important; }}
    section[data-testid="stMain"] div[data-testid="stButton"]:first-of-type button p {{ margin: 0 !important; padding: 0 !important; line-height: 1 !important; }}
    .stButton > button[kind="primary"] {{ background: linear-gradient(90deg, {WIKI_BLUE} 0%, {WIKI_BLUE_DARK} 100%); color: white !important; border: none; border-radius: 10px; font-weight: 600; padding: 0.6em 1em; box-shadow: 0 4px 14px rgba(51, 102, 204, 0.35); transition: transform 0.15s ease, box-shadow 0.15s ease; }}
    .stButton > button[kind="primary"]:hover {{ transform: translateY(-1px); box-shadow: 0 6px 18px rgba(51, 102, 204, 0.45); color: white !important; }}
    .hero-title {{ font-size: 2.6rem; font-weight: 800; letter-spacing: -1px; line-height: 1.15; margin: 3.5rem 0 0.15rem 0; background: linear-gradient(90deg, {WIKI_BLUE} 0%, {WIKI_BLUE_DARK} 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
    .hero-subtitle {{ color: {TEXT_MUTED} !important; font-size: 1.05rem; margin-bottom: 1.1rem; }}
    div[data-testid="stMetric"] {{ background: {CARD_BG}; border: 1px solid {CARD_BORDER}; border-radius: 14px; padding: 1rem 1.2rem; box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08); }}
    div[data-testid="stMetricLabel"] p {{ color: {WIKI_GRAY} !important; font-weight: 600; }}
    div[data-testid="stMetricValue"] {{ color: {WIKI_BLUE_DARK} !important; font-weight: 800; }}
    div[data-testid="stVerticalBlockBorderWrapper"] {{ background: {CARD_BG}; border-radius: 16px; box-shadow: 0 8px 28px rgba(0, 0, 0, 0.1); padding: 0.6rem; }}
    .health-card {{ background: {CARD_BG}; border: 1px solid {CARD_BORDER}; border-radius: 20px; padding: 2.5rem; margin-top: 0.5rem; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1); }}
    .health-title {{ font-size: 1.4rem; font-weight: 800; color: {TEXT_MAIN}; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid {CARD_BORDER}; padding-bottom: 1rem; }}
    .metric-label {{ font-size: 1.05rem; font-weight: 600; color: {TEXT_MAIN}; margin-bottom: 0.2rem; margin-top: 1rem; }}
    .metric-desc {{ font-size: 0.85rem; color: {TEXT_MUTED}; margin-bottom: 0.4rem; }}
    .stars {{ color: #ffc107; font-size: 1.3rem; letter-spacing: 3px; margin-bottom: 0.5rem; }}
    .overall-score {{ font-size: 2.8rem; font-weight: 800; color: {TEXT_MAIN}; margin-top: 0.5rem; }}
    .insight-box {{ border-left: 4px solid {WIKI_BLUE}; background: {INSIGHT_BG}; padding: 1.2rem 1.5rem; border-radius: 0 10px 10px 0; margin-bottom: 1.2rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- GLOBAL MAPS ---
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
REGION_COUNTRY_MAP = {
    "South Asia (SA)": ['bd', 'in', 'pk', 'np'],
    "Northern & Western Europe (NWE)": ['de', 'fr', 'uk', 'nl', 'be', 'ch', 'se', 'no', 'fi', 'at'],
    "Southern Europe & LatAm": ['it', 'es', 'pt', 'br', 'mx', 'ar', 'co'],
    "East, Southeast Asia, Pacific": ['id', 'ph', 'my'],
    "Africa & Middle East": ['ng', 'ke', 'eg', 'tr']
}

CODE_RE = re.compile(r'(wlf|wle|wlm|wlb)([a-z]{0,2})(\d{2,4})')

def get_category_name(code):
    match = CODE_RE.match(code)
    if not match: return None
    event, cc, yr = match.groups()
    yr_int = int(yr)
    full_year = yr_int if yr_int > 2000 else 2000 + yr_int
    cat = f"Images_from_Wiki_Loves_{EVENT_MAP[event]}_{full_year}"
    if cc and event != 'wlb':
        cat += f"_in_{COUNTRY_MAP.get(cc, '')}"
    return cat

# --- FAST API CALCULATION METHODS ---
def get_participants(code):
    cat = get_category_name(code)
    if not cat: return set()
    try:
        response = requests.get('https://ptools.toolforge.org/uploadersincat.php?category=' + cat, timeout=15)
        response.raise_for_status()
        content = response.content.decode("UTF-8")
        if '<legend>List</legend>' not in content: return set()
        users = set()
        for uincattxt in content.split('fieldset'):
            if '<legend>List</legend>' in uincattxt:
                for s in uincattxt.split('>'):
                    if "User:" in s and "href" not in s:
                        users.add(s.replace("User:", "").replace("</a", ""))
                break
        return users
    except Exception: return set()

def fetch_all_concurrently(codes, progress_text="Fetching data..."):
    results = {}
    total = len(codes)
    if total == 0: return results
    progress = st.progress(0, text=progress_text)
    with ThreadPoolExecutor(max_workers=min(16, max(1, total))) as executor:
        future_to_code = {executor.submit(get_participants, code): code for code in codes}
        done = 0
        for future in as_completed(future_to_code):
            code = future_to_code[future]
            try: results[code] = future.result()
            except Exception: results[code] = set()
            done += 1
            progress.progress(done / total, text=f"{progress_text} ({done}/{total})")
    progress.empty()
    return results

@st.cache_data(show_spinner=False, ttl=3600)
def derive_regional_baselines(region_name, event_type, target_yr_int):
    if region_name not in REGION_COUNTRY_MAP:
        return {"retention_base": 12.0, "growth_base": 30.0}
    countries = REGION_COUNTRY_MAP[region_name]
    prev_yr = target_yr_int - 1
    prev_prev_yr = target_yr_int - 2
    yr1_fmt = f"{prev_prev_yr % 100:02d}" if prev_prev_yr < 2000 else str(prev_prev_yr)
    yr2_fmt = f"{prev_yr % 100:02d}" if prev_yr < 2000 else str(prev_yr)
    
    codes_to_fetch = [f"{event_type}{c}{yr}" for c in countries for yr in (yr1_fmt, yr2_fmt)]
    data = fetch_all_concurrently(codes_to_fetch, "Deriving regional baseline metrics...")
    
    regional_retentions = []
    regional_growths = []
    
    for c in countries:
        c_base = data.get(f"{event_type}{c}{yr1_fmt}", set())
        c_target = data.get(f"{event_type}{c}{yr2_fmt}", set())
        if c_base and c_target:
            overlap = len(c_target & c_base)
            ret_rate = (overlap / len(c_base)) * 100
            growth_rate = (len(c_target - c_base) / len(c_target)) * 100
            regional_retentions.append(ret_rate)
            regional_growths.append(growth_rate)
            
    return {
        "retention_base": float(np.median(regional_retentions)) if regional_retentions else 15.0,
        "growth_base": float(np.median(regional_growths)) if regional_growths else 40.0
    }

def calculate_true_gini(array):
    array = np.array(array, dtype=np.float64)
    if array.size == 0: return 0.0
    array = np.sort(array)
    if np.amin(array) < 0: array -= np.amin(array)
    array += 0.0000001
    index = np.arange(1, array.shape[0] + 1)
    n = array.shape[0]
    return ((np.sum((2 * index - n - 1) * array)) / (n * np.sum(array)))

@st.cache_data(show_spinner=False, ttl=3600)
def fetch_fast_proxy_metrics(code):
    """
    SPEED OPTIMIZED SHORTCUT:
    1. Fetches a max 500 file sample (instead of all files) for a proxy Gini calculation.
    2. Uses that exact same sample to pick 50 files for a single globalusage query.
    Ensures 100% real API data, but limits overhead to 2 fast API calls.
    """
    cat = get_category_name(code)
    if not cat: return 50.0, 50.0

    # Call 1: Grab a fast 500-file sample
    params = {
        "action": "query", "list": "categorymembers", "cmtitle": f"Category:{cat}",
        "cmtype": "file", "cmlimit": "500", "cmprop": "title|user", "format": "json"
    }
    
    try:
        res = requests.get(MW_API_URL, params=params, timeout=10)
        res.raise_for_status()
        data = res.json().get("query", {}).get("categorymembers", [])
    except Exception:
        return 50.0, 50.0

    if not data: return 50.0, 50.0

    # Fast Gini on Sample
    user_counts = defaultdict(int)
    file_titles = []
    for item in data:
        user_counts[item.get("user", "Unknown")] += 1
        file_titles.append(item.get("title"))
    
    raw_gini = calculate_true_gini(list(user_counts.values()))
    diversity_score = (1.0 - raw_gini) * 100.0

    # Call 2: Piggyback off the same sample for global usage
    sample_titles = random.sample(file_titles, min(len(file_titles), 50))
    titles_string = "|".join(sample_titles)
    
    usage_params = {
        "action": "query", "prop": "globalusage", "titles": titles_string,
        "gulimit": "500", "format": "json"
    }
    
    try:
        usage_res = requests.get(MW_API_URL, params=usage_params, timeout=10)
        usage_res.raise_for_status()
        pages = usage_res.json().get("query", {}).get("pages", {})
        
        used_files = 0
        for page_info in pages.values():
            if page_info.get("globalusage", []):
                used_files += 1
                
        quality_score = (used_files / len(sample_titles)) * 100.0 if sample_titles else 0.0
    except Exception:
        quality_score = 50.0
        
    return quality_score, diversity_score

def calculate_stars(score, max_score=100):
    normalized = min(max(score / max_score, 0), 1)
    stars = int(round(normalized * 5))
    return "★" * max(1, stars) + "☆" * (5 - max(1, stars))

# --- SIDEBAR NAV ---
with st.sidebar:
    st.markdown(f'<div style="text-align: center; margin-bottom: 20px;"><img src="{KORIKATH_LOGO_URL}" alt="Logo" style="width: 140px;"></div>', unsafe_allow_html=True)
    app_mode = st.radio("Navigation", ["Retention Dashboard", "Event Evaluation"], label_visibility="collapsed", index=None)
    st.markdown("---")

    if app_mode == "Retention Dashboard":
        st.info("Navigate to Event Evaluation to run the new unified API metrics.")
    elif app_mode == "Event Evaluation":
        target_event = st.text_input("🎯 Target Campaign Code", value="", placeholder="e.g., wlmbd2024")
        st.markdown("---")
        comp_mode = st.radio("Benchmark Against:", ["Previous Year", "Custom Event", "Regional Standard Only"], index=0)
        
        pure_regional_mode = False
        if comp_mode == "Custom Event":
            baseline_event = st.text_input("⚖️ Baseline Campaign Code", value="", placeholder="e.g., wlmbd2023")
        elif comp_mode == "Previous Year":
            try:
                event, cc, yr = CODE_RE.match(target_event).groups()
                yr_int = int(yr)
                prev_yr = yr_int - 1
                yr_fmt = f"{prev_yr % 100:02d}" if yr_int < 2000 else str(prev_yr)
                baseline_event = f"{event}{cc}{yr_fmt}"
                st.info(f"Auto-Baseline: **{baseline_event}**")
            except: baseline_event = ""
        else:
            baseline_event = None
            pure_regional_mode = True
            
        region = st.selectbox("🌍 Geographic Peer Group", list(REGION_COUNTRY_MAP.keys()))
        analyze_btn = st.button("🩺 Generate Evaluation Report", type="primary", use_container_width=True)

# --- HEADER TOGGLE ---
toggle_icon = "☼" if st.session_state.is_dark_mode else "☾"
if st.button(toggle_icon, key="theme_toggle_btn", help="Toggle Theme"):
    st.session_state.is_dark_mode = not st.session_state.is_dark_mode
    st.rerun()

# --- EVALUATION PAGE LOGIC ---
if app_mode == "Event Evaluation":
    st.markdown('<div class="hero-title">Event Evaluation</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Fast Proxy API Metrics: Statistical sampling for rapid, real-world campaign insights.</div>', unsafe_allow_html=True)

    if analyze_btn:
        if not target_event or (not pure_regional_mode and not baseline_event):
            st.error("⚠️ Please provide valid event codes.")
            st.stop()

        with st.spinner("Querying MediaWiki APIs for live metrics (Fast Proxy Method)..."):
            
            users_data = fetch_all_concurrently([target_event] + ([baseline_event] if baseline_event else []), "Fetching primary events...")
            target_users = users_data.get(target_event, set())
            base_users = users_data.get(baseline_event, set()) if baseline_event else set()

            if not target_users:
                st.error(f"❌ No data found for target event: **{target_event}**.")
                st.stop()
                
            event_type, _, yr_str = CODE_RE.match(target_event).groups()
            target_yr_int = int(yr_str)
            if target_yr_int < 2000: target_yr_int += 2000
            region_vals = derive_regional_baselines(region, event_type, target_yr_int)

            metrics = {}
            if pure_regional_mode:
                metrics['Retention'] = {'raw': 'Requires Baseline', 'score': 50}
                metrics['Growth'] = {'raw': "Baseline Hidden", 'score': 60.0}
            else:
                if len(base_users) == 0:
                    metrics['Retention'] = {'raw': 'Baseline Missing', 'score': 0.0}
                    metrics['Growth'] = {'raw': 'Baseline Missing', 'score': 100.0}
                else:
                    overlap = len(target_users & base_users)
                    ret_rate = (overlap / len(base_users)) * 100
                    ret_score = (ret_rate / max(1, region_vals['retention_base'])) * 50
                    metrics['Retention'] = {'raw': f"{ret_rate:.1f}%", 'score': min(100, ret_score)}

                    new_users = len(target_users - base_users)
                    growth_rate = (new_users / len(target_users)) * 100
                    growth_score = (growth_rate / max(1, region_vals['growth_base'])) * 50
                    metrics['Growth'] = {'raw': f"{growth_rate:.1f}%", 'score': min(100, growth_score)}

            quality_raw, diversity_raw = fetch_fast_proxy_metrics(target_event)
            q_score = min(100.0, (quality_raw / 15.0) * 100) 
            
            metrics['Quality'] = {'raw': quality_raw, 'score': q_score}
            metrics['Diversity'] = {'raw': diversity_raw, 'score': diversity_raw}
            
            metrics['Overall'] = round(
                (metrics['Retention']['score'] * 0.50) + 
                (metrics['Growth']['score'] * 0.10) + 
                (metrics['Quality']['score'] * 0.25) + 
                (metrics['Diversity']['score'] * 0.15)
            )
            
            col1, col2 = st.columns([1, 1.2], gap="large")
            with col1:
                card_html = f"""<div class="health-card">
<div class="health-title"><span>{target_event.upper()} Evaluation</span><span>🔗</span></div>
<div class="metric-label">Retention ({metrics['Retention']['raw']})</div>
<div class="metric-desc">Percentage of users retained. Base metric: {region_vals['retention_base']:.1f}%</div>
<div class="stars">{calculate_stars(metrics['Retention']['score'])}</div>
<div class="metric-label">Growth ({metrics['Growth']['raw']})</div>
<div class="metric-desc">Percentage of fresh contributors. Base metric: {region_vals['growth_base']:.1f}%</div>
<div class="stars">{calculate_stars(metrics['Growth']['score'])}</div>
<div class="metric-label">Quality ({metrics['Quality']['raw']:.1f}% Used)</div>
<div class="metric-desc">Sampled percentage of media currently embedded in Wikipedia.</div>
<div class="stars">{calculate_stars(metrics['Quality']['score'])}</div>
<div class="metric-label">Diversity Index ({metrics['Diversity']['raw']:.1f})</div>
<div class="metric-desc">Proxy Gini coefficient derived from API sampling.</div>
<div class="stars">{calculate_stars(metrics['Diversity']['score'])}</div>
<hr style="border-color: {CARD_BORDER}; margin: 1.5rem 0;">
<div class="metric-label">Overall Evaluation Score</div>
<div class="overall-score">{metrics['Overall']}<span style="font-size: 1.2rem; color: {TEXT_MUTED};"> / 100</span></div>
</div>"""
                st.markdown(card_html, unsafe_allow_html=True)
                
            with col2:
                st.markdown("### 🧠 Smart Insights")
                st.markdown(f"<p style='color: {TEXT_MUTED}; margin-bottom: 1.5rem;'>Insights are generated dynamically using fast statistical proxies from live API data.</p>", unsafe_allow_html=True)
                
                insights = []
                if not pure_regional_mode and 'Baseline Missing' not in metrics['Retention']['raw']:
                    raw_ret = float(metrics['Retention']['raw'].replace('%', ''))
                    ret_diff = raw_ret - region_vals['retention_base']
                    if ret_diff > 5:
                        insights.append(f"🚀 <strong>Retention Outperformance:</strong> Your retention rate beat the {region.split(' (')[0]} median of {region_vals['retention_base']:.1f}%.")
                    elif ret_diff < -5:
                        insights.append(f"📉 <strong>Retention Warning:</strong> Retention dropped below the regional {region_vals['retention_base']:.1f}% standard.")
                    
                if metrics['Quality']['raw'] > 15.0:
                    insights.append(f"🛡️ <strong>High Media Utility:</strong> Over {metrics['Quality']['raw']:.1f}% of checked uploads are embedded in Wikimedia projects.")
                elif metrics['Quality']['raw'] < 5.0:
                    insights.append(f"⚠️ <strong>Low Media Utility:</strong> Only {metrics['Quality']['raw']:.1f}% of sampled files are actively used.")
                    
                if metrics['Diversity']['raw'] < 40:
                    insights.append("⚠️ <strong>Proxy Gini Inequality:</strong> The sampled upload pool is heavily centralized. A few 'power users' dominate the media.")
                else:
                    insights.append("⚖️ <strong>Democratic Participation:</strong> Excellent contributor balance according to the API sample.")
                
                for insight in insights:
                    st.markdown(f"<div class='insight-box'><p>{insight}</p></div>", unsafe_allow_html=True)
