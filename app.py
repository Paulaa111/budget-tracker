import streamlit as st
import pandas as pd
from datetime import date
import calendar
import base64
from pathlib import Path
import re

import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Ermon. | Budget Tracker", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

VAT_RATE  = 0.23
SHEET_ID  = "1l_fX5ydioIsKVyhitrnR3rcdf6RyZOq-x6oQ3mhP9uQ"
SCOPES    = ["https://www.googleapis.com/auth/spreadsheets"]

@st.cache_resource
def get_gsheet():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
    return gspread.authorize(creds).open_by_key(SHEET_ID)

def load_clients():
    try:
        ws = get_gsheet().worksheet("klienci")
        data = ws.get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame(columns=["nazwa","google_ads_id","meta_ads_id","typ_kwoty"])
    except Exception as e:
        st.error(f"Błąd odczytu klientów: {e}")
        return pd.DataFrame(columns=["nazwa","google_ads_id","meta_ads_id","typ_kwoty"])

def load_budgets():
    try:
        ws = get_gsheet().worksheet("budzety")
        data = ws.get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame(columns=["klient","miesiac","budzet_total"])
    except Exception as e:
        st.error(f"Błąd odczytu budżetów: {e}")
        return pd.DataFrame(columns=["klient","miesiac","budzet_total"])

def save_client(nazwa, google_id, meta_id, typ, mcc_id=""):
    get_gsheet().worksheet("klienci").append_row([nazwa, google_id, meta_id, typ, mcc_id])

def save_budget(klient, miesiac, budzet_total):
    ws = get_gsheet().worksheet("budzety")
    all_rows = ws.get_all_records()
    for i, row in enumerate(all_rows):
        if row["klient"] == klient and row["miesiac"] == miesiac:
            ws.update(f"A{i+2}:C{i+2}", [[klient, miesiac, budzet_total]])
            return
    ws.append_row([klient, miesiac, budzet_total])

def save_spend(klient, miesiac, google_spend, meta_spend):
    try:
        g_val = round(float(google_spend), 2)
        f_val = round(float(meta_spend), 2)
        ws = get_gsheet().worksheet("wydatki")
        all_rows = ws.get_all_records()
        for i, row in enumerate(all_rows):
            if row["klient"] == klient and row["miesiac"] == miesiac:
                ws.update(f"A{i+2}:D{i+2}", [[klient, miesiac, g_val, f_val]], value_input_option="RAW")
                return
        ws.append_row([klient, miesiac, g_val, f_val], value_input_option="RAW")
    except Exception as e:
        st.error(f"Błąd zapisu wydatków: {e}")

def load_spend():
    try:
        ws = get_gsheet().worksheet("wydatki")
        data = ws.get_all_records()
        if not data:
            return pd.DataFrame(columns=["klient","miesiac","google_spend","meta_spend"])
        df = pd.DataFrame(data)
        def clean_value(val, divide_by_100=False):
            if isinstance(val, (int, float)):
                result = float(val)
                if divide_by_100:
                    result = result / 100
                return round(result, 2)
            s = str(val).strip()
            s = s.replace('\xa0', '').replace('\u00a0', '').replace(' ', '')
            if '.' in s and ',' in s:
                s = s.replace(',', '')
            elif ',' in s and '.' not in s:
                s = s.replace(',', '.')
            s = re.sub(r'[^0-9.]', '', s)
            try:
                result = float(s)
                if divide_by_100:
                    result = result / 100
                return round(result, 2)
            except:
                return 0.0
        df["google_spend"] = df["google_spend"].apply(lambda x: clean_value(x, divide_by_100=False))
        df["meta_spend"]   = df["meta_spend"].apply(lambda x: clean_value(x, divide_by_100=False))
        return df
    except Exception as e:
        st.error(f"Błąd ładowania wydatków: {e}")
        return pd.DataFrame(columns=["klient","miesiac","google_spend","meta_spend"])

def delete_client(nazwa):
    ws = get_gsheet().worksheet("klienci")
    cell = ws.find(nazwa)
    if cell:
        ws.delete_rows(cell.row)

def days_remaining(year, month):
    today = date.today()
    last  = calendar.monthrange(year, month)[1]
    end   = date(year, month, last)
    if today.year == year and today.month == month:
        return max(0, (end - today).days + 1)
    if date(year, month, 1) > today:
        return last
    return 0

def gross(net):
    return round(net * (1 + VAT_RATE), 2)

def netto(gross_val):
    return round(gross_val / (1 + VAT_RATE), 2)

def get_logo_base64():
    logo_path = Path(__file__).parent / "logo.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

LOGO_B64 = get_logo_base64()

