import streamlit as st
import pandas as pd
from datetime import date
import calendar
import base64
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ermon. | Budget Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── constants ─────────────────────────────────────────────────────────────────
VAT_RATE  = 0.23
SHEET_ID  = "1l_fX5ydioIsKVyhitrnR3rcdf6RyZOq-x6oQ3mhP9uQ"
SCOPES    = ["https://www.googleapis.com/auth/spreadsheets"]

# ── Google Sheets ─────────────────────────────────────────────────────────────
@st.cache_resource
def get_gsheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES)
    return gspread.authorize(creds).open_by_key(SHEET_ID)

def load_clients() -> pd.DataFrame:
    try:
        ws = get_gsheet().worksheet("klienci")
        data = ws.get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame(
            columns=["nazwa","google_ads_id","meta_ads_id","typ_kwoty"])
    except Exception as e:
        st.error(f"Błąd odczytu klientów: {e}")
        return pd.DataFrame(columns=["nazwa","google_ads_id","meta_ads_id","typ_kwoty"])

def load_budgets() -> pd.DataFrame:
    try:
        ws = get_gsheet().worksheet("budzety")
        data = ws.get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame(
            columns=["klient","miesiac","budzet_total"])
    except Exception as e:
        st.error(f"Błąd odczytu budżetów: {e}")
        return pd.DataFrame(columns=["klient","miesiac","budzet_total"])

def save_client(nazwa, google_id, meta_id, typ, mcc_id=""):
    get_gsheet().worksheet("klienci").append_row([nazwa, google_id, meta_id, typ, mcc_id])

def save_budget(klient, miesiac, budzet_total):
    ws  = get_gsheet().worksheet("budzety")
    all_rows = ws.get_all_records()
    for i, row in enumerate(all_rows):
        if row["klient"] == klient and row["miesiac"] == miesiac:
            ws.update(f"A{i+2}:C{i+2}", [[klient, miesiac, budzet_total]])
            return
    ws.append_row([klient, miesiac, budzet_total])

def save_spend(klient, miesiac, google_spend, meta_spend):
    try:
        # Upewniamy się, że to liczby (float), zamieniając ewentualne przecinki na kropki
        g_val = float(str(google_spend).replace(',', '.'))
        f_val = float(str(meta_spend).replace(',', '.'))
        
        ws = get_gsheet().worksheet("wydatki")
        all_rows = ws.get_all_records()
        
        # Sprawdzamy czy wiersz już istnieje
        for i, row in enumerate(all_rows):
            if row["klient"] == klient and row["miesiac"] == miesiac:
                # Nadpisujemy wiersz czystymi wartościami (z kropką)
                ws.update(f"A{i+2}:D{i+2}", [[klient, miesiac, g_val, f_val]])
                return
        
        # Jeśli nie znaleziono, dodajemy nowy wiersz
        ws.append_row([klient, miesiac, g_val, f_val])
        
    except Exception as e:
        st.error(f"Błąd zapisu wydatków: {e}")

def load_spend() -> pd.DataFrame:
    try:
        ws = get_gsheet().worksheet("wydatki")
        data = ws.get_all_records()
        if not data:
            return pd.DataFrame(columns=["klient","miesiac","google_spend","meta_spend"])
        
        df = pd.DataFrame(data)
        
        # Funkcja czyszcząca, która zamienia wszystko na float z kropką
        def clean(val):
            try:
                return float(str(val).replace(',', '.'))
            except:
                return 0.0
                
        df["google_spend"] = df["google_spend"].apply(clean)
        df["meta_spend"] = df["meta_spend"].apply(clean)
        return df
    except:
        return pd.DataFrame(columns=["klient","miesiac","google_spend","meta_spend"])

def delete_client(nazwa):
    ws   = get_gsheet().worksheet("klienci")
    cell = ws.find(nazwa)
    if cell:
        ws.delete_rows(cell.row)

# ── helpers ───────────────────────────────────────────────────────────────────
def days_remaining(year: int, month: int) -> int:
    today = date.today()
    last  = calendar.monthrange(year, month)[1]
    end   = date(year, month, last)
    if today.year == year and today.month == month:
        return max(0, (end - today).days + 1)
    if date(year, month, 1) > today:
        return last
    return 0

def gross(net: float) -> float:
    return round(net * (1 + VAT_RATE), 2)

