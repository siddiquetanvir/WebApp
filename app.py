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

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Wikimedia Retention",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- WIKIPEDIA-INSPIRED DARK THEME (forced via .streamlit/config.toml — not left to the visitor's OS setting) ---
WIKI_BLUE = "#3366cc"
WIKI_BLUE_LIGHT = "#7aa7ff"
WIKI_BLUE_DARK = "#14428e"
WIKI_INK = "#202122"
WIKI_GRAY = "#54595d"
CARD_LIGHT = "#f7f9fc"

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
        border-radius: 12px;
    }}
    section[data-testid="stSidebar"] .stCaption, section[data-testid="stSidebar"] small {{
        color: #cdd9f2 !important;
    }}
    section[data-testid="stSidebar"] textarea {{
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        border-radius: 10px !important;
        color: #ffffff !important;
    }}
    section[data-testid="stSidebar"] textarea::placeholder {{
        color: rgba(255, 255, 255, 0.45) !important;
        font-style: italic;
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

    /* Hero title — gradient text, no emoji icon */
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
    .hint {{
        font-size: 0.78rem;
        color: {TEXT_LIGHT};
        opacity: 0.6;
        font-style: italic;
        margin-top: -6px;
        margin-bottom: 0.7rem;
    }}

    /* Segmented view-mode selector (pill-style radio) */
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

    /* Metric cards — light surface for contrast against the dark canvas */
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

    /* Heatmap cards — same light-surface treatment as the chart itself */
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
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- CONSTANTS ---
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

CODE_RE = re.compile(r'(wlf|wle|wlm|wlb)([a-z]{0,2})(\d{2})')
EXAMPLE_CODES = "wlfbd21 wlfbd22 wlfbd23 wlfin21 wlfin22 wlfin23"
COUNTRY_OPTIONS = sorted(COUNTRY_MAP.keys(), key=lambda k: COUNTRY_MAP[k])

# Wikipedia-blue gradient colormap for the heatmap (light card surface)
WIKI_CMAP = LinearSegmentedColormap.from_list(
    "wiki_blue", [CARD_LIGHT, "#bcd4f7", WIKI_BLUE, WIKI_BLUE_DARK, "#0b2b5c"]
)
# Glow-style scale for the dark-mode world map
WORLD_SCALE = ["#16233d", "#1f3f73", WIKI_BLUE, WIKI_BLUE_LIGHT, "#cfe0ff"]


def country_display_name(cc):
    return COUNTRY_MAP[cc].replace('_', ' ')


# --- DATA FETCHING (official Wikimedia Commons API, paginated) ---
@st.cache_data(show_spinner=False, ttl=3600)
def get_participants(code):
    try:
        code = re.sub(r'\s+', '', code).lower()
        match = CODE_RE.match(code)
        if not match:
            return set()
        event, cc, yr = match.groups()
        category = f"Images_from_Wiki_Loves_{EVENT_MAP[event]}_{2000 + int(yr)}"
        if cc and cc in COUNTRY_MAP:
            category += f"_in_{COUNTRY_MAP[cc]}"

        participants = set()
        url = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query", "generator": "categorymembers",
            "gcmtitle": f"Category:{category}", "gcmnamespace": 6,
            "gcmtype": "file", "prop": "imageinfo", "iiprop": "user",
            "format": "json", "gcmlimit": "max"
        }
        while True:
            data = requests.get(url, params=params, timeout=15).json()
            pages = data.get('query', {}).get('pages', {})
            participants.update(
                p['imageinfo'][0]['user'] for p in pages.values() if p.get('imageinfo')
            )
            if 'continue' in data and 'gcmcontinue' in data['continue']:
                params['gcmcontinue'] = data['continue']['gcmcontinue']
            else:
                break
        return participants
    except Exception:
        return set()


def fetch_all_concurrently(codes):
    """Fetch participant sets for all codes in parallel for speed."""
    results = {}
    total = len(codes)
    progress = st.progress(0, text="Fetching data from the Wikimedia Commons API…")

    with ThreadPoolExecutor(max_workers=min(16, max(1, total))) as executor:
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


def compute_retention_percentages(events):
    """Ordered-pair (source != target) retention percentages — the basis
    for the Table and Worldmap summary stats."""
    percentages = []
    for source, target in permutations(events.keys(), 2):
        source_users = events[source]
        if not source_users:
            continue
        overlap = len(source_users & events[target])
        percentages.append((overlap / len(source_users)) * 100)
    return percentages


# --- HEATMAP VIEW ---
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
    ax.set_ylabel("Source Event", fontweight='bold', color=WIKI_GRAY)
    ax.set_xlabel("Target Event", fontweight='bold', color=WIKI_GRAY)
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


# --- TABLE VIEW ---
def build_global_table(valid_countries):
    rows = []
    for country_code, events in valid_countries.items():
        percentages = compute_retention_percentages(events)
        if not percentages:
            continue
        rows.append({
            "Country": country_display_name(country_code),
            "Events": len(events),
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
        st.info("No comparable country data yet.")
        return
    st.dataframe(table_df, use_container_width=True)
    csv_bytes = table_df.to_csv(index=True, index_label="Rank").encode("utf-8")
    st.download_button(
        "⬇️ Download CSV", data=csv_bytes,
        file_name="wikimedia_retention_by_country.csv", mime="text/csv"
    )


# --- WORLDMAP VIEW ---
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
            "Events Compared": len(events),
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
        hover_data={"Events Compared": True, "Retention (%)": True},
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
        st.info("No mappable country data yet.")
        return
    fig = create_worldmap(world_df, metric_choice)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(world_df, use_container_width=True, hide_index=True)


# --- CODE BUILDER (selector-assisted entry, appends into the manual box) ---
def add_codes_from_selectors():
    """Callback: builds codes from the selectors and merges them into the
    manual text box, run before the text_area widget re-renders."""
    sel_events = st.session_state.get("sel_events", [])
    sel_countries = st.session_state.get("sel_countries", [])
    yr_start, yr_end = st.session_state.get("yr_range", (2021, 2023))

    if not sel_events:
        st.session_state.builder_msg = "*Pick at least one event first."
        return
    if not sel_countries:
        st.session_state.builder_msg = "*Pick at least one country too."
        return

    new_codes = []
    for event in sel_events:
        for country in sel_countries:
            for yr in range(yr_start, yr_end + 1):
                new_codes.append(f"{event}{country}{yr % 100:02d}")

    existing = st.session_state.get("code_input", "").split()
    merged = existing + [c for c in new_codes if c not in existing]
    st.session_state.code_input = " ".join(merged)
    st.session_state.builder_msg = f"*Added {len(new_codes)} code(s) — edit freely below."


def clear_code_input():
    st.session_state.code_input = ""
    st.session_state.builder_msg = ""


if "code_input" not in st.session_state:
    st.session_state.code_input = ""

VIEW_LABELS = {"Table": "📋 Table", "Heatmap": "🌡️ Heatmap", "Worldmap": "🗺️ Worldmap"}
METRIC3_LABELS = {"Table": "Rows in Table", "Heatmap": "Heatmaps Generated", "Worldmap": "Countries Mapped"}

# --- SIDEBAR ---
with st.sidebar:
    st.image(KORIKATH_LOGO_URL, width=100)
    st.title("Configuration")
    st.markdown("Type codes manually, or use the builder below to add them for you.")

    user_input = st.text_area(
        "Event Codes", key="code_input", placeholder=EXAMPLE_CODES, height=110
    )
    st.markdown('<div class="hint">*separate multiple codes with spaces</div>', unsafe_allow_html=True)

    with st.expander("🧭 Guided Builder"):
        st.markdown(
            '<div class="hint">*pick options below — no codes to memorize</div>',
            unsafe_allow_html=True
        )
        st.multiselect(
            "Events", options=list(EVENT_MAP.keys()),
            format_func=lambda k: EVENT_MAP[k], key="sel_events"
        )
        st.multiselect(
            "Countries", options=COUNTRY_OPTIONS,
            format_func=country_display_name, key="sel_countries"
        )
        st.slider("Year range", 2010, 2026, (2021, 2023), key="yr_range")

        b_col1, b_col2 = st.columns(2)
        b_col1.button("➕ Add to input", on_click=add_codes_from_selectors, use_container_width=True)
        b_col2.button("🗑️ Clear", on_click=clear_code_input, use_container_width=True)

        if st.session_state.get("builder_msg"):
            st.markdown(f'<div class="hint">{st.session_state.builder_msg}</div>', unsafe_allow_html=True)

    st.markdown("---")
    view_mode = st.radio(
        "Choose a view", list(VIEW_LABELS.keys()),
        format_func=lambda m: VIEW_LABELS[m], horizontal=True, key="view_mode"
    )
    run_button = st.button("🚀 Generate", type="primary", use_container_width=True)

    st.markdown("---")
    st.caption("Powered by the Wikimedia Commons API & Streamlit")

# --- MAIN CONTENT ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="hero-title">Cross-Event Retention Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Compare participant retention across Wikimedia campaigns '
    '— as a heatmap, table, or interactive world map.</div>',
    unsafe_allow_html=True
)

if run_button:
    raw_input = user_input.strip() or EXAMPLE_CODES
    codes = raw_input.split()
    valid = [c for c in (re.sub(r'\s+', '', cd).lower() for cd in codes) if CODE_RE.match(c)]

    if not valid:
        st.error("⚠️ No valid event codes found. Please check your formatting.")
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

results = st.session_state.get("last_valid_countries")

if results is not None:
    if not results:
        st.warning(
            "⚠️ **Not enough data.** Each view needs at least two events "
            "in the same country to calculate overlap."
        )
    else:
        st.success("✅ Data fetched successfully!")
        st.markdown("---")

        total_events = sum(len(events) for events in results.values())
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Countries Analyzed", len(results))
        col_m2.metric("Total Events Included", total_events)
        col_m3.metric(METRIC3_LABELS[view_mode], len(results))

        st.markdown("<br>", unsafe_allow_html=True)

        if view_mode == "Heatmap":
            render_heatmap_view(results)
        elif view_mode == "Table":
            render_table_view(results)
        else:
            render_worldmap_view(results)
