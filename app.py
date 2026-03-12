import streamlit as st
import pandas as pd
from datetime import date
import calendar
import json
import base64
from pathlib import Path

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ermon. | Budget Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── helpers ───────────────────────────────────────────────────────────────────
DATA_FILE = Path("clients_data.json")
VAT_RATE  = 0.23

def load_data() -> dict:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {}

def save_data(data: dict):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

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

# ── global CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif;
    background-color: #08080f;
    color: #e8e8f5;
}}
section[data-testid="stSidebar"] {{
    background: #0d0d1f !important;
    border-right: 1px solid #1e1e3a;
}}
.main .block-container {{
    padding: 2rem 2.5rem;
    max-width: 1400px;
}}
.ermon-logo-wrap {{
    padding: 1.5rem 1.2rem 1rem;
    border-bottom: 1px solid #1e1e3a;
    margin-bottom: 1rem;
}}
.ermon-logo-wrap img {{
    width: 120px;
    filter: brightness(0) invert(1);
}}
.ermon-tagline {{
    font-family: 'DM Sans', sans-serif;
    font-size: 0.7rem;
    letter-spacing: 0.15em;
    color: #5050a0;
    text-transform: uppercase;
    margin-top: 6px;
}}
.ermon-page-title {{
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.03em;
    margin-bottom: 0.2rem;
}}
.ermon-page-subtitle {{
    font-size: 0.8rem;
    color: #5a5a8a;
    margin-bottom: 2rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}}
