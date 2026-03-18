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
            # usuń spacje i niełamliwe spacje
            s = s.replace('\xa0', '').replace('\u00a0', '').replace(' ', '')
            # format angielski: 1,542.92 - usuń przecinek (separator tysięcy), zostaw kropkę
            # format polski: 1 542,92 - usuń spację, zamień przecinek na kropkę
            if '.' in s and ',' in s:
                # mamy oba - przecinek to separator tysięcy, kropka to dziesiętna
                s = s.replace(',', '')
            elif ',' in s and '.' not in s:
                # tylko przecinek - to separator dziesiętny
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

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] {{ font-family: 'DM Sans', sans-serif; background-color: #1a1a2e; color: #e8e8f5; }}
section[data-testid="stSidebar"] {{ background: #16213e !important; border-right: 1px solid #2a2a4a; min-width: 220px !important; }}
section[data-testid="stSidebar"] label {{ font-size: 1rem !important; padding: 8px 0 !important; }}
.main .block-container {{ padding: 2rem 2.5rem; max-width: 1600px; }}
.ermon-logo-wrap {{ padding: 1.5rem 1.2rem 1rem; border-bottom: 1px solid #2a2a4a; margin-bottom: 1rem; }}
.ermon-logo-wrap img {{ width: 130px; filter: brightness(0) invert(1); }}
.ermon-tagline {{ font-family:'DM Sans',sans-serif; font-size:0.7rem; letter-spacing:0.15em; color:#7070b0; text-transform:uppercase; margin-top:6px; }}
.ermon-page-title {{ font-family:'Syne',sans-serif; font-size:2rem; font-weight:800; color:#ffffff; letter-spacing:-0.03em; margin-bottom:0.2rem; }}
.ermon-page-subtitle {{ font-size:0.8rem; color:#7070a0; margin-bottom:2rem; letter-spacing:0.08em; text-transform:uppercase; }}
.kpi-card {{ background:linear-gradient(135deg,#1e1e3a,#252545); border:1px solid #2e2e5a; border-radius:16px; padding:1.4rem 1.6rem; transition:border-color .3s,transform .2s; margin-bottom:1rem; }}
.kpi-card:hover {{ border-color:#4040a0; transform:translateY(-2px); }}
.kpi-label {{ font-size:0.7rem; letter-spacing:0.12em; text-transform:uppercase; color:#7070a0; margin-bottom:0.5rem; }}
.kpi-value {{ font-family:'Syne',sans-serif; font-size:1.65rem; font-weight:700; color:#ffffff; line-height:1; }}
.kpi-value-accent {{ color:#8878f0; }}
.kpi-sub {{ font-size:0.72rem; color:#8080b0; margin-top:0.3rem; }}
.section-header {{ font-family:'Syne',sans-serif; font-size:0.85rem; font-weight:700; color:#8080c0; letter-spacing:0.14em; text-transform:uppercase; border-bottom:1px solid #2a2a4a; padding-bottom:0.5rem; margin:1.8rem 0 1.2rem; }}
.stButton > button {{ background:linear-gradient(135deg,#2D1B8E,#4428c0) !important; color:white !important; border:none !important; border-radius:8px !important; font-family:'DM Sans',sans-serif !important; font-weight:500 !important; transition:opacity .2s !important; }}
.stButton > button:hover {{ opacity:0.82 !important; }}
hr {{ border-color:#2a2a4a !important; }}
.stDataFrame {{ font-size: 16px !important; }}
.stDataFrame td {{ font-size: 16px !important; padding: 14px 18px !important; background-color: #3a4a6a !important; }}
.stDataFrame th {{ font-size: 16px !important; padding: 14px 18px !important; background-color: #2a3a5a !important; color: #ffffff !important; }}
</style>
<div class="ermon-logo-wrap">
    {"<img src='data:image/png;base64," + LOGO_B64 + "' />" if LOGO_B64 else "<span style='font-family:Syne,sans-serif;font-size:1.4rem;font-weight:800;color:#fff;'>Ermon.</span>"}
    <div class="ermon-tagline">Budget Tracker</div>
</div>
""", unsafe_allow_html=True)

menu_map = {
    "🏠 Dashboard": "Dashboard",
    "👥 Klienci": "Klienci",
    "💰 Budżety": "Budżety",
    "📥 Pobierz z API": "Pobierz",
    "⚙️ Ustawienia API": "Ustawienia"
}

with st.sidebar:
    selection = st.radio("Menu", list(menu_map.keys()), label_visibility="collapsed")
    page = menu_map[selection]
    st.markdown("---")
    today = date.today()
    st.caption(f"📅 {today.strftime('%d.%m.%Y')}")

def kpi_card(label, value, sub="", accent=False):
    vc = "kpi-value kpi-value-accent" if accent else "kpi-value"
    sh = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="{vc}">{value}</div>{sh}</div>', unsafe_allow_html=True)

def page_header(title, subtitle=""):
    st.markdown(f'<div class="ermon-page-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="ermon-page-subtitle">{subtitle}</div>', unsafe_allow_html=True)

def section(title):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)

if page == "Dashboard":
    page_header("Dashboard", "Przegląd budżetów reklamowych")
    clients_df = load_clients()
    budgets_df = load_budgets()
    spend_df   = load_spend()

    if clients_df.empty:
        st.info("Brak danych. Dodaj klientów w zakładce 👥 Klienci.")
        st.stop()

    cy, cm, _, _ = st.columns([1,1,1,2])
    sel_year  = cy.selectbox("Rok",  [today.year-1, today.year, today.year+1], index=1, key="dy")
    sel_month = cm.selectbox("Miesiąc", range(1,13), index=today.month-1, format_func=lambda m: calendar.month_abbr[m], key="dm")
    period    = f"{sel_year}-{sel_month:02d}"
    days_left = days_remaining(sel_year, sel_month)

    # grupowanie klientów
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
    
    section("Tabela zbiorcza")
    df = pd.DataFrame([{
       "Klient":        r["cname"],
       "Budżet netto":  f"{r['total_n']:.2f}",
       "Budżet brutto": f"{r['total_g']:.2f}",
       "Google wydano": f"{r['g_sn']:.2f}",
       "Meta wydano":   f"{r['fb_sn']:.2f}",
       "Razem wydano":  f"{r['tot_sn']:.2f}",
       "Razem brutto":  f"{r['tot_sg']:.2f}",
       "Pozostało":     f"{r['rem_n']:.2f}",
       "Max dziennie":  f"{r['daily']:.2f}",
       "% budżetu":     f"{r['pct']:.1f}%",
    } for r in rows])
    
    st.markdown("""
    <style>
    [data-testid="stDataFrame"] td { font-size: 25px !important; padding: 14px 18px !important; }
    [data-testid="stDataFrame"] th { font-size: 25px !important; padding: 14px 18px !important; }
    iframe { min-height: 500px !important; }
    </style>
    """, unsafe_allow_html=True)
    st.dataframe(
        df.style
          .set_properties(subset=["Pozostało", "Max dziennie", "% budżetu"],
                          **{"background-color": "#1e2d4a", "font-weight": "bold", "color": "#8878f0"}),
        use_container_width=True, hide_index=True, height=400
    )
    csv = df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
    st.download_button("⬇️ Pobierz CSV", csv, file_name=f"ermon_budgety_{period}.csv", mime="text/csv")

    import plotly.express as px
    import plotly.graph_objects as go
    
    k1,k2,k3,k4,k5 = st.columns(5)
    with k1: kpi_card("Łączny budżet",  f"{sum_bud:.2f} zł",   "netto")
    with k2: kpi_card("Łącznie wydano", f"{sum_spent:.2f} zł", f"brutto: {gross(sum_spent):.2f} zł")
    with k3: kpi_card("Pozostało",      f"{sum_rem:.2f} zł",   "netto", accent=True)
    with k4: kpi_card("Max dziennie",   f"{sum_daily:.2f} zł", f"na {days_left} dni")
    with k5: kpi_card("Klientów",       str(len(rows)),        f"{calendar.month_name[sel_month]} {sel_year}")

    
    section("Wykresy")
    col_chart1, col_chart2 = st.columns(2)
    df_chart = pd.DataFrame([{"Klient":r["cname"],"Google":r["g_sn"],"Meta":r["fb_sn"],"Budżet":r["total_n"]} for r in rows])

    with col_chart1:
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(name="Google", x=df_chart["Klient"], y=df_chart["Google"], marker_color="#4285F4"))
        fig1.add_trace(go.Bar(name="Meta",   x=df_chart["Klient"], y=df_chart["Meta"],   marker_color="#1877F2"))
        fig1.add_trace(go.Scatter(name="Budżet", x=df_chart["Klient"], y=df_chart["Budżet"],
                                  mode="markers", marker=dict(color="#f0b030", size=12, symbol="line-ew-open", line=dict(width=3))))
        fig1.update_layout(title="Wydatki vs Budżet", barmode="stack",
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font=dict(color="#e0e0f0", family="DM Sans"),
                           legend=dict(bgcolor="rgba(0,0,0,0)"),
                           xaxis=dict(gridcolor="#2a2a4a"), yaxis=dict(gridcolor="#2a2a4a"), height=380)
        st.plotly_chart(fig1, use_container_width=True)

    with col_chart2:
        df_pie = pd.DataFrame([{"Klient":r["cname"],"Wydano":r["tot_sn"]} for r in rows if r["tot_sn"]>0])
        if not df_pie.empty:
            fig2 = px.pie(df_pie, names="Klient", values="Wydano", title="Podział wydatków",
                          color_discrete_sequence=["#2D1B8E","#4428c0","#6040d0","#8060e0","#a080f0"])
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e0e0f0", family="DM Sans"), height=380)
            st.plotly_chart(fig2, use_container_width=True)

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
            submit = st.form_submit_button("➕ Dodaj klienta", use_container_width=True)
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
                with st.expander(f"📌 {row['nazwa']}"):
                    c1,c2,c3 = st.columns(3)
                    c1.write(f"**Google Ads:** {row.get('google_ads_id') or '—'}")
                    c2.write(f"**Meta Ads:** {row.get('meta_ads_id') or '—'}")
                    c3.write(f"**Typ kwoty:** {row.get('typ_kwoty','netto')}")
                    if st.button("🗑️ Usuń", key=f"del_{row['nazwa']}"):
                        delete_client(row['nazwa'])
                        st.cache_resource.clear()
                        st.rerun()

elif page == "Budżety":
    page_header("Budżety", "Ustawianie budżetów miesięcznych")
    clients_df = load_clients()
    if clients_df.empty:
        st.warning("Najpierw dodaj klientów.")
        st.stop()
    sel_client = st.selectbox("Klient", clients_df["nazwa"].tolist())
    c1,c2 = st.columns(2)
    sel_year  = c1.selectbox("Rok",  [today.year-1,today.year,today.year+1], index=1)
    sel_month = c2.selectbox("Miesiąc", range(1,13), index=today.month-1, format_func=lambda m: calendar.month_name[m])
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

elif page == "Pobierz":
    page_header("Pobierz dane z API", "Synchronizacja z Google Ads i Meta Ads")
    clients_df = load_clients()
    c1,c2 = st.columns(2)
    sel_year2  = c1.selectbox("Rok",  [today.year-1,today.year,today.year+1], index=1)
    sel_month2 = c2.selectbox("Miesiąc", range(1,13), index=today.month-1, format_func=lambda m: calendar.month_name[m])
    period2 = f"{sel_year2}-{sel_month2:02d}"

    if st.button("🔄 Pobierz dla wszystkich klientów", use_container_width=True, type="primary"):
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
                    g_msg = "✅ OK"
                except GoogleAdsException as e:
                    g_msg = f"❌ {e.error.code().name}"
                except Exception as e:
                    g_msg = f"❌ {str(e)[:50]}"

            if fb_id:
                try:
                    acc_id   = fb_id if fb_id.startswith("act_") else f"act_{fb_id}"
                    insights = AdAccount(acc_id).get_insights(params={
                        "time_range": {"since": date_from, "until": date_to},
                        "fields": [AdsInsights.Field.spend],
                        "level": "account",
                    })
                    fb_net = round(sum(float(r["spend"]) for r in insights if "spend" in r), 2)
                    fb_msg = "✅ OK"
                except Exception as e:
                    fb_msg = f"❌ {str(e)[:50]}"

            save_spend(cname, period2, g_net, fb_net)
            results.append({"Klient":cname,"Google":g_msg,"G netto":f"{g_net:.2f} zł","Meta":fb_msg,"FB netto":f"{fb_net:.2f} zł"})
            progress.progress((i+1)/len(clients_df))

        st.success("Zaktualizowano! Przejdź do Dashboard. ✅")
        st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)

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
