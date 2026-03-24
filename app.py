import streamlit as st
import pandas as pd
from datetime import date, timedelta
import calendar
import base64
from pathlib import Path
import json
import re

import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="Ermon. | Ads Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
SHEET_ID = "1l_fX5ydioIsKVyhitrnR3rcdf6RyZOq-x6oQ3mhP9uQ"
SCOPES   = ["https://www.googleapis.com/auth/spreadsheets"]

# ── AUTH ──────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_gsheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    return gspread.authorize(creds).open_by_key(SHEET_ID)

def load_clients():
    try:
        ws   = get_gsheet().worksheet("klienci")
        data = ws.get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame(
            columns=["nazwa","google_ads_id","meta_ads_id","typ_kwoty","mcc_id"]
        )
    except Exception as e:
        st.error(f"Błąd odczytu klientów: {e}")
        return pd.DataFrame(columns=["nazwa","google_ads_id","meta_ads_id","typ_kwoty","mcc_id"])

def get_logo_base64():
    logo_path = Path(__file__).parent / "logo.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

LOGO_B64 = get_logo_base64()

# ── DESIGN SYSTEM ─────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap');

:root {{
  --violet:  #2c016d;
  --coral:   #ff466b;
  --blue:    #3337bd;
  --bg:      #0c0c18;
  --surface: #13132a;
  --surface2:#1a1a35;
  --border:  #2a2a50;
  --text:    #e8e8f5;
  --muted:   #6060a0;
  --white:   #ffffff;
  --green:   #00e5a0;
  --yellow:  #ffb800;
  --red:     #ff466b;
}}

html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg);
    color: var(--text);
}}

section[data-testid="stSidebar"] {{
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}}
.sidebar-logo {{
    padding: 2rem 1.5rem 1.5rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 0.5rem;
}}
.sidebar-logo img {{ width: 110px; filter: brightness(0) invert(1); }}
.sidebar-tagline {{
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    color: var(--muted);
    text-transform: uppercase;
    margin-top: 8px;
}}

.main .block-container {{ padding: 2.5rem 3rem; max-width: 1700px; }}

.page-title {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3.5rem;
    color: var(--white);
    letter-spacing: 0.05em;
    line-height: 1;
    margin-bottom: 0.1rem;
}}
.page-subtitle {{
    font-size: 0.75rem;
    color: var(--muted);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 2.5rem;
}}
.section-hdr {{
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--muted);
    letter-spacing: 0.18em;
    text-transform: uppercase;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.6rem;
    margin: 2.5rem 0 1.5rem;
}}

.kpi {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1rem;
}}
.kpi-label {{ font-size: 0.65rem; color: var(--muted); text-transform: uppercase; }}
.kpi-value {{ font-family: 'Bebas Neue', sans-serif; font-size: 2rem; color: var(--white); }}
.kpi-accent {{ color: var(--coral); }}

