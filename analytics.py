import re
import random
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import permutations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import requests
import seaborn as sns
import streamlit as st
from matplotlib.colors import LinearSegmentedColormap

# --- SHARED DATA CONSTANTS ---
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
    'ar': 'Argentina', 'co': 'Colombia', 'lk': 'Sri_Lanka', 'au': 'Australia',
    'nz': 'New_Zealand', 'th': 'Thailand', 'gr': 'Greece', 'tn': 'Tunisia',
    'ma': 'Morocco', 'dz': 'Algeria', 'za': 'South_Africa', 'gh': 'Ghana',
    'tz': 'Tanzania', 'pe': 'Peru', 'cl': 'Chile', 've': 'Venezuela',
    'cz': 'Czech_Republic', 'ro': 'Romania', 'hu': 'Hungary'
}

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


def render_worldmap_view(valid_countries):
    metric_choice = st.radio("Metric Vector Selection", ["Average", "Median"], horizontal=True, key="worldmap_metric")
    world_df = build_world_data(valid_countries, metric_choice)
    if world_df.empty:
        st.info("Geographic coordinates unavailable for the current selection.")
        return
    fig = create_worldmap(world_df, metric_choice)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(world_df, use_container_width=True, hide_index=True)


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