.kpi-card {{
    background: linear-gradient(135deg, #0f0f25, #141430);
    border: 1px solid #1e1e3a;
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    transition: border-color .3s, transform .2s;
    margin-bottom: 1rem;
}}
.kpi-card:hover {{ border-color: #2D1B8E; transform: translateY(-2px); }}
.kpi-label {{
    font-size: 0.7rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #5050a0;
    margin-bottom: 0.5rem;
}}
.kpi-value {{
    font-family: 'Syne', sans-serif;
    font-size: 1.65rem;
    font-weight: 700;
    color: #ffffff;
    line-height: 1;
}}
.kpi-value-accent {{ color: #7060e0; }}
.kpi-sub {{ font-size: 0.72rem; color: #606090; margin-top: 0.3rem; }}
.metric-mini {{
    background: #111124;
    border: 1px solid #1a1a32;
    border-radius: 10px;
    padding: 0.8rem 1rem;
    text-align: center;
    margin-bottom: 0.5rem;
}}
.metric-mini-label {{
    font-size: 0.63rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #40406a;
    margin-bottom: 4px;
}}
.metric-mini-value {{
    font-family: 'Syne', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    color: #d0d0f0;
}}
.metric-mini-sub {{ font-size: 0.65rem; color: #40406a; margin-top: 2px; }}
.section-header {{
    font-family: 'Syne', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    color: #6060a0;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    border-bottom: 1px solid #1a1a32;
    padding-bottom: 0.5rem;
    margin: 1.8rem 0 1.2rem;
}}
.client-card {{
    background: #0d0d20;
    border: 1px solid #1a1a32;
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.5rem;
    transition: border-color .25s;
}}
.client-card:hover {{ border-color: #2D1B8E; }}
.client-name {{
    font-family: 'Syne', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 0.6rem;
}}
.prog-wrap {{
    background: #1a1a32;
    border-radius: 99px;
    height: 5px;
    overflow: hidden;
    margin: 0.3rem 0 0.6rem;
    flex: 1;
}}
.prog-bar {{ height: 100%; border-radius: 99px; }}
.prog-green  {{ background: linear-gradient(90deg,#1a8050,#2ecc88); }}
.prog-yellow {{ background: linear-gradient(90deg,#8a6000,#f0b030); }}
.prog-red    {{ background: linear-gradient(90deg,#8a0020,#e03060); }}
.badge {{
    display: inline-block;
    padding: 2px 9px;
    border-radius: 99px;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}}
.badge-green  {{ background:#0d2b1d; color:#2ecc88; border:1px solid #1a4030; }}
.badge-yellow {{ background:#2b210d; color:#f0b030; border:1px solid #40300a; }}
.badge-red    {{ background:#2b0d16; color:#e03060; border:1px solid #401020; }}
.stButton > button {{
    background: linear-gradient(135deg, #2D1B8E, #4428c0) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    transition: opacity .2s !important;
}}
.stButton > button:hover {{ opacity: 0.82 !important; }}
#MainMenu, footer, header {{ visibility: hidden; }}
hr {{ border-color: #1a1a32 !important; }}
</style>

<div class="ermon-logo-wrap">
    {"<img src='data:image/png;base64," + LOGO_B64 + "' />" if LOGO_B64 else "<span style='font-family:Syne,sans-serif;font-size:1.4rem;font-weight:800;color:#fff;'>Ermon.</span>"}
    <div class="ermon-tagline">Budget Tracker</div>
</div>
""", unsafe_allow_html=True)

# ── sidebar nav ───────────────────────────────────────────────────────────────
with st.sidebar:
    page = st.radio("", ["🏠  Dashboard", "👥  Klienci", "💰  Budżety", "📥  Pobierz z API", "⚙️  Ustawienia API"],
                    label_visibility="collapsed")
    st.markdown("---")
    today = date.today()
    st.caption(f"📅 {today.strftime('%d.%m.%Y')}")

if "data" not in st.session_state:
    st.session_state.data = load_data()
data = st.session_state.data

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
    if not data:
        st.info("Brak danych. Dodaj klientów w zakładce 👥 Klienci.")
        st.stop()

    cy, cm, _, _ = st.columns([1,1,1,2])
    sel_year  = cy.selectbox("Rok",  [today.year-1, today.year, today.year+1], index=1, key="dy")
    sel_month = cm.selectbox("Miesiąc", range(1,13), index=today.month-1,
                             format_func=lambda m: calendar.month_abbr[m], key="dm")
    period    = f"{sel_year}-{sel_month:02d}"
    days_left = days_remaining(sel_year, sel_month)

    rows = []
    for cname, cinfo in data.items():
        bud  = cinfo.get("budgets",{}).get(period,{})
        spnd = cinfo.get("spend_override",{}).get(period,{})
        gm   = cinfo.get("budgets_are_gross", False)
        total_r = float(bud.get("total",0))
        g_r     = float(bud.get("google",0))
        fb_r    = float(bud.get("facebook",0))
        g_sn    = float(spnd.get("google",0))
        fb_sn   = float(spnd.get("facebook",0))
        tot_sn  = g_sn + fb_sn
        total_n = netto(total_r) if gm else total_r
        rem_n   = max(0, total_n - tot_sn)
        daily   = round(rem_n/days_left,2) if days_left>0 else 0
        pct     = round(tot_sn/total_n*100,1) if total_n>0 else 0
        rows.append(dict(cname=cname, total_n=total_n, total_g=gross(total_n),
                         g_sn=g_sn, g_sg=gross(g_sn), fb_sn=fb_sn, fb_sg=gross(fb_sn),
                         tot_sn=tot_sn, tot_sg=gross(tot_sn),
                         rem_n=rem_n, rem_g=gross(rem_n), daily=daily, pct=pct, days_left=days_left))

    sum_bud   = sum(r["total_n"] for r in rows)
    sum_spent = sum(r["tot_sn"]  for r in rows)
    sum_rem   = sum_bud - sum_spent
    sum_daily = round(sum_rem/days_left,2) if days_left>0 else 0

    k1,k2,k3,k4,k5 = st.columns(5)
    with k1: kpi_card("Łączny budżet",  f"{sum_bud:,.0f} zł",   "netto")
    with k2: kpi_card("Łącznie wydano", f"{sum_spent:,.0f} zł", f"brutto: {gross(sum_spent):,.0f} zł")
    with k3: kpi_card("Pozostało",      f"{sum_rem:,.0f} zł",   "netto", accent=True)
    with k4: kpi_card("Max dziennie",   f"{sum_daily:,.0f} zł", f"na {days_left} dni")
    with k5: kpi_card("Klientów",       str(len(rows)),         f"{calendar.month_name[sel_month]} {sel_year}")

    section("Klienci")
    for r in rows:
        st.markdown(f'<div class="client-card"><div class="client-name">{r["cname"]}</div>', unsafe_allow_html=True)
        progress_bar(r["pct"])
        st.markdown("</div>", unsafe_allow_html=True)
        c1,c2,c3,c4,c5,c6 = st.columns(6)
        with c1: metric_mini("Budżet netto",  f"{r['total_n']:,.0f} zł", f"brutto {r['total_g']:,.0f}")
        with c2: metric_mini("Google netto",  f"{r['g_sn']:,.0f} zł",    f"brutto {r['g_sg']:,.0f}")
        with c3: metric_mini("Meta netto",    f"{r['fb_sn']:,.0f} zł",   f"brutto {r['fb_sg']:,.0f}")
        with c4: metric_mini("Razem wydano",  f"{r['tot_sn']:,.0f} zł",  f"brutto {r['tot_sg']:,.0f}")
        with c5: metric_mini("Pozostało",     f"{r['rem_n']:,.0f} zł",   f"brutto {r['rem_g']:,.0f}")
        with c6: metric_mini("Max dziennie",  f"{r['daily']:,.0f} zł",   f"{r['days_left']} dni")
        st.markdown("<br>", unsafe_allow_html=True)

    section("Tabela zbiorcza")
    df = pd.DataFrame([{"Klient":r["cname"],"Budżet netto":r["total_n"],"Budżet brutto":r["total_g"],
                         "Google netto":r["g_sn"],"Google brutto":r["g_sg"],
                         "Meta netto":r["fb_sn"],"Meta brutto":r["fb_sg"],
                         "Razem netto":r["tot_sn"],"Razem brutto":r["tot_sg"],
                         "Pozostało netto":r["rem_n"],"Max dziennie":r["daily"],"% budżetu":r["pct"]} for r in rows])
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
            name    = st.text_input("Nazwa klienta")
            g_id    = st.text_input("Google Ads Customer ID", placeholder="123-456-7890")
            fb_id   = st.text_input("Meta Ads Account ID",    placeholder="act_123456789")
            vat_tog = st.checkbox("Budżety podane BRUTTO (z VAT)")
            submit  = st.form_submit_button("➕ Dodaj klienta", use_container_width=True)
        if submit and name.strip():
            key = name.strip()
            if key not in data:
                data[key] = {"google_ads_id":g_id.strip(),"fb_ads_id":fb_id.strip(),
                             "budgets_are_gross":vat_tog,"budgets":{},"spend_override":{}}
                save_data(data); st.success(f"Dodano: **{key}**"); st.rerun()
            else:
                st.warning("Klient o tej nazwie już istnieje.")
    with col2:
        section("Lista klientów")
        if not data:
            st.info("Brak klientów.")
        for cname, cinfo in list(data.items()):
            with st.expander(f"📌 {cname}"):
                c1,c2,c3 = st.columns(3)
                c1.write(f"**Google Ads:** {cinfo.get('google_ads_id') or '—'}")
                c2.write(f"**Meta Ads:** {cinfo.get('fb_ads_id') or '—'}")
                c3.write(f"**Brutto:** {'Tak' if cinfo.get('budgets_are_gross') else 'Nie'}")
                if st.button("🗑️ Usuń", key=f"del_{cname}"):
                    del data[cname]; save_data(data); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# BUDŻETY
# ══════════════════════════════════════════════════════════════════════════════
elif "Budżety" in page:
    page_header("Budżety", "Ustawianie budżetów miesięcznych")
    if not data:
        st.warning("Najpierw dodaj klientów."); st.stop()
    sel_client = st.selectbox("Klient", list(data.keys()))
    cinfo = data[sel_client]
    c1,c2 = st.columns(2)
    sel_year  = c1.selectbox("Rok",  [today.year-1,today.year,today.year+1], index=1)
    sel_month = c2.selectbox("Miesiąc", range(1,13), index=today.month-1,
                             format_func=lambda m: calendar.month_name[m])
    period   = f"{sel_year}-{sel_month:02d}"
    existing = cinfo["budgets"].get(period,{})
    ov       = cinfo.get("spend_override",{}).get(period,{})
    section(f"Budżet — {calendar.month_name[sel_month]} {sel_year}")
    st.caption(f"Tryb: {'BRUTTO' if cinfo.get('budgets_are_gross') else 'NETTO'}")
    with st.form("set_budget"):
        b1,b2,b3 = st.columns(3)
        total_bud = b1.number_input("Łączny budżet (zł)", min_value=0.0, step=100.0, value=float(existing.get("total",0)))
        g_bud     = b2.number_input("Google Ads (zł)",    min_value=0.0, step=100.0, value=float(existing.get("google",0)))
        fb_bud    = b3.number_input("Meta Ads (zł)",      min_value=0.0, step=100.0, value=float(existing.get("facebook",0)))
        st.markdown("---")
        st.caption("Ręczne wydatki (gdy API nie skonfigurowane)")
        s1,s2 = st.columns(2)
        g_spent  = s1.number_input("Wydano Google Ads (zł)", min_value=0.0, step=10.0, value=float(ov.get("google",0)))
        fb_spent = s2.number_input("Wydano Meta Ads (zł)",   min_value=0.0, step=10.0, value=float(ov.get("facebook",0)))
        saved = st.form_submit_button("💾 Zapisz", use_container_width=True)
    if saved:
        cinfo["budgets"][period] = {"total":total_bud,"google":g_bud,"facebook":fb_bud}
        if "spend_override" not in cinfo: cinfo["spend_override"] = {}
        cinfo["spend_override"][period] = {"google":g_spent,"facebook":fb_spent}
        save_data(data); st.success("Zapisano!"); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# POBIERZ Z API
# ══════════════════════════════════════════════════════════════════════════════
elif "Pobierz" in page:
    page_header("Pobierz dane z API", "Synchronizacja z Google Ads i Meta Ads")
    c1,c2 = st.columns(2)
    sel_year2  = c1.selectbox("Rok",  [today.year-1,today.year,today.year+1], index=1)
    sel_month2 = c2.selectbox("Miesiąc", range(1,13), index=today.month-1,
                              format_func=lambda m: calendar.month_name[m])
    period2 = f"{sel_year2}-{sel_month2:02d}"
    if st.button("🔄 Pobierz dla wszystkich klientów", use_container_width=True, type="primary"):
        from api_connectors import fetch_google_spend, fetch_meta_spend, APINotConfiguredError
        progress = st.progress(0)
        clients  = list(data.items())
        results  = []
        for i,(cname,cinfo) in enumerate(clients):
            g_net,fb_net = 0.0,0.0
            g_ok,fb_ok   = False,False
            g_msg,fb_msg = "brak ID","brak ID"
            if cinfo.get("google_ads_id"):
                try:    g_net=fetch_google_spend(cinfo["google_ads_id"],sel_year2,sel_month2); g_ok=True; g_msg="✅ OK"
                except APINotConfiguredError as e: g_msg=f"⚠️ {e}"
                except Exception as e:             g_msg=f"❌ {e}"
            if cinfo.get("fb_ads_id"):
                try:    fb_net=fetch_meta_spend(cinfo["fb_ads_id"],sel_year2,sel_month2); fb_ok=True; fb_msg="✅ OK"
                except APINotConfiguredError as e: fb_msg=f"⚠️ {e}"
                except Exception as e:             fb_msg=f"❌ {e}"
            if g_ok or fb_ok:
                if "spend_override" not in cinfo: cinfo["spend_override"]={}
                ov=cinfo["spend_override"].get(period2,{})
                cinfo["spend_override"][period2]={"google":g_net if g_ok else ov.get("google",0),
                                                   "facebook":fb_net if fb_ok else ov.get("facebook",0)}
            results.append({"Klient":cname,"Google":g_msg,"G netto":f"{g_net:.2f} zł" if g_ok else "—",
                             "Meta":fb_msg,"FB netto":f"{fb_net:.2f} zł" if fb_ok else "—"})
            progress.progress((i+1)/len(clients))
        save_data(data); st.success("Zaktualizowano!")
        st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# USTAWIENIA API
# ══════════════════════════════════════════════════════════════════════════════
elif "Ustawienia" in page:
    page_header("Ustawienia API", "Konfiguracja połączeń z platformami reklamowymi")
    st.info("Dane zapisywane są w pliku `.env` — nigdy nie wrzucaj go na GitHub.")
    env_path = Path(".env")
    env_vals: dict = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k,v = line.split("=",1)
                env_vals[k.strip()] = v.strip()
    section("Google Ads API")
    with st.expander("Rozwiń konfigurację"):
        ga_dev = st.text_input("Developer Token",         value=env_vals.get("GOOGLE_ADS_DEVELOPER_TOKEN",""), type="password")
        ga_cid = st.text_input("Client ID",               value=env_vals.get("GOOGLE_ADS_CLIENT_ID",""))
        ga_cs  = st.text_input("Client Secret",           value=env_vals.get("GOOGLE_ADS_CLIENT_SECRET",""), type="password")
        ga_rt  = st.text_input("Refresh Token",           value=env_vals.get("GOOGLE_ADS_REFRESH_TOKEN",""), type="password")
        ga_lid = st.text_input("Login Customer ID (MCC)", value=env_vals.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID",""))
    section("Meta Ads API")
    with st.expander("Rozwiń konfigurację"):
        fb_tok = st.text_input("Access Token", value=env_vals.get("META_ACCESS_TOKEN",""), type="password")
        fb_ver = st.text_input("API Version",  value=env_vals.get("META_API_VERSION","v19.0"))
    if st.button("💾 Zapisz konfigurację", type="primary"):
        lines=[f"GOOGLE_ADS_DEVELOPER_TOKEN={ga_dev}",f"GOOGLE_ADS_CLIENT_ID={ga_cid}",
               f"GOOGLE_ADS_CLIENT_SECRET={ga_cs}",f"GOOGLE_ADS_REFRESH_TOKEN={ga_rt}",
               f"GOOGLE_ADS_LOGIN_CUSTOMER_ID={ga_lid}",f"META_ACCESS_TOKEN={fb_tok}",f"META_API_VERSION={fb_ver}"]
        env_path.write_text("\n".join(lines)); st.success("Zapisano! Zrestartuj aplikację.")
    section("Jak uzyskać tokeny?")
    with st.expander("Google Ads API — instrukcja"):
        st.markdown("1. Zaloguj się na konto **MCC** → https://ads.google.com/aw/apicenter → pobierz **Developer Token**\n2. W **Google Cloud Console** włącz **Google Ads API** → utwórz OAuth 2.0 credentials\n3. Wygeneruj `refresh_token` przez [OAuth Playground](https://developers.google.com/oauthplayground)")
    with st.expander("Meta Ads API — instrukcja"):
        st.markdown("1. Wejdź na https://developers.facebook.com/ → utwórz aplikację **Business**\n2. Dodaj produkt **Marketing API**\n3. Wygeneruj **Long-lived Access Token** z uprawnieniami `ads_read`")
