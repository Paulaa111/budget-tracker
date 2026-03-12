"""
api_connectors.py
-----------------
Thin wrappers around Google Ads API and Meta Marketing API.
Both functions return the NETTO (net) spend in PLN for a given month.

Requirements (install via requirements.txt):
    google-ads>=23.1.0
    facebook-business>=19.0.0
    python-dotenv
"""

from __future__ import annotations
import os
import calendar
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the app directory
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=False)


class APINotConfiguredError(Exception):
    """Raised when required API credentials are missing."""


# ─────────────────────────────────────────────────────────────────────────────
# Google Ads
# ─────────────────────────────────────────────────────────────────────────────

def fetch_google_spend(customer_id: str, year: int, month: int) -> float:
    """
    Returns total NET spend (PLN) for the given customer_id in the given month.
    customer_id can be with or without dashes, e.g. "123-456-7890" or "1234567890".
    """
    dev_token   = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
    client_id   = os.getenv("GOOGLE_ADS_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
    refresh_token = os.getenv("GOOGLE_ADS_REFRESH_TOKEN")
    login_cid   = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")

    missing = [k for k, v in {
        "GOOGLE_ADS_DEVELOPER_TOKEN": dev_token,
        "GOOGLE_ADS_CLIENT_ID":       client_id,
        "GOOGLE_ADS_CLIENT_SECRET":   client_secret,
        "GOOGLE_ADS_REFRESH_TOKEN":   refresh_token,
    }.items() if not v]

    if missing:
        raise APINotConfiguredError(
            f"Brak konfiguracji Google Ads API: {', '.join(missing)}"
        )

    try:
        from google.ads.googleads.client import GoogleAdsClient  # type: ignore
        from google.ads.googleads.errors import GoogleAdsException  # type: ignore
    except ImportError:
        raise APINotConfiguredError(
            "Pakiet google-ads nie jest zainstalowany. "
            "Uruchom: pip install google-ads"
        )

    # Build config dict (no yaml file needed)
    config = {
        "developer_token": dev_token,
        "client_id":       client_id,
        "client_secret":   client_secret,
        "refresh_token":   refresh_token,
        "use_proto_plus":  True,
    }
    if login_cid:
        config["login_customer_id"] = login_cid.replace("-", "")

    client = GoogleAdsClient.load_from_dict(config)
    ga_service = client.get_service("GoogleAdsService")

    cid_clean = customer_id.replace("-", "")
    last_day  = calendar.monthrange(year, month)[1]
    date_from = f"{year}-{month:02d}-01"
    date_to   = f"{year}-{month:02d}-{last_day:02d}"

    query = f"""
        SELECT
          metrics.cost_micros
        FROM customer
        WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
    """

    try:
        response  = ga_service.search_stream(customer_id=cid_clean, query=query)
        total_micros = 0
        for batch in response:
            for row in batch.results:
                total_micros += row.metrics.cost_micros
        # cost_micros is in the account currency × 10^6
        return round(total_micros / 1_000_000, 2)
    except GoogleAdsException as ex:
        raise RuntimeError(
            f"Google Ads API error: {ex.error.code().name} – "
            + "; ".join(e.message for e in ex.failure.errors)
        )


# ─────────────────────────────────────────────────────────────────────────────
# Meta / Facebook Ads
# ─────────────────────────────────────────────────────────────────────────────

def fetch_meta_spend(account_id: str, year: int, month: int) -> float:
    """
    Returns total NET spend (PLN) for the given Meta Ads account in the given month.
    account_id should be in format "act_XXXXXXXXX".
    """
    access_token = os.getenv("META_ACCESS_TOKEN")
    api_version  = os.getenv("META_API_VERSION", "v19.0")

    if not access_token:
        raise APINotConfiguredError(
            "Brak konfiguracji Meta Ads API: META_ACCESS_TOKEN"
        )

    try:
        from facebook_business.api import FacebookAdsApi  # type: ignore
        from facebook_business.adobjects.adaccount import AdAccount  # type: ignore
        from facebook_business.adobjects.adsinsights import AdsInsights  # type: ignore
    except ImportError:
        raise APINotConfiguredError(
            "Pakiet facebook-business nie jest zainstalowany. "
            "Uruchom: pip install facebook-business"
        )

    FacebookAdsApi.init(access_token=access_token, api_version=api_version)

    last_day  = calendar.monthrange(year, month)[1]
    date_from = f"{year}-{month:02d}-01"
    date_to   = f"{year}-{month:02d}-{last_day:02d}"

    # Ensure account_id starts with act_
    if not account_id.startswith("act_"):
        account_id = f"act_{account_id}"

    account = AdAccount(account_id)
    params  = {
        "time_range": {"since": date_from, "until": date_to},
        "fields":     [AdsInsights.Field.spend],
        "level":      "account",
    }

    insights = account.get_insights(params=params)
    total    = sum(float(row["spend"]) for row in insights if "spend" in row)
    return round(total, 2)