.badge {{ display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.7rem; font-weight: 600; }}
.badge-red    {{ background: rgba(255,70,107,0.15); color: #ff466b; }}
.badge-yellow {{ background: rgba(255,184,0,0.15);  color: #ffb800; }}
.badge-green  {{ background: rgba(0,229,160,0.15);  color: #00e5a0; }}

.rec-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.8rem;
    border-left: 3px solid var(--coral);
}}
.rec-card.ok   {{ border-left-color: #00e5a0; }}
.rec-card.warn {{ border-left-color: #ffb800; }}
.rec-card.crit {{ border-left-color: #ff466b; }}
.rec-title {{ font-weight: 600; color: var(--white); }}
.rec-body {{ font-size: 0.85rem; color: #a0a0c0; }}
.rec-action {{ margin-top: 0.6rem; color: #8090ff; font-size: 0.75rem; }}

.stButton > button {{
    background: linear-gradient(135deg, var(--violet), var(--blue)) !important;
    color: white !important;
    border-radius: 8px !important;
}}

.analyze-box {{
    background: linear-gradient(135deg, rgba(44,1,109,0.3), rgba(51,55,189,0.2));
    border: 1px solid rgba(51,55,189,0.4);
    border-radius: 16px;
    padding: 2rem;
    text-align: center;
    margin: 2rem 0;
}}
</style>

<div class="sidebar-logo">
    {"<img src='data:image/png;base64," + LOGO_B64 + "' />" if LOGO_B64 else "<span style='font-family:Bebas Neue,sans-serif;font-size:1.8rem;color:#fff;letter-spacing:0.05em;'>Ermon.</span>"}
    <div class="sidebar-tagline">Ads Analyzer</div>
</div>
""", unsafe_allow_html=True)

# ── AUDIT LOGIC (Musi być na wierzchu) ────────────────────────────────────────
def run_local_audit(data):
    """Analizuje dane lokalnie i zwraca słownik z rekomendacjami."""
    recommendations = {
        "podsumowanie": "Automatyczny audyt techniczny wykonany na podstawie twardych danych z konta.",
        "ocena_ogolna": "dobra",
        "problemy_krytyczne": [],
        "slowa_do_wykluczenia": [],
        "rekomendacje_reklam": [],
        "nastepne_kroki": ["Sprawdź listę wykluczeń", "Skoryguj stawki w najdroższych kampaniach"]
    }

    # 1. Analiza kampanii
    for c in data.get("campaigns", []):
        if c['cost'] > 100 and c['conversions'] == 0:
            recommendations["problemy_krytyczne"].append({
                "tytul": f"Przepalanie budżetu: {c['name']}",
                "opis": f"Kampania wydała {c['cost']} PLN i nie przyniosła żadnej konwersji.",
                "akcja": "Zmniejsz budżet dzienny lub sprawdź stronę docelową.",
                "priorytet": "wysoki"
            })
            recommendations["ocena_ogolna"] = "zła"

    # 2. Analiza Search Terms
    for t in data.get("search_terms", []):
        if t['cost'] > 20 and t['conversions'] == 0:
            recommendations["slowa_do_wykluczenia"].append(t['term'])

    # 3. Analiza Quality Score
    for k in data.get("keywords", []):
        if k.get('qs') and k['qs'] < 4:
            recommendations["problemy_krytyczne"].append({
                "tytul": f"Niska jakość: {k['keyword']}",
                "opis": f"Wynik jakości (QS) wynosi tylko {k['qs']}/10.",
                "akcja": "Dopasuj treść reklamy do tego słowa.",
                "priorytet": "średni"
            })

    # 4. Słaby CTR
    for a in data.get("ads", []):
        if a['impressions'] > 500 and a['ctr'] < 1.0:
            recommendations["rekomendacje_reklam"].append({
                "problem": f"Niski CTR ({a['ctr']}%) w grupie {a['ad_group']}",
                "akcja": "Napisz nowe nagłówki."
            })

    return recommendations

# ── HELPERS ───────────────────────────────────────────────────────────────────
def kpi_card(label, value, sub="", accent=False):
    vc = "kpi-value kpi-accent" if accent else "kpi-value"
    sh = f'<div class="kpi-sub" style="font-size:0.7rem;color:var(--muted);">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="kpi"><div class="kpi-label">{label}</div>'
        f'<div class="{vc}">{value}</div>{sh}</div>',
        unsafe_allow_html=True
    )

def page_header(title, subtitle=""):
    st.markdown(f'<div class="page-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)

def section(title):
    st.markdown(f'<div class="section-hdr">{title}</div>', unsafe_allow_html=True)

# ── GOOGLE ADS DATA FETCHER ───────────────────────────────────────────────────
def get_ga_client(customer_id, mcc_id=""):
    from google.ads.googleads.client import GoogleAdsClient
    config = {
        "developer_token": st.secrets["google_ads"]["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id":       st.secrets["google_ads"]["GOOGLE_ADS_CLIENT_ID"],
        "client_secret":   st.secrets["google_ads"]["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token":   st.secrets["google_ads"]["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus":  True,
    }
    if mcc_id:
        config["login_customer_id"] = mcc_id.replace("-", "")
    return GoogleAdsClient.load_from_dict(config)

def fetch_campaigns(ga_client, customer_id, date_from, date_to):
    svc = ga_client.get_service("GoogleAdsService")
    cid = customer_id.replace("-", "")
    query = f"SELECT campaign.id, campaign.name, campaign.status, campaign.advertising_channel_type, campaign.bidding_strategy_type, metrics.clicks, metrics.impressions, metrics.ctr, metrics.cost_micros, metrics.conversions, metrics.conversions_value, metrics.cost_per_conversion FROM campaign WHERE segments.date BETWEEN '{date_from}' AND '{date_to}' AND campaign.status != 'REMOVED'"
    rows = []
    try:
        resp = svc.search_stream(customer_id=cid, query=query)
        for batch in resp:
            for row in batch.results:
                m = row.metrics
                rows.append({
                    "name": row.campaign.name,
                    "cost": round(m.cost_micros / 1e6, 2),
                    "clicks": m.clicks,
                    "conversions": round(m.conversions, 1),
                    "ctr": round(m.ctr * 100, 2)
                })
    except Exception as e: st.warning(f"Błąd kampanii: {e}")
    return rows

def fetch_keywords(ga_client, customer_id, date_from, date_to):
    svc = ga_client.get_service("GoogleAdsService")
    query = f"SELECT ad_group_criterion.keyword.text, ad_group_criterion.quality_info.quality_score, metrics.cost_micros, metrics.conversions FROM keyword_view WHERE segments.date BETWEEN '{date_from}' AND '{date_to}' LIMIT 100"
    rows = []
    try:
        resp = svc.search_stream(customer_id=customer_id.replace("-",""), query=query)
        for batch in resp:
            for row in batch.results:
                rows.append({
                    "keyword": row.ad_group_criterion.keyword.text,
                    "qs": row.ad_group_criterion.quality_info.quality_score,
                    "cost": round(row.metrics.cost_micros / 1e6, 2),
                    "conversions": row.metrics.conversions
                })
    except: pass
    return rows

def fetch_search_terms(ga_client, customer_id, date_from, date_to):
    svc = ga_client.get_service("GoogleAdsService")
    query = f"SELECT search_term_view.search_term, metrics.cost_micros, metrics.conversions FROM search_term_view WHERE segments.date BETWEEN '{date_from}' AND '{date_to}' AND metrics.impressions > 3"
    rows = []
    try:
        resp = svc.search_stream(customer_id=customer_id.replace("-",""), query=query)
        for batch in resp:
            for row in batch.results:
                rows.append({
                    "term": row.search_term_view.search_term,
                    "cost": round(row.metrics.cost_micros / 1e6, 2),
                    "conversions": row.metrics.conversions
                })
    except: pass
    return rows

def fetch_ads(ga_client, customer_id, date_from, date_to):
    svc = ga_client.get_service("GoogleAdsService")
    query = f"SELECT ad_group.name, metrics.impressions, metrics.ctr FROM ad_group_ad WHERE segments.date BETWEEN '{date_from}' AND '{date_to}' LIMIT 50"
    rows = []
    try:
        resp = svc.search_stream(customer_id=customer_id.replace("-",""), query=query)
        for batch in resp:
            for row in batch.results:
                rows.append({
                    "ad_group": row.ad_group.name,
                    "impressions": row.metrics.impressions,
                    "ctr": round(row.metrics.ctr * 100, 2)
                })
    except: pass
    return rows

# ── RENDER ANALYSIS ───────────────────────────────────────────────────────────
def render_analysis(analysis: dict):
    if not analysis: return
    ocena = analysis.get("ocena_ogolna", "średnia")
    badge_color = {"dobra": "green", "średnia": "yellow", "zła": "red"}.get(ocena, "yellow")
    
    st.markdown(f"""
    <div style="background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:1.5rem;margin-bottom:1.5rem;">
        <span class="badge badge-{badge_color}">OCENA: {ocena.upper()}</span>
        <div style="margin-top:0.8rem; color:#a0a0c0;">{analysis.get("podsumowanie","")}</div>
    </div>
    """, unsafe_allow_html=True)

    # Problemy
    for p in analysis.get("problemy_krytyczne", []):
        st.markdown(f"""
        <div class="rec-card crit">
            <div class="rec-title">{p.get("tytul")}</div>
            <div class="rec-body">{p.get("opis")}</div>
            <div class="rec-action">AKCJA: {p.get("akcja")}</div>
        </div>
        """, unsafe_allow_html=True)

    # Wykluczenia
    if analysis.get("slowa_do_wykluczenia"):
        section("Słowa do wykluczenia")
        st.write(", ".join(analysis["slowa_do_wykluczenia"]))

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
clients_df = load_clients()
with st.sidebar:
    st.markdown("---")
    if clients_df.empty: st.stop()
    ga_clients = clients_df[clients_df["google_ads_id"].notna()]
    sel_client = st.selectbox("Klient", ga_clients["nazwa"].tolist())
    date_from = st.date_input("Od", value=date.today() - timedelta(days=30))
    date_to = st.date_input("Do", value=date.today())
    run_analysis = st.button("🔍 Analizuj kampanie", use_container_width=True, type="primary")

# ── MAIN ──────────────────────────────────────────────────────────────────────
page_header("Ads Analyzer")

if not run_analysis:
    st.info("Wybierz klienta i kliknij przycisk analizy w menu bocznym.")
    st.stop()

# ── RUN ───────────────────────────────────────────────────────────────────────
client_row = ga_clients[ga_clients["nazwa"] == sel_client].iloc[0]
g_id = str(client_row["google_ads_id"]).strip()
mcc_id = str(client_row.get("mcc_id", "")).strip()

with st.status("Pracuję...", expanded=True) as status:
    ga_client = get_ga_client(g_id, mcc_id)
    campaigns = fetch_campaigns(ga_client, g_id, str(date_from), str(date_to))
    keywords = fetch_keywords(ga_client, g_id, str(date_from), str(date_to))
    terms = fetch_search_terms(ga_client, g_id, str(date_from), str(date_to))
    ads = fetch_ads(ga_client, g_id, str(date_from), str(date_to))
    
    all_data = {"campaigns": campaigns, "keywords": keywords, "search_terms": terms, "ads": ads}
    analysis = run_local_audit(all_data)
    status.update(label="Gotowe!", state="complete", expanded=False)

# KPIs
if campaigns:
    total_cost = sum(c["cost"] for c in campaigns)
    total_conv = sum(c["conversions"] for c in campaigns)
    waste_cost = sum(t["cost"] for t in terms if t["conversions"] == 0 and t["cost"] > 10)

    section("KPI")
    c1, c2, c3 = st.columns(3)
    with c1: kpi_card("Koszt", f"{total_cost:.0f} PLN")
    with c2: kpi_card("Konwersje", f"{total_conv:.0f}")
    with c3: kpi_card("Marnotrawstwo", f"{waste_cost:.0f} PLN", accent=True)

# Wynik
section("Analiza AI")
render_analysis(analysis)