# ── DESIGN SYSTEM ─────────────────────────────────────────────────────────────
# Brand: #2c016d (deep violet), #ff466b (coral red), #3337bd (electric blue)
# Aesthetic: Dark luxury editorial — high contrast, sharp typography, confident spacing

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
}}

html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg);
    color: var(--text);
}}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {{
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}}
section[data-testid="stSidebar"] > div {{
    padding: 0 !important;
}}
.sidebar-logo {{
    padding: 2rem 1.5rem 1.5rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 0.5rem;
}}
.sidebar-logo img {{
    width: 110px;
    filter: brightness(0) invert(1);
}}
.sidebar-tagline {{
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    color: var(--muted);
    text-transform: uppercase;
    margin-top: 8px;
    font-family: 'DM Sans', sans-serif;
}}
section[data-testid="stSidebar"] .stRadio {{
    padding: 0 1rem;
}}
section[data-testid="stSidebar"] .stRadio label {{
    font-family: 'DM Sans', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
    color: var(--muted) !important;
    padding: 0.75rem 1rem !important;
    border-radius: 8px !important;
    margin: 2px 0 !important;
    transition: all 0.2s !important;
    display: block !important;
    letter-spacing: 0.02em !important;
}}
section[data-testid="stSidebar"] .stRadio label:hover {{
    color: var(--white) !important;
    background: rgba(255,70,107,0.08) !important;
}}
section[data-testid="stSidebar"] .stRadio [data-checked="true"] label,
section[data-testid="stSidebar"] .stRadio label[aria-checked="true"] {{
    color: var(--white) !important;
    background: linear-gradient(135deg, rgba(44,1,109,0.6), rgba(51,55,189,0.3)) !important;
    border-left: 3px solid var(--coral) !important;
}}

/* ── MAIN ── */
.main .block-container {{
    padding: 2.5rem 3rem;
    max-width: 1700px;
}}

/* ── PAGE HEADER ── */
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

/* ── SECTION HEADER ── */
.section-hdr {{
    font-family: 'DM Sans', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--muted);
    letter-spacing: 0.18em;
    text-transform: uppercase;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.6rem;
    margin: 2.5rem 0 1.5rem;
}}

/* ── KPI CARDS ── */
.kpi {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.5rem 1.8rem;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s, border-color 0.2s;
    margin-bottom: 1rem;
}}
.kpi::after {{
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--violet), var(--coral));
    opacity: 0;
    transition: opacity 0.3s;
}}
.kpi:hover {{ transform: translateY(-3px); border-color: var(--blue); }}
.kpi:hover::after {{ opacity: 1; }}
.kpi-label {{
    font-size: 0.65rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.6rem;
    font-family: 'DM Sans', sans-serif;
}}
.kpi-value {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2rem;
    color: var(--white);
    line-height: 1;
    letter-spacing: 0.04em;
}}
.kpi-accent {{ color: var(--coral); }}
.kpi-sub {{
    font-size: 0.7rem;
    color: var(--muted);
    margin-top: 0.4rem;
    font-family: 'DM Sans', sans-serif;
}}

/* ── BUTTONS ── */
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

/* ── INPUTS ── */
.stTextInput input, .stNumberInput input, .stSelectbox > div > div {{
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
}}

/* ── MISC ── */
hr {{ border-color: var(--border) !important; }}
#MainMenu, footer, header {{ visibility: hidden; }}
.stDataFrame {{ font-size: 15px !important; }}
</style>

<div class="sidebar-logo">
    {"<img src='data:image/png;base64," + LOGO_B64 + "' />" if LOGO_B64 else "<span style='font-family:Bebas Neue,sans-serif;font-size:1.8rem;color:#fff;letter-spacing:0.05em;'>Ermon.</span>"}
    <div class="sidebar-tagline">Budget Tracker</div>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
menu_map = {
    "Dashboard":    "Dashboard",
    "Klienci":      "Klienci",
    "Budżety":      "Budżety",
    "Pobierz z API":"Pobierz",
    "Ustawienia":   "Ustawienia",
    "PMax": "PMax",
}

with st.sidebar:
    selection = st.radio("", list(menu_map.keys()), label_visibility="collapsed")
    page = menu_map[selection]
    st.markdown("---")
    today = date.today()
    st.caption(f"📅 {today.strftime('%d.%m.%Y')}")

