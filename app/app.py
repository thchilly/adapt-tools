import os
import textwrap
from pathlib import Path
from html import escape
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
import streamlit as st
import re

# ---------- SITE & THEME ----------
st.set_page_config(
    page_title="FutureMed — Tools & Data",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {max-width: 1250px; padding-right: 100px;}
      .tool-card { 
        border:1px solid #e6e6e6; border-radius:12px; background:#fff; 
        height: 440px; /* fixed card height for uniform boxes */
        display:flex; flex-direction:column; justify-content:flex-start; align-items:stretch;
        box-sizing: border-box;
        padding: 0; /* image should touch the card border */
        cursor: pointer;
        transition: transform 120ms ease, box-shadow 160ms ease;
      }
      .tool-card:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
      }
      .tool-title {font-weight:600; font-size:1.05rem; margin-bottom:6px;}
      .tool-desc {color:#444; font-size:0.95rem; min-height:48px;}
      .muted {color:#666; font-size:0.9rem;}
      .pill {display:inline-block; background:#f2f2f2; padding:2px 8px; border-radius:999px; font-size:0.8rem; margin-right:6px;}
      .banner {width:100%; border-radius:12px; margin:8px 0 18px 0;}
      .back-link a {text-decoration:none;}

      /* --- Grid polish --- */
      .tool-image { width:100%; height:240px; object-fit:cover; border-radius:12px 12px 0 0; display:block; }
      .tool-body { padding:16px; display:flex; flex-direction:column; align-items:center; gap:10px; flex:1; }
      .tool-title-wrap {
        min-height: 60px; /* room for ~3 lines at ~1.1rem */
        display:flex; align-items:center; justify-content:center; text-align:center;
        padding: 0 6px;
      }
      .tool-title {font-weight:700; font-size:1.1rem; line-height:1.2; margin:0;}
      /* Uniform responsive card grid with equal gaps */
      .card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 24px; /* controls BOTH horizontal & vertical spacing */
        align-items: stretch;
      }
      /* Optional: tighten inside spacing on very wide screens */
      @media (min-width: 1600px) {
        .card-grid { gap: 28px; }
      }
      /* Pills */
      .pill { display:inline-block; padding:4px 10px; border-radius:999px; font-size:0.78rem; margin:2px; opacity:0.7; }
      .pill--sector { background: #7bd389; }   /* light green */
      .pill--type { background: #87b5ff; }     /* light blue */
      .pill--scale { background: #c9a7ff; }    /* light purple */
      .pill--output { background: #ffcc99; }   /* light orange */
      .pill--cost { background: #c8d6e5; }     /* light grey-blue */
      /* --- Fixed top navigation bar (white) --- */
      .topbar {
        position: fixed; top: 60px; left: 0; right: 0; z-index: 3000;
        background: #fff; border-bottom: 1px solid #ececec;
        height: 55px; /* keep in sync with .nav-spacer */
      }
      /* center content within the same max width as the page */
      .topbar .inner {
        max-width: 1250px; margin: 0 auto; height: 100%; padding: 0 18px;
        display:flex; align-items:center; justify-content:flex-end; gap:10px;
      }
      .topbar .nav { display:flex; align-items:center; gap:10px; }
      .topbar .nav a { text-decoration:none; color:#222; font-weight:600; padding:4px 20px; border-radius:18px; }
      .topbar .nav a:hover { background:#f3f3f3; }
      .topbar .nav a.active { background: var(--merlot-red); color:#fff; }

      /* Spacer to keep content below the fixed topbar */
      .nav-spacer { height: 55px; }
      /* --- Header / Hero banner --- */
      .site-header { position: relative; z-index: 1; }
      .hero {
        width: 100%; /* height is set inline from Python */ border-radius: 5px; margin: 8px 0 18px 0;
        background-size: cover; background-position: center; background-repeat: no-repeat;
        display:flex; align-items:center; justify-content:space-between; gap:16px; padding: 14px 18px;
      }
      .hero .brand { display:flex; align-items:center; gap:14px; }
      .hero .brand img { height: 120px; filter: drop-shadow(0 1px 2px rgba(0,0,0,.2)); margin-left: 30px; }
      .hero .brand .title { color:#fff; font-weight:700; font-size:1.2rem; text-shadow: 0 1px 3px rgba(0,0,0,.35); }

      /* --- FutureMed brand palette --- */
      :root {
        --merlot-red: #821810;    /* Merlot */
        --dijon-yellow: #FCCF8F;  /* Dijon */
        --creme-white: #FEFDEF; /* very light yellow */
      }

      /* Selected filter pills in sidebar + anywhere (BaseWeb tags) */
      .stMultiSelect [data-baseweb="tag"],
      [data-baseweb="tag"] {
        background-color: var(--merlot-red) !important;
        color: #fff !important;
      }
      /* Make inner label/icon white too */
      [data-baseweb="tag"] * { color: #fff !important; }

      /* Reduce top padding so banner sits closer to the top */
      .block-container {
        padding-top: 3rem !important; /* was 5rem */
      }

      /* Floating "Suggest a tool!" button (appears after delay) */
      .fab-suggest {
        position: fixed; /* float over the whole app */
        right: 22px; bottom: 22px;
        z-index: 2000;
        background: var(--merlot-red); color:#fff; font-weight:700;
        padding: 12px 16px; border-radius: 999px; text-decoration:none;
        box-shadow: 0 6px 18px rgba(0,0,0,.18);
        transition: transform 120ms ease, box-shadow 160ms ease, opacity 200ms ease;
        opacity: 0; pointer-events: none;
        animation: fmFadeIn 500ms ease 3s forwards; /* show after 3s */
      }
      @keyframes fmFadeIn { to { opacity: 0.96; pointer-events: auto; } }
      .fab-suggest:hover { transform: translateY(-1px) scale(1.02); box-shadow: 0 10px 26px rgba(0,0,0,.22); }
      .fab-suggest:link, .fab-suggest:visited { color:#fff; }

      /* Floating "Suggest a tool!" button — never underline */
      .stApp a.fab-suggest,
      .stApp a.fab-suggest:link,
      .stApp a.fab-suggest:visited,
      .stApp a.fab-suggest:hover,
      .stApp a.fab-suggest:active,
      .stApp a.fab-suggest:focus {
        position: fixed !important;
        right: 22px !important;
        bottom: 22px !important;
        z-index: 2000 !important;
      
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 8px !important;
      
        background: var(--merlot-red) !important;
        color: #fff !important;
        font-weight: 700 !important;
        padding: 12px 16px !important;
        border-radius: 999px !important;
      
        text-decoration: none !important;
        border: none !important;
        border-bottom: 0 !important;
        outline: none !important;
      
        box-shadow: 0 6px 18px rgba(0,0,0,.18) !important;
        transition: transform 120ms ease, box-shadow 160ms ease, opacity 200ms ease !important;
      
        opacity: 0 !important;
        pointer-events: none !important;
        animation: fmFadeIn 500ms ease 3s forwards !important; /* show after 3s */
      }
      @keyframes fmFadeIn { 
        to { opacity: 0.96; pointer-events: auto; } 
      }
      .stApp a.fab-suggest:hover {
        transform: translateY(-1px) scale(1.02) !important;
        box-shadow: 0 10px 26px rgba(0,0,0,.22) !important;
      }
       
       /* Guard against any global link underline rules inside markdown containers */
       .stApp .element-container a.fab-suggest { text-decoration: none !important; border-bottom: 0 !important; }
      
      /* Brand primary buttons */
      .stButton > button { background: var(--merlot-red) !important; color:#fff !important; border: none !important; }

      /* --- Lock Streamlit sidebar open & hide collapse control --- */
      /* Keep the sidebar visible and prevent the translateX collapse */
      section[data-testid="stSidebar"] {
      transform: none !important;
      visibility: visible !important;
      min-width: 350px !important;
      width: 350px !important;  /* adjust 300–360 to taste */
      }

      /* Add a tiny top padding so it doesn't feel glued under the topbar */
      section[data-testid="stSidebar"] > div:first-child {
      padding-top: 20px;
      }

      /* Hide the chevron/handle so the user cannot close it */
      [data-testid="stSidebarCollapseButton"],
      [data-testid="collapsedControl"] {
      display: none !important;
      }

      /* Brand button for external links */
      a.brand-btn{
        display:inline-block;
        text-decoration:none;
        background: var(--merlot-red);
        color:#fff;
        font-weight:700;
        padding:12px 16px;
        border-radius:8px;
        box-shadow: 0 6px 18px rgba(0,0,0,.12);
        transition: transform 120ms ease, box-shadow 160ms ease, opacity 200ms ease;
      }
      a.brand-btn:hover{
        transform: translateY(-1px);
        box-shadow: 0 10px 26px rgba(0,0,0,.20);
      }
      a.brand-btn.brand-btn--wide{
        display:block; width:100%; text-align:center;
      }

      /* --- Tool detail page layout --- */
      .tool-hero-banner { width:100%; height:220px; object-fit:cover; border-radius:8px; display:block; margin-bottom: 22px; }
      .tool-detail-split { display:grid; grid-template-columns: 65% 35%; gap:32px; align-items:start; margin-top: 28px; }
      .tool-detail-left { 
        text-align: justify; 
        border-right: 2px solid #d9d9d9; 
        padding-right: 50px; 
        padding-bottom: 0;
      }
      .meta-details {
        margin-top: 24px;
      }
      .tool-detail-right { padding-left: 22px; }
      .tool-detail-right h4 { margin: 0 0 10px 0; }
      .pill-stack { display:flex; flex-wrap:wrap; gap: 2px 6px; }
      .glance-group { margin-bottom: 14px; }
      .glance-group h5 { margin: 0 0 1px 0; font-size: 0.95rem; }
      .tool-highlights{ margin-top:22px; margin-bottom:30px; }
      .tool-highlights ul{ margin:6px 0 0 20px; }
    </style>
    """,
    unsafe_allow_html=True
)
# Simple slugify helper for generating stable widget keys
def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")

def tool_card_html(tool: pd.Series, badges: dict[str, dict[int, list[str]]]) -> str:
    # img_path = tool_image_path(tool["tool_id"])
    # if not img_path or not Path(img_path).exists():
    #     img_path = PLACEHOLDER_PATH
    # with open(img_path, "rb") as f:
    #     img_base64 = base64.b64encode(f.read()).decode()

    img_url = tool_image_url(int(tool["tool_id"]))

    tid = int(tool["tool_id"])
    # escape dynamic text
    tool_name = escape(str(tool.get("tool_name", "(No name)")))

    # collect minimal labels for the colored pills (cap to 2 each for compactness) and escape them
    sector_vals = [escape(p) for p in badges["sector"].get(tid, [])[:2]]
    type_vals   = [escape(p) for p in badges["tool_type"].get(tid, [])[:2]]
    scale_vals  = [escape(p) for p in badges["scale_political"].get(tid, [])[:2]]
    output_vals = [escape(p) for p in badges["output_type"].get(tid, [])[:2]]
    cost_val    = escape(str(tool.get("cost", "") or "").strip())

    pills_html = "".join(f'<span class="pill pill--sector">{p}</span>' for p in sector_vals)
    pills_html += "".join(f'<span class="pill pill--type">{p}</span>' for p in type_vals)
    pills_html += "".join(f'<span class="pill pill--scale">{p}</span>' for p in scale_vals)
    pills_html += "".join(f'<span class="pill pill--output">{p}</span>' for p in output_vals)
    if cost_val:
        pills_html += f'<span class="pill pill--cost">{cost_val}</span>'

    # single-line HTML to avoid Markdown’s code-block interpretation of indented lines
    return (
        f'<a class="tool-card-link" href="?page=tool&id={tid}" style="display:block; text-decoration:none; color:inherit;">'
        f'  <div class="tool-card">'
        f'    <img class="tool-image" loading="lazy" decoding="async" src="{img_url}">'
        f'    <div class="tool-body">'
        f'      <div class="tool-title-wrap"><div class="tool-title">{tool_name}</div></div>'
        f'      <div>{pills_html}</div>'
        f'    </div>'
        f'  </div>'
        f'</a>'
    )



#
# ---------- HELP TEXTS FOR FILTERS (hover tooltips) ----------
# HELP_TEXTS = {
#     "User Group": "Who is the tool primarily built for (e.g., policymakers, local government, private sector, researchers, NGOs, general public).",
#     "Sector Focus": "Which sectors the tool targets (e.g., water, health, energy, agriculture, urban planning). Choose multiple if applicable.",
#     "Tool Type": "What the tool fundamentally does (e.g., data/visualization, risk assessment, planning & policy, early warning, education).",
#     "Target Scale (Political)": "Political/administrative scale the tool addresses (local, regional, national, international, multi‑level).",
#     "Target Scale (Physical)": "Physical/geographic units (catchment, ecosystem/biome, urban/rural, landscape/seascape, multi‑level).",
#     "Temporal Scale": "Time horizon supported (past/present, short‑term days, medium‑term months, long‑term decades, multiple).",
#     "Temporal Resolution": "Granularity of outputs (hourly, daily, monthly, seasonal, annual, multi‑year statistics).",
#     "Methodological Approach": "Core methods used (participatory, scenario/predictive, policy/economic, spatial/GIS, frameworks/MCDA).",
#     "Data Utilization": "Type and source of data (quantitative/qualitative, primary/secondary, detailed/aggregated, or mixed).",
#     "Output Type": "What you get from the tool (maps/visuals, reports/guidelines, datasets, simulations/models, decision aids).",
#     "Accessibility & Usability": "How easy it is to use (high = general users; moderate = some technical knowledge; low = expert‑level).",
#     "Multi-language Support": "Does the tool interface/support exist in more than one language (Yes/No).",
#     "Languages": "Available interface or documentation languages.",
#     "Customizability": "How much you can configure workflows, parameters, or outputs (low/moderate/high).",
#     "Integration Capability": "How well it plugs into other tools/data (APIs, export formats, embedding).",
#     "Validation & Reliability": "Evidence of quality (peer‑reviewed, case‑study validated, expert‑verified, user‑tested).",
#     "Cost": "Licensing/price (e.g., free, freemium, subscription, paid).",
#     "Maintenance": "Update pattern (regular updates, occasional, static).",
#     "Support": "Type of support (full technical support, limited, community‑based, none).",
#     "Area Scope": "Geographic scope category (Global, Continent, Region, Country, Subnational).",
#     "Area (Names)": "Specific places (e.g., Europe, Italy, California). Filter names are narrowed by the selected scope above.",
# }

HELP_TEXTS = {
        # -------------------- TOOL BASICS --------------------
        "User Group": """
    **Who the tool is for.**
    - **Policymakers** — shape policy and regulation  
    - **Municipal/Local Government** — city/regional planning and services  
    - **Researchers/Educators** — research, teaching, analysis  
    - **Private sector** — consulting, insurance, agriculture, real estate, engineering  
    - **NGOs/Community** — awareness, participation, community resilience  
    - **General public** — personal risk awareness and learning
    """,

        # -------------------- FOCUS & APPLICABILITY --------------------
        "Sector Focus": """
    **Which domains the tool covers.**
    Choose one or more (e.g., **Agriculture**, **Health**, **Water**, **Energy**, **Urban Planning**).  
    **All Sectors** indicates broad, cross-domain applicability.
    """,

        "Tool Type": """
    **What the tool fundamentally does.**
    - **Decision Support System (DSS)** — scenarios, cost–benefit, MCDA  
    - **Risk & Vulnerability Assessment** — risk mapping/profiling  
    - **Planning & Policy Guidance** — frameworks/guidelines/recommendations  
    - **Data & Visualization** — indicators, datasets, dashboards/maps  
    - **Early Warning & Resilience** — hazard alerts, resilience diagnostics  
    - **Education & Awareness** — training, outreach, engagement
    """,

        "Target Scale (Political)": """
    **Administrative level addressed.**
    - **Local** — cities/neighbourhoods  
    - **Regional** — provinces/states, multi-city areas  
    - **National** — country-level  
    - **International** — multi-country/global  
    - **Multi-level (Political)** — works across several political levels
    """,

        "Target Scale (Physical)": """
    **Physical/geographic unit used.**
    - **Catchment/Watershed** — hydrologic basins  
    - **Ecosystem/Biome** — forests, deserts, marine systems  
    - **Urban/Rural Zone** — settlement types  
    - **Landscape/Seascape** — mountains, coasts, wider regions  
    - **Multi-level (Physical)** — combines multiple physical scales
    """,

        # -------------------- TECHNICAL SPECS --------------------
        "Temporal Scale": """
    **Time horizon supported.**
    - **Past & Present** — baselines, trends  
    - **Short-term (days)** — immediate/operational use  
    - **Medium-term (months)** — seasonal planning  
    - **Long-term (decades)** — strategies and scenarios  
    - **Multiple** — lets you pick among several horizons
    """,

        "Temporal Resolution": """
    **Granularity of outputs.**
    - **Hourly** — operations, warnings  
    - **Daily / Monthly** — planning/tactical use  
    - **Seasonal / Annual** — trends, summaries  
    - **Multi-year** — long-term statistics/averages
    """,

        "Methodological Approach": """
    **Core methods employed.**
    - **Participatory/Stakeholder** — workshops, co-production, surveys  
    - **Scenario/Predictive/Quantitative** — models, statistics, ML  
    - **Policy & Economic** — impact, CBA, macro/micro-economics  
    - **Spatial/GIS** — mapping, remote sensing, land-use analysis  
    - **Frameworks/MCDA** — structured decision processes
    """,

        "Data Utilization": """
    **Type and source of data.**
    - **Quantitative — Primary — Detailed** — fine-grained field/survey data  
    - **Quantitative — Secondary — Aggregated** — existing datasets at broader scales  
    - **Qualitative — Primary — Detailed** — interviews, cases, stakeholder input  
    - **Qualitative — Secondary — Aggregated** — literature/report syntheses  
    - **Mixed** — combines quantitative & qualitative
    """,

        # -------------------- OUTPUTS & UX --------------------
        "Output Type": """
    **What you get from the tool.**
    - **Reports & Guidelines** — text documents, frameworks  
    - **Maps & Visualizations** — dashboards, charts, maps  
    - **Simulations & Interactive Models** — scenario explorers, digital twins  
    - **Datasets** — raw/processed data for download or integration  
    - **Decision Facilitation** — indices, matrices, scorecards  
    - **Educational/Engagement** — learning/participation materials
    """,

        "Accessibility & Usability": """
    **Ease of use.**
    - **High** — intuitive for general users; guides/tutorials available  
    - **Moderate** — some technical/scientific knowledge required  
    - **Low** — expert-level knowledge needed
    """,

        "Multi-language Support": """
    **Whether multiple languages are provided.**
    - **Yes** — interface and/or docs available in several languages  
    - **No** — single language only
    """,

        "Languages": """
    **Which languages are supported.**
    Useful for stakeholder engagement and localisation.
    """,

        # -------------------- CUSTOMIZATION & INTEGRATION --------------------
        "Customizability": """
    **How much you can adjust the tool.**
    - **High** — extensive parameter/scenario configuration  
    - **Moderate** — some adjustable settings  
    - **Low** — minimal adjustments  
    - **Fixed** — no customization
    """,

        "Integration Capability": """
    **How well it connects with other systems.**
    - **High** — APIs/standards; common formats; easy interoperability  
    - **Moderate** — basic import/export or partial compatibility  
    - **No** — stand-alone (no integration options)
    """,

        # -------------------- VALIDATION --------------------
        "Validation & Reliability": """
    **Evidence of credibility.**
    - **Peer-reviewed/endorsed** — formal review/endorsement  
    - **Case-study validated** — documented real-world use  
    - **Expert verified** — assessed by practitioners/experts  
    - **User-tested/community feedback** — iterative improvements from users  
    - **Not validated** — no formal evidence (use with caution)
    """,

        # -------------------- COST & SUPPORT --------------------
        "Cost": """
    **Pricing model.**
    - **Free** — no cost  
    - **Subscription-based** — recurring fee  
    - **One-time purchase** — upfront payment  
    - **Tiered pricing** — varies by user type/usage level
    """,

        "Maintenance": """
    **Update frequency.**
    - **Regular Updates** — actively maintained  
    - **Occasional Updates** — periodic releases  
    - **Static (No Updates)** — use as-is
    """,

        "Support": """
    **Available help.**
    - **Full Technical Support** — comprehensive assistance  
    - **Limited Support** — restricted help/response  
    - **Community Support** — forums/user groups  
    - **Static (No Support)** — no formal support
    """,

        # -------------------- GEOGRAPHY --------------------
        "Area Scope": """
    **Geographic coverage category.**
    - **Global** — worldwide  
    - **Continent** — e.g., Europe, Africa  
    - **Region** — supra-national/trans-boundary areas (e.g., Mediterranean)  
    - **Country** — single nation  
    - **Subnational** — state/province/district
    """,

        "Area (Names)": """
    **Specific places within the chosen scope.**
    Examples: **Europe**, **Italy**, **California**, **Danube Basin**, **Alps**, **Mediterranean**.  
    Selecting **Area Scope** first narrows these options.
    """,
}


 # ---------- FILTER DETAILS (for the Guide page) ----------
# Detailed option lists matching the master Word file / database taxonomy.
FILTER_DETAILS = {
    "User Group": [
        ("Policymakers", "National policymakers, regulators, decision‑makers setting and implementing climate policy."),
        ("Municipal/Local Government", "Local representatives, urban planners, municipal authorities working on adaptation and local planning."),
        ("Educators/Academia", "University researchers, faculty, students, and educators using the tool for research/teaching."),
        ("Private Sector", "Engineers, consultants, insurers, agriculture/real‑estate and other industry professionals doing impact/risk work."),
        ("Community Organizations/NGOs", "Non‑profits and community groups doing adaptation, awareness and resilience work."),
        ("Researchers", "Climate/environmental researchers and analysts focused on technical analysis in adaptation."),
        ("General Public", "People using the tool for awareness, personal risk assessment or learning."),
        ("Other", "Not covered by the above."),
    ],

    "Sector Focus": [
        ("Agriculture", "Farming systems, crops, livestock, agronomy."),
        ("All Sectors", "Cross‑sectoral scope."),
        ("Biodiversity", "Species, habitats, conservation and ecosystems."),
        ("Coastal Management", "Coasts, sea‑level rise, erosion and coastal hazards."),
        ("Cultural Heritage", "Sites, monuments, and heritage conservation."),
        ("Emergency Management", "Preparedness/response, civil protection, risk services."),
        ("Energy", "Supply, demand, grids, renewables, energy systems."),
        ("Food Security", "Availability, access, utilization and stability of food systems."),
        ("Forestry", "Forest resources, management, wildfire risk in forests."),
        ("Health", "Public health, heatwaves, disease risk, healthcare systems."),
        ("Industry", "Manufacturing and industrial processes."),
        ("Infrastructure", "Built assets, utilities, networks and their resilience."),
        ("Socio‑Economic", "Livelihoods, equity, economics and society."),
        ("Tourism", "Tourism destinations, seasonality and services."),
        ("Transport", "Road, rail, air and maritime transport systems."),
        ("Urban Planning", "Cities, land‑use, planning and services."),
        ("Waste", "Waste management and circularity."),
        ("Water (Resources/Extremes)", "Water resources, droughts/floods, hydrology."),
        ("Wildfire", "Wildfire risk, monitoring and response."),
    ],

    "Tool Type": [
        ("Decision Support System (DSS)", "Integrates data/analyses for structured decisions (scenarios, CBA, MCDA)."),
        ("Risk & Vulnerability Assessment", "Assesses climate risks/vulnerabilities; often mapping and profiling."),
        ("Planning & Policy Guidance", "Frameworks/guidance for adaptation planning and policy development."),
        ("Data & Visualization", "Provides indicators/datasets with visualizations (maps, dashboards)."),
        ("Early Warning & Resilience", "Hazard alerts and/or resilience assessments for proactive action."),
        ("Education & Awareness", "Learning/engagement tools and participatory platforms."),
        ("Other", "Not covered by the above."),
    ],

    "Target Scale (Political)": [
        ("Local", "Neighborhoods or cities and similar small administrative units."),
        ("Regional", "Sub‑national areas (multi‑city regions, counties, provinces/states)."),
        ("National", "Country‑level applications."),
        ("International", "Multi‑country or global regions."),
        ("Multi‑level (Political)", "Operates across multiple political scales."),
        ("Other", "Not covered by the above."),
    ],

    "Target Scale (Physical)": [
        ("Catchment/Watershed", "River basins, watersheds, hydrological boundaries."),
        ("Ecosystem/Biome", "Forests, deserts, marine ecosystems and other biomes."),
        ("Urban/Rural Zone", "Urban, peri‑urban or rural areas."),
        ("Landscape/Seascape", "Broader landscape/seascape units (mountain ranges, coastal zones)."),
        ("Multi‑level (Physical)", "Combines multiple ecological/geographical units."),
        ("Other", "Not covered by the above."),
    ],

    "Temporal Scale": [
        ("Past & Present", "Historical/current conditions and trends."),
        ("Short Term (days)", "Next days for near‑immediate decisions."),
        ("Medium Term (months)", "Next months (seasonal planning)."),
        ("Long Term (decades)", "Decadal/multi‑decadal projections and scenarios."),
        ("Multiple Scales", "Supports several of the above horizons."),
    ],

    "Temporal Resolution": [
        ("Hourly", ""), ("Daily", ""), ("Monthly", ""), ("Seasonal", ""), ("Annual", ""),
        ("Multi‑Year / Long‑Term Stats", "Averages/trends aggregated over multiple years."),
    ],

    "Methodological Approach": [
        ("Participatory / Stakeholder", "Workshops, co‑production, consultations, surveys."),
        ("Scenario / Predictive / Quantitative", "Process‑based models, statistics, forecasting, ML."),
        ("Policy & Economic", "Policy impact assessment, CBA, economics."),
        ("Spatial / GIS", "GIS mapping, spatial analysis, remote sensing, land‑use mapping."),
        ("Frameworks / Structured Processes", "Resilience frameworks, adaptation pathways, MCDA."),
        ("Other", "Not covered by the above."),
    ],

    "Data Utilization": [
        ("Quantitative, Primary, Detailed", "Fine‑grained numerical data collected for the tool (surveys, field)."),
        ("Quantitative, Secondary, Aggregated", "Existing numeric data aggregated to broader scales."),
        ("Qualitative, Primary, Detailed", "Interviews, cases, stakeholder inputs with rich detail."),
        ("Qualitative, Secondary, Aggregated", "Summaries/generalized non‑numeric evidence."),
        ("Mixed (Quantitative + Qualitative)", "Flexible sources and granularity, combining methods."),
        ("Other", "Not covered by the above."),
    ],

    "Output Type": [
        ("Reports & Guidelines", "Text‑based outputs (reports, frameworks, manuals)."),
        ("Maps & Visualizations", "Maps, charts, dashboards and visuals."),
        ("Simulations & Interactive Models", "Dynamic models, digital twins, scenario explorers."),
        ("Data Provision / Datasets", "Raw/processed datasets and indicators for download/integration."),
        ("Decision Facilitation", "Scorecards, decision matrices, indices for prioritization."),
        ("Educational / Engagement", "Training modules, awareness/engagement resources."),
        ("Other", "Not covered by the above."),
    ],

    "Accessibility & Usability": [
        ("High", "General‑user friendly; guides/tutorials; minimal technical knowledge needed."),
        ("Moderate", "Some technical/scientific knowledge required."),
        ("Low", "Expert‑level knowledge required; specialized resources."),
        ("Unclear", "Not specified by the provider."),
    ],

    "Multi-language Support": [
        ("Yes", "Supports multiple interface/documentation languages."),
        ("No", "Single language only."),
    ],

    "Customizability": [
        ("High", "Extensive parameter/scenario configuration; often with external integrations."),
        ("Moderate", "Some adjustable parameters/scenarios."),
        ("Low", "Minimal settings; mostly presets."),
        ("Fixed", "No customization; standardized outputs."),
        ("Not Specified", "No clear information provided."),
    ],

    "Integration Capability": [
        ("High", "APIs/standards; broad data format support; easy interoperability."),
        ("Moderate", "Some import/export; limited compatibility or needs customization."),
        ("No", "Stand‑alone with no integration options."),
        ("Not Specified", "No clear information provided."),
    ],

    "Validation & Reliability": [
        ("Peer‑reviewed/endorsed", "Formally reviewed or endorsed by reputable bodies."),
        ("Case‑study validated", "Validated via documented real‑world applications."),
        ("Expert verified", "Assessed by domain experts/practitioners."),
        ("User‑tested/community feedback", "Reliability indicated by user feedback and iteration."),
        ("Not validated", "No formal validation evidence."),
        ("Not specified", "No clear information provided."),
    ],

    "Cost": [
        ("Free", "No cost to access and use."),
        ("Subscription‑based", "Recurring fee for access (monthly/annual)."),
        ("One‑time purchase", "Single upfront payment."),
        ("Tiered pricing", "Pricing varies by user type or usage level."),
        ("Other", "Not covered by the above."),
    ],

    "Maintenance": [
        ("Regular Updates", "Actively maintained with frequent releases."),
        ("Occasional Updates", "Periodic updates without fixed schedule."),
        ("Static (No Updates)", "No updates; use as‑is."),
        ("Other", "Not covered by the above."),
    ],

    "Support": [
        ("Full Technical Support", "Comprehensive support and troubleshooting."),
        ("Limited Support", "Restricted support or slower response."),
        ("Community Support", "Forums/user groups; peer assistance."),
        ("Static (No Support)", "No formal support available."),
        ("Other", "Not covered by the above."),
    ],

    "Area Scope": [
        ("Global", "Worldwide applicability."),
        ("Continent", "Whole‑continent focus (e.g., Europe, Africa)."),
        ("Region", "Supra‑national/trans‑boundary regions (e.g., Mediterranean)."),
        ("Country", "Single nation focus."),
        ("Subnational", "State/province/district level."),
    ],
}

# ---------- STATIC / ASSETS LAYOUT ----------
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = (BASE_DIR / ".." / "public").resolve()
ASSETS_DIR = PUBLIC_DIR / "assets"                 # public/assets
TOOLS_DIR = ASSETS_DIR / "tools"                   # public/assets/tools/{tool_id}.png
BANNERS_DIR = ASSETS_DIR / "tool_banners"          # public/assets/tool_banners/{tool_id}.png

# ---------- STATIC URL BASE ----------
# In Docker (behind Nginx), assets are served at /assets.
# You can override at runtime (e.g., CDN or different mount) with STATIC_BASE.
# Examples:
#   STATIC_BASE=""              -> "/assets/..." (default; recommended in Compose)
#   STATIC_BASE="https://cdn"   -> "https://cdn/assets/..."
STATIC_BASE = os.getenv("STATIC_BASE", "").rstrip("/")
STATIC_ASSETS = f"{STATIC_BASE}/assets" if STATIC_BASE else "/assets"

# Common URLs
LOGO_URL = f"{STATIC_ASSETS}/logo.png"
HERO_BANNER_URL = f"{STATIC_ASSETS}/banner.jpg"
PLACEHOLDER_URL = f"{STATIC_ASSETS}/placeholder.png"
TOOLS_URL_BASE = f"{STATIC_ASSETS}/tools"
TOOL_BANNERS_URL_BASE = f"{STATIC_ASSETS}/tool_banners"
# Footer assets
FOOTER_COST_URL = f"{STATIC_ASSETS}/footer/COST_LOGO_mediumgrey_transparentbackground.png"
FOOTER_EU_URL   = f"{STATIC_ASSETS}/footer/Funded-by-the-European-Union.png"


# ---------- HEADER / BANNER CONFIG ----------
BANNER_HEIGHT_PX = 200  # change to make the banner taller/shorter

# ---------- DB CONNECTION ----------
# Read credentials from environment (see .env / docker-compose.yml)
def _need(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return v

DB_USER = _need("DB_USER")
DB_PASSWORD = _need("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "mysql")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = _need("DB_NAME")

db_url = URL.create(
    drivername="mysql+pymysql",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT) if str(DB_PORT).isdigit() else None,
    database=DB_NAME,
)
engine = create_engine(db_url, pool_pre_ping=True)

# ---------- APP VERSION ----------
def _read_version() -> str:
    # Prefer env injected by Docker build; fallback to VERSION file; finally a dev default
    v = os.getenv("APP_VERSION", "").strip()
    if v:
        return v
    try:
        ver_path = (BASE_DIR / ".." / "VERSION").resolve()
        return ver_path.read_text(encoding="utf-8").strip()
    except Exception:
        return "0.0.0-dev"

def _read_rev() -> str:
    rev = os.getenv("GIT_SHA", "").strip()
    return rev[:7] if rev else ""

APP_VERSION = _read_version()
APP_REV = _read_rev()

# ---------- DATA LOADERS ----------
@st.cache_data(ttl=300)
def load_tools() -> pd.DataFrame:
    """
    Loads the new Tools schema (post Excel import) and provides snake_case aliases
    used by the UI.
    """
    df = pd.read_sql("SELECT * FROM Tools", engine)

    # Normalize to the short names the UI expects
    rename_map = {
        "tool_id": "tool_id",
        "tool_name": "tool_name",
        "customizability": "customizability",
        "integration_capability": "integration",
        "validation_and_reliability": "validation",
        "cost": "cost",
        "maintenance": "maintenance",
        "support": "support",
        "primary_area_scope": "area_scope",
        "primary_area_of_focus": "area_text",
        "link": "link",
        "is_multi_language": "is_multi_language",
        "tool_description": "tool_description",
        "bullet1": "bullet1",
        "bullet2": "bullet2",
        "bullet3": "bullet3",
    }
    present = {k: v for k, v in rename_map.items() if k in df.columns}
    df = df.rename(columns=present)

    # Ensure essentials exist
    for col in ["tool_id", "tool_name", "tool_description", "bullet1", "bullet2", "bullet3"]:
        if col not in df.columns:
            df[col] = ""

    try:
        df["tool_id"] = df["tool_id"].astype(int)
    except Exception:
        pass

    return df


@st.cache_data(ttl=300)
def load_filter_table(table_name: str) -> pd.DataFrame:
    """
    Load any Tool_* mapping table and return (tool_id, label).
    Works with the new normalized tables.
    """
    df = pd.read_sql(f"SELECT * FROM `{table_name}`", engine)

    # find tool_id
    cand_ids = [c for c in df.columns if c.lower().replace(" ", "").replace("_", "") in ("toolid", "toolid", "tool_id")]
    tool_id_col = cand_ids[0] if cand_ids else ("tool_id" if "tool_id" in df.columns else df.columns[0])

    # choose a text column for label
    exclude = set([tool_id_col.lower(), "id", "tool_id", "Tool ID".lower()])
    text_cols = [c for c in df.columns if c.lower() not in exclude and df[c].dtype == object]
    label_col = text_cols[0] if text_cols else [c for c in df.columns if c != tool_id_col][0]

    out = df[[tool_id_col, label_col]].copy()
    out.columns = ["tool_id", "label"]

    try:
        out["tool_id"] = out["tool_id"].astype(int)
    except Exception:
        pass

    out["label"] = out["label"].astype(str).str.strip()
    out = out.dropna(subset=["label"])
    out = out[out["label"] != ""]
    out = out.drop_duplicates()
    return out

@st.cache_data(ttl=300)
def options_from_tools_column(col_name: str) -> list[str]:
    """Return distinct non-empty values from a Tools table column."""
    df = pd.read_sql(f"SELECT DISTINCT `{col_name}` AS val FROM Tools", engine)
    vals = (
        df["val"]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .unique()
        .tolist()
    )
    vals = sorted(vals, key=lambda x: x.lower())
    return vals

@st.cache_data(ttl=300)
def load_area_table() -> pd.DataFrame:
    """
    Return areas as columns: tool_id (Int64), scope (str), name (str).

    Supports two Tool_Area schemas:
      1) New:    tool_id, scope, name
      2) Legacy: tool_id, label  (name only)  → join Tools to get primary_area_scope as scope
    """
    a = pd.read_sql("SELECT * FROM `Tool_Area`", engine)
    cols = {c.lower(): c for c in a.columns}

    if {"tool_id", "scope", "name"}.issubset(cols):
        out = a[[cols["tool_id"], cols["scope"], cols["name"]]].copy()
        out.columns = ["tool_id", "scope", "name"]

    elif "tool_id" in cols and "label" in cols:
        # legacy: use label for name, fetch scope from Tools
        t = pd.read_sql("SELECT tool_id, primary_area_scope FROM `Tools`", engine)
        out = a[[cols["tool_id"], cols["label"]]].copy()
        out.columns = ["tool_id", "name"]
        out = out.merge(t, on="tool_id", how="left").rename(columns={"primary_area_scope": "scope"})

    else:
        # last-resort best effort: try to infer two text columns
        str_cols = [c for c in a.columns if a[c].dtype == object]
        if "tool_id" in a.columns and len(str_cols) >= 2:
            out = a[["tool_id", str_cols[0], str_cols[1]]].copy()
            out.columns = ["tool_id", "scope", "name"]
        else:
            raise ValueError(f"Tool_Area has unsupported columns: {list(a.columns)}")

    # normalize
    out["tool_id"] = pd.to_numeric(out["tool_id"], errors="coerce").astype("Int64")
    out["scope"] = out["scope"].astype(str).str.strip()
    out["name"]  = out["name"].astype(str).str.strip()
    out = out.dropna(subset=["tool_id"])
    out = out[(out["scope"] != "") & (out["name"] != "")]
    out = out.drop_duplicates()
    return out


@st.cache_data(ttl=300)
def load_badge_maps() -> dict[str, dict[int, list[str]]]:
    """
    Return a dict keyed by badge group with {tool_id -> [labels]} maps:
      - sector, tool_type, scale_political, output_type
    """
    maps: dict[str, dict[int, list[str]]] = {}
    def make_map(table: str) -> dict[int, list[str]]:
        df = load_filter_table(table)
        out: dict[int, list[str]] = {}
        for tid, g in df.groupby("tool_id"):
            out[int(tid)] = sorted(g["label"].dropna().unique().tolist(), key=lambda x: x.lower())
        return out
    maps["sector"] = make_map("Tool_SectorFocus")
    maps["tool_type"] = make_map("Tool_ToolType")
    maps["scale_political"] = make_map("Tool_TargetScale_Political")
    maps["output_type"] = make_map("Tool_OutputType")
    maps["user_group"] = make_map("Tool_UserGroup")
    return maps

# Map sidebar sections -> table names (NEW SCHEMA)
# ---------- FILTER SECTIONS (grouped) ----------
# Mapping-table filters (tables that look like: tool_id, label)
MAP_TABLES = {
    "User Group": "Tool_UserGroup",
    "Sector Focus": "Tool_SectorFocus",
    "Tool Type": "Tool_ToolType",
    "Target Scale (Political)": "Tool_TargetScale_Political",
    "Target Scale (Physical)": "Tool_TargetScale_Physical",
    "Temporal Scale": "Tool_TemporalScale",
    "Temporal Resolution": "Tool_TemporalResolution",
    "Methodological Approach": "Tool_MethodologicalApproach",
    "Data Utilization": "Tool_DataUtilization",
    "Output Type": "Tool_OutputType",
    "Accessibility & Usability": "Tool_AccessibilityAndUsability",
    "Languages": "Tool_Language",
    # Geography handled via a special loader (Tool_Area)
    "Maintenance": "Tool_Maintenance",
    "Support": "Tool_Support",
}

# Tools-table (single-value) columns we want to expose as filters
TOOLS_VALUE_COLS = {
    "Customizability": "customizability",
    "Integration Capability": "integration_capability",
    "Validation & Reliability": "validation_and_reliability",
    "Cost": "cost",
    # We’ll also expose Multi-language flag from Tools
    "Multi-language Support": "is_multi_language",  # values like "Yes"/"No"
}

# Sidebar sections and which filters live in each
SECTIONS = {
    "Tool Basics": [
        ("_SEARCH_", None),               # a sentinel for the search box
        ("User Group", MAP_TABLES["User Group"]),
    ],
    "Focus & Applicability": [
        ("Sector Focus", MAP_TABLES["Sector Focus"]),
        ("Tool Type", MAP_TABLES["Tool Type"]),
        ("Target Scale (Political)", MAP_TABLES["Target Scale (Political)"]),
        ("Target Scale (Physical)", MAP_TABLES["Target Scale (Physical)"]),
    ],
    "Technical Specifications": [
        ("Temporal Scale", MAP_TABLES["Temporal Scale"]),
        ("Temporal Resolution", MAP_TABLES["Temporal Resolution"]),
        ("Methodological Approach", MAP_TABLES["Methodological Approach"]),
        ("Data Utilization", MAP_TABLES["Data Utilization"]),
    ],
    "Outputs & User Interaction": [
        ("Output Type", MAP_TABLES["Output Type"]),
        ("Accessibility & Usability", MAP_TABLES["Accessibility & Usability"]),
        ("Multi-language Support", TOOLS_VALUE_COLS["Multi-language Support"]),
        ("Languages", MAP_TABLES["Languages"]),
    ],
    "Customization & Integration": [
        ("Customizability", TOOLS_VALUE_COLS["Customizability"]),
        ("Integration Capability", TOOLS_VALUE_COLS["Integration Capability"]),
    ],
    "Validation & Reliability": [
        ("Validation & Reliability", TOOLS_VALUE_COLS["Validation & Reliability"]),
    ],
    "Cost & Support": [
        ("Cost", TOOLS_VALUE_COLS["Cost"]),
        ("Maintenance", MAP_TABLES["Maintenance"]),
        ("Support", MAP_TABLES["Support"]),
    ],
    "Geography": [
        ("Area Scope", "_AREA_SCOPE_"),   # special (from Tool_Area.scope)
        ("Area (Names)", "_AREA_NAME_"),  # special (from Tool_Area.name)
    ],
}

# # Single-value filter coming directly from Tools (not a link table)
# TOOLS_COLUMN_FILTERS = {
#     "Area Scope": ("area_scope", ["Global", "Continent", "Region", "Country", "Subnational"])
# }


def tool_image_url(tool_id: int) -> str:
    """
    Return a URL for the tool card image. We check the filesystem (public/assets)
    just to decide between a real image and the placeholder.
    """
    if (TOOLS_DIR / f"{tool_id}.png").exists():
        return f"{TOOLS_URL_BASE}/{tool_id}.png"
    return PLACEHOLDER_URL


def tool_banner_url(tool_id: int) -> str:
    """
    Return a URL for the tool's wide banner if it exists; otherwise fall back to card image or placeholder.
    """
    if (BANNERS_DIR / f"{tool_id}.png").exists():
        return f"{TOOL_BANNERS_URL_BASE}/{tool_id}.png"
    return tool_image_url(tool_id)


def header_nav(active: str = "Tools",
               gradient_color: str = "255,255,255",
               left_opacity: float = 0.35,
               right_opacity: float = 0.15,
               show_hero: bool = True):
    """
    Thin white sticky nav + (optional) hero banner below it.
    The hero background is a gradient over the static banner image at /assets/banner.jpg.
    """
    grad = f"linear-gradient(90deg, rgba({gradient_color},{left_opacity}), rgba({gradient_color},{right_opacity}))"
    preload_and_style = (
        f'<link rel="preload" as="image" href="{HERO_BANNER_URL}"/>'
        f"<style>.hero{{"
        f"background-image:{grad}, url('{HERO_BANNER_URL}');"
        f"height:{BANNER_HEIGHT_PX}px; position:relative;"
        f"}}</style>"
    )

    # Brand logo (served by Nginx)
    brand_html = f'<img src="{LOGO_URL}" alt="FutureMed" />'

    def nav_link(href: str, label: str, is_active: bool) -> str:
        cls = 'class="active"' if is_active else ""
        return f'<a href="{href}" {cls}>{label}</a>'

    topbar_html = (
        '<div class="topbar">'
        '  <div class="inner">'
        '    <div class="nav">'
        f"      {nav_link('?page=tools', 'Tools', active=='Tools')}"
        f"      {nav_link('?page=guide', 'Filter Guide', active=='Guide')}"
        f"      {nav_link('?page=suggest', 'Contribute', active=='Suggest')}"
        f"      <a href=\"https://futuremedaction.eu/en/\" target=\"_blank\">FutureMed</a>"
        f"      {nav_link('?page=team', 'Team', active=='Team')}"
        f"      {nav_link('?page=contact', 'Contact', active=='Contact')}"
        '    </div>'
        '  </div>'
        '</div>'
        '<div class="nav-spacer"></div>'
    )

    hero_html = """
    <div class="hero">
      <div class="brand">{brand_html}</div>
    </div>
    """.format(brand_html=brand_html)

    if show_hero:
        st.markdown(preload_and_style + '<div class="site-header">' + topbar_html + hero_html + '</div>', unsafe_allow_html=True)
    else:
        st.markdown(preload_and_style + '<div class="site-header">' + topbar_html + '</div>', unsafe_allow_html=True)

# Floating FAB helper
def render_fab_suggest(show: bool = True):
    if not show:
        return
    st.markdown('<a class="fab-suggest" href="?page=suggest">Suggest a tool!</a>', unsafe_allow_html=True)
@st.cache_data(ttl=300)
def options_for(table_name: str) -> list[str]:
    try:
        df = load_filter_table(table_name)
        opts = sorted(df["label"].dropna().unique().tolist(), key=lambda x: x.lower())
        return opts
    except Exception:
        return []

# Small DDL helper to ensure the Tool_Submissions table exists
def ensure_submissions_table():
    with engine.begin() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS Tool_Submissions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tool_name VARCHAR(255) NOT NULL,
            link TEXT NOT NULL,
            contact_email VARCHAR(255),
            payload JSON
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

def render_footer():
    year = datetime.now().year
    footer_text = (
        "COST (European Cooperation in Science and Technology) is a funding organisation for research and "
        "innovation networks. Our Actions help connect research initiatives across Europe and beyond and enable "
        "researchers and innovators to grow their ideas in any science and technology field by sharing them with "
        "their peers. COST Actions are bottom-up networks with a duration of four years that boost research, "
        "innovation and careers."
    )

    css = """
    .site-footer { margin-top: 48px; }
    .site-footer .footer-top {
      background: #821810; /* Merlot */
      color: #fff;
      padding: 28px 0;
    }
    .site-footer .footer-bottom {
      background: #6d130d;
      color: #fff;
      padding: 10px 0;
    }
    .site-footer .inner {
      max-width: 1250px; margin: 0 auto; padding: 0 28px;
    }
    .site-footer .footer-bottom .inner {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .site-footer .version {
      opacity: 0.75; font-size: 0.85rem;
    }
    .site-footer .row {
      display: grid;
      grid-template-columns: minmax(420px, 1fr) auto; 
      gap: 28px 48px;
      align-items: center;
    }

    .site-footer .foot-left {
      max-width: 920px;           /* prevent sprawling text on ultra-wide screens */
      line-height: 1.35;
      font-size: 0.85rem;
      font-weight: 300;
      color: rgba(255,255,255,0.8);
      text-align: justify;
    }

    .site-footer .foot-right {
      display: flex; align-items: center; justify-content: flex-end;
      gap: 28px; flex-wrap: wrap;
    }

    /* Make logos scale safely without overlapping text */
    .site-footer .foot-logo {
      max-height: 68px;      /* cap height */
      height: auto;          /* keep aspect ratio */
      width: auto;           /* keep aspect ratio */
      object-fit: contain;
      display: block;
    }
    .site-footer .foot-logo.eu { max-height: 64px; }

    .site-footer .copyright { font-size: 0.95rem; opacity: 0.95; }

    /* Stack text ABOVE logos on medium screens */
    @media (max-width: 1200px) {
      .site-footer .row {
        grid-template-columns: 1fr;
        align-items: start;
      }
      .site-footer .foot-right {
        justify-content: flex-start;
      }
    }

    /* Extra tightening on small screens */
    @media (max-width: 760px) {
      .site-footer .footer-top { padding: 22px 0; }
      .site-footer .inner { padding: 0 18px; }
      .site-footer .foot-left { font-size: 0.92rem; }
      .site-footer .foot-logo { max-height: 56px; }
      .site-footer .foot-logo.eu { max-height: 52px; }
      .site-footer .copyright { font-size: 0.9rem; }
    }
    """

    version_str = APP_VERSION + (f" · {APP_REV}" if APP_REV else "")
    html = f"""
    <style>{css}</style>
    <div class="site-footer">
      <div class="footer-top">
        <div class="inner">
          <div class="row">
            <div class="foot-left">
              {footer_text}
            </div>
            <div class="foot-right">
              <img class="foot-logo" src="{FOOTER_COST_URL}" alt="COST logo">
              <img class="foot-logo eu" src="{FOOTER_EU_URL}" alt="Funded by the European Union">
            </div>
          </div>
        </div>
      </div>
      <div class="footer-bottom">
        <div class="inner">
            <span class="copyright">FutureMed © {year}. All Rights Reserved.</span>
            <span class="version">adapt-tools v{version_str}</span>
        </div>
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def suggest_page():
    header_nav(active="Suggest")
    st.title("Suggest a CCA Tool")
    st.caption("Submitted tools are **reviewed by moderators** before appearing in the catalog. Fields with * are required.")

    # Preload options from mapping tables
    user_groups = options_for("Tool_UserGroup")
    sectors = options_for("Tool_SectorFocus")
    tool_types = options_for("Tool_ToolType")
    scale_pol = options_for("Tool_TargetScale_Political")
    scale_phy = options_for("Tool_TargetScale_Physical")
    temporal_scales = options_for("Tool_TemporalScale")
    temporal_res = options_for("Tool_TemporalResolution")
    methods = options_for("Tool_MethodologicalApproach")
    data_util = options_for("Tool_DataUtilization")
    outputs = options_for("Tool_OutputType")
    access = options_for("Tool_AccessibilityAndUsability")
    languages = options_for("Tool_Language")
    maintenance_opts = options_for("Tool_Maintenance")
    support_opts = options_for("Tool_Support")

    # single-value columns from Tools (use existing distincts)
    customizability_opts = options_from_tools_column("customizability")
    integration_opts = options_from_tools_column("integration_capability")
    validation_opts = options_from_tools_column("validation_and_reliability")
    cost_opts = options_from_tools_column("cost")

    area_scopes = ["Global", "Continent", "Region", "Country", "Subnational"]
    try:
        area_names = sorted(load_area_table()["name"].dropna().unique().tolist(), key=lambda x: x.lower())
    except Exception:
        area_names = []

    def with_other(opts: list[str]) -> list[str]:
        out = [o for o in (opts or []) if isinstance(o, str) and o.strip()]
        if "Other" not in out:
            out.append("Other")
        return out

    user_groups = with_other(user_groups)
    sectors = with_other(sectors)
    tool_types = with_other(tool_types)
    scale_pol = with_other(scale_pol)
    scale_phy = with_other(scale_phy)
    temporal_scales = with_other(temporal_scales)
    temporal_res = with_other(temporal_res)
    methods = with_other(methods)
    data_util = with_other(data_util)
    outputs = with_other(outputs)
    access = with_other(access)
    languages = with_other(languages)
    maintenance_opts = with_other(maintenance_opts)
    support_opts = with_other(support_opts)
    customizability_opts = with_other(customizability_opts)
    integration_opts = with_other(integration_opts)
    validation_opts = with_other(validation_opts)
    cost_opts = with_other(cost_opts)

    with st.form("tool_suggestion_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            tool_name = st.text_input("Tool name *")
            link = st.text_input("Tool URL *", placeholder="https://…")

            st.markdown("**Tool Basics**")
            ug = st.multiselect("User group(s)", options=user_groups)

            st.markdown("**Focus & Applicability**")
            sec = st.multiselect("Sector focus", options=sectors)
            ttype = st.multiselect("Tool type", options=tool_types)
            tscale_pol = st.multiselect("Target scale (political)", options=scale_pol)
            tscale_phy = st.multiselect("Target scale (physical)", options=scale_phy)

            st.markdown("**Technical specifications**")
            tscale = st.multiselect("Temporal scale", options=temporal_scales)
            tres = st.multiselect("Temporal resolution", options=temporal_res)
            meth = st.multiselect("Methodological approach", options=methods)
            dutil = st.multiselect("Data utilization", options=data_util)

        with col2:
            st.markdown("**Outputs & User Interaction**")
            out = st.multiselect("Output type", options=outputs)
            acc = st.selectbox("Accessibility & usability", options=[""] + access, index=0)
            is_multi = st.selectbox("Multi-language support?", options=["", "Yes", "No"], index=0)
            langs = st.multiselect("Languages (if applicable)", options=languages)

            st.markdown("**Customization & Integration**")
            cust = st.selectbox("Customizability", options=[""] + customizability_opts, index=0)
            integ = st.selectbox("Integration capability", options=[""] + integration_opts, index=0)

            st.markdown("**Validation & Reliability**")
            valid = st.selectbox("Validation & reliability", options=[""] + validation_opts, index=0)

            st.markdown("**Cost & Support**")
            cost = st.selectbox("Cost", options=[""] + cost_opts, index=0)
            maint = st.multiselect("Maintenance", options=maintenance_opts)
            supp = st.multiselect("Support", options=support_opts)

            st.markdown("**Geography**")
            scope = st.selectbox("Primary area scope", options=[""] + area_scopes, index=0)
            areas = st.multiselect("Primary area(s)", options=area_names, help="Start typing to search. You can also leave this blank and describe below.")
        
        desc = st.text_area("Short description / notes for moderators (optional)", height=110)

        st.markdown("**Verification**")
        human_check = st.checkbox("I'm not a robot (temporary)")

        submitted = st.form_submit_button("Submit suggestion")

    if submitted:
        errs = []
        if not tool_name.strip():
            errs.append("Tool name is required.")
        if not link.strip():
            errs.append("Tool URL is required.")
        if not human_check:
            errs.append("Please confirm you're not a robot.")
        if errs:
            for e in errs: st.error(e)
            return

        ensure_submissions_table()

        # assemble payload
        payload = {
            "tool_name": tool_name.strip(),
            "link": link.strip(),
            "user_groups": ug,
            "sectors": sec,
            "tool_types": ttype,
            "target_scale_political": tscale_pol,
            "target_scale_physical": tscale_phy,
            "temporal_scale": tscale,
            "temporal_resolution": tres,
            "methodological_approach": meth,
            "data_utilization": dutil,
            "output_type": out,
            "accessibility_and_usability": acc,
            "is_multi_language": is_multi,
            "languages": langs,
            "customizability": cust,
            "integration_capability": integ,
            "validation_and_reliability": valid,
            "cost": cost,
            "maintenance": maint,
            "support": supp,
            "primary_area_scope": scope,
            "primary_area_of_focus": areas,
            "notes": desc.strip(),
        }

        try:
            import json
            with engine.begin() as conn:
                conn.execute(
                    "INSERT INTO Tool_Submissions (tool_name, link, payload) VALUES (%s, %s, CAST(%s AS JSON))",
                    (tool_name.strip(), link.strip(), json.dumps(payload))
                )
            st.success("Thank you! Your suggestion was submitted and will be reviewed by moderators.")
            st.info("You can close this page or suggest another tool.")
        except Exception as e:
            st.error(f"Could not save your submission: {e}")

    render_footer()


def sidebar_filters(tools_df: pd.DataFrame):
    """
    Render grouped sidebar sections.
    Returns:
      selections: dict of chosen options by logical key
      tables: mapping table dataframes (for apply_filters)
      search_q: text
      geo: dict with 'scopes' and 'areas' (sets)
    """
    selections: dict[str, set] = {}
    tables: dict[str, pd.DataFrame] = {}
    search_q = ""
    geo_scopes: set[str] = set()
    geo_areas: set[str] = set()


    st.sidebar.header("Tool Basics")
    st.sidebar.markdown('New here? See the **[Filter Guide](?page=guide)** for explanations.', unsafe_allow_html=True)

    for section, items in SECTIONS.items():
        if section != "Tool Basics":
            st.sidebar.markdown("<hr>", unsafe_allow_html=True)   # ← add this line
            st.sidebar.markdown(f"### {section}")

        for label, ref in items:
            # 1) Search box
            if label == "_SEARCH_":
                search_q = st.sidebar.text_input("Search tool", "", key="flt_search", help="Find tools by name. Use the filters below to refine results.")
                continue

            # Area Scope
            if ref == "_AREA_SCOPE_":
                try:
                    area_df = load_area_table()
                    scopes = sorted(area_df["scope"].dropna().unique().tolist(), key=lambda x: x.lower())
                    chosen = st.sidebar.multiselect("Area Scope", options=scopes, default=[], key="flt_area_scope", help=HELP_TEXTS.get("Area Scope"))
                    geo_scopes = set(chosen)
                except Exception as e:
                    st.sidebar.warning(f"Area Scope: {e}")
                continue

            # Area (Names) – cascaded by selected scopes
            if ref == "_AREA_NAME_":
                try:
                    area_df = load_area_table()
                    if geo_scopes:
                        area_df = area_df[area_df["scope"].isin(geo_scopes)]
                    names = sorted(area_df["name"].dropna().unique().tolist(), key=lambda x: x.lower())
                    chosen = st.sidebar.multiselect("Area (Names)", options=names, default=[], key="flt_area_names", help=HELP_TEXTS.get("Area (Names)"))
                    geo_areas = set(chosen)
                except Exception as e:
                    st.sidebar.warning(f"Area (Names): {e}")
                continue

            # 3) Tools-table single-value columns
            if isinstance(ref, str) and ref in TOOLS_VALUE_COLS.values():
                try:
                    col = ref
                    opts = options_from_tools_column(col)
                    # For Multi-language Support, show simple choices if present (Yes/No)
                    # Use explicit key for widget
                    key = f"flt_{_slug(label)}"
                    chosen = st.sidebar.multiselect(label, options=opts, default=[], key=key, help=HELP_TEXTS.get(label))
                    selections[label] = set(chosen)
                except Exception as e:
                    st.sidebar.warning(f"{label}: {e}")
                    selections[label] = set()
                continue

            # 4) Mapping-table filters (Tool_*)
            try:
                tbl = ref if isinstance(ref, str) else None
                df = load_filter_table(tbl)
                tables[label] = df
                options = sorted(df["label"].dropna().unique().tolist())
                key = f"flt_{_slug(label)}"
                chosen = st.sidebar.multiselect(label, options=options, default=[], key=key, help=HELP_TEXTS.get(label))
                selections[label] = set(chosen)
            except Exception as e:
                st.sidebar.warning(f"{label}: {e}")
                selections[label] = set()
                tables[label] = pd.DataFrame(columns=["tool_id", "label"])


    # ---- Clear-all must run after all widgets instantiate ----
    clear_clicked = st.sidebar.button("Clear all filters", key="btn_clear_all")
    if clear_clicked:
        # remove our filter-related widget state keys BEFORE widgets are created
        for k in list(st.session_state.keys()):
            if k.startswith("flt_"):
                st.session_state.pop(k, None)
        # force a fresh run where widgets will be built with empty state
        st.rerun()

    geo = {"scopes": geo_scopes, "areas": geo_areas}
    return selections, tables, search_q, geo

def apply_filters(tools_df: pd.DataFrame, selections: dict, tables: dict, search_q: str, geo: dict) -> pd.DataFrame:
    """
    Intersect tool_ids across:
      - mapping-table selections (Tool_* tables via `tables`)
      - Tools-table single-value filters (TOOLS_VALUE_COLS)
      - Geography (Tool_Area with scope/name)
      - Free-text search (tool_name)
    """
    current_ids = set(tools_df["tool_id"].dropna().astype(int).tolist())

    # 1) Mapping-table filters
    for label, df_map in tables.items():
        chosen = selections.get(label, set())
        if not chosen:
            continue
        if df_map is None or df_map.empty:
            current_ids = set()
            break
        keep = set(df_map[df_map["label"].isin(chosen)]["tool_id"].astype(int).tolist())
        current_ids &= keep

    # 2) Tools-table single-value filters
    col_by_label = {lbl: col for lbl, col in TOOLS_VALUE_COLS.items()}
    for label, chosen in selections.items():
        if label not in col_by_label:
            continue
        if not chosen:
            continue
        col = col_by_label[label]
        # accept multiple selected values
        subset = tools_df[tools_df[col].astype(str).isin(chosen)]
        keep = set(subset["tool_id"].astype(int).tolist())
        current_ids &= keep

    # 3) Geography
    scopes = geo.get("scopes", set())
    areas  = geo.get("areas", set())
    if scopes or areas:
        a = load_area_table()
        if scopes:
            a = a[a["scope"].isin(scopes)]
        if areas:
            a = a[a["name"].isin(areas)]
        keep = set(a["tool_id"].dropna().astype(int).tolist())
        current_ids &= keep

    # 4) Text search (tool name only to keep it precise)
    out = tools_df[tools_df["tool_id"].isin(current_ids)].copy()
    if search_q:
        q = search_q.strip().lower()
        # search in name + description + bullets
        cols = ["tool_name", "tool_description", "bullet1", "bullet2", "bullet3"]
        for c in cols:
            if c not in out.columns:
                out[c] = ""  # safety
        mask = (
            out["tool_name"].astype(str).str.lower().str.contains(q, na=False) |
            out["tool_description"].astype(str).str.lower().str.contains(q, na=False) |
            out["bullet1"].astype(str).str.lower().str.contains(q, na=False) |
            out["bullet2"].astype(str).str.lower().str.contains(q, na=False) |
            out["bullet3"].astype(str).str.lower().str.contains(q, na=False)
        )
        out = out[mask]

    out = out.sort_values(by=["tool_name"], na_position="last")
    return out


def tool_card(tool: pd.Series, badges: dict[str, dict[int, list[str]]]):
    # img_path = tool_image_path(tool["tool_id"])
    # if not img_path or not Path(img_path).exists():
    #     img_path = PLACEHOLDER_PATH

    # with open(img_path, "rb") as f:
    #     img_base64 = base64.b64encode(f.read()).decode()
    img_url = tool_image_url(int(tool["tool_id"]))

    tid = int(tool["tool_id"])
    # Collect minimal labels for the colored pills (cap to 2 each for compactness)
    sector_vals = badges["sector"].get(tid, [])[:3]
    type_vals = badges["tool_type"].get(tid, [])[:3]
    scale_vals = badges["scale_political"].get(tid, [])[:3]
    output_vals = badges["output_type"].get(tid, [])[:3]
    cost_val = str(tool.get("cost", "") or "").strip()

    pills_html = ""
    pills_html += "".join(f'<span class="pill pill--sector">{p}</span>' for p in sector_vals)
    pills_html += "".join(f'<span class="pill pill--type">{p}</span>' for p in type_vals)
    pills_html += "".join(f'<span class="pill pill--scale">{p}</span>' for p in scale_vals)
    pills_html += "".join(f'<span class="pill pill--output">{p}</span>' for p in output_vals)
    if cost_val:
        pills_html += f'<span class="pill pill--cost">{cost_val}</span>'

    st.markdown(
        f"""
        <a class="tool-card-link" href="?page=tool&id={tool['tool_id']}" style="display:block; text-decoration:none; color:inherit;">
          <div class="tool-card">
              <img class="tool-image" src="{img_url}" loading="lazy" decoding="async">
              <div class="tool-body">
                <div class="tool-title-wrap">
                  <div class="tool-title">{tool.get("tool_name","(No name)")}</div>
                </div>
                <div>{pills_html}</div>
              </div>
          </div>
        </a>
        """,
        unsafe_allow_html=True
    )

def list_tools_page():
    header_nav(active="Tools")
    render_fab_suggest(True)
    tools = load_tools()

    selections, tables, search_q, geo = sidebar_filters(tools)

    st.title("Climate Change Adaptation Tools Catalog")
    st.write("Use the filters on the left to explore the catalog.")

    filtered = apply_filters(tools, selections, tables, search_q, geo)
    st.caption(f"{len(filtered)} result(s)")

    badges = load_badge_maps()
    cards_html = "".join(tool_card_html(row, badges) for _, row in filtered.iterrows())
    cards_html = cards_html.replace("\n", "")
    st.markdown(f'<div class="card-grid">{cards_html}</div>', unsafe_allow_html=True)

    st.markdown("")  # tiny spacer if you want
    render_footer()


def team_page():
    header_nav(active="Team")
    render_fab_suggest(True)
    st.title("Team")
    st.image(HERO_BANNER_URL, use_container_width=True)
    st.markdown(
        """
        This is a placeholder Team page.  
        We can list coordinators, contributors, and link to their affiliations here.
        """
    )
    render_footer()



def contact_page():
    header_nav(active="Contact")
    render_fab_suggest(True)
    st.title("Contact")
    st.image(HERO_BANNER_URL, use_container_width=True)
    st.markdown(
        """
        **Get in touch**  
        - Email: info@futuremedaction.eu  
        - Web: https://futuremedaction.eu/en/  
        """
    )

    render_footer()


# ---------- GUIDE PAGE ----------
def guide_page():
    header_nav(active="Guide")
    render_fab_suggest(True)
    st.title("Filter Guide")
    st.caption("What each filter means and the choices available. Use this page as a reference while filtering.")

    sections = [
        ("Tool Basics", ["User Group"]),
        ("Focus & Applicability", ["Sector Focus", "Tool Type", "Target Scale (Political)", "Target Scale (Physical)"]),
        ("Technical Specifications", ["Temporal Scale", "Temporal Resolution", "Methodological Approach", "Data Utilization"]),
        ("Outputs & User Interaction", ["Output Type", "Accessibility & Usability", "Multi-language Support", "Languages"]),
        ("Customization & Integration", ["Customizability", "Integration Capability"]),
        ("Validation & Reliability", ["Validation & Reliability"]),
        ("Cost & Support", ["Cost", "Maintenance", "Support"]),
        ("Geography", ["Area Scope", "Area (Names)"]),
    ]

    for title, keys in sections:
        st.subheader(title)
        for k in keys:
            st.markdown(f"### {k}")
            if k in HELP_TEXTS:
                st.markdown(f"<div class='muted'>{HELP_TEXTS[k]}</div>", unsafe_allow_html=True)

            details = FILTER_DETAILS.get(k, [])
            if details:
                # bullet list with name — description
                items = "\n".join([f"- **{name}** — {desc}" if desc else f"- **{name}**" for name, desc in details])
                st.markdown(items)
            elif k == "Languages":
                st.markdown("- **Languages** — Interface or documentation languages provided by the tool.")
            elif k == "Area (Names)":
                st.markdown("- **Examples** — Europe, Italy, California, Danube Basin, Alps, Mediterranean.")

        st.markdown("---")

    st.markdown(
        """
        **Tips**
        - Start broad (e.g., pick a *Sector* and a *Tool Type*), then narrow with *Scale* and *Temporal* filters.
        - Use *Area Scope* first; it will narrow options shown in *Area (Names).* 
        - Selecting multiple values within a single filter acts as **OR**; across different filters acts as **AND**.
        - Combine *Output Type* and *Accessibility* to quickly find tools that match the way you prefer to work.
        """
    )

    render_footer()



def tool_detail_page(tool_id: int):
    tools = load_tools()
    try:
        tool_id = int(tool_id)
    except Exception:
        tool_id = None

    row = tools[tools["tool_id"] == tool_id].iloc[0] if tool_id in tools["tool_id"].values else None

    header_nav(active="Tools", show_hero=False)
    render_fab_suggest(True)

    # Tighten top spacing since we hide the hero image on detail pages
    st.markdown("<style>.block-container{padding-top:2rem !important;}</style>", unsafe_allow_html=True)

    if row is None:
        st.error("Tool not found.")
        st.markdown('<div class="back-link">↩︎ <a href="?page=tools">Back to all tools</a></div>', unsafe_allow_html=True)
        return

    # Title and banner image (wide)
    st.title(str(row.get("tool_name", "Tool")))
    # TODO: Tool banner temporarily disabled — uncomment after banner images are fixed.
    # st.markdown(f"<img class='tool-hero-banner' src='{tool_banner_url(int(row['tool_id']))}' loading='lazy' decoding='async'>", unsafe_allow_html=True)

    # Build right-side badge pills from mapping tables (same scheme as cards)
    badges = load_badge_maps()
    tid = int(row["tool_id"])
    sector_vals = badges["sector"].get(tid, [])
    type_vals   = badges["tool_type"].get(tid, [])
    scale_vals  = badges["scale_political"].get(tid, [])
    output_vals = badges["output_type"].get(tid, [])
    user_vals  = badges.get("user_group", {}).get(tid, [])

    def pills_html(values, css):
        return "".join(f"<span class='pill {css}'>{escape(str(v))}</span>" for v in values)

    def group_block(title, values, css):
        if not values:
            return ""
        pills = pills_html(values, css)
        return f"<div class='glance-group'><h5>{escape(title)}</h5><div class='pill-stack'>{pills}</div></div>"

    right_panel = (
        "<div class='tool-detail-right'>"
        "<h4>At a glance</h4>"
        f"{group_block('Sector', sector_vals, 'pill--sector')}"
        f"{group_block('User Group', user_vals, 'pill--type')}"
        f"{group_block('Output Type', output_vals, 'pill--output')}"
        f"{group_block('Target Scale (Political)', scale_vals, 'pill--scale')}"
        "</div>"
    )

    # Build Highlights HTML (inline, below the Overview)
    b1 = (row.get("bullet1") or "").strip()
    b2 = (row.get("bullet2") or "").strip()
    b3 = (row.get("bullet3") or "").strip()
    highlights_html = ""
    if any([b1, b2, b3]):
        items = "".join([f"<li>{escape(b)}</li>" for b in [b1, b2, b3] if b])
        highlights_html = f"<div class='tool-highlights'><h3>Highlights</h3><ul>{items}</ul></div>"

    # Split layout: description on the left, pills on the right
    desc = (row.get("tool_description") or "").strip()
    if desc:
        left_html = f"<div class='tool-detail-left'><h3>Overview</h3><p>{escape(desc)}</p>{highlights_html}</div>"
    else:
        left_html = f"<div class='tool-detail-left'>{highlights_html}</div>" if highlights_html else ""
    st.markdown(
        f"<div class='tool-detail-split'>{left_html}{right_panel}</div>",
        unsafe_allow_html=True,
    )

    # --- Meta details after Highlights (render as HTML with <strong>, escape values)
    meta_bits: list[str] = []
    if type_vals:
        meta_bits.append(f"<strong>Tool Type:</strong> {escape(', '.join(map(str, type_vals)))}")

    val = str(row.get('cost', '') or '').strip()
    if val:
        meta_bits.append(f"<strong>Cost:</strong> {escape(val)}")

    val = str(row.get('validation', '') or '').strip()
    if val:
        meta_bits.append(f"<strong>Validation:</strong> {escape(val)}")

    val = str(row.get('maintenance', '') or '').strip()
    if val:
        meta_bits.append(f"<strong>Maintenance:</strong> {escape(val)}")

    val = str(row.get('support', '') or '').strip()
    if val:
        meta_bits.append(f"<strong>Support:</strong> {escape(val)}")

    val = str(row.get('area_scope', '') or '').strip()
    if val:
        meta_bits.append(f"<strong>Area scope:</strong> {escape(val)}")

    if meta_bits:
        st.markdown(f"<div class='meta-details'>{' • '.join(meta_bits)}</div>", unsafe_allow_html=True)

    # --- Wide merlot button to the tool site
    link = str(row.get("link", "") or "").strip()
    if link:
        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
        st.markdown(
            f"<a class='brand-btn brand-btn--wide' href='{escape(link)}' target='_blank' rel='noopener'>Open the tool ↗</a>",
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown('<div class="back-link">↩︎ <a href="?page=tools">Back to all tools</a></div>', unsafe_allow_html=True)

    render_footer()


def main():
    qp = st.query_params
    page = (qp.get("page")[0] if isinstance(qp.get("page"), list) else qp.get("page")) if qp.get("page") else "tools"

    if page == "tool":
        tool_id = qp.get("id")
        tool_id = tool_id[0] if isinstance(tool_id, list) else tool_id
        tool_detail_page(tool_id)
    elif page == "team":
        team_page()
    elif page == "contact":
        contact_page()
    elif page == "suggest":
        suggest_page()
    elif page == "guide":
        guide_page()
    else:
        list_tools_page()


if __name__ == "__main__":
    main()
