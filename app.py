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

SHEET_ID = "1l_fX5ydioIsKVyhitrnR3rcdf6RyZOq-x6oQ3mhP9uQ"
SCOPES   = ["https://www.googleapis.com/auth/spreadsheets"]

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

# ══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap');

:root {{
  --violet:  #2c016d; --coral: #ff466b; --blue: #3337bd;
  --bg: #0c0c18; --surface: #13132a; --surface2: #1a1a35;
  --border: #2a2a50; --text: #e8e8f5; --muted: #6060a0; --white: #ffffff;
  --green: #00e5a0; --yellow: #ffb800; --red: #ff466b;
}}
html, body, [class*="css"] {{ font-family: 'DM Sans', sans-serif; background-color: var(--bg); color: var(--text); }}
section[data-testid="stSidebar"] {{ background: var(--surface) !important; border-right: 1px solid var(--border); }}
section[data-testid="stSidebar"] > div {{ padding: 0 !important; }}
.sidebar-logo {{ padding: 2rem 1.5rem 1.5rem; border-bottom: 1px solid var(--border); margin-bottom: 0.5rem; }}
.sidebar-logo img {{ width: 110px; filter: brightness(0) invert(1); }}
.sidebar-tagline {{ font-size: 0.65rem; letter-spacing: 0.2em; color: var(--muted); text-transform: uppercase; margin-top: 8px; }}
.main .block-container {{ padding: 2.5rem 3rem; max-width: 1700px; }}
.page-title {{ font-family: 'Bebas Neue', sans-serif; font-size: 3.5rem; color: var(--white); letter-spacing: 0.05em; line-height: 1; margin-bottom: 0.1rem; }}
.page-subtitle {{ font-size: 0.75rem; color: var(--muted); letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 2.5rem; }}
.section-hdr {{ font-size: 0.7rem; font-weight: 600; color: var(--muted); letter-spacing: 0.18em; text-transform: uppercase; border-bottom: 1px solid var(--border); padding-bottom: 0.6rem; margin: 2.5rem 0 1.5rem; }}
.kpi {{ background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 1.5rem 1.8rem; margin-bottom: 1rem; }}
.kpi-label {{ font-size: 0.65rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 0.4rem; }}
.kpi-value {{ font-family: 'Bebas Neue', sans-serif; font-size: 2rem; color: var(--white); line-height: 1; }}
.kpi-sub {{ font-size: 0.7rem; color: var(--muted); margin-top: 0.3rem; }}
.kpi-accent {{ color: var(--coral); }}
.badge {{ display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; }}
.badge-red    {{ background: rgba(255,70,107,0.15); color: #ff6b87; border: 1px solid rgba(255,70,107,0.3); }}
.badge-yellow {{ background: rgba(255,184,0,0.15);  color: #ffc933; border: 1px solid rgba(255,184,0,0.3); }}
.badge-green  {{ background: rgba(0,229,160,0.15);  color: #00e5a0; border: 1px solid rgba(0,229,160,0.3); }}
.badge-blue   {{ background: rgba(51,55,189,0.2);   color: #8090ff; border: 1px solid rgba(51,55,189,0.4); }}
.rec-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.2rem 1.5rem; margin-bottom: 0.8rem; border-left: 3px solid var(--coral); }}
.rec-card.ok   {{ border-left-color: #00e5a0; }}
.rec-card.warn {{ border-left-color: #ffb800; }}
.rec-card.crit {{ border-left-color: #ff466b; }}
.rec-card.info {{ border-left-color: #3337bd; }}
.rec-title {{ font-weight: 600; font-size: 0.95rem; color: var(--white); margin-bottom: 0.4rem; }}
.rec-body  {{ font-size: 0.85rem; color: #a0a0c0; line-height: 1.65; }}
.rec-action {{ display: inline-block; margin-top: 0.6rem; padding: 4px 12px; background: rgba(51,55,189,0.2); border: 1px solid rgba(51,55,189,0.4); border-radius: 6px; font-size: 0.75rem; color: #8090ff; font-weight: 500; }}
.stButton > button {{ background: linear-gradient(135deg, var(--violet), var(--blue)) !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; padding: 0.55rem 1.4rem !important; }}
.analyze-box {{ background: linear-gradient(135deg, rgba(44,1,109,0.3), rgba(51,55,189,0.2)); border: 1px solid rgba(51,55,189,0.4); border-radius: 16px; padding: 2rem; text-align: center; margin: 2rem 0; }}
.score-ring {{ display: flex; align-items: center; gap: 2rem; padding: 1.5rem 2rem; background: var(--surface); border: 1px solid var(--border); border-radius: 16px; margin-bottom: 1.5rem; }}
.score-number {{ font-family: 'Bebas Neue', sans-serif; font-size: 4rem; line-height: 1; }}
.excl-pill {{ display: inline-block; margin: 3px 4px; padding: 4px 12px; background: rgba(255,70,107,0.1); border: 1px solid rgba(255,70,107,0.25); border-radius: 20px; font-size: 0.8rem; color: #ff8099; }}
#MainMenu, footer, header {{ visibility: hidden; }}
</style>
<div class="sidebar-logo">
    {"<img src='data:image/png;base64," + LOGO_B64 + "' />" if LOGO_B64 else "<span style='font-family:Bebas Neue,sans-serif;font-size:1.8rem;color:#fff;'>Ermon.</span>"}
    <div class="sidebar-tagline">Ads Analyzer</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# GOOGLE ADS FETCHERS — pobieramy WSZYSTKO co potrzeba do pełnego audytu
# ══════════════════════════════════════════════════════════════════════════════
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
    elif "GOOGLE_ADS_LOGIN_CUSTOMER_ID" in st.secrets.get("google_ads", {}):
        config["login_customer_id"] = st.secrets["google_ads"]["GOOGLE_ADS_LOGIN_CUSTOMER_ID"]
    return GoogleAdsClient.load_from_dict(config)

def fetch_campaigns(ga_client, cid, date_from, date_to):
    """Kampanie z pełnymi metrykami włącznie z budżetem i impression share."""
    svc   = ga_client.get_service("GoogleAdsService")
    query = f"""
        SELECT
            campaign.id, campaign.name, campaign.status,
            campaign.advertising_channel_type,
            campaign.bidding_strategy_type,
            campaign.target_cpa.target_cpa_micros,
            campaign.target_roas.target_roas,
            campaign_budget.amount_micros,
            campaign_budget.has_recommended_budget,
            campaign_budget.recommended_budget_amount_micros,
            metrics.cost_micros,
            metrics.clicks, metrics.impressions, metrics.ctr,
            metrics.average_cpc,
            metrics.conversions, metrics.conversions_value,
            metrics.cost_per_conversion,
            metrics.search_impression_share,
            metrics.search_budget_lost_impression_share,
            metrics.search_rank_lost_impression_share,
            metrics.search_absolute_top_impression_share
        FROM campaign
        WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
          AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
    """
    rows = []
    try:
        for batch in svc.search_stream(customer_id=cid.replace("-",""), query=query):
            for r in batch.results:
                m  = r.metrics
                cb = r.campaign_budget
                c  = r.campaign
                budget_day  = round(cb.amount_micros / 1e6, 2) if cb.amount_micros else None
                rec_budget  = round(cb.recommended_budget_amount_micros / 1e6, 2) if cb.recommended_budget_amount_micros else None
                cost        = round(m.cost_micros / 1e6, 2)
                conv        = round(m.conversions, 1)
                conv_val    = round(m.conversions_value, 2)
                rows.append({
                    "id":           str(c.id),
                    "name":         c.name,
                    "status":       c.status.name,
                    "channel":      c.advertising_channel_type.name,
                    "bidding":      c.bidding_strategy_type.name,
                    "target_cpa":   round(c.target_cpa.target_cpa_micros / 1e6, 2) if c.target_cpa.target_cpa_micros else None,
                    "target_roas":  round(c.target_roas.target_roas, 2) if c.target_roas.target_roas else None,
                    "budget_day":   budget_day,
                    "rec_budget":   rec_budget,
                    "budget_limited": cb.has_recommended_budget,
                    "cost":         cost,
                    "clicks":       m.clicks,
                    "impressions":  m.impressions,
                    "ctr":          round(m.ctr * 100, 2),
                    "avg_cpc":      round(m.average_cpc / 1e6, 2),
                    "conversions":  conv,
                    "conv_value":   conv_val,
                    "cpa":          round(m.cost_per_conversion / 1e6, 2) if conv > 0 else None,
                    "roas":         round(conv_val / cost, 2) if cost > 0 and conv_val > 0 else None,
                    "is":           round(m.search_impression_share * 100, 1) if m.search_impression_share else None,
                    "is_lost_budget": round(m.search_budget_lost_impression_share * 100, 1) if m.search_budget_lost_impression_share else None,
                    "is_lost_rank":   round(m.search_rank_lost_impression_share * 100, 1) if m.search_rank_lost_impression_share else None,
                    "abs_top_is":     round(m.search_absolute_top_impression_share * 100, 1) if m.search_absolute_top_impression_share else None,
                })
    except Exception as e:
        st.warning(f"Błąd kampanii: {e}")
    return rows

def fetch_keywords(ga_client, cid, date_from, date_to):
    """Słowa kluczowe z Quality Score i metrykami."""
    svc   = ga_client.get_service("GoogleAdsService")
    query = f"""
        SELECT
            campaign.name, ad_group.name,
            ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type,
            ad_group_criterion.status,
            ad_group_criterion.quality_info.quality_score,
            ad_group_criterion.quality_info.creative_quality_score,
            ad_group_criterion.quality_info.post_click_quality_score,
            ad_group_criterion.quality_info.search_predicted_ctr,
            ad_group_criterion.cpc_bid_micros,
            metrics.clicks, metrics.impressions, metrics.cost_micros,
            metrics.conversions, metrics.cost_per_conversion, metrics.ctr
        FROM keyword_view
        WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
          AND ad_group_criterion.status != 'REMOVED'
          AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
        LIMIT 150
    """
    rows = []
    try:
        for batch in svc.search_stream(customer_id=cid.replace("-",""), query=query):
            for r in batch.results:
                kw = r.ad_group_criterion
                m  = r.metrics
                conv = round(m.conversions, 1)
                rows.append({
                    "campaign":   r.campaign.name,
                    "ad_group":   r.ad_group.name,
                    "keyword":    kw.keyword.text,
                    "match_type": kw.keyword.match_type.name,
                    "status":     kw.status.name,
                    "qs":         kw.quality_info.quality_score or None,
                    "qs_ad":      kw.quality_info.creative_quality_score.name if kw.quality_info.creative_quality_score else None,
                    "qs_lp":      kw.quality_info.post_click_quality_score.name if kw.quality_info.post_click_quality_score else None,
                    "qs_ctr":     kw.quality_info.search_predicted_ctr.name if kw.quality_info.search_predicted_ctr else None,
                    "cpc_bid":    round(kw.cpc_bid_micros / 1e6, 2) if kw.cpc_bid_micros else None,
                    "clicks":     m.clicks,
                    "impressions":m.impressions,
                    "ctr":        round(m.ctr * 100, 2),
                    "cost":       round(m.cost_micros / 1e6, 2),
                    "conversions":conv,
                    "cpa":        round(m.cost_per_conversion / 1e6, 2) if conv > 0 else None,
                })
    except Exception as e:
        st.warning(f"Błąd keywords: {e}")
    return rows

def fetch_search_terms(ga_client, cid, date_from, date_to):
    """Search terms — frazy których szukali użytkownicy."""
    svc   = ga_client.get_service("GoogleAdsService")
    query = f"""
        SELECT
            campaign.name, ad_group.name,
            search_term_view.search_term,
            search_term_view.status,
            metrics.clicks, metrics.impressions, metrics.cost_micros,
            metrics.conversions, metrics.ctr
        FROM search_term_view
        WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
          AND metrics.impressions > 2
          AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
        LIMIT 300
    """
    rows = []
    try:
        for batch in svc.search_stream(customer_id=cid.replace("-",""), query=query):
            for r in batch.results:
                m = r.metrics
                rows.append({
                    "campaign":    r.campaign.name,
                    "ad_group":    r.ad_group.name,
                    "term":        r.search_term_view.search_term,
                    "status":      r.search_term_view.status.name,
                    "clicks":      m.clicks,
                    "impressions": m.impressions,
                    "cost":        round(m.cost_micros / 1e6, 2),
                    "conversions": round(m.conversions, 1),
                    "ctr":         round(m.ctr * 100, 2),
                })
    except Exception as e:
        st.warning(f"Błąd search terms: {e}")
    return rows

def fetch_ads(ga_client, cid, date_from, date_to):
    """Reklamy z CTR i konwersjami."""
    svc   = ga_client.get_service("GoogleAdsService")
    query = f"""
        SELECT
            campaign.name, ad_group.name,
            ad_group_ad.ad.type, ad_group_ad.status,
            metrics.clicks, metrics.impressions, metrics.ctr,
            metrics.conversions, metrics.cost_micros
        FROM ad_group_ad
        WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
          AND ad_group_ad.status != 'REMOVED'
          AND campaign.status != 'REMOVED'
        ORDER BY metrics.impressions DESC
        LIMIT 100
    """
    rows = []
    try:
        for batch in svc.search_stream(customer_id=cid.replace("-",""), query=query):
            for r in batch.results:
                m  = r.metrics
                rows.append({
                    "campaign":   r.campaign.name,
                    "ad_group":   r.ad_group.name,
                    "type":       r.ad_group_ad.ad.type_.name,
                    "status":     r.ad_group_ad.status.name,
                    "clicks":     m.clicks,
                    "impressions":m.impressions,
                    "ctr":        round(m.ctr * 100, 2),
                    "conversions":round(m.conversions, 1),
                    "cost":       round(m.cost_micros / 1e6, 2),
                })
    except Exception as e:
        st.warning(f"Błąd ads: {e}")
    return rows

def fetch_ad_groups(ga_client, cid, date_from, date_to):
    """Grupy reklam — sprawdzamy czy nie ma za dużo słów i czy są aktywne."""
    svc   = ga_client.get_service("GoogleAdsService")
    query = f"""
        SELECT
            campaign.name, ad_group.name, ad_group.status,
            metrics.clicks, metrics.impressions, metrics.cost_micros,
            metrics.conversions, metrics.ctr
        FROM ad_group
        WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
          AND ad_group.status != 'REMOVED'
          AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
        LIMIT 100
    """
    rows = []
    try:
        for batch in svc.search_stream(customer_id=cid.replace("-",""), query=query):
            for r in batch.results:
                m = r.metrics
                rows.append({
                    "campaign":   r.campaign.name,
                    "ad_group":   r.ad_group.name,
                    "status":     r.ad_group.status.name,
                    "clicks":     m.clicks,
                    "impressions":m.impressions,
                    "cost":       round(m.cost_micros / 1e6, 2),
                    "conversions":round(m.conversions, 1),
                    "ctr":        round(m.ctr * 100, 2),
                })
    except Exception as e:
        st.warning(f"Błąd ad groups: {e}")
    return rows

# ══════════════════════════════════════════════════════════════════════════════
# EXPERT AUDIT ENGINE
# ══════════════════════════════════════════════════════════════════════════════
def run_full_audit(data: dict) -> dict:
    """
    Pełna diagnostyka konta Google Ads.
    Zwraca pogrupowane znaleziska z priorytetami HIGH / MEDIUM / LOW.
    """
    campaigns    = data.get("campaigns", [])
    keywords     = data.get("keywords", [])
    search_terms = data.get("search_terms", [])
    ads          = data.get("ads", [])
    ad_groups    = data.get("ad_groups", [])

    findings = []   # każde: {priority, category, title, desc, action}
    score    = 100  # punkty odejmujemy za problemy

    # ── Progi eksperckie ──────────────────────────────────────────────────────
    CTR_SEARCH_MIN   = 2.0    # % — search powinien mieć CTR > 2%
    CTR_DISPLAY_MIN  = 0.3
    CPA_WARN_MULT    = 3.0    # CPA > 3× target_cpa = problem
    IS_LOST_BUDGET_H = 20     # % — strata IS przez budżet > 20% = HIGH
    IS_LOST_BUDGET_M = 10
    IS_LOST_RANK_H   = 30     # % — strata przez ranking
    QS_LOW           = 4      # QS ≤ 4 = problem
    QS_VERY_LOW      = 2
    WASTE_COST_THRESH = 15    # PLN — fraza bez konwersji powyżej tej kwoty = do wykluczenia
    BROAD_WITHOUT_CONV= 50    # PLN — broad match bez konwersji
    ZERO_CONV_CAMP   = 200    # PLN — kampania bez konwersji powyżej tej kwoty = HIGH
    MIN_CTR_AD       = 1.5    # % — reklamy poniżej tego CTR przy > 300 wyświetleniach
    AD_GROUP_MIN_ADS = 2      # min liczba reklam w grupie

    # ── 1. BUDŻETY KAMPANII ───────────────────────────────────────────────────
    for c in campaigns:
        if c.get("budget_limited") and c.get("is_lost_budget") and c["is_lost_budget"] >= IS_LOST_BUDGET_H:
            score -= 8
            findings.append({
                "priority": "HIGH", "category": "Budżet",
                "title": f"Kampania ograniczona budżetem: {c['name']}",
                "desc": (
                    f"Tracisz <strong>{c['is_lost_budget']}%</strong> impression share z powodu za niskiego budżetu dziennego "
                    f"({c['budget_day']} PLN/dzień). "
                    + (f"Google rekomenduje zwiększenie do <strong>{c['rec_budget']} PLN/dzień</strong>." if c.get("rec_budget") else "")
                ),
                "action": (
                    f"Zwiększ budżet dzienny kampanii '{c['name']}' "
                    + (f"do minimum {c['rec_budget']} PLN." if c.get("rec_budget") else "o co najmniej 30%.")
                    + " Jeśli nie masz budżetu, ogranicz słowa kluczowe do najlepiej konwertujących."
                ),
            })
        elif c.get("is_lost_budget") and c["is_lost_budget"] >= IS_LOST_BUDGET_M:
            score -= 4
            findings.append({
                "priority": "MEDIUM", "category": "Budżet",
                "title": f"Częściowe ograniczenie budżetem: {c['name']}",
                "desc": f"Tracisz {c['is_lost_budget']}% wyświetleń przez budżet. Budżet dzienny: {c.get('budget_day','?')} PLN.",
                "action": f"Rozważ zwiększenie budżetu kampanii '{c['name']}' lub zawęź targeting do godzin/lokalizacji o najwyższej konwersji.",
            })

    # ── 2. KAMPANIE BEZ KONWERSJI ─────────────────────────────────────────────
    for c in campaigns:
        if (c["cost"] or 0) >= ZERO_CONV_CAMP and (c["conversions"] or 0) == 0:
            score -= 10
            findings.append({
                "priority": "HIGH", "category": "Konwersje",
                "title": f"Kampania przepala budżet bez konwersji: {c['name']}",
                "desc": (
                    f"Wydano <strong>{c['cost']} PLN</strong> i zero konwersji. "
                    f"Kliknięcia: {c['clicks']}, CTR: {c['ctr']}%. "
                    f"Strategia: {c['bidding']}."
                ),
                "action": (
                    "1. Sprawdź śledzenie konwersji — czy piksel działa poprawnie. "
                    "2. Przejrzyj stronę docelową — czy jest spójna z reklamami. "
                    "3. Sprawdź search termy — czy nie przyciągasz złego ruchu. "
                    "4. Jeśli tracking OK, wstrzymaj kampanię i przebuduj."
                ),
            })
        elif (c["cost"] or 0) >= 50 and (c["conversions"] or 0) == 0:
            score -= 4
            findings.append({
                "priority": "MEDIUM", "category": "Konwersje",
                "title": f"Brak konwersji: {c['name']}",
                "desc": f"Wydano {c['cost']} PLN bez konwersji. Kliknięcia: {c['clicks']}.",
                "action": "Sprawdź search termy i stronę docelową. Rozważ zmianę strategii bidowania.",
            })

    # ── 3. CPA vs TARGET CPA ──────────────────────────────────────────────────
    for c in campaigns:
        if c.get("target_cpa") and c.get("cpa") and c["cpa"] > 0:
            ratio = c["cpa"] / c["target_cpa"]
            if ratio > CPA_WARN_MULT:
                score -= 7
                findings.append({
                    "priority": "HIGH", "category": "Konwersje",
                    "title": f"CPA {ratio:.1f}× powyżej celu: {c['name']}",
                    "desc": (
                        f"Rzeczywiste CPA: <strong>{c['cpa']} PLN</strong>, "
                        f"cel: {c['target_cpa']} PLN ({ratio:.1f}× za drogo). "
                        f"Konwersje: {c['conversions']}."
                    ),
                    "action": (
                        f"1. Podnieś cel CPA tymczasowo do {round(c['cpa']*0.8, 0)} PLN, żeby dać algorytmowi więcej swobody. "
                        "2. Sprawdź słowa kluczowe — wyklucz te z najwyższym CPA i zerową wartością. "
                        "3. Przejrzyj harmonogram reklam — wyłącz godziny/dni bez konwersji."
                    ),
                })
            elif ratio > 1.5:
                score -= 3
                findings.append({
                    "priority": "MEDIUM", "category": "Konwersje",
                    "title": f"CPA powyżej celu: {c['name']}",
                    "desc": f"CPA: {c['cpa']} PLN, cel: {c['target_cpa']} PLN.",
                    "action": "Przejrzyj search termy i wyklucz frazy bez konwersji.",
                })

    # ── 4. ROAS vs TARGET ROAS ────────────────────────────────────────────────
    for c in campaigns:
        if c.get("target_roas") and c.get("roas") and c["roas"] > 0:
            if (c["roas"] or 0) < (c["target_roas"] or 0) * 0.6:
                score -= 7
                findings.append({
                    "priority": "HIGH", "category": "Konwersje",
                    "title": f"ROAS znacznie poniżej celu: {c['name']}",
                    "desc": (
                        f"Rzeczywisty ROAS: <strong>{c['roas']:.2f}</strong>, "
                        f"cel: {c['target_roas']:.2f}. "
                        f"Wartość konwersji: {c['conv_value']} PLN, koszt: {c['cost']} PLN."
                    ),
                    "action": (
                        f"1. Obniż cel ROAS do {round(c['target_roas']*0.75, 2)} na 2 tygodnie — algorytm się skalibruje. "
                        "2. Sprawdź śledzenie wartości konwersji — czy wartości są poprawnie przypisane. "
                        "3. Wyklucz produkty/słowa z ujemnym ROAS."
                    ),
                })

    # ── 5. IMPRESSION SHARE — utrata przez ranking ────────────────────────────
    for c in campaigns:
        if c.get("is_lost_rank") and c["is_lost_rank"] >= IS_LOST_RANK_H:
            score -= 6
            findings.append({
                "priority": "HIGH", "category": "Stawki",
                "title": f"Słabe pozycje rankingowe: {c['name']}",
                "desc": (
                    f"Tracisz <strong>{c['is_lost_rank']}%</strong> wyświetleń przez niski ranking reklamy. "
                    f"IS całkowite: {c.get('is','?')}%, Abs. Top IS: {c.get('abs_top_is','?')}%."
                ),
                "action": (
                    "1. Podnieś CPC bid lub docelowe CPA dla tej kampanii. "
                    "2. Popraw Quality Score słów kluczowych (CTR reklam, relevancja landing page). "
                    "3. Rozważ przełączenie na Target Impression Share jeśli widoczność jest priorytetem."
                ),
            })
        elif c.get("is_lost_rank") and c["is_lost_rank"] >= 15:
            score -= 3
            findings.append({
                "priority": "MEDIUM", "category": "Stawki",
                "title": f"Umiarkowana utrata IS przez ranking: {c['name']}",
                "desc": f"Tracisz {c['is_lost_rank']}% wyświetleń przez niski ranking.",
                "action": "Popraw QS słów kluczowych lub nieznacznie podnieś stawki.",
            })

    # ── 6. QUALITY SCORE ──────────────────────────────────────────────────────
    very_low_qs = [k for k in keywords if k.get("qs") and k["qs"] <= QS_VERY_LOW and (k["cost"] or 0) > 5]
    low_qs      = [k for k in keywords if k.get("qs") and QS_VERY_LOW < k["qs"] <= QS_LOW and (k["cost"] or 0) > 10]

    for k in very_low_qs[:5]:
        score -= 5
        lp_note = ""
        if k.get("qs_lp") and "BELOW" in k["qs_lp"]:
            lp_note = " Landing page jest oceniany jako słaby — popraw spójność treści."
        ad_note = ""
        if k.get("qs_ad") and "BELOW" in k["qs_ad"]:
            ad_note = " Trafność reklamy jest niska — dodaj słowo kluczowe do nagłówka."
        findings.append({
            "priority": "HIGH", "category": "Quality Score",
            "title": f"Bardzo niski QS ({k['qs']}/10): \"{k['keyword']}\"",
            "desc": (
                f"[{k['match_type']}] w kampanii <em>{k['campaign']}</em>. "
                f"Koszt: {k['cost']} PLN, konwersje: {k['conversions']}."
                f"{lp_note}{ad_note}"
            ),
            "action": (
                f"Opcja A: Utwórz dedykowaną grupę reklam dla frazy '{k['keyword']}' z reklamą dopasowaną 1:1. "
                "Opcja B: Jeśli fraza nie konwertuje — wstrzymaj ją. "
                "Nie zostawiaj aktywnych słów z QS ≤ 2 — podnosisz CPC całej kampanii."
            ),
        })

    if low_qs:
        score -= 3
        kw_list = ", ".join(f"\"{k['keyword']}\" (QS:{k['qs']})" for k in low_qs[:6])
        findings.append({
            "priority": "MEDIUM", "category": "Quality Score",
            "title": f"Niski Quality Score ({len(low_qs)} słów kluczowych)",
            "desc": f"Słowa z QS 3–4: {kw_list}.",
            "action": (
                "1. Dodaj słowo kluczowe do nagłówka reklamy. "
                "2. Sprawdź landing page — czy zawiera tę frazę. "
                "3. Sprawdź expected CTR — dodaj rozszerzenia (sitelinki, callouts)."
            ),
        })

    # ── 7. SŁOWA KLUCZOWE DO WYKLUCZENIA — smart filter ──────────────────────
    # Buduj słownik branży z aktywnych słów kluczowych kampanii.
    # Tokenizuj każde słowo kluczowe na pojedyncze tokeny (min 3 znaki).
    # Search term który nie zawiera żadnego tokenu = nierelated = kandydat do wykluczenia.

    def build_brand_vocab(keywords: list) -> set:
        """Wyciąga unikalne tokeny ze słów kluczowych kampanii."""
        stop_words = {
            # ogólne słowa które są w każdej branży — ignoruj przy porównaniu
            "jak", "co", "ile", "czy", "dla", "bez", "przy", "pod", "nad",
            "gdzie", "kiedy", "który", "która", "które", "tego", "tej",
            "the", "and", "for", "with", "how", "what", "best", "buy",
            "cena", "ceny", "sklep", "online", "tanie", "tanio", "najtaniej",
            "opinie", "ranking", "porównanie", "oferta", "promocja", "rabat",
            "dostawa", "wysyłka", "zamówienie", "zamów", "kup", "kupić",
        }
        vocab = set()
        for kw in keywords:
            text = kw.get("keyword", "").lower()
            # usuń operatory dopasowania (+, "", [])
            text = re.sub(r'[\[\]"+]', '', text)
            tokens = re.split(r'\s+', text.strip())
            for token in tokens:
                token = token.strip(".,!?")
                if len(token) >= 3 and token not in stop_words:
                    vocab.add(token)
        return vocab

    def is_irrelevant(term: str, vocab: set) -> bool:
        """
        Zwraca True jeśli żaden token z frazy nie pasuje do słownika branży.
        Używa stemming-lite: sprawdza czy token z frazy jest podciągiem
        tokenu z vocab lub odwrotnie (obsługuje odmianę).
        """
        term_tokens = re.split(r'\s+', term.lower().strip())
        term_tokens = [t.strip(".,!?") for t in term_tokens if len(t) >= 3]
        if not term_tokens:
            return False
        for t_tok in term_tokens:
            for v_tok in vocab:
                # dopasowanie dokładne lub prefiks (stem-lite dla j. polskiego)
                if t_tok == v_tok:
                    return False
                if len(t_tok) >= 4 and len(v_tok) >= 4:
                    # sprawdź czy jeden jest prefiksem drugiego (min 4 znaki)
                    prefix_len = min(len(t_tok), len(v_tok), 6)
                    if t_tok[:prefix_len] == v_tok[:prefix_len]:
                        return False
        return True

    # Zbuduj słownik branży
    brand_vocab = build_brand_vocab(keywords)

    # Filtruj search terms: nierelated + minimalny koszt/kliki żeby nie śmiecić
    waste_terms = []
    for t in search_terms:
        if t["status"] == "NEGATIVE":
            continue
        if (t["conversions"] or 0) > 0:
            continue
        # Progi — fraza musi mieć realny koszt żeby warto było ją wykluczać
        if (t["cost"] or 0) < WASTE_COST_THRESH and (t["clicks"] or 0) < 8:
            continue
        # Kluczowy test: czy fraza jest nierelated z branżą klienta?
        if brand_vocab and not is_irrelevant(t["term"], brand_vocab):
            # Fraza pasuje do branży — nie wykluczaj, nawet jeśli 0 konwersji
            continue
        waste_terms.append(t)

    waste_terms.sort(key=lambda x: x["cost"], reverse=True)
    excl_words = [t["term"] for t in waste_terms]

    if waste_terms:
        total_waste = sum(t["cost"] for t in waste_terms)
        score -= min(15, len(waste_terms))
        vocab_note = (
            f" Filtr branżowy oparty na {len(brand_vocab)} tokenach z aktywnych słów kluczowych — "
            "sugerowane frazy nie pasują tematycznie do konta."
            if brand_vocab else
            " Uwaga: brak słów kluczowych do porównania — sprawdź listę ręcznie."
        )
        findings.append({
            "priority": "HIGH" if total_waste > 100 else "MEDIUM",
            "category": "Wykluczenia",
            "title": f"Nierelated frazy bez konwersji — {total_waste:.0f} PLN przepalone ({len(waste_terms)} fraz)",
            "desc": (
                "Te frazy nie mają związku z branżą klienta "
                "(nie zawierają żadnego słowa z aktywnych kampanii) i nie wygenerowały konwersji. Top: "
                + ", ".join(f'"{t["term"]}" ({t["cost"]} PLN, {t["clicks"]} kliknięć)' for t in waste_terms[:6])
                + ("..." if len(waste_terms) > 6 else ".")
                + vocab_note
            ),
            "action": (
                "Dodaj jako [exact match] do listy wykluczeń kampanii lub na poziomie konta (shared negative list). "
                "Google Ads → Słowa kluczowe → Wykluczające. "
                f"Potencjalny odzysk budżetu: {total_waste:.0f} PLN / okres."
            ),
            "_excl_terms": excl_words,
        })

    # ── 8. BROAD MATCH bez konwersji ──────────────────────────────────────────
    broad_waste = [
        k for k in keywords
        if k["match_type"] == "BROAD" and (k["conversions"] or 0) == 0 and (k["cost"] or 0) >= BROAD_WITHOUT_CONV
    ]
    if broad_waste:
        score -= 5
        bw_list = ", ".join(f"\"{k['keyword']}\" ({k['cost']} PLN)" for k in broad_waste[:4])
        findings.append({
            "priority": "HIGH", "category": "Słowa kluczowe",
            "title": f"Broad match bez konwersji ({len(broad_waste)} słów)",
            "desc": f"Słowa: {bw_list}. Broad match przynosi masę irrelewantnego ruchu.",
            "action": (
                "1. Zmień dopasowanie na Phrase lub Exact match dla tych słów. "
                "2. Dodaj listę wykluczeń. "
                "3. Jeśli zostawiasz broad — koniecznie dodaj Smart Bidding z sygnałami konwersji."
            ),
        })

    # ── 9. SŁOWA Z WYSOKIM KOSZTEM BEZ WARTOŚCI ──────────────────────────────
    expensive_no_conv = [
        k for k in keywords
        if (k["conversions"] or 0) == 0 and (k["cost"] or 0) >= 80 and (k.get("qs") or 10) >= 5
    ]
    for k in expensive_no_conv[:4]:
        score -= 4
        findings.append({
            "priority": "MEDIUM", "category": "Słowa kluczowe",
            "title": f"Drogie słowo bez konwersji: \"{k['keyword']}\"",
            "desc": f"Koszt: {k['cost']} PLN, konwersje: 0. Match: {k['match_type']}, QS: {k.get('qs','?')}.",
            "action": f"Wstrzymaj słowo \"{k['keyword']}\" lub obniż stawkę o 50%. Dodaj je jako wykluczenie jeśli jest irrelewantne.",
        })

    # ── 10. CTR kampanii ──────────────────────────────────────────────────────
    for c in campaigns:
        if (c["impressions"] or 0) < 200:
            continue
        channel = c.get("channel", "")
        threshold = CTR_DISPLAY_MIN if "DISPLAY" in channel else CTR_SEARCH_MIN
        if (c["ctr"] or 0) < threshold:
            score -= 3
            findings.append({
                "priority": "MEDIUM", "category": "Reklamy",
                "title": f"Niski CTR ({c['ctr']}%): {c['name']}",
                "desc": f"Oczekiwany minimum: {threshold}%. Wyświetlenia: {c['impressions']:,}.",
                "action": (
                    "1. Odśwież nagłówki reklam — dodaj USP, liczby, CTA. "
                    "2. Dodaj rozszerzenia: sitelinki, callouts, structured snippets. "
                    "3. Sprawdź relevancję — czy reklama odpowiada na intent zapytania."
                ),
            })

    # ── 11. REKLAMY — za mało w grupie, słaby CTR ─────────────────────────────
    # Grupuj reklamy po ad_group
    ag_ads = {}
    for a in ads:
        key = (a["campaign"], a["ad_group"])
        ag_ads.setdefault(key, []).append(a)

    for (camp, ag), ag_list in ag_ads.items():
        enabled = [a for a in ag_list if a["status"] == "ENABLED"]
        if len(enabled) < AD_GROUP_MIN_ADS:
            score -= 3
            findings.append({
                "priority": "MEDIUM", "category": "Reklamy",
                "title": f"Za mało aktywnych reklam w grupie: {ag}",
                "desc": f"Kampania: {camp}. Aktywne reklamy: {len(enabled)}. Minimum to {AD_GROUP_MIN_ADS}.",
                "action": "Dodaj przynajmniej 3 warianty RSA z różnymi nagłówkami. Google potrzebuje wariantów do optymalizacji.",
            })

    low_ctr_ads = [
        a for a in ads
        if (a["impressions"] or 0) >= 300 and (a["ctr"] or 0) < MIN_CTR_AD and a["status"] == "ENABLED"
    ]
    if low_ctr_ads:
        worst = sorted(low_ctr_ads, key=lambda x: x["ctr"])[:3]
        findings.append({
            "priority": "MEDIUM", "category": "Reklamy",
            "title": f"Reklamy z bardzo niskim CTR ({len(low_ctr_ads)} reklam)",
            "desc": "Najsłabsze: " + ", ".join(f"{a['ad_group']} ({a['ctr']}%)" for a in worst),
            "action": (
                "Przejrzyj i przepisz nagłówki reklam. "
                "Skup się na benefitach, nie cechach. "
                "Użyj liczb (np. '-30%', 'Od 99 PLN', 'Dostawa w 24h')."
            ),
        })

    # ── 12. GRUPY REKLAM bez ruchu ────────────────────────────────────────────
    dead_groups = [
        ag for ag in ad_groups
        if (ag["impressions"] or 0) == 0 and ag["status"] == "ENABLED"
    ]
    if dead_groups:
        score -= 3
        findings.append({
            "priority": "LOW", "category": "Struktura",
            "title": f"Grupy reklam bez wyświetleń ({len(dead_groups)})",
            "desc": ", ".join(ag["ad_group"] for ag in dead_groups[:5]),
            "action": "Sprawdź czy grupy mają słowa kluczowe i aktywne reklamy. Wstrzymaj lub usuń martwe grupy.",
        })

    # ── 13. CPC vs BID ────────────────────────────────────────────────────────
    # Słowa gdzie avg CPC jest blisko lub powyżej bidu — sygnał że bid jest za niski
    for k in keywords:
        if k.get("cpc_bid") and k.get("cost") > 20:
            # Oblicz avg_cpc z kosztu i kliknięć
            if (k["clicks"] or 0) > 0:
                avg_cpc_kw = round(k["cost"] / k["clicks"], 2)
                if avg_cpc_kw > k["cpc_bid"] * 0.9:
                    findings.append({
                        "priority": "LOW", "category": "Stawki",
                        "title": f"Bid bliski limitu CPC: \"{k['keyword']}\"",
                        "desc": f"Avg CPC: {avg_cpc_kw} PLN, max bid: {k['cpc_bid']} PLN. Możliwe ograniczenie aukcji.",
                        "action": f"Rozważ zwiększenie bidu dla \"{k['keyword']}\" o 15–20% jeśli słowo konwertuje.",
                    })
                    break  # max 1 taki komunikat żeby nie zaśmiecać

    # ── POZYTYWNE ZNALEZISKA ──────────────────────────────────────────────────
    positives = []

    well_conv = [c for c in campaigns if (c["conversions"] or 0) > 5 and c.get("cpa") and (c["cpa"] or 0) > 0]
    if well_conv:
        best = min(well_conv, key=lambda x: x["cpa"])
        positives.append({
            "title": f"Najlepsza kampania: {best['name']}",
            "desc": f"CPA: {best['cpa']} PLN, konwersje: {best['conversions']}. Rozważ zwiększenie budżetu tej kampanii.",
        })

    high_qs = [k for k in keywords if k.get("qs") and k["qs"] >= 8]
    if high_qs:
        positives.append({
            "title": f"Świetny Quality Score ({len(high_qs)} słów kluczowych)",
            "desc": f"Słowa z QS 8–10: " + ", ".join(f'"{k["keyword"]}"' for k in high_qs[:4]) + ". Dobra robota.",
        })

    good_is = [c for c in campaigns if c.get("is") and (c["is"] or 0) >= 70]
    if good_is:
        positives.append({
            "title": f"Wysoki Impression Share ({len(good_is)} kampanii)",
            "desc": ", ".join(f"{c['name']}: {c['is']}%" for c in good_is[:3]),
        })

    # ── SCORE FINALNY ──────────────────────────────────────────────────────────
    score = max(0, min(100, score))
    if score >= 75:
        ocena = "dobra"
    elif score >= 50:
        ocena = "średnia"
    else:
        ocena = "zła"

    h = len([f for f in findings if f["priority"] == "HIGH"])
    m = len([f for f in findings if f["priority"] == "MEDIUM"])
    l = len([f for f in findings if f["priority"] == "LOW"])

    podsumowanie = (
        f"Audyt wykrył <strong>{h} problemów HIGH</strong>, {m} MEDIUM i {l} LOW. "
    )
    if h == 0 and m <= 2:
        podsumowanie += "Konto jest w dobrej kondycji — utrzymaj monitoring wykluczeń i QS."
    elif h >= 3:
        podsumowanie += "Konto wymaga pilnej interwencji — skup się najpierw na problemach HIGH."
    else:
        podsumowanie += "Wdroż najpierw wykluczenia i poprawki QS — największy ROI w krótkim czasie."

    return {
        "score":        score,
        "ocena":        ocena,
        "podsumowanie": podsumowanie,
        "findings":     findings,
        "positives":    positives,
        "excl_words":   excl_words,
    }

# ══════════════════════════════════════════════════════════════════════════════
# RENDER
# ══════════════════════════════════════════════════════════════════════════════
def render_audit(result: dict):
    score = result["score"]
    ocena = result["ocena"]
    findings  = result.get("findings", [])
    positives = result.get("positives", [])
    excl_words= result.get("excl_words", [])

    score_color = {"dobra": "#00e5a0", "średnia": "#ffb800", "zła": "#ff466b"}.get(ocena, "#ffb800")
    badge_kind  = {"dobra": "green",   "średnia": "yellow",  "zła": "red"}.get(ocena, "yellow")

    # Score header
    st.markdown(f"""
    <div class="score-ring">
        <div>
            <div style="font-size:0.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.15em;margin-bottom:4px;">Wynik konta</div>
            <div class="score-number" style="color:{score_color};">{score}</div>
            <div style="font-size:0.7rem;color:var(--muted);">/ 100 punktów</div>
        </div>
        <div style="flex:1;">
            <div style="margin-bottom:0.6rem;">
                <span class="badge badge-{badge_kind}" style="font-size:0.85rem;padding:5px 14px;">
                    {ocena.upper()}
                </span>
            </div>
            <div style="color:#a0a0c0;font-size:0.9rem;line-height:1.7;">{result["podsumowanie"]}</div>
        </div>
        <div style="text-align:right;min-width:140px;">
            <div style="margin-bottom:6px;"><span class="badge badge-red">HIGH &nbsp;{len([f for f in findings if f['priority']=='HIGH'])}</span></div>
            <div style="margin-bottom:6px;"><span class="badge badge-yellow">MEDIUM &nbsp;{len([f for f in findings if f['priority']=='MEDIUM'])}</span></div>
            <div><span class="badge badge-blue">LOW &nbsp;{len([f for f in findings if f['priority']=='LOW'])}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Tabs po kategorii
    categories = ["Wszystko", "Budżet", "Konwersje", "Quality Score", "Wykluczenia", "Słowa kluczowe", "Stawki", "Reklamy", "Struktura"]
    tabs = st.tabs(categories)

    priority_card = {"HIGH": "crit", "MEDIUM": "warn", "LOW": "info"}
    priority_badge= {"HIGH": "red",  "MEDIUM": "yellow", "LOW": "blue"}

    def render_finding(f):
        card_cls = priority_card.get(f["priority"], "warn")
        badge_cls= priority_badge.get(f["priority"], "yellow")
        st.markdown(f"""
        <div class="rec-card {card_cls}">
            <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.5rem;">
                <span class="badge badge-{badge_cls}">{f['priority']}</span>
                <div class="rec-title" style="margin:0;">{f['title']}</div>
            </div>
            <div class="rec-body">{f['desc']}</div>
            <div class="rec-action">▶ {f['action']}</div>
        </div>
        """, unsafe_allow_html=True)

    with tabs[0]:  # Wszystko
        high = [f for f in findings if f["priority"] == "HIGH"]
        mid  = [f for f in findings if f["priority"] == "MEDIUM"]
        low  = [f for f in findings if f["priority"] == "LOW"]
        if high:
            st.markdown('<div class="section-hdr">🔴 Krytyczne — napraw teraz</div>', unsafe_allow_html=True)
            for f in high: render_finding(f)
        if mid:
            st.markdown('<div class="section-hdr">🟡 Ważne — napraw w tym tygodniu</div>', unsafe_allow_html=True)
            for f in mid: render_finding(f)
        if low:
            st.markdown('<div class="section-hdr">🔵 Do rozważenia</div>', unsafe_allow_html=True)
            for f in low: render_finding(f)
        if not findings:
            st.success("Nie wykryto problemów — konto wygląda dobrze!")

    for i, cat in enumerate(categories[1:], 1):
        with tabs[i]:
            cat_findings = [f for f in findings if f["category"] == cat]
            if cat_findings:
                for f in cat_findings: render_finding(f)
            else:
                st.markdown(f'<div style="color:var(--muted);padding:1rem 0;">Brak problemów w kategorii <strong>{cat}</strong>.</div>', unsafe_allow_html=True)

    # Wykluczenia — osobny blok
    if excl_words:
        st.markdown('<div class="section-hdr">Frazy do natychmiastowego wykluczenia</div>', unsafe_allow_html=True)
        pills = "".join(f'<span class="excl-pill">✕ {w}</span>' for w in excl_words[:40])
        st.markdown(f'<div style="margin-bottom:1rem;">{pills}</div>', unsafe_allow_html=True)
        csv_excl = "\n".join(excl_words)
        st.download_button(
            "📥 Pobierz listę wykluczeń (.txt)",
            data=csv_excl.encode("utf-8"),
            file_name="wykluczenia.txt",
            mime="text/plain",
        )

    # Pozytywne
    if positives:
        st.markdown('<div class="section-hdr">Co działa dobrze ✓</div>', unsafe_allow_html=True)
        for p in positives:
            st.markdown(f"""
            <div class="rec-card ok">
                <div class="rec-title">✓ {p['title']}</div>
                <div class="rec-body">{p['desc']}</div>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def kpi_card(label, value, sub="", accent=False):
    vc = "kpi-value kpi-accent" if accent else "kpi-value"
    sh = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="{vc}">{value}</div>{sh}</div>', unsafe_allow_html=True)

def page_header(title, subtitle=""):
    st.markdown(f'<div class="page-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)

def section(title):
    st.markdown(f'<div class="section-hdr">{title}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
clients_df = load_clients()
today      = date.today()

with st.sidebar:
    st.markdown("---")
    st.caption(f"📅 {today.strftime('%d.%m.%Y')}")
    st.markdown("---")

    if clients_df.empty:
        st.warning("Brak klientów w bazie.")
        st.stop()

    ga_clients = clients_df[
        clients_df["google_ads_id"].astype(str).str.strip().ne("") &
        clients_df["google_ads_id"].notna()
    ]
    if ga_clients.empty:
        st.warning("Żaden klient nie ma Google Ads ID.")
        st.stop()

    sel_client = st.selectbox("Klient", ga_clients["nazwa"].tolist())
    st.markdown("**Zakres dat**")
    date_from = st.date_input("Od", value=today - timedelta(days=30))
    date_to   = st.date_input("Do", value=today)
    st.markdown("---")
    run_btn = st.button("🔍 Uruchom audyt", use_container_width=True, type="primary")

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
page_header("Ads Analyzer", "Pełny audyt konta Google Ads")

if not run_btn:
    client_row = ga_clients[ga_clients["nazwa"] == sel_client].iloc[0]
    g_id = str(client_row.get("google_ads_id","")).strip()
    st.markdown(f"""
    <div class="analyze-box">
        <div style="font-family:'Bebas Neue',sans-serif;font-size:2.5rem;color:var(--white);margin-bottom:0.5rem;">{sel_client}</div>
        <div style="color:var(--muted);font-size:0.8rem;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:1.2rem;">
            Google Ads ID: {g_id} &nbsp;·&nbsp; {date_from.strftime("%d.%m.%Y")} — {date_to.strftime("%d.%m.%Y")}
        </div>
        <div style="color:#8090ff;font-size:0.9rem;">Kliknij <strong style="color:var(--white);">Uruchom audyt</strong> w menu bocznym.</div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:1rem;">
        <div class="kpi"><div class="kpi-label">Sprawdzam</div><div class="kpi-value" style="font-size:1rem;color:#8090ff;">Budżety</div><div class="kpi-sub">ograniczenia, IS budget</div></div>
        <div class="kpi"><div class="kpi-label">Sprawdzam</div><div class="kpi-value" style="font-size:1rem;color:#8090ff;">Konwersje</div><div class="kpi-sub">CPA, ROAS, zero-conv</div></div>
        <div class="kpi"><div class="kpi-label">Sprawdzam</div><div class="kpi-value" style="font-size:1rem;color:#8090ff;">Quality Score</div><div class="kpi-sub">QS, qs_lp, qs_ad</div></div>
        <div class="kpi"><div class="kpi-label">Sprawdzam</div><div class="kpi-value" style="font-size:1rem;color:#8090ff;">Wykluczenia</div><div class="kpi-sub">search terms bez konwersji</div></div>
        <div class="kpi"><div class="kpi-label">Sprawdzam</div><div class="kpi-value" style="font-size:1rem;color:#8090ff;">Stawki</div><div class="kpi-sub">IS rank, CPC bid, broad</div></div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── RUN ───────────────────────────────────────────────────────────────────────
client_row = ga_clients[ga_clients["nazwa"] == sel_client].iloc[0]
g_id   = str(client_row["google_ads_id"]).strip()
mcc_id = str(client_row.get("mcc_id", "")).strip()

with st.status("Pobieranie danych z Google Ads...", expanded=True) as status:
    try:
        ga_client = get_ga_client(g_id, mcc_id)

        st.write("📊 Kampanie + budżety...")
        campaigns = fetch_campaigns(ga_client, g_id, str(date_from), str(date_to))
        st.write(f"   ✓ {len(campaigns)} kampanii")

        st.write("🔑 Słowa kluczowe + Quality Score...")
        keywords = fetch_keywords(ga_client, g_id, str(date_from), str(date_to))
        st.write(f"   ✓ {len(keywords)} słów kluczowych")

        st.write("🔍 Search terms...")
        search_terms = fetch_search_terms(ga_client, g_id, str(date_from), str(date_to))
        st.write(f"   ✓ {len(search_terms)} fraz")

        st.write("📢 Reklamy...")
        ads = fetch_ads(ga_client, g_id, str(date_from), str(date_to))
        st.write(f"   ✓ {len(ads)} reklam")

        st.write("📁 Grupy reklam...")
        ad_groups = fetch_ad_groups(ga_client, g_id, str(date_from), str(date_to))
        st.write(f"   ✓ {len(ad_groups)} grup")

        st.write("🧠 Analiza ekspercka...")
        result = run_full_audit({
            "campaigns":    campaigns,
            "keywords":     keywords,
            "search_terms": search_terms,
            "ads":          ads,
            "ad_groups":    ad_groups,
        })

        status.update(label=f"Audyt gotowy — wynik: {result['score']}/100", state="complete", expanded=False)

    except Exception as e:
        status.update(label=f"Błąd: {e}", state="error")
        st.exception(e)
        st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────────
if campaigns:
    total_cost  = sum(c["cost"] for c in campaigns)
    total_conv  = sum(c["conversions"] for c in campaigns)
    total_clicks= sum(c["clicks"] for c in campaigns)
    avg_cpa     = round(total_cost / total_conv, 2) if total_conv > 0 else 0
    waste_cost  = sum(t["cost"] for t in search_terms if (t["conversions"] or 0) == 0 and (t["cost"] or 0) >= 15)
    total_roas  = round(sum(c["conv_value"] for c in campaigns) / total_cost, 2) if total_cost > 0 else 0

    section("Podsumowanie okresu")
    cols = st.columns(6)
    with cols[0]: kpi_card("Koszt",       f"{total_cost:.0f} PLN")
    with cols[1]: kpi_card("Konwersje",   f"{total_conv:.0f}", f"CPA śr: {avg_cpa:.0f} PLN")
    with cols[2]: kpi_card("ROAS",        f"{total_roas:.2f}",  "wartość / koszt")
    with cols[3]: kpi_card("Kliknięcia",  f"{total_clicks:,}")
    with cols[4]: kpi_card("Kampanie",    str(len(campaigns)))
    with cols[5]: kpi_card("Przepalone",  f"{waste_cost:.0f} PLN", "search terms 0 konwersji", accent=True)

# ── AUDIT RESULTS ─────────────────────────────────────────────────────────────
section("Wyniki audytu")
render_audit(result)

# ── RAW DATA ──────────────────────────────────────────────────────────────────
with st.expander("📋 Dane surowe — kampanie"):
    if campaigns:
        st.dataframe(pd.DataFrame(campaigns), use_container_width=True, hide_index=True)

with st.expander("🔑 Dane surowe — słowa kluczowe"):
    if keywords:
        st.dataframe(pd.DataFrame(keywords), use_container_width=True, hide_index=True)

with st.expander("🔍 Search terms (wszystkie)"):
    if search_terms:
        df_st = pd.DataFrame(search_terms).sort_values("cost", ascending=False)
        st.dataframe(df_st, use_container_width=True, hide_index=True)