# ── HELPERS ───────────────────────────────────────────────────────────────────
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
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "Dashboard":
    page_header("Dashboard", "Przegląd budżetów reklamowych")
    clients_df = load_clients()
    budgets_df = load_budgets()
    spend_df   = load_spend()

    if clients_df.empty:
        st.info("Brak danych. Dodaj klientów w zakładce Klienci.")
        st.stop()

    cy, cm, _, _ = st.columns([1,1,1,2])
    sel_year  = cy.selectbox("Rok",  [today.year-1, today.year, today.year+1], index=1, key="dy")
    sel_month = cm.selectbox("Miesiąc", range(1,13), index=today.month-1,
                             format_func=lambda m: calendar.month_abbr[m], key="dm")
    period    = f"{sel_year}-{sel_month:02d}"
    days_left = days_remaining(sel_year, sel_month)

    groups = {}
    for _, client in clients_df.iterrows():
        cname = client["nazwa"]
        grupa = str(client.get("grupa", cname)).strip() or cname
        gm    = str(client.get("typ_kwoty","netto")).lower() == "brutto"
        spnd_row = spend_df[(spend_df["klient"]==cname) & (spend_df["miesiac"]==period)]
        g_sn  = float(spnd_row["google_spend"].values[0]) if not spnd_row.empty else 0.0
        fb_sn = float(spnd_row["meta_spend"].values[0])   if not spnd_row.empty else 0.0
        if grupa not in groups:
            groups[grupa] = {"g_sn": 0.0, "fb_sn": 0.0, "gm": gm}
        groups[grupa]["g_sn"]  += g_sn
        groups[grupa]["fb_sn"] += fb_sn

    rows = []
    for grupa, gdata in groups.items():
        bud_row = budgets_df[(budgets_df["klient"]==grupa) & (budgets_df["miesiac"]==period)]
        total_r = float(bud_row["budzet_total"].values[0]) if not bud_row.empty else 0.0
        total_n = netto(total_r) if gdata["gm"] else total_r
        g_sn    = round(gdata["g_sn"], 2)
        fb_sn   = round(gdata["fb_sn"], 2)
        tot_sn  = round(g_sn + fb_sn, 2)
        rem_n   = max(0, total_n - tot_sn)
        daily   = round(rem_n/days_left, 2) if days_left > 0 else 0
        pct     = round(tot_sn/total_n*100, 1) if total_n > 0 else 0
        rows.append(dict(
            cname=grupa,
            total_n=round(total_n,2), total_g=round(gross(total_n),2),
            g_sn=g_sn, g_sg=round(gross(g_sn),2),
            fb_sn=fb_sn, fb_sg=round(gross(fb_sn),2),
            tot_sn=tot_sn, tot_sg=round(gross(tot_sn),2),
            rem_n=round(rem_n,2), rem_g=round(gross(rem_n),2),
            daily=round(daily,2), pct=round(pct,1)
        ))

    sum_bud   = sum(r["total_n"] for r in rows)
    sum_spent = sum(r["tot_sn"]  for r in rows)
    sum_rem   = sum_bud - sum_spent
    sum_daily = round(sum_rem/days_left, 2) if days_left > 0 else 0

    # ── TABELA ──
    section("Tabela zbiorcza")
    html_rows = ""
    for i, r in enumerate(rows):
        bg = "#13132a" if i % 2 == 0 else "#0f0f22"
        pct_color = "#00e5a0" if r['pct'] < 75 else ("#ffb800" if r['pct'] < 95 else "#ff466b")
        html_rows += f"""
        <tr style="background:{bg};border-bottom:1px solid #2a2a50;">
            <td style="padding:22px 24px;font-weight:600;color:#ffffff;border-right:1px solid #2a2a50;font-size:17px;">{r['cname']}</td>
            <td style="padding:22px 24px;text-align:right;border-right:1px solid #2a2a50;font-size:17px;">{r['total_n']:.0f} zł</td>
            <td style="padding:22px 24px;text-align:right;border-right:1px solid #2a2a50;color:#6060a0;font-size:17px;">{r['total_g']:.0f} zł</td>
            <td style="padding:22px 24px;text-align:right;border-right:1px solid #2a2a50;color:#5b8af5;font-size:17px;">{r['g_sn']:.0f} zł</td>
            <td style="padding:22px 24px;text-align:right;border-right:1px solid #2a2a50;color:#4a6fd4;font-size:17px;">{r['fb_sn']:.0f} zł</td>
            <td style="padding:22px 24px;text-align:right;border-right:1px solid #2a2a50;font-weight:600;font-size:17px;">{r['tot_sn']:.0f} zł</td>
            <td style="padding:22px 24px;text-align:right;border-right:1px solid #2a2a50;color:#6060a0;font-size:17px;">{r['tot_sg']:.0f} zł</td>
            <td style="padding:22px 24px;text-align:right;border-right:1px solid #2a2a50;color:#a080ff;font-weight:600;font-size:17px;">{r['rem_n']:.0f} zł</td>
            <td style="padding:22px 24px;text-align:right;border-right:1px solid #2a2a50;color:#a080ff;font-weight:600;font-size:17px;">{r['daily']:.0f} zł</td>
            <td style="padding:22px 24px;text-align:right;color:{pct_color};font-weight:700;font-size:17px;font-family:'Bebas Neue',sans-serif;letter-spacing:0.05em;">{r['pct']:.0f}%</td>
        </tr>"""

    st.html(f"""
    <style>@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;500;600&display=swap');</style>
    <div style="border-radius:16px;overflow:hidden;border:1px solid #2a2a50;box-shadow:0 8px 32px rgba(0,0,0,0.4);">
    <table style="width:100%;border-collapse:collapse;font-family:'DM Sans',sans-serif;">
        <thead>
            <tr style="background:linear-gradient(135deg,#2c016d,#3337bd);color:rgba(255,255,255,0.7);font-size:11px;letter-spacing:0.18em;text-transform:uppercase;">
                <th style="padding:18px 24px;text-align:left;border-bottom:1px solid rgba(255,255,255,0.1);">Klient</th>
                <th style="padding:18px 24px;text-align:right;border-bottom:1px solid rgba(255,255,255,0.1);">Budżet netto</th>
                <th style="padding:18px 24px;text-align:right;border-bottom:1px solid rgba(255,255,255,0.1);">Budżet brutto</th>
                <th style="padding:18px 24px;text-align:right;border-bottom:1px solid rgba(255,255,255,0.1);">Google</th>
                <th style="padding:18px 24px;text-align:right;border-bottom:1px solid rgba(255,255,255,0.1);">Meta</th>
                <th style="padding:18px 24px;text-align:right;border-bottom:1px solid rgba(255,255,255,0.1);">Razem netto</th>
                <th style="padding:18px 24px;text-align:right;border-bottom:1px solid rgba(255,255,255,0.1);">Razem brutto</th>
                <th style="padding:18px 24px;text-align:right;border-bottom:1px solid rgba(255,255,255,0.1);color:#c0a0ff;">Pozostało</th>
                <th style="padding:18px 24px;text-align:right;border-bottom:1px solid rgba(255,255,255,0.1);color:#c0a0ff;">Max dziennie</th>
                <th style="padding:18px 24px;text-align:right;border-bottom:1px solid rgba(255,255,255,0.1);color:#ff9090;">% budżetu</th>
            </tr>
        </thead>
        <tbody>{html_rows}</tbody>
    </table>
    </div>
    """)

    st.markdown("<br>", unsafe_allow_html=True)
    csv = pd.DataFrame([{
        "Klient": r["cname"], "Budżet netto": r["total_n"],
        "Google wydano": r["g_sn"], "Meta wydano": r["fb_sn"],
        "Razem wydano": r["tot_sn"], "Pozostało": r["rem_n"],
        "Max dziennie": r["daily"], "% budżetu": r["pct"],
    } for r in rows]).to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
    st.download_button("Pobierz CSV", csv, file_name=f"ermon_budgety_{period}.csv", mime="text/csv")

    # ── KPI ──
    section("Podsumowanie")
    k1,k2,k3,k4,k5 = st.columns(5)
    with k1: kpi_card("Łączny budżet",  f"{sum_bud:.0f} zł",   "netto")
    with k2: kpi_card("Łącznie wydano", f"{sum_spent:.0f} zł", f"brutto: {gross(sum_spent):.0f} zł")
    with k3: kpi_card("Pozostało",      f"{sum_rem:.0f} zł",   "netto", accent=True)
    with k4: kpi_card("Max dziennie",   f"{sum_daily:.0f} zł", f"na {days_left} dni")
    with k5: kpi_card("Klientów",       str(len(rows)),        f"{calendar.month_name[sel_month]} {sel_year}")

    # ── WYKRESY ──
    import plotly.express as px
    import plotly.graph_objects as go

    section("Wykresy")
    col_chart1, col_chart2 = st.columns(2)
    df_chart = pd.DataFrame([{"Klient":r["cname"],"Google":r["g_sn"],"Meta":r["fb_sn"],"Budżet":r["total_n"]} for r in rows])

    with col_chart1:
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(name="Google", x=df_chart["Klient"], y=df_chart["Google"], marker_color="#3337bd"))
        fig1.add_trace(go.Bar(name="Meta",   x=df_chart["Klient"], y=df_chart["Meta"],   marker_color="#ff466b"))
        fig1.add_trace(go.Scatter(name="Budżet", x=df_chart["Klient"], y=df_chart["Budżet"],
                                  mode="markers", marker=dict(color="#ffffff", size=10, symbol="line-ew-open", line=dict(width=3))))
        fig1.update_layout(title="Wydatki vs Budżet", barmode="stack",
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font=dict(color="#a0a0c0", family="DM Sans"),
                           legend=dict(bgcolor="rgba(0,0,0,0)"),
                           xaxis=dict(gridcolor="#1e1e3a"), yaxis=dict(gridcolor="#1e1e3a"), height=380)
        st.plotly_chart(fig1, use_container_width=True)

    with col_chart2:
        df_pie = pd.DataFrame([{"Klient":r["cname"],"Wydano":r["tot_sn"]} for r in rows if r["tot_sn"]>0])
        if not df_pie.empty:
            fig2 = px.pie(df_pie, names="Klient", values="Wydano", title="Podział wydatków",
                          color_discrete_sequence=["#2c016d","#3337bd","#ff466b","#7040d0","#ff8099"])
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#a0a0c0", family="DM Sans"), height=380)
            st.plotly_chart(fig2, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# ZAKŁADKA PMAX — wklej do app.py jako nowy elif
# ══════════════════════════════════════════════════════════════════════════════

# 1. W menu_map dodaj:
# "PMax": "PMax",

# 2. Dodaj nową pozycję w menu:
# "PMax Breakdown": "PMax",

# 3. Wklej poniższy elif po sekcji Dashboard

elif page == "PMax":
    page_header("PMax Breakdown", "Podział wydatków kampanii Performance Max")

    clients_df = load_clients()
    if clients_df.empty:
        st.info("Brak klientów.")
        st.stop()

    # filtruj tylko klientów z PMax
    pmax_clients = clients_df[clients_df.get("has_pmax", pd.Series(dtype=str)).astype(str).str.lower() == "tak"]
    
    if "has_pmax" in clients_df.columns:
        pmax_clients = clients_df[clients_df["has_pmax"].astype(str).str.lower() == "tak"]
    else:
        st.warning("Brak kolumny 'has_pmax' w arkuszu klienci.")
        st.stop()

    if pmax_clients.empty:
        st.info("Brak klientów z PMax. Dodaj kolumnę 'has_pmax' w arkuszu klienci.")
        st.stop()

    c1, c2 = st.columns(2)
    sel_year3  = c1.selectbox("Rok",  [today.year-1, today.year, today.year+1], index=1, key="py")
    sel_month3 = c2.selectbox("Miesiąc", range(1,13), index=today.month-1,
                              format_func=lambda m: calendar.month_name[m], key="pm")
    period3   = f"{sel_year3}-{sel_month3:02d}"

    if st.button("Pobierz dane PMax", use_container_width=True, type="primary"):
        from google.ads.googleads.client import GoogleAdsClient
        from google.ads.googleads.errors import GoogleAdsException
        import calendar as cal

        ga_base_config = {
            "developer_token": st.secrets["google_ads"]["GOOGLE_ADS_DEVELOPER_TOKEN"],
            "client_id":       st.secrets["google_ads"]["GOOGLE_ADS_CLIENT_ID"],
            "client_secret":   st.secrets["google_ads"]["GOOGLE_ADS_CLIENT_SECRET"],
            "refresh_token":   st.secrets["google_ads"]["GOOGLE_ADS_REFRESH_TOKEN"],
            "use_proto_plus":  True,
        }

        last_day  = cal.monthrange(sel_year3, sel_month3)[1]
        date_from = f"{sel_year3}-{sel_month3:02d}-01"
        date_to   = f"{sel_year3}-{sel_month3:02d}-{last_day:02d}"

        all_results = []
        progress = st.progress(0)

        for i, (_, client) in enumerate(pmax_clients.iterrows()):
            cname = client["nazwa"]
            g_id  = str(client.get("google_ads_id","")).strip()
            grupa = str(client.get("grupa", cname)).strip() or cname

            if not g_id:
                continue

            try:
                mcc = str(client.get("mcc_id","")).strip()
                ga_config = ga_base_config.copy()
                if mcc:
                    ga_config["login_customer_id"] = mcc
                elif "GOOGLE_ADS_LOGIN_CUSTOMER_ID" in st.secrets["google_ads"]:
                    ga_config["login_customer_id"] = st.secrets["google_ads"]["GOOGLE_ADS_LOGIN_CUSTOMER_ID"]

                ga_client  = GoogleAdsClient.load_from_dict(ga_config)
                ga_service = ga_client.get_service("GoogleAdsService")

                # Zapytanie o podział PMax na kanały
                query = f"""
                    SELECT
                        campaign.name,
                        segments.date,
                        segments.ad_network_type,
                        metrics.cost_micros,
                        metrics.impressions,
                        metrics.clicks
                    FROM campaign
                    WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
                    AND segments.date BETWEEN '{date_from}' AND '{date_to}'
                    AND metrics.cost_micros > 0
                """

                response = ga_service.search_stream(
                    customer_id=g_id.replace("-",""), query=query)

                for batch in response:
                    for row in batch.results:
                        network = str(row.segments.ad_network_type).replace("AdNetworkType.", "")
                        cost    = round(row.metrics.cost_micros / 1_000_000, 2)
                        all_results.append({
                            "Klient":    grupa,
                            "Kampania":  row.campaign.name,
                            "Kanał":     network,
                            "Koszt":     cost,
                            "Kliknięcia": row.metrics.clicks,
                            "Wyświetlenia": row.metrics.impressions,
                        })

            except GoogleAdsException as e:
                st.warning(f"{cname}: {e.error.code().name}")
            except Exception as e:
                st.warning(f"{cname}: {str(e)[:80]}")

            progress.progress((i+1)/len(pmax_clients))

        if not all_results:
            st.warning("Brak danych PMax dla wybranego okresu.")
            st.stop()

        df_pmax = pd.DataFrame(all_results)

        # mapowanie nazw kanałów na polskie
        channel_map = {
            "SEARCH":          "Wyszukiwarka",
            "DISPLAY":         "Sieć reklamowa",
            "YOUTUBE_WATCH":   "YouTube",
            "YOUTUBE_SEARCH":  "YouTube Search",
            "MIXED":           "Mixed",
            "UNKNOWN":         "Inne",
            "UNSPECIFIED":     "Inne",
            "2":               "Wyszukiwarka",
            "3":               "Sieć reklamowa",
            "4":               "Sieć reklamowa",
            "8":               "YouTube",
            "12":              "Discover / Gmail / Maps",
            "16":              "Wyszukiwarka",
        }
        df_pmax["Kanał"] = df_pmax["Kanał"].map(channel_map).fillna(df_pmax["Kanał"])

        # zapisz w session state
        st.session_state["pmax_data"]   = df_pmax
        st.session_state["pmax_period"] = period3

    # wyświetl dane jeśli są w session state
    if "pmax_data" in st.session_state and st.session_state.get("pmax_period") == period3:
        df_pmax = st.session_state["pmax_data"]

        st.success(f"Dane za {calendar.month_name[sel_month3]} {sel_year3}")

        # ── tabela zbiorcza per klient + kanał
        section("Podział wydatków per klient i kanał")
        df_grouped = df_pmax.groupby(["Klient","Kanał"])["Koszt"].sum().reset_index()
        df_grouped["Koszt"] = df_grouped["Koszt"].round(0).astype(int)
        df_pivot = df_grouped.pivot_table(
            index="Klient", columns="Kanał", values="Koszt", fill_value=0
        ).reset_index()
        df_pivot["RAZEM"] = df_pivot.select_dtypes("number").sum(axis=1)

        html_rows = ""
        cols = [c for c in df_pivot.columns if c != "Klient"]
        for i, row in df_pivot.iterrows():
            bg = "#13132a" if i % 2 == 0 else "#0f0f22"
            cells = f'<td style="padding:18px 20px;font-weight:600;color:#fff;border-right:1px solid #2a2a50;">{row["Klient"]}</td>'
            for col in cols:
                color = "#a080ff" if col == "RAZEM" else "#e8e8f5"
                fw    = "700" if col == "RAZEM" else "400"
                val   = row.get(col, 0)
                cells += f'<td style="padding:18px 20px;text-align:right;border-right:1px solid #2a2a50;color:{color};font-weight:{fw};">{val} zł</td>'
            html_rows += f'<tr style="background:{bg};border-bottom:1px solid #2a2a50;">{cells}</tr>'

        header_cols = "".join([
            f'<th style="padding:16px 20px;text-align:{"left" if c=="Klient" else "right"};border-bottom:1px solid rgba(255,255,255,0.1);">{c}</th>'
            for c in ["Klient"] + cols
        ])

        st.html(f"""
        <div style="border-radius:16px;overflow:hidden;border:1px solid #2a2a50;box-shadow:0 8px 32px rgba(0,0,0,0.4);">
        <table style="width:100%;border-collapse:collapse;font-family:'DM Sans',sans-serif;font-size:16px;">
            <thead>
                <tr style="background:linear-gradient(135deg,#2c016d,#3337bd);color:rgba(255,255,255,0.7);font-size:11px;letter-spacing:0.18em;text-transform:uppercase;">
                    {header_cols}
                </tr>
            </thead>
            <tbody>{html_rows}</tbody>
        </table>
        </div>
        """)

        # ── szczegóły kampanii
        section("Szczegóły kampanii")
        import plotly.express as px

        df_camp = df_pmax.groupby(["Klient","Kampania","Kanał"])["Koszt"].sum().reset_index()
        df_camp["Koszt"] = df_camp["Koszt"].round(0).astype(int)

        sel_klient = st.selectbox("Wybierz klienta", df_pmax["Klient"].unique().tolist())
        df_filtered = df_camp[df_camp["Klient"] == sel_klient]

        if not df_filtered.empty:
            fig = px.bar(df_filtered, x="Kampania", y="Koszt", color="Kanał",
                         barmode="stack",
                         color_discrete_sequence=["#2c016d","#3337bd","#ff466b","#7040d0","#ff8099"],
                         title=f"Wydatki PMax — {sel_klient}")
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#a0a0c0", family="DM Sans"),
                legend=dict(bgcolor="rgba(0,0,0,0)"),
                xaxis=dict(gridcolor="#1e1e3a"),
                yaxis=dict(gridcolor="#1e1e3a"),
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)

        # ── eksport
        csv_pmax = df_pmax.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
        st.download_button("Pobierz CSV", csv_pmax,
                           file_name=f"ermon_pmax_{period3}.csv", mime="text/csv")
    else:
        st.info("Kliknij 'Pobierz dane PMax' aby załadować dane.")

