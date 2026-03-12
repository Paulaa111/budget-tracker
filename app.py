import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import calendar
import json
import os
from pathlib import Path

# ── page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Budget Tracker – Klienci",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── helpers ───────────────────────────────────────────────────────────────────
DATA_FILE = Path("clients_data.json")
VAT_RATE   = 0.23          # 23 % VAT

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
        return max(0, (end - today).days + 1)   # include today
    if date(year, month, 1) > today:
        return last
    return 0

def gross(net: float) -> float:
    return round(net * (1 + VAT_RATE), 2)

def netto(gross_val: float) -> float:
    return round(gross_val / (1 + VAT_RATE), 2)

# ── sidebar – navigation ──────────────────────────────────────────────────────
st.sidebar.title("📊 Budget Tracker")
page = st.sidebar.radio(
    "Nawigacja",
    ["🏠 Dashboard", "👥 Klienci", "💰 Budżety", "📥 Pobierz dane z API", "⚙️ Ustawienia API"],
)
st.sidebar.markdown("---")
today = date.today()
st.sidebar.caption(f"Dziś: **{today.strftime('%d.%m.%Y')}**")

# ── load persistent data ──────────────────────────────────────────────────────
if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data   # shortcut

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Klienci
# ══════════════════════════════════════════════════════════════════════════════
if page == "👥 Klienci":
    st.title("👥 Zarządzanie klientami")
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Dodaj klienta")
        with st.form("add_client"):
            name    = st.text_input("Nazwa klienta")
            g_id    = st.text_input("Google Ads Customer ID (opcjonalnie)", placeholder="123-456-7890")
            fb_id   = st.text_input("Meta Ads Account ID (opcjonalnie)", placeholder="act_123456789")
            vat_tog = st.checkbox("Budżety podane BRUTTO (z VAT)", value=False)
            submit  = st.form_submit_button("➕ Dodaj", use_container_width=True)

        if submit and name.strip():
            key = name.strip()
            if key not in data:
                data[key] = {
                    "google_ads_id": g_id.strip(),
                    "fb_ads_id": fb_id.strip(),
                    "budgets_are_gross": vat_tog,
                    "budgets": {},
                    "spend_override": {},
                }
                save_data(data)
                st.success(f"Dodano klienta: **{key}**")
                st.rerun()
            else:
                st.warning("Klient o tej nazwie już istnieje.")

    with col2:
        st.subheader("Lista klientów")
        if not data:
            st.info("Brak klientów. Dodaj pierwszego klienta.")
        else:
            for cname, cinfo in list(data.items()):
                with st.expander(f"📌 {cname}"):
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"**Google Ads ID:** {cinfo.get('google_ads_id') or '—'}")
                    c2.write(f"**Meta Ads ID:** {cinfo.get('fb_ads_id') or '—'}")
                    c3.write(f"**Budżety brutto:** {'Tak' if cinfo.get('budgets_are_gross') else 'Nie'}")
                    if st.button(f"🗑️ Usuń {cname}", key=f"del_{cname}"):
                        del data[cname]
                        save_data(data)
                        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Budżety
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💰 Budżety":
    st.title("💰 Budżety miesięczne")

    if not data:
        st.warning("Najpierw dodaj klientów w zakładce 👥 Klienci.")
        st.stop()

    sel_client = st.selectbox("Wybierz klienta", list(data.keys()))
    cinfo = data[sel_client]

    col_y, col_m = st.columns(2)
    sel_year  = col_y.selectbox("Rok",  [today.year - 1, today.year, today.year + 1], index=1)
    sel_month = col_m.selectbox("Miesiąc", list(range(1, 13)),
                                index=today.month - 1,
                                format_func=lambda m: calendar.month_name[m])

    period = f"{sel_year}-{sel_month:02d}"
    existing = cinfo["budgets"].get(period, {})

    st.subheader(f"Budżet dla: **{sel_client}** — {calendar.month_name[sel_month]} {sel_year}")
    gross_mode = cinfo.get("budgets_are_gross", False)
    st.caption(f"Tryb kwot: {'BRUTTO (z VAT)' if gross_mode else 'NETTO (bez VAT)'}")

    with st.form("set_budget"):
        c1, c2, c3 = st.columns(3)
        total_bud  = c1.number_input("Łączny budżet (zł)", min_value=0.0, step=100.0,
                                     value=float(existing.get("total", 0)))
        google_bud = c2.number_input("Google Ads (zł)",    min_value=0.0, step=100.0,
                                     value=float(existing.get("google", 0)))
        fb_bud     = c3.number_input("Meta / FB Ads (zł)", min_value=0.0, step=100.0,
                                     value=float(existing.get("facebook", 0)))

        # manual spend overrides (if API not connected)
        st.markdown("---")
        st.caption("Ręczne wydatki (jeśli API nie jest skonfigurowane)")
        c4, c5 = st.columns(2)
        ov = cinfo.get("spend_override", {}).get(period, {})
        google_spent = c4.number_input("Wydano Google Ads (zł)", min_value=0.0, step=10.0,
                                       value=float(ov.get("google", 0)))
        fb_spent     = c5.number_input("Wydano Meta Ads (zł)",   min_value=0.0, step=10.0,
                                       value=float(ov.get("facebook", 0)))

        saved = st.form_submit_button("💾 Zapisz", use_container_width=True)

    if saved:
        cinfo["budgets"][period] = {
            "total": total_bud,
            "google": google_bud,
            "facebook": fb_bud,
        }
        if "spend_override" not in cinfo:
            cinfo["spend_override"] = {}
        cinfo["spend_override"][period] = {
            "google": google_spent,
            "facebook": fb_spent,
        }
        save_data(data)
        st.success("Zapisano budżet!")
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Pobierz dane z API
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📥 Pobierz dane z API":
    st.title("📥 Pobierz wydatki z API")

    col_y2, col_m2 = st.columns(2)
    sel_year2  = col_y2.selectbox("Rok",  [today.year - 1, today.year, today.year + 1], index=1)
    sel_month2 = col_m2.selectbox("Miesiąc", list(range(1, 13)),
                                  index=today.month - 1,
                                  format_func=lambda m: calendar.month_name[m])
    period2 = f"{sel_year2}-{sel_month2:02d}"

    if st.button("🔄 Pobierz dla wszystkich klientów", use_container_width=True, type="primary"):
        from api_connectors import fetch_google_spend, fetch_meta_spend, APINotConfiguredError

        progress = st.progress(0)
        clients  = list(data.items())
        results  = []

        for i, (cname, cinfo) in enumerate(clients):
            g_net, fb_net = 0.0, 0.0
            g_ok,  fb_ok  = False, False
            g_msg,  fb_msg = "brak ID", "brak ID"

            if cinfo.get("google_ads_id"):
                try:
                    g_net = fetch_google_spend(
                        customer_id=cinfo["google_ads_id"],
                        year=sel_year2, month=sel_month2,
                    )
                    g_ok  = True
                    g_msg = "✅ OK"
                except APINotConfiguredError as e:
                    g_msg = f"⚠️ {e}"
                except Exception as e:
                    g_msg = f"❌ {e}"

            if cinfo.get("fb_ads_id"):
                try:
                    fb_net = fetch_meta_spend(
                        account_id=cinfo["fb_ads_id"],
                        year=sel_year2, month=sel_month2,
                    )
                    fb_ok  = True
                    fb_msg = "✅ OK"
                except APINotConfiguredError as e:
                    fb_msg = f"⚠️ {e}"
                except Exception as e:
                    fb_msg = f"❌ {e}"

            if g_ok or fb_ok:
                if "spend_override" not in cinfo:
                    cinfo["spend_override"] = {}
                existing_ov = cinfo["spend_override"].get(period2, {})
                cinfo["spend_override"][period2] = {
                    "google":   g_net if g_ok else existing_ov.get("google", 0),
                    "facebook": fb_net if fb_ok else existing_ov.get("facebook", 0),
                }

            results.append({
                "Klient": cname,
                "Google Ads": g_msg,
                "G wydano (netto)": f"{g_net:.2f} zł" if g_ok else "—",
                "Meta Ads": fb_msg,
                "FB wydano (netto)": f"{fb_net:.2f} zł" if fb_ok else "—",
            })
            progress.progress((i + 1) / len(clients))

        save_data(data)
        st.success("Zaktualizowano dane!")
        st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Ustawienia API
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Ustawienia API":
    st.title("⚙️ Konfiguracja API")
    st.info("Dane są zapisywane w pliku `.env` i nigdy nie trafiają do repozytorium.")

    env_path = Path(".env")
    env_vals: dict[str, str] = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env_vals[k.strip()] = v.strip()

    st.subheader("Google Ads API")
    with st.expander("Pokaż / edytuj"):
        ga_dev  = st.text_input("GOOGLE_ADS_DEVELOPER_TOKEN", value=env_vals.get("GOOGLE_ADS_DEVELOPER_TOKEN", ""), type="password")
        ga_cid  = st.text_input("GOOGLE_ADS_CLIENT_ID",       value=env_vals.get("GOOGLE_ADS_CLIENT_ID", ""))
        ga_cs   = st.text_input("GOOGLE_ADS_CLIENT_SECRET",   value=env_vals.get("GOOGLE_ADS_CLIENT_SECRET", ""), type="password")
        ga_rt   = st.text_input("GOOGLE_ADS_REFRESH_TOKEN",   value=env_vals.get("GOOGLE_ADS_REFRESH_TOKEN", ""), type="password")
        ga_lid  = st.text_input("GOOGLE_ADS_LOGIN_CUSTOMER_ID (MCC)", value=env_vals.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", ""))

    st.subheader("Meta Ads API")
    with st.expander("Pokaż / edytuj"):
        fb_tok  = st.text_input("META_ACCESS_TOKEN", value=env_vals.get("META_ACCESS_TOKEN", ""), type="password")
        fb_ver  = st.text_input("META_API_VERSION",  value=env_vals.get("META_API_VERSION", "v19.0"))

    if st.button("💾 Zapisz ustawienia API", type="primary"):
        lines = [
            f"GOOGLE_ADS_DEVELOPER_TOKEN={ga_dev}",
            f"GOOGLE_ADS_CLIENT_ID={ga_cid}",
            f"GOOGLE_ADS_CLIENT_SECRET={ga_cs}",
            f"GOOGLE_ADS_REFRESH_TOKEN={ga_rt}",
            f"GOOGLE_ADS_LOGIN_CUSTOMER_ID={ga_lid}",
            f"META_ACCESS_TOKEN={fb_tok}",
            f"META_API_VERSION={fb_ver}",
        ]
        env_path.write_text("\n".join(lines))
        st.success("Zapisano! Zrestartuj aplikację, aby odświeżyć połączenia.")

    st.markdown("---")
    st.subheader("📖 Jak uzyskać tokeny?")
    with st.expander("Google Ads API"):
        st.markdown("""
1. Wejdź na [Google Ads API Center](https://ads.google.com/aw/apicenter)
2. Pobierz **Developer Token** (konto MCC)
3. Utwórz projekt w [Google Cloud Console](https://console.cloud.google.com/)
4. Włącz **Google Ads API**
5. Utwórz OAuth 2.0 credentials → pobierz `client_id` i `client_secret`
6. Wygeneruj `refresh_token` za pomocą [OAuth Playground](https://developers.google.com/oauthplayground/)
        """)
    with st.expander("Meta Ads API"):
        st.markdown("""
1. Wejdź na [Meta for Developers](https://developers.facebook.com/)
2. Utwórz aplikację typu **Business**
3. Dodaj produkt **Marketing API**
4. Wygeneruj **Long-lived Access Token** z uprawnieniami `ads_read`
5. Account ID znajdziesz w Menedżerze Reklam Meta
        """)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Dashboard  (domyślna)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🏠 Dashboard":
    st.title("🏠 Dashboard – Budżety klientów")

    if not data:
        st.info("Brak danych. Przejdź do zakładki 👥 **Klienci**, aby dodać pierwszego klienta.")
        st.stop()

    # period selector
    col_y0, col_m0, _ = st.columns([1, 1, 3])
    sel_year0  = col_y0.selectbox("Rok",  [today.year - 1, today.year, today.year + 1], index=1, key="dy")
    sel_month0 = col_m0.selectbox("Miesiąc", list(range(1, 13)),
                                  index=today.month - 1,
                                  format_func=lambda m: calendar.month_name[m], key="dm")
    period0     = f"{sel_year0}-{sel_month0:02d}"
    days_left   = days_remaining(sel_year0, sel_month0)
    total_days  = calendar.monthrange(sel_year0, sel_month0)[1]
    days_passed = total_days - days_left

    # ── build summary rows ────────────────────────────────────────────────────
    rows = []
    for cname, cinfo in data.items():
        bud   = cinfo.get("budgets", {}).get(period0, {})
        spend = cinfo.get("spend_override", {}).get(period0, {})
        gross_mode = cinfo.get("budgets_are_gross", False)

        total_bud_raw = float(bud.get("total", 0))
        g_bud_raw     = float(bud.get("google", 0))
        fb_bud_raw    = float(bud.get("facebook", 0))

        g_spent_net  = float(spend.get("google", 0))
        fb_spent_net = float(spend.get("facebook", 0))
        total_spent_net = g_spent_net + fb_spent_net

        # normalise all budgets to netto
        if gross_mode:
            total_bud_net = netto(total_bud_raw)
            g_bud_net     = netto(g_bud_raw)
            fb_bud_net    = netto(fb_bud_raw)
        else:
            total_bud_net = total_bud_raw
            g_bud_net     = g_bud_raw
            fb_bud_net    = fb_bud_raw

        remaining_net   = max(0, total_bud_net - total_spent_net)
        daily_remaining = round(remaining_net / days_left, 2) if days_left > 0 else 0
        pct_used        = round(total_spent_net / total_bud_net * 100, 1) if total_bud_net > 0 else 0

        rows.append({
            "cname":            cname,
            "total_bud_net":    total_bud_net,
            "total_bud_gross":  gross(total_bud_net),
            "g_bud_net":        g_bud_net,
            "fb_bud_net":       fb_bud_net,
            "g_spent_net":      g_spent_net,
            "g_spent_gross":    gross(g_spent_net),
            "fb_spent_net":     fb_spent_net,
            "fb_spent_gross":   gross(fb_spent_net),
            "total_spent_net":  total_spent_net,
            "total_spent_gross":gross(total_spent_net),
            "remaining_net":    remaining_net,
            "remaining_gross":  gross(remaining_net),
            "daily_remaining":  daily_remaining,
            "pct_used":         pct_used,
            "days_left":        days_left,
        })

    # ── top KPI strip ─────────────────────────────────────────────────────────
    total_budget_sum = sum(r["total_bud_net"] for r in rows)
    total_spent_sum  = sum(r["total_spent_net"] for r in rows)
    total_remaining  = total_budget_sum - total_spent_sum

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Łączny budżet (netto)", f"{total_budget_sum:,.0f} zł")
    k2.metric("Łącznie wydano (netto)", f"{total_spent_sum:,.0f} zł",
              delta=f"{total_spent_sum/total_budget_sum*100:.1f} %" if total_budget_sum else None)
    k3.metric("Pozostało (netto)", f"{total_remaining:,.0f} zł")
    k4.metric("Dni pozostałych w miesiącu", days_left)

    st.markdown("---")

    # ── per-client cards ──────────────────────────────────────────────────────
    st.subheader("Szczegóły per klient")
    for r in rows:
        with st.expander(f"📌 {r['cname']}  —  {r['pct_used']}% budżetu wykorzystane", expanded=False):
            # progress bar
            pct_clamped = min(r["pct_used"] / 100, 1.0)
            bar_color   = "🟢" if r["pct_used"] < 75 else ("🟡" if r["pct_used"] < 95 else "🔴")
            st.markdown(f"{bar_color} **{r['pct_used']}%** wykorzystanego budżetu")
            st.progress(pct_clamped)

            # metrics row
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Budżet netto",         f"{r['total_bud_net']:,.2f} zł")
            m1.caption(f"brutto: {r['total_bud_gross']:,.2f} zł")
            m2.metric("Google Ads wydano",    f"{r['g_spent_net']:,.2f} zł netto")
            m2.caption(f"brutto: {r['g_spent_gross']:,.2f} zł")
            m3.metric("Meta Ads wydano",      f"{r['fb_spent_net']:,.2f} zł netto")
            m3.caption(f"brutto: {r['fb_spent_gross']:,.2f} zł")
            m4.metric("Pozostało (netto)",    f"{r['remaining_net']:,.2f} zł")
            m4.caption(f"brutto: {r['remaining_gross']:,.2f} zł")
            m5.metric("Max dziennie",         f"{r['daily_remaining']:,.2f} zł/dzień")
            m5.caption(f"na {r['days_left']} dni")

    st.markdown("---")

    # ── table view ────────────────────────────────────────────────────────────
    st.subheader("📋 Tabela zbiorcza")
    df = pd.DataFrame([{
        "Klient":               r["cname"],
        "Budżet netto (zł)":    r["total_bud_net"],
        "Budżet brutto (zł)":   r["total_bud_gross"],
        "Google wydano netto":  r["g_spent_net"],
        "Google wydano brutto": r["g_spent_gross"],
        "Meta wydano netto":    r["fb_spent_net"],
        "Meta wydano brutto":   r["fb_spent_gross"],
        "Razem wydano netto":   r["total_spent_net"],
        "Razem wydano brutto":  r["total_spent_gross"],
        "Pozostało netto":      r["remaining_net"],
        "Max dziennie (netto)": r["daily_remaining"],
        "% budżetu":            r["pct_used"],
    } for r in rows])

    st.dataframe(
        df.style.format({
            "Budżet netto (zł)":    "{:.2f}",
            "Budżet brutto (zł)":   "{:.2f}",
            "Google wydano netto":  "{:.2f}",
            "Google wydano brutto": "{:.2f}",
            "Meta wydano netto":    "{:.2f}",
            "Meta wydano brutto":   "{:.2f}",
            "Razem wydano netto":   "{:.2f}",
            "Razem wydano brutto":  "{:.2f}",
            "Pozostało netto":      "{:.2f}",
            "Max dziennie (netto)": "{:.2f}",
            "% budżetu":            "{:.1f}%",
        }).background_gradient(subset=["% budżetu"], cmap="RdYlGn_r", vmin=0, vmax=100),
        use_container_width=True,
        hide_index=True,
    )

    # export
    csv = df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
    st.download_button("⬇️ Pobierz CSV", csv,
                       file_name=f"budgety_{period0}.csv",
                       mime="text/csv")