def netto(gross_val: float) -> float:
    return round(gross_val / (1 + VAT_RATE), 2)

def get_logo_base64() -> str:
    logo_path = Path(__file__).parent / "logo.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

LOGO_B64 = get_logo_base64()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] {{ font-family: 'DM Sans', sans-serif; background-color: #08080f; color: #e8e8f5; }}
section[data-testid="stSidebar"] {{ background: #0d0d1f !important; border-right: 1px solid #1e1e3a; }}
.main .block-container {{ padding: 2rem 2.5rem; max-width: 1400px; }}
.ermon-logo-wrap {{ padding: 1.5rem 1.2rem 1rem; border-bottom: 1px solid #1e1e3a; margin-bottom: 1rem; }}
.ermon-logo-wrap img {{ width: 120px; filter: brightness(0) invert(1); }}
.ermon-tagline {{ font-family:'DM Sans',sans-serif; font-size:0.7rem; letter-spacing:0.15em; color:#5050a0; text-transform:uppercase; margin-top:6px; }}
.ermon-page-title {{ font-family:'Syne',sans-serif; font-size:2rem; font-weight:800; color:#ffffff; letter-spacing:-0.03em; margin-bottom:0.2rem; }}
.ermon-page-subtitle {{ font-size:0.8rem; color:#5a5a8a; margin-bottom:2rem; letter-spacing:0.08em; text-transform:uppercase; }}
.kpi-card {{ background:linear-gradient(135deg,#0f0f25,#141430); border:1px solid #1e1e3a; border-radius:16px; padding:1.4rem 1.6rem; transition:border-color .3s,transform .2s; margin-bottom:1rem; }}
.kpi-card:hover {{ border-color:#2D1B8E; transform:translateY(-2px); }}
.kpi-label {{ font-size:0.7rem; letter-spacing:0.12em; text-transform:uppercase; color:#5050a0; margin-bottom:0.5rem; }}
.kpi-value {{ font-family:'Syne',sans-serif; font-size:1.65rem; font-weight:700; color:#ffffff; line-height:1; }}
.kpi-value-accent {{ color:#7060e0; }}
.kpi-sub {{ font-size:0.72rem; color:#606090; margin-top:0.3rem; }}
.metric-mini {{ background:#111124; border:1px solid #1a1a32; border-radius:10px; padding:0.8rem 1rem; text-align:center; margin-bottom:0.5rem; }}
.metric-mini-label {{ font-size:0.63rem; letter-spacing:0.1em; text-transform:uppercase; color:#40406a; margin-bottom:4px; }}
.metric-mini-value {{ font-family:'Syne',sans-serif; font-size:1rem; font-weight:700; color:#d0d0f0; }}
.metric-mini-sub {{ font-size:0.65rem; color:#40406a; margin-top:2px; }}
.section-header {{ font-family:'Syne',sans-serif; font-size:0.85rem; font-weight:700; color:#6060a0; letter-spacing:0.14em; text-transform:uppercase; border-bottom:1px solid #1a1a32; padding-bottom:0.5rem; margin:1.8rem 0 1.2rem; }}
.client-card {{ background:#0d0d20; border:1px solid #1a1a32; border-radius:14px; padding:1.2rem 1.4rem; margin-bottom:0.5rem; transition:border-color .25s; }}
.client-card:hover {{ border-color:#2D1B8E; }}
.client-name {{ font-family:'Syne',sans-serif; font-size:1.05rem; font-weight:700; color:#ffffff; margin-bottom:0.6rem; }}
.prog-wrap {{ background:#1a1a32; border-radius:99px; height:5px; overflow:hidden; margin:0.3rem 0 0.6rem; flex:1; }}
.prog-bar {{ height:100%; border-radius:99px; }}
.prog-green  {{ background:linear-gradient(90deg,#1a8050,#2ecc88); }}
.prog-yellow {{ background:linear-gradient(90deg,#8a6000,#f0b030); }}
.prog-red    {{ background:linear-gradient(90deg,#8a0020,#e03060); }}
.badge {{ display:inline-block; padding:2px 9px; border-radius:99px; font-size:0.65rem; font-weight:600; letter-spacing:0.06em; text-transform:uppercase; }}
.badge-green  {{ background:#0d2b1d; color:#2ecc88; border:1px solid #1a4030; }}
.badge-yellow {{ background:#2b210d; color:#f0b030; border:1px solid #40300a; }}
.badge-red    {{ background:#2b0d16; color:#e03060; border:1px solid #401020; }}
.stButton > button {{ background:linear-gradient(135deg,#2D1B8E,#4428c0) !important; color:white !important; border:none !important; border-radius:8px !important; font-family:'DM Sans',sans-serif !important; font-weight:500 !important; transition:opacity .2s !important; }}
.stButton > button:hover {{ opacity:0.82 !important; }}
/* #MainMenu, footer, header {{ visibility:hidden; }} */
hr {{ border-color:#1a1a32 !important; }}
</style>
<div class="ermon-logo-wrap">
    {"<img src='data:image/png;base64," + LOGO_B64 + "' />" if LOGO_B64 else "<span style='font-family:Syne,sans-serif;font-size:1.4rem;font-weight:800;color:#fff;'>Ermon.</span>"}
    <div class="ermon-tagline">Budget Tracker</div>
</div>
""", unsafe_allow_html=True)


# ── sidebar ───────────────────────────────────────────────────────────────────
# Definiujemy mapę: co widzisz w menu -> co program rozumie jako stronę
menu_map = {
    "🏠 Dashboard": "Dashboard",
    "👥 Klienci": "Klienci",
    "💰 Budżety": "Budżety",
    "📥 Pobierz z API": "Pobierz",
    "⚙️ Ustawienia API": "Ustawienia"
}

with st.sidebar:
    selection = st.radio("Menu", list(menu_map.keys()), label_visibility="collapsed")
    page = menu_map[selection] # Tutaj przypisujemy czystą nazwę strony
    
    st.markdown("---")
    today = date.today()
    st.caption(f"📅 {today.strftime('%d.%m.%Y')}")

# ══════════════════════════════════════════════════════════════════════════════
# GŁÓWNA LOGIKA NAWIGACJI
# ══════════════════════════════════════════════════════════════════════════════

if page == "Dashboard":
    # ... (Twój kod dashboardu bez zmian)
    pass

elif page == "Klienci":
    # ... (Twój kod klientów bez zmian)
    pass

elif page == "Budżety":
    # ... (Twój kod budżetów bez zmian)
    pass

elif page == "Pobierz":
    # ... (Twój kod pobierania bez zmian)
    pass

elif page == "Ustawienia":
    # ... (Twój kod ustawień bez zmian)
    pass

# ── component helpers ─────────────────────────────────────────────────────────
def kpi_card(label, value, sub="", accent=False):
    vc = "kpi-value kpi-value-accent" if accent else "kpi-value"
    sh = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="{vc}">{value}</div>{sh}</div>', unsafe_allow_html=True)

def metric_mini(label, value, sub=""):
    sh = f'<div class="metric-mini-sub">{sub}</div>' if sub else ""
    st.markdown(f'<div class="metric-mini"><div class="metric-mini-label">{label}</div><div class="metric-mini-value">{value}</div>{sh}</div>', unsafe_allow_html=True)

def progress_bar(pct):
    cl = min(max(pct,0),100)
    pc = "prog-green" if pct<75 else ("prog-yellow" if pct<95 else "prog-red")
    bc = "badge-green" if pct<75 else ("badge-yellow" if pct<95 else "badge-red")
    lb = "W normie" if pct<75 else ("Uwaga" if pct<95 else "Przekroczony")
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:0.4rem;">
        <div class="prog-wrap"><div class="prog-bar {pc}" style="width:{cl}%;"></div></div>
        <span style="font-family:Syne,sans-serif;font-size:0.82rem;color:#c0c0e0;min-width:38px;">{pct:.1f}%</span>
        <span class="badge {bc}">{lb}</span>
    </div>""", unsafe_allow_html=True)

def page_header(title, subtitle=""):
    st.markdown(f'<div class="ermon-page-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="ermon-page-subtitle">{subtitle}</div>', unsafe_allow_html=True)

def section(title):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if "Dashboard" in page:
    page_header("Dashboard", "Przegląd budżetów reklamowych")

    clients_df = load_clients()
    budgets_df = load_budgets()
    spend_df   = load_spend()

    if clients_df.empty:
        st.info("Brak danych. Dodaj klientów w zakładce 👥 Klienci.")
        st.stop()

    cy, cm, _, _ = st.columns([1,1,1,2])
    sel_year  = cy.selectbox("Rok",  [today.year-1, today.year, today.year+1], index=1, key="dy")
    sel_month = cm.selectbox("Miesiąc", range(1,13), index=today.month-1,
                             format_func=lambda m: calendar.month_abbr[m], key="dm")
    period    = f"{sel_year}-{sel_month:02d}"
    days_left = days_remaining(sel_year, sel_month)

    rows = []
    for _, client in clients_df.iterrows():
        cname = client["nazwa"]
        gm    = str(client.get("typ_kwoty","netto")).lower() == "brutto"

        bud_row = budgets_df[(budgets_df["klient"]==cname) & (budgets_df["miesiac"]==period)]
        total_r = float(bud_row["budzet_total"].values[0]) if not bud_row.empty else 0.0
        total_n = netto(total_r) if gm else total_r

        spnd_row = spend_df[(spend_df["klient"]==cname) & (spend_df["miesiac"]==period)]
        g_sn  = float(spnd_row["google_spend"].values[0]) if not spnd_row.empty else 0.0
        fb_sn = float(spnd_row["meta_spend"].values[0])   if not spnd_row.empty else 0.0
        tot_sn = g_sn + fb_sn

        rem_n  = max(0, total_n - tot_sn)
        daily  = round(rem_n/days_left, 2) if days_left > 0 else 0
        pct    = round(tot_sn/total_n*100, 1) if total_n > 0 else 0

        rows.append(dict(cname=cname, total_n=total_n, total_g=gross(total_n),
                         g_sn=g_sn, g_sg=gross(g_sn), fb_sn=fb_sn, fb_sg=gross(fb_sn),
                         tot_sn=tot_sn, tot_sg=gross(tot_sn),
                         rem_n=rem_n, rem_g=gross(rem_n), daily=daily, pct=pct))

    sum_bud   = sum(r["total_n"] for r in rows)
    sum_spent = sum(r["tot_sn"]  for r in rows)
    sum_rem   = sum_bud - sum_spent
    sum_daily = round(sum_rem/days_left, 2) if days_left > 0 else 0

    k1,k2,k3,k4,k5 = st.columns(5)
    with k1: kpi_card("Łączny budżet",  f"{sum_bud:.2f} zł",   "netto")
    with k2: kpi_card("Łącznie wydano", f"{sum_spent:.2f} zł", f"brutto: {gross(sum_spent):.2f} zł")
    with k3: kpi_card("Pozostało",      f"{sum_rem:.2f} zł",   "netto", accent=True)
    with k4: kpi_card("Max dziennie",   f"{sum_daily:.2f} zł", f"na {days_left} dni")
    with k5: kpi_card("Klientów",       str(len(rows)),         f"{calendar.month_name[sel_month]} {sel_year}")

    section("Klienci")
    for r in rows:
        st.markdown(f'<div class="client-card"><div class="client-name">{r["cname"]}</div>', unsafe_allow_html=True)
        progress_bar(r["pct"])
        st.markdown("</div>", unsafe_allow_html=True)
        c1,c2,c3,c4,c5 = st.columns(5)
        with c1: metric_mini("Budżet netto",  f"{r['total_n']:.2f} zł", f"brutto {r['total_g']:.2f}")
        with c2: metric_mini("Google wydano", f"{r['g_sn']:.2f} zł",    f"brutto {r['g_sg']:.2f}")
        with c3: metric_mini("Meta wydano",   f"{r['fb_sn']:.2f} zł",   f"brutto {r['fb_sg']:.2f}")
        with c4: metric_mini("Pozostało",     f"{r['rem_n']:.2f} zł",   f"brutto {r['rem_g']:.2f}")
        with c5: metric_mini("Max dziennie",  f"{r['daily']:.2f} zł",   f"{days_left} dni")
        st.markdown("<br>", unsafe_allow_html=True)

    section("Tabela zbiorcza")
    df = pd.DataFrame([{"Klient":r["cname"],"Budżet netto":r["total_n"],"Budżet brutto":r["total_g"],
                         "Google wydano":r["g_sn"],"Meta wydano":r["fb_sn"],
                         "Razem wydano":r["tot_sn"],"Razem brutto":r["tot_sg"],
                         "Pozostało":r["rem_n"],"Max dziennie":r["daily"],"% budżetu":r["pct"]} for r in rows])
    st.dataframe(df.style.format({c:"{:.2f}" for c in df.columns if c!="Klient"})
                   .background_gradient(subset=["% budżetu"], cmap="RdYlGn_r", vmin=0, vmax=100),
                 use_container_width=True, hide_index=True)
    csv = df.to_csv(index=False,sep=";",decimal=",").encode("utf-8-sig")
    st.download_button("⬇️ Pobierz CSV", csv, file_name=f"ermon_budgety_{period}.csv", mime="text/csv")

# ══════════════════════════════════════════════════════════════════════════════
# KLIENCI
# ══════════════════════════════════════════════════════════════════════════════
elif "Klienci" in page:
    page_header("Klienci", "Zarządzanie bazą klientów")
    col1, col2 = st.columns([1,2])

    with col1:
        section("Dodaj klienta")
        with st.form("add_client"):
            name   = st.text_input("Nazwa klienta")
            g_id   = st.text_input("Google Ads Customer ID", placeholder="123-456-7890")
            mcc_id = st.text_input("MCC ID (konto menedżera nad klientem)", placeholder="1234567890")
            fb_id  = st.text_input("Meta Ads Account ID",    placeholder="act_123456789")
            typ    = st.selectbox("Typ kwoty budżetu", ["netto","brutto"])
            submit = st.form_submit_button("➕ Dodaj klienta", use_container_width=True)
        if submit and name.strip():
            save_client(name.strip(), g_id.strip(), fb_id.strip(), typ, mcc_id.strip())

    with col2:
        section("Lista klientów")
        clients_df = load_clients()
        if clients_df.empty:
            st.info("Brak klientów.")
        else:
            for _, row in clients_df.iterrows():
                with st.expander(f"📌 {row['nazwa']}"):
                    c1,c2,c3 = st.columns(3)
                    c1.write(f"**Google Ads:** {row.get('google_ads_id') or '—'}")
                    c2.write(f"**Meta Ads:** {row.get('meta_ads_id') or '—'}")
                    c3.write(f"**Typ kwoty:** {row.get('typ_kwoty','netto')}")
                    if st.button("🗑️ Usuń", key=f"del_{row['nazwa']}"):
                        delete_client(row['nazwa'])
                        st.cache_resource.clear()
                        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# BUDŻETY
# ══════════════════════════════════════════════════════════════════════════════
elif "Budżety" in page:
    page_header("Budżety", "Ustawianie budżetów miesięcznych")
    clients_df = load_clients()
    if clients_df.empty:
        st.warning("Najpierw dodaj klientów."); st.stop()

    sel_client = st.selectbox("Klient", clients_df["nazwa"].tolist())
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
        saved  = st.form_submit_button("💾 Zapisz", use_container_width=True)
    if saved:
        save_budget(sel_client, period, budzet)
        st.success("Zapisano w Google Sheets! ✅")
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# POBIERZ Z API
# ══════════════════════════════════════════════════════════════════════════════
elif "Pobierz" in page:
    page_header("Pobierz dane z API", "Synchronizacja z Google Ads i Meta Ads")
    clients_df = load_clients()

    c1,c2 = st.columns(2)
    sel_year2  = c1.selectbox("Rok",  [today.year-1,today.year,today.year+1], index=1)
    sel_month2 = c2.selectbox("Miesiąc", range(1,13), index=today.month-1,
                              format_func=lambda m: calendar.month_name[m])
    period2 = f"{sel_year2}-{sel_month2:02d}"

    if st.button("🔄 Pobierz dla wszystkich klientów", use_container_width=True, type="primary"):
        from google.ads.googleads.client import GoogleAdsClient
        from google.ads.googleads.errors import GoogleAdsException
        from facebook_business.api import FacebookAdsApi
        from facebook_business.adobjects.adaccount import AdAccount
        from facebook_business.adobjects.adsinsights import AdsInsights
        import calendar as cal

        # init Google Ads
        ga_base_config = {
            "developer_token": st.secrets["google_ads"]["GOOGLE_ADS_DEVELOPER_TOKEN"],
            "client_id":       st.secrets["google_ads"]["GOOGLE_ADS_CLIENT_ID"],
            "client_secret":   st.secrets["google_ads"]["GOOGLE_ADS_CLIENT_SECRET"],
            "refresh_token":   st.secrets["google_ads"]["GOOGLE_ADS_REFRESH_TOKEN"],
            "use_proto_plus":  True,
        }

        # init Meta
        meta_token = st.secrets["meta"]["META_ACCESS_TOKEN"]
        meta_version = st.secrets["meta"].get("META_API_VERSION", "v19.0")
        FacebookAdsApi.init(access_token=meta_token, api_version=meta_version)

        last_day  = cal.monthrange(sel_year2, sel_month2)[1]
        date_from = f"{sel_year2}-{sel_month2:02d}-01"
        date_to   = f"{sel_year2}-{sel_month2:02d}-{last_day:02d}"

        progress = st.progress(0)
        results  = []

        for i, (_, client) in enumerate(clients_df.iterrows()):
            cname = client["nazwa"]
            g_id  = str(client.get("google_ads_id","")).strip()
            fb_id = str(client.get("meta_ads_id","")).strip()
            g_net, fb_net = 0.0, 0.0
            g_msg, fb_msg = "brak ID", "brak ID"

            if g_id:
                try:
                    mcc_id = str(client.get("mcc_id","")).strip()
                    ga_config = ga_base_config.copy()
                    if mcc_id:
                        ga_config["login_customer_id"] = mcc_id
                    elif "GOOGLE_ADS_LOGIN_CUSTOMER_ID" in st.secrets["google_ads"]:
                        ga_config["login_customer_id"] = st.secrets["google_ads"]["GOOGLE_ADS_LOGIN_CUSTOMER_ID"]
                    ga_client  = GoogleAdsClient.load_from_dict(ga_config)
                    ga_service = ga_client.get_service("GoogleAdsService")
                    query = f"""
                        SELECT metrics.cost_micros
                        FROM customer
                        WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
                    """
                    response = ga_service.search_stream(
                        customer_id=g_id.replace("-",""), query=query)
                    total_micros = sum(row.metrics.cost_micros
                                       for batch in response for row in batch.results)
                    g_net = round(total_micros / 1_000_000, 2)
                    g_msg = "✅ OK"
                except GoogleAdsException as e:
                    g_msg = f"❌ {e.error.code().name}"
                except Exception as e:
                    g_msg = f"❌ {str(e)[:50]}"

            if fb_id:
                try:
                    acc_id = fb_id if fb_id.startswith("act_") else f"act_{fb_id}"
                    insights = AdAccount(acc_id).get_insights(params={
                        "time_range": {"since": date_from, "until": date_to},
                        "fields": [AdsInsights.Field.spend],
                        "level": "account",
                    })
                    # Zmień w kodzie (sekcja Meta):
                    # Zamiast fb_net = round(...)
                    raw_spend = sum(float(r["spend"]) for r in insights if "spend" in r)
                    st.write(f"Debug - Raw spend dla {cname}: {raw_spend}") # To pokaże Ci w aplikacji, co dokładnie zwraca Meta
                    fb_net = round(raw_spend, 2)
                    fb_msg = "✅ OK"
                except Exception as e:
                    fb_msg = f"❌ {str(e)[:50]}"

            save_spend(cname, period2, g_net, fb_net)
            results.append({"Klient":cname,"Google":g_msg,
                             "G netto":f"{g_net:.2f} zł","Meta":fb_msg,
                             "FB netto":f"{fb_net:.2f} zł"})
            progress.progress((i+1)/len(clients_df))

        st.success("Zaktualizowano! Przejdź do Dashboard. ✅")
        st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# USTAWIENIA API
# ══════════════════════════════════════════════════════════════════════════════
elif "Ustawienia" in page:
    page_header("Ustawienia API", "Konfiguracja połączeń z platformami reklamowymi")
    st.info("Tokeny API wpisuj w **Streamlit Cloud → Settings → Secrets** — nigdy w kodzie!")

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

GOOGLE_ADS_DEVELOPER_TOKEN = "..."
GOOGLE_ADS_CLIENT_ID = "..."
GOOGLE_ADS_CLIENT_SECRET = "..."
GOOGLE_ADS_REFRESH_TOKEN = "..."
GOOGLE_ADS_LOGIN_CUSTOMER_ID = "..."

META_ACCESS_TOKEN = "..."
META_API_VERSION = "v19.0"
    """, language="toml")