# ══════════════════════════════════════════════════════════════════════════════
# KLIENCI
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Klienci":
    page_header("Klienci", "Zarządzanie bazą klientów")
    col1, col2 = st.columns([1,2])
    with col1:
        section("Dodaj klienta")
        with st.form("add_client"):
            name   = st.text_input("Nazwa klienta")
            g_id   = st.text_input("Google Ads Customer ID", placeholder="123-456-7890")
            mcc_id = st.text_input("MCC ID (konto menedżera)", placeholder="1234567890")
            fb_id  = st.text_input("Meta Ads Account ID", placeholder="act_123456789")
            typ    = st.selectbox("Typ kwoty budżetu", ["netto","brutto"])
            submit = st.form_submit_button("Dodaj klienta", use_container_width=True)
        if submit and name.strip():
            save_client(name.strip(), g_id.strip(), fb_id.strip(), typ, mcc_id.strip())
            st.cache_resource.clear()
            st.success(f"Dodano: **{name.strip()}**")
            st.rerun()
    with col2:
        section("Lista klientów")
        clients_df = load_clients()
        if clients_df.empty:
            st.info("Brak klientów.")
        else:
            for _, row in clients_df.iterrows():
                with st.expander(f"{row['nazwa']}"):
                    c1,c2,c3 = st.columns(3)
                    c1.write(f"**Google Ads:** {row.get('google_ads_id') or '—'}")
                    c2.write(f"**Meta Ads:** {row.get('meta_ads_id') or '—'}")
                    c3.write(f"**Typ kwoty:** {row.get('typ_kwoty','netto')}")
                    if st.button("Usuń", key=f"del_{row['nazwa']}"):
                        delete_client(row['nazwa'])
                        st.cache_resource.clear()
                        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# BUDŻETY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Budżety":
    page_header("Budżety", "Ustawianie budżetów miesięcznych")
    clients_df = load_clients()
    if clients_df.empty:
        st.warning("Najpierw dodaj klientów.")
        st.stop()
    sel_client = st.selectbox("Klient / Grupa", clients_df["nazwa"].tolist())
    c1,c2 = st.columns(2)
    sel_year  = c1.selectbox("Rok",  [today.year-1,today.year,today.year+1], index=1)
    sel_month = c2.selectbox("Miesiąc", range(1,13), index=today.month-1,
                             format_func=lambda m: calendar.month_name[m])
    period = f"{sel_year}-{sel_month:02d}"
    budgets_df  = load_budgets()
    existing    = budgets_df[(budgets_df["klient"]==sel_client) & (budgets_df["miesiac"]==period)]
    current_val = float(existing["budzet_total"].values[0]) if not existing.empty else 0.0
    section(f"Budżet — {calendar.month_name[sel_month]} {sel_year}")
    with st.form("set_budget"):
        budzet = st.number_input("Łączny budżet (zł)", min_value=0.0, step=100.0, value=current_val)
        saved  = st.form_submit_button("Zapisz", use_container_width=True)
    if saved:
        save_budget(sel_client, period, budzet)
        st.success("Zapisano w Google Sheets!")
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# POBIERZ Z API
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Pobierz":
    page_header("Pobierz dane z API", "Synchronizacja z Google Ads i Meta Ads")
    clients_df = load_clients()
    c1,c2 = st.columns(2)
    sel_year2  = c1.selectbox("Rok",  [today.year-1,today.year,today.year+1], index=1)
    sel_month2 = c2.selectbox("Miesiąc", range(1,13), index=today.month-1,
                              format_func=lambda m: calendar.month_name[m])
    period2 = f"{sel_year2}-{sel_month2:02d}"

    if st.button("Pobierz dla wszystkich klientów", use_container_width=True, type="primary"):
        from google.ads.googleads.client import GoogleAdsClient
        from google.ads.googleads.errors import GoogleAdsException
        from facebook_business.api import FacebookAdsApi
        from facebook_business.adobjects.adaccount import AdAccount
        from facebook_business.adobjects.adsinsights import AdsInsights
        import calendar as cal

        ga_base_config = {
            "developer_token": st.secrets["google_ads"]["GOOGLE_ADS_DEVELOPER_TOKEN"],
            "client_id":       st.secrets["google_ads"]["GOOGLE_ADS_CLIENT_ID"],
            "client_secret":   st.secrets["google_ads"]["GOOGLE_ADS_CLIENT_SECRET"],
            "refresh_token":   st.secrets["google_ads"]["GOOGLE_ADS_REFRESH_TOKEN"],
            "use_proto_plus":  True,
        }
        FacebookAdsApi.init(access_token=st.secrets["meta"]["META_ACCESS_TOKEN"],
                            api_version=st.secrets["meta"].get("META_API_VERSION","v19.0"))

        last_day  = cal.monthrange(sel_year2, sel_month2)[1]
        date_from = f"{sel_year2}-{sel_month2:02d}-01"
        date_to   = f"{sel_year2}-{sel_month2:02d}-{last_day:02d}"
        progress  = st.progress(0)
        results   = []

        for i, (_, client) in enumerate(clients_df.iterrows()):
            cname = client["nazwa"]
            g_id  = str(client.get("google_ads_id","")).strip()
            fb_id = str(client.get("meta_ads_id","")).strip()
            g_net, fb_net = 0.0, 0.0
            g_msg, fb_msg = "brak ID", "brak ID"

            if g_id:
                try:
                    mcc = str(client.get("mcc_id","")).strip()
                    ga_config = ga_base_config.copy()
                    if mcc:
                        ga_config["login_customer_id"] = mcc
                    elif "GOOGLE_ADS_LOGIN_CUSTOMER_ID" in st.secrets["google_ads"]:
                        ga_config["login_customer_id"] = st.secrets["google_ads"]["GOOGLE_ADS_LOGIN_CUSTOMER_ID"]
                    ga_client  = GoogleAdsClient.load_from_dict(ga_config)
                    ga_service = ga_client.get_service("GoogleAdsService")
                    query = f"SELECT metrics.cost_micros FROM customer WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'"
                    response = ga_service.search_stream(customer_id=g_id.replace("-",""), query=query)
                    total_micros = sum(row.metrics.cost_micros for batch in response for row in batch.results)
                    g_net = round(total_micros / 1_000_000, 2)
                    g_msg = "OK"
                except GoogleAdsException as e:
                    g_msg = f"Błąd: {e.error.code().name}"
                except Exception as e:
                    g_msg = f"Błąd: {str(e)[:50]}"

            if fb_id:
                try:
                    acc_id   = fb_id if fb_id.startswith("act_") else f"act_{fb_id}"
                    insights = AdAccount(acc_id).get_insights(params={
                        "time_range": {"since": date_from, "until": date_to},
                        "fields": [AdsInsights.Field.spend],
                        "level": "account",
                    })
                    fb_net = round(sum(float(r["spend"]) for r in insights if "spend" in r), 2)
                    fb_msg = "OK"
                except Exception as e:
                    fb_msg = f"Błąd: {str(e)[:50]}"

            save_spend(cname, period2, g_net, fb_net)
            results.append({"Klient":cname,"Google":g_msg,"G netto":f"{g_net:.0f} zł","Meta":fb_msg,"FB netto":f"{fb_net:.0f} zł"})
            progress.progress((i+1)/len(clients_df))

        st.success("Zaktualizowano! Przejdź do Dashboard.")
        st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# USTAWIENIA
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Ustawienia":
    page_header("Ustawienia API", "Konfiguracja połączeń z platformami reklamowymi")
    st.info("Tokeny API wpisuj w Streamlit Cloud → Settings → Secrets — nigdy w kodzie!")
    section("Wymagane wpisy w Secrets")
    st.code("""
[gcp_service_account]
type = "service_account"
project_id = "ermon-budget-tracker"
private_key_id = "..."
private_key = "..."
client_email = "ermon-sheets@ermon-budget-tracker.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."

[google_ads]
GOOGLE_ADS_DEVELOPER_TOKEN = "..."
GOOGLE_ADS_CLIENT_ID = "..."
GOOGLE_ADS_CLIENT_SECRET = "..."
GOOGLE_ADS_REFRESH_TOKEN = "..."
GOOGLE_ADS_LOGIN_CUSTOMER_ID = "..."

[meta]
META_ACCESS_TOKEN = "..."
META_API_VERSION = "v19.0"
    """, language="toml")
