"""
Marketing Automation - Campaign Type 2 Monthly Report
Brand_A / Brand_B / Brand_C
Runs automatically on the 1st of each month
Writes to Google Sheets tab: Campaign_Type_2
"""

import requests
import os
import json
import smtplib
import calendar
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# ============================================================
# Config )
# ============================================================

BRAND_A_API_KEY = os.environ.get("BRAND_A_API_KEY")
BRAND_C_API_KEY = os.environ.get("BRAND_C_API_KEY")

SHEETS_ID  = os.environ.get("GOOGLE_SHEETS_ID")
SHEETS_URL = f"https://docs.google.com/spreadsheets/d/{SHEETS_ID}/edit"

GMAIL_USER     = os.environ.get("GMAIL_USER")
GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD")
NOTIFY_EMAIL   = os.environ.get("NOTIFY_EMAIL")

TAB_NAME = "Campaign_Type_2"
HEADERS  = ["Month",
            "Brand_A Campaign_Type_2 Entered",
            "Brand_B Campaign_Type_2 Entered",
            "Brand_C Campaign_Type_2 Entered",
            "Date Range", "Updated At"]

JOURNEYS = [
    {"label": "Brand_A Campaign_Type_2 Entered", "journey_id": int(os.environ.get("JOURNEY_ID_BRAND_A_CAMPAIGN2")), "api_key": BRAND_A_API_KEY},
    {"label": "Brand_B Campaign_Type_2 Entered", "journey_id": int(os.environ.get("JOURNEY_ID_BRAND_B_CAMPAIGN2")), "api_key": BRAND_A_API_KEY},
    {"label": "Brand_C Campaign_Type_2 Entered", "journey_id": int(os.environ.get("JOURNEY_ID_BRAND_C_CAMPAIGN2")), "api_key": BRAND_C_API_KEY},
]

# ============================================================
# Date calculation (previous month)
# ============================================================

def get_last_month_range():
    today = datetime.today()
    prev_month = today.month - 1 if today.month > 1 else 12
    prev_year  = today.year if today.month > 1 else today.year - 1
    last_day   = calendar.monthrange(prev_year, prev_month)[1]
    start = datetime(prev_year, prev_month, 1)
    end   = datetime(prev_year, prev_month, last_day)
    return {
        "month_label": start.strftime("%Y-%m"),
        "stat_date":   f"{start.strftime('%d/%m/%Y')} - {end.strftime('%d/%m/%Y')}",
    }

# ============================================================
# Marketing platform API
# ============================================================

def fetch_entered(journey_id, api_key, stat_date):
    url = f"https://architect-analytics.api.useinsider.com/v1/journey/{journey_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    resp = requests.get(url, headers=headers, params={"statDate": stat_date}, timeout=30)
    resp.raise_for_status()
    return resp.json().get("userMetrics", {}).get("entered", 0)

# ============================================================
# Google Sheets
# ============================================================

def get_sheets_client():
    creds_dict = json.loads(os.environ.get("GOOGLE_CREDENTIALS"))
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    return gspread.authorize(creds)

def ensure_tab(sh, tab_name):
    try:
        return sh.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=tab_name, rows=500, cols=10)
        ws.append_row(HEADERS)
        return ws

# ============================================================
# Email
# ============================================================

def send_email(subject, body):
    msg = MIMEMultipart()
    msg["From"]    = GMAIL_USER
    msg["To"]      = NOTIFY_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, NOTIFY_EMAIL, msg.as_bytes())
    print(f"[Email] Sent: {subject}")

# ============================================================
# Main
# ============================================================

def main():
    date_info   = get_last_month_range()
    stat_date   = date_info["stat_date"]
    month_label = date_info["month_label"]
    now_str     = datetime.today().strftime("%Y/%m/%d %H:%M")

    print(f"[Info] Month: {month_label}, Date range: {stat_date}")

    results = {}
    errors  = []

    for j in JOURNEYS:
        try:
            entered = fetch_entered(j["journey_id"], j["api_key"], stat_date)
            results[j["label"]] = entered
            print(f"[OK] {j['label']} entered={entered:,}")
        except Exception as e:
            results[j["label"]] = ""
            errors.append(f"{j['label']}: {e}")
            print(f"[Error] {j['label']}: {e}")

    gc = get_sheets_client()
    sh = gc.open_by_key(SHEETS_ID)
    ws = ensure_tab(sh, TAB_NAME)
    ws.insert_row([
        month_label,
        results.get("Brand_A Campaign_Type_2 Entered", ""),
        results.get("Brand_B Campaign_Type_2 Entered", ""),
        results.get("Brand_C Campaign_Type_2 Entered", ""),
        stat_date,
        now_str,
    ], index=2)
    print(f"[Sheets] Written to tab '{TAB_NAME}'")

    lines = [
        f"Campaign_Type_2 - {month_label}",
        f"Date range: {stat_date}",
        "",
    ]
    for label, val in results.items():
        lines.append(f"{label}: {val:,}" if isinstance(val, int) else f"{label}: (failed)")
    if errors:
        lines += ["", "== Errors =="] + errors
    lines += ["", f"Google Sheets: {SHEETS_URL}"]

    send_email(f"[Auto Report] Campaign_Type_2 {month_label}", "\n".join(lines))

if __name__ == "__main__":
    main()
