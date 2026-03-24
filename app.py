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

# ── DESIGN SYSTEM (identyczny z Budget Tracker) ───────────────────────────────
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
section[data-testid="stSidebar"] > div {{ padding: 0 !important; }}
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

/* KPI cards */
.kpi {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.5rem 1.8rem;
    position: relative;
    overflow: hidden;
    margin-bottom: 1rem;
}}
.kpi-label {{
    font-size: 0.65rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.6rem;
}}
.kpi-value {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2rem;
    color: var(--white);
    line-height: 1;
    letter-spacing: 0.04em;
}}
.kpi-accent {{ color: var(--coral); }}
.kpi-sub {{ font-size: 0.7rem; color: var(--muted); margin-top: 0.4rem; }}

/* Status badges */
.badge {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}}
.badge-red    {{ background: rgba(255,70,107,0.15); color: #ff466b; border: 1px solid rgba(255,70,107,0.3); }}
.badge-yellow {{ background: rgba(255,184,0,0.15);  color: #ffb800; border: 1px solid rgba(255,184,0,0.3); }}
.badge-green  {{ background: rgba(0,229,160,0.15);  color: #00e5a0; border: 1px solid rgba(0,229,160,0.3); }}

/* Recommendation cards */
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
.rec-title {{
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--white);
    margin-bottom: 0.3rem;
}}
.rec-body {{ font-size: 0.85rem; color: #a0a0c0; line-height: 1.6; }}
.rec-action {{
    display: inline-block;
    margin-top: 0.6rem;
    padding: 4px 12px;
    background: rgba(51,55,189,0.2);
    border: 1px solid rgba(51,55,189,0.4);
    border-radius: 6px;
    font-size: 0.75rem;
    color: #8090ff;
    font-weight: 500;
}}

.stButton > button {{
    background: linear-gradient(135deg, var(--violet), var(--blue)) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    padding: 0.55rem 1.4rem !important;
    transition: opacity 0.2s, transform 0.15s !important;
}}
.stButton > button:hover {{
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}}

.stTextInput input, .stNumberInput input, .stSelectbox > div > div {{
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
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

hr {{ border-color: var(--border) !important; }}
#MainMenu, footer, header {{ visibility: hidden; }}
</style>

<div class="sidebar-logo">
    {"<img src='data:image/png;base64," + LOGO_B64 + "' />" if LOGO_B64 else "<span style='font-family:Bebas Neue,sans-serif;font-size:1.8rem;color:#fff;letter-spacing:0.05em;'>Ermon.</span>"}
    <div class="sidebar-tagline">Ads Analyzer</div>
</div>
""", unsafe_allow_html=True)

# ── HELPERS ───────────────────────────────────────────────────────────────────
def kpi_card(label, value, sub="", accent=False):
    vc = "kpi-value kpi-accent" if accent else "kpi-value"
    sh = f'<div class="kpi-sub">{sub}</div>' if sub else ""
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

def badge(text, kind="red"):
    return f'<span class="badge badge-{kind}">{text}</span>'

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
    elif "GOOGLE_ADS_LOGIN_CUSTOMER_ID" in st.secrets["google_ads"]:
        config["login_customer_id"] = st.secrets["google_ads"]["GOOGLE_ADS_LOGIN_CUSTOMER_ID"]
    return GoogleAdsClient.load_from_dict(config)

def fetch_campaigns(ga_client, customer_id, date_from, date_to):
    """Pobiera kampanie z metrykami."""
    svc = ga_client.get_service("GoogleAdsService")
    cid = customer_id.replace("-", "")
    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.advertising_channel_type,
            campaign.bidding_strategy_type,
            campaign.target_cpa.target_cpa_micros,
            campaign.target_roas.target_roas,
            metrics.clicks,
            metrics.impressions,
            metrics.ctr,
            metrics.average_cpc,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value,
            metrics.cost_per_conversion,
            metrics.search_impression_share,
            metrics.search_budget_lost_impression_share,
            metrics.search_rank_lost_impression_share
        FROM campaign
        WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
          AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
    """
    rows = []
    try:
        resp = svc.search_stream(customer_id=cid, query=query)
        for batch in resp:
            for row in batch.results:
                c  = row.campaign
                m  = row.metrics
                rows.append({
                    "id":              str(c.id),
                    "name":            c.name,
                    "status":          c.status.name,
                    "channel":         c.advertising_channel_type.name,
                    "bidding":         c.bidding_strategy_type.name,
                    "target_cpa":      round(c.target_cpa.target_cpa_micros / 1e6, 2) if c.target_cpa.target_cpa_micros else None,
                    "target_roas":     round(c.target_roas.target_roas, 2) if c.target_roas.target_roas else None,
                    "clicks":          m.clicks,
                    "impressions":     m.impressions,
                    "ctr":             round(m.ctr * 100, 2),
                    "avg_cpc":         round(m.average_cpc / 1e6, 2),
                    "cost":            round(m.cost_micros / 1e6, 2),
                    "conversions":     round(m.conversions, 1),
                    "conv_value":      round(m.conversions_value, 2),
                    "cpa":             round(m.cost_per_conversion / 1e6, 2) if m.conversions > 0 else None,
                    "roas":            round(m.conversions_value / (m.cost_micros / 1e6), 2) if m.cost_micros > 0 and m.conversions_value > 0 else None,
                    "impression_share":round(m.search_impression_share * 100, 1) if m.search_impression_share else None,
                    "lost_budget":     round(m.search_budget_lost_impression_share * 100, 1) if m.search_budget_lost_impression_share else None,
                    "lost_rank":       round(m.search_rank_lost_impression_share * 100, 1) if m.search_rank_lost_impression_share else None,
                })
    except Exception as e:
        st.warning(f"Błąd pobierania kampanii: {e}")
    return rows

def fetch_keywords(ga_client, customer_id, date_from, date_to):
    """Pobiera słowa kluczowe z Quality Score."""
    svc = ga_client.get_service("GoogleAdsService")
    cid = customer_id.replace("-", "")
    query = f"""
        SELECT
            campaign.name,
            ad_group.name,
            ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type,
            ad_group_criterion.quality_info.quality_score,
            ad_group_criterion.quality_info.creative_quality_score,
            ad_group_criterion.quality_info.post_click_quality_score,
            ad_group_criterion.quality_info.search_predicted_ctr,
            metrics.clicks,
            metrics.impressions,
            metrics.cost_micros,
            metrics.conversions,
            metrics.cost_per_conversion
        FROM keyword_view
        WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
          AND ad_group_criterion.status != 'REMOVED'
          AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
        LIMIT 100
    """
    rows = []
    try:
        resp = svc.search_stream(customer_id=cid, query=query)
        for batch in resp:
            for row in batch.results:
                kw = row.ad_group_criterion
                m  = row.metrics
                qs = kw.quality_info.quality_score if kw.quality_info.quality_score else None
                rows.append({
                    "campaign":    row.campaign.name,
                    "ad_group":    row.ad_group.name,
                    "keyword":     kw.keyword.text,
                    "match_type":  kw.keyword.match_type.name,
                    "qs":          qs,
                    "clicks":      m.clicks,
                    "impressions": m.impressions,
                    "cost":        round(m.cost_micros / 1e6, 2),
                    "conversions": round(m.conversions, 1),
                    "cpa":         round(m.cost_per_conversion / 1e6, 2) if m.conversions > 0 else None,
                })
    except Exception as e:
        st.warning(f"Błąd pobierania słów kluczowych: {e}")
    return rows

def fetch_search_terms(ga_client, customer_id, date_from, date_to):
    """Pobiera search terms — złoto do wykluczeń."""
    svc = ga_client.get_service("GoogleAdsService")
    cid = customer_id.replace("-", "")
    query = f"""
        SELECT
            campaign.name,
            ad_group.name,
            search_term_view.search_term,
            search_term_view.status,
            metrics.clicks,
            metrics.impressions,
            metrics.cost_micros,
            metrics.conversions,
            metrics.ctr
        FROM search_term_view
        WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
          AND metrics.impressions > 3
        ORDER BY metrics.cost_micros DESC
        LIMIT 200
    """
    rows = []
    try:
        resp = svc.search_stream(customer_id=cid, query=query)
        for batch in resp:
            for row in batch.results:
                m = row.metrics
                rows.append({
                    "campaign":   row.campaign.name,
                    "ad_group":   row.ad_group.name,
                    "term":       row.search_term_view.search_term,
                    "status":     row.search_term_view.status.name,
                    "clicks":     m.clicks,
                    "impressions":m.impressions,
                    "cost":       round(m.cost_micros / 1e6, 2),
                    "conversions":round(m.conversions, 1),
                    "ctr":        round(m.ctr * 100, 2),
                })
    except Exception as e:
        st.warning(f"Błąd pobierania search terms: {e}")
    return rows

def fetch_ads(ga_client, customer_id, date_from, date_to):
    """Pobiera reklamy (RSA/ETA) z CTR i konwersjami."""
    svc = ga_client.get_service("GoogleAdsService")
    cid = customer_id.replace("-", "")
    query = f"""
        SELECT
            campaign.name,
            ad_group.name,
            ad_group_ad.ad.type,
            ad_group_ad.status,
            ad_group_ad.ad.final_urls,
            metrics.clicks,
            metrics.impressions,
            metrics.ctr,
            metrics.conversions,
            metrics.cost_micros
        FROM ad_group_ad
        WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
          AND ad_group_ad.status != 'REMOVED'
          AND campaign.status != 'REMOVED'
        ORDER BY metrics.impressions DESC
        LIMIT 50
    """
    rows = []
    try:
        resp = svc.search_stream(customer_id=cid, query=query)
        for batch in resp:
            for row in batch.results:
                m = row.metrics
                ad = row.ad_group_ad.ad
                rows.append({
                    "campaign":   row.campaign.name,
                    "ad_group":   row.ad_group.name,
                    "type":       ad.type_.name,
                    "status":     row.ad_group_ad.status.name,
                    "final_url":  ad.final_urls[0] if ad.final_urls else "",
                    "clicks":     m.clicks,
                    "impressions":m.impressions,
                    "ctr":        round(m.ctr * 100, 2),
                    "conversions":round(m.conversions, 1),
                    "cost":       round(m.cost_micros / 1e6, 2),
                })
    except Exception as e:
        st.warning(f"Błąd pobierania reklam: {e}")
    return rows


# ── RENDER ANALYSIS ───────────────────────────────────────────────────────────
def render_analysis(analysis: dict):
    if not analysis:
        st.error("Brak wyników analizy.")
        return

    ocena = analysis.get("ocena_ogolna", "średnia")
    ocena_badge = {"dobra": "green", "średnia": "yellow", "zła": "red"}.get(ocena, "yellow")
    ocena_icon  = {"dobra": "✓", "średnia": "⚠", "zła": "✕"}.get(ocena, "⚠")

    st.markdown(f"""
    <div style="background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:1.8rem 2rem;margin-bottom:1.5rem;">
        <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.8rem;">
            <span style="font-family:'Bebas Neue',sans-serif;font-size:1.5rem;color:var(--white);">Ocena ogólna</span>
            <span class="badge badge-{ocena_badge}">{ocena_icon} {ocena.upper()}</span>
        </div>
        <div style="color:#a0a0c0;font-size:0.95rem;line-height:1.6;">{analysis.get("podsumowanie","")}</div>
    </div>
    """, unsafe_allow_html=True)

    # Problemy krytyczne
    problems = analysis.get("problemy_krytyczne", [])
    if problems:
        section(f"Problemy do naprawienia ({len(problems)})")
        for p in problems:
            pri   = p.get("priorytet", "średni")
            color = {"wysoki": "crit", "średni": "warn", "niski": "ok"}.get(pri, "warn")
            pri_badge = {"wysoki": "red", "średni": "yellow", "niski": "green"}.get(pri, "yellow")
            st.markdown(f"""
            <div class="rec-card {color}">
                <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.4rem;">
                    <div class="rec-title">{p.get("tytul","")}</div>
                    <span class="badge badge-{pri_badge}">{pri}</span>
                </div>
                <div class="rec-body">{p.get("opis","")}</div>
                <div class="rec-action">▶ {p.get("akcja","")}</div>
            </div>
            """, unsafe_allow_html=True)

    # Co działa dobrze
    good = analysis.get("co_dziala_dobrze", [])
    if good:
        section(f"Co działa dobrze ({len(good)})")
        for g in good:
            st.markdown(f"""
            <div class="rec-card ok">
                <div class="rec-title">✓ {g.get("tytul","")}</div>
                <div class="rec-body">{g.get("opis","")}</div>
            </div>
            """, unsafe_allow_html=True)

    # Słowa do wykluczenia
    exclusions = analysis.get("slowa_do_wykluczenia", [])
    if exclusions:
        section(f"Słowa kluczowe do wykluczenia ({len(exclusions)})")
        cols = st.columns(3)
        for i, word in enumerate(exclusions):
            with cols[i % 3]:
                st.markdown(f"""
                <div style="background:rgba(255,70,107,0.08);border:1px solid rgba(255,70,107,0.2);
                     border-radius:8px;padding:0.5rem 0.8rem;margin-bottom:0.5rem;
                     font-size:0.85rem;color:#ff8099;font-family:'DM Sans',sans-serif;">
                    ✕ {word}
                </div>
                """, unsafe_allow_html=True)

    # Rekomendacje stawek
    bids = analysis.get("rekomendacje_stawek", [])
    if bids:
        section(f"Rekomendacje stawek i strategii bidowania ({len(bids)})")
        for b in bids:
            st.markdown(f"""
            <div class="rec-card warn">
                <div class="rec-title">💰 {b.get("kampania","")}</div>
                <div class="rec-body">
                    <strong style="color:#ffb800;">Teraz:</strong> {b.get("obecna_strategia","")}<br>
                    <strong style="color:#a0a0c0;">Rekomendacja:</strong> {b.get("rekomendacja","")}
                </div>
                <div class="rec-action">▶ {b.get("akcja","")}</div>
            </div>
            """, unsafe_allow_html=True)

    # Rekomendacje słów kluczowych
    kw_recs = analysis.get("rekomendacje_slow_kluczowych", [])
    if kw_recs:
        section(f"Rekomendacje słów kluczowych ({len(kw_recs)})")
        type_colors = {
            "dodaj":              ("green", "+"),
            "wyklucz":            ("red",   "✕"),
            "zmień_dopasowanie":  ("yellow","~"),
            "wstrzymaj":          ("yellow","⏸"),
        }
        for k in kw_recs:
            typ   = k.get("akcja_typ", "zmień_dopasowanie")
            color, icon = type_colors.get(typ, ("yellow", "~"))
            st.markdown(f"""
            <div class="rec-card {'ok' if color=='green' else ('crit' if color=='red' else 'warn')}">
                <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.3rem;">
                    <span class="badge badge-{color}">{icon} {typ.replace('_',' ')}</span>
                    <div class="rec-title" style="margin:0;">"{k.get('slowo','')}"</div>
                </div>
                <div class="rec-body">{k.get('powod','')}</div>
                <div class="rec-action">▶ {k.get('szczegoly','')}</div>
            </div>
            """, unsafe_allow_html=True)

    # Reklamy
    ad_recs = analysis.get("rekomendacje_reklam", [])
    if ad_recs:
        section("Rekomendacje dotyczące reklam")
        for a in ad_recs:
            st.markdown(f"""
            <div class="rec-card warn">
                <div class="rec-title">📢 {a.get("problem","")}</div>
                <div class="rec-action">▶ {a.get("akcja","")}</div>
            </div>
            """, unsafe_allow_html=True)

    # Następne kroki
    steps = analysis.get("nastepne_kroki", [])
    if steps:
        section("Następne kroki — co zrobić teraz")
        for i, step in enumerate(steps, 1):
            st.markdown(f"""
            <div style="display:flex;align-items:flex-start;gap:1rem;padding:0.8rem 0;
                 border-bottom:1px solid var(--border);">
                <div style="font-family:'Bebas Neue',sans-serif;font-size:1.8rem;
                     color:var(--coral);line-height:1;min-width:32px;">{i}</div>
                <div style="color:var(--text);font-size:0.9rem;line-height:1.6;padding-top:0.2rem;">
                    {step}
                </div>
            </div>
            """, unsafe_allow_html=True)


    def run_local_audit(data):
    """Analizuje dane pobrane z Google Ads i zwraca rekomendacje (zamiast Claude)."""
    recommendations = {
        "podsumowanie": "Automatyczny audyt techniczny wykonany na podstawie twardych danych z konta.",
        "ocena_ogolna": "dobra",
        "problemy_krytyczne": [],
        "slowa_do_wykluczenia": [],
        "rekomendacje_reklam": [],
        "nastepne_kroki": ["Sprawdź listę wykluczeń", "Skoryguj stawki w najdroższych kampaniach"]
    }

    # 1. Analiza kampanii (Marnotrawstwo)
    for c in data.get("campaigns", []):
        if c['cost'] > 100 and c['conversions'] == 0:
            recommendations["problemy_krytyczne"].append({
                "tytul": f"Przepalanie budżetu: {c['name']}",
                "opis": f"Kampania wydała {c['cost']} PLN i nie przyniosła żadnej konwersji.",
                "akcja": "Zmniejsz budżet dzienny lub sprawdź stronę docelową.",
                "priorytet": "wysoki"
            })
            recommendations["ocena_ogolna"] = "zła"

    # 2. Analiza Search Terms (Słowa do wykluczenia)
    for t in data.get("search_terms", []):
        if t['cost'] > 20 and t['conversions'] == 0:
            recommendations["slowa_do_wykluczenia"].append(t['term'])

    # 3. Analiza Słów Kluczowych (Quality Score)
    for k in data.get("keywords", []):
        if k['qs'] and k['qs'] < 4:
            recommendations["problemy_krytyczne"].append({
                "tytul": f"Niska jakość: {k['keyword']}",
                "opis": f"Wynik jakości (QS) wynosi tylko {k['qs']}/10.",
                "akcja": "Dopasuj treść reklamy do tego słowa, aby obniżyć koszty kliknięć.",
                "priorytet": "średni"
            })

    # 4. Analiza Reklam (Słaby CTR)
    for a in data.get("ads", []):
        if a['impressions'] > 500 and a['ctr'] < 1.0:
            recommendations["rekomendacje_reklam"].append({
                "problem": f"Niski CTR ({a['ctr']}%) w grupie {a['ad_group']}",
                "akcja": "Napisz nowe nagłówki, obecne nie przyciągają uwagi użytkowników."
            })

    return recommendations

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
clients_df = load_clients()
today      = date.today()

with st.sidebar:
    st.markdown("---")
    st.caption("📅 " + today.strftime("%d.%m.%Y"))
    st.markdown("---")

    if clients_df.empty:
        st.warning("Brak klientów w bazie.")
        st.stop()

    # Filtruj klientów którzy mają google_ads_id
    ga_clients = clients_df[
        clients_df["google_ads_id"].astype(str).str.strip().ne("") &
        clients_df["google_ads_id"].notna()
    ]
    if ga_clients.empty:
        st.warning("Żaden klient nie ma ustawionego Google Ads ID.")
        st.stop()

    sel_client = st.selectbox(
        "Klient",
        ga_clients["nazwa"].tolist(),
        help="Tylko klienci z Google Ads ID"
    )

    st.markdown("**Zakres dat**")
    col_d1, col_d2 = st.columns(2)
    # Domyślnie ostatnie 30 dni
    default_from = today - timedelta(days=30)
    date_from = col_d1.date_input("Od", value=default_from, key="df")
    date_to   = col_d2.date_input("Do", value=today, key="dt")

    st.markdown("---")
    run_analysis = st.button(
        "🔍 Analizuj kampanie",
        use_container_width=True,
        type="primary"
    )

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
page_header("Ads Analyzer", f"Analiza AI · Google Ads")

if not run_analysis:
    # Stan startowy
    client_row = ga_clients[ga_clients["nazwa"] == sel_client].iloc[0]
    g_id = str(client_row.get("google_ads_id", "")).strip()

    st.markdown(f"""
    <div class="analyze-box">
        <div style="font-family:'Bebas Neue',sans-serif;font-size:2.5rem;color:var(--white);
             letter-spacing:0.05em;margin-bottom:0.5rem;">
            {sel_client}
        </div>
        <div style="color:var(--muted);font-size:0.8rem;letter-spacing:0.12em;
             text-transform:uppercase;margin-bottom:1.5rem;">
            Google Ads ID: {g_id} &nbsp;·&nbsp; {date_from.strftime("%d.%m.%Y")} — {date_to.strftime("%d.%m.%Y")}
        </div>
        <div style="color:#8090ff;font-size:0.9rem;">
            Kliknij <strong style="color:var(--white);">Analizuj kampanie</strong> w menu bocznym,<br>
            żeby pobrać dane i uruchomić analizę AI.
        </div>
    </div>

    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-top:1rem;">
        <div class="kpi"><div class="kpi-label">Co analizuję</div><div class="kpi-value" style="font-size:1.2rem;color:#8090ff;">Kampanie</div><div class="kpi-sub">status, metryki, IS, bidding</div></div>
        <div class="kpi"><div class="kpi-label">Co analizuję</div><div class="kpi-value" style="font-size:1.2rem;color:#8090ff;">Słowa kluczowe</div><div class="kpi-sub">QS, CPA, match type</div></div>
        <div class="kpi"><div class="kpi-label">Co analizuję</div><div class="kpi-value" style="font-size:1.2rem;color:#8090ff;">Search Terms</div><div class="kpi-sub">frazy do wykluczenia</div></div>
        <div class="kpi"><div class="kpi-label">Co analizuję</div><div class="kpi-value" style="font-size:1.2rem;color:#8090ff;">Reklamy</div><div class="kpi-sub">CTR, konwersje, URL</div></div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── RUN ANALYSIS ──────────────────────────────────────────────────────────────
client_row = ga_clients[ga_clients["nazwa"] == sel_client].iloc[0]
g_id       = str(client_row.get("google_ads_id", "")).strip()
mcc_id     = str(client_row.get("mcc_id", "")).strip()
date_from_str = date_from.strftime("%Y-%m-%d")
date_to_str   = date_to.strftime("%Y-%m-%d")

st.markdown(f"""
<div style="font-size:0.75rem;color:var(--muted);letter-spacing:0.1em;
     text-transform:uppercase;margin-bottom:1rem;">
    {sel_client} &nbsp;·&nbsp; {date_from.strftime("%d.%m.%Y")} — {date_to.strftime("%d.%m.%Y")}
</div>
""", unsafe_allow_html=True)

# ZNAJDŹ TO MIEJSCE W SWOIM KODZIE:
with st.status("Pobieranie danych z Google Ads...", expanded=True) as status:
    try:
        ga_client = get_ga_client(g_id, mcc_id)
        
        # Pobierasz dane (to zostaje bez zmian)
        campaigns = fetch_campaigns(ga_client, g_id, date_from_str, date_to_str)
        keywords = fetch_keywords(ga_client, g_id, date_from_str, date_to_str)
        terms = fetch_search_terms(ga_client, g_id, date_from_str, date_to_str)
        ads = fetch_ads(ga_client, g_id, date_from_str, date_to_str)

        all_data = {
            "campaigns": campaigns,
            "keywords": keywords,
            "search_terms": terms,
            "ads": ads
        }

        # --- TĄ LINIĘ ZMIENIAMY ---
        # ZAMIAST: analysis = analyze_with_claude(all_data, sel_client, ...)
        analysis = run_local_audit(all_data) 
        # --------------------------

        status.update(label="Analiza zakończona!", state="complete", expanded=False)
        
        # To zostaje - Twoja funkcja render_analysis wyświetli 
        # wyniki z Pythona tak samo ładnie, jak te od Claude!
        render_analysis(analysis)

    except Exception as e:
        st.error(f"Coś poszło nie tak: {e}")

# ── QUICK KPIs ────────────────────────────────────────────────────────────────
if campaigns:
    total_cost  = sum(c["cost"] for c in campaigns)
    total_conv  = sum(c["conversions"] for c in campaigns)
    total_clicks= sum(c["clicks"] for c in campaigns)
    avg_cpa     = round(total_cost / total_conv, 2) if total_conv > 0 else 0
    waste_cost  = sum(t["cost"] for t in search_terms if t["conversions"] == 0 and t["cost"] > 10)

    section("Podsumowanie okresu")
    k1,k2,k3,k4,k5 = st.columns(5)
    with k1: kpi_card("Łączny koszt",   f"{total_cost:.0f} PLN", "netto")
    with k2: kpi_card("Konwersje",      f"{total_conv:.0f}",     f"CPA: {avg_cpa:.0f} PLN")
    with k3: kpi_card("Kliknięcia",     f"{total_clicks:,}",     "łącznie")
    with k4: kpi_card("Kampanie",       str(len(campaigns)),     "aktywnych")
    with k5: kpi_card("Przepalone",     f"{waste_cost:.0f} PLN", "frazy 0 konwersji", accent=True)

# ── RENDER AI ANALYSIS ────────────────────────────────────────────────────────
if analysis:
    section("Analiza AI")
    render_analysis(analysis)

    # Dane surowe w ekspanderze
    with st.expander("📋 Dane surowe (kampanie)"):
        if campaigns:
            df_camp = pd.DataFrame(campaigns)
            st.dataframe(df_camp, use_container_width=True, hide_index=True)

    with st.expander("🔑 Dane surowe (słowa kluczowe)"):
        if keywords:
            df_kw = pd.DataFrame(keywords)
            st.dataframe(df_kw, use_container_width=True, hide_index=True)

    with st.expander("🔍 Search terms (wszystkie)"):
        if search_terms:
            df_st = pd.DataFrame(search_terms)
            st.dataframe(df_st, use_container_width=True, hide_index=True)

    # Eksport JSON
    st.markdown("---")
    json_export = json.dumps(analysis, ensure_ascii=False, indent=2)
    st.download_button(
        "📥 Pobierz raport JSON",
        data=json_export.encode("utf-8"),
        file_name=f"analiza_{sel_client.lower().replace(' ','_')}_{date_from_str}.json",
        mime="application/json"
    )
