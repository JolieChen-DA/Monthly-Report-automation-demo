"""
Marketing Automation - Campaign Type 1 Monthly Report
Brand A & Brand B - Journey Campaign_Type_1
Runs automatically on the 6th of each month
Writes to Google Sheets tab: Campaign_Type_1
"""

import requests
import json
import os
import smtplib
import calendar
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# ============================================================
# Config
# ============================================================

API_KEY            = os.environ.get("BRAND_A_API_KEY")
SHEETS_ID          = os.environ.get("GOOGLE_SHEETS_ID")
SHEETS_URL         = f"https://docs.google.com/spreadsheets/d/{SHEETS_ID}/edit"
JOURNEY_ID         = int(os.environ.get("JOURNEY_ID_BRAND_A_CAMPAIGN1"))
JOURNEY_START_DATE = os.environ.get("JOURNEY_START_DATE_BRAND_A_CAMPAIGN1")  # format: DD/MM/YYYY
GMAIL_USER         = os.environ.get("GMAIL_USER")
GMAIL_PASSWORD     = os.environ.get("GMAIL_PASSWORD")
NOTIFY_EMAIL       = os.environ.get("NOTIFY_EMAIL")

TAB_NAME = "Campaign_Type_1"
HEADERS  = ["Month", "Brand_A&B Cumulative Reached", "Brand_A&B Monthly Reached",
            "Brand_C Cumulative Reached", "Brand_C Monthly Reached", "Date Range", "Updated At"]

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
        "month_label":   start.strftime("%Y-%m"),
        "month_range":   f"{start.strftime('%d/%m/%Y')} - {end.strftime('%d/%m/%Y')}",
        "alltime_range": f"{JOURNEY_START_DATE} - {datetime.today().strftime('%d/%m/%Y')}",
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
    """Ensure tab exists; create with headers if not found."""
    try:
        return sh.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=tab_name, rows=500, cols=10)
        ws.append_row(HEADERS)
        return ws

def prepend_row(ws, row_data):
    """Insert new row at index 2 (below header) so latest month is always on top."""
    ws.insert_row(row_data, index=2)
    print(f"[Sheets] Inserted new row into tab '{ws.title}'")

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
    date_info     = get_last_month_range()
    month_label   = date_info["month_label"]
    month_range   = date_info["month_range"]
    alltime_range = date_info["alltime_range"]
    now_str       = datetime.today().strftime("%Y/%m/%d %H:%M")

    print(f"[Info] Month: {month_label}")
    print(f"[Info] Monthly range: {month_range}")
    print(f"[Info] Cumulative range: {alltime_range}")

    entered_month   = fetch_entered(JOURNEY_ID, API_KEY, month_range)
    entered_alltime = fetch_entered(JOURNEY_ID, API_KEY, alltime_range)
    print(f"[OK] Brand_A&B monthly={entered_month:,}  cumulative={entered_alltime:,}")

    gc = get_sheets_client()
    sh = gc.open_by_key(SHEETS_ID)
    ws = ensure_tab(sh, TAB_NAME)
    # Brand_C columns left blank; filled later by report_brand_c.py
    prepend_row(ws, [month_label, entered_alltime, entered_month, "", "", month_range, now_str])

    body = "\n".join([
        f"Campaign_Type_1 Brand_A&B - {month_label}",
        f"Monthly reached: {entered_month:,}",
        f"Cumulative reached: {entered_alltime:,}",
        f"Date range: {month_range}",
        "",
        f"Google Sheets: {SHEETS_URL}",
    ])
    send_email(f"[Auto Report] Campaign_Type_1 Brand_A&B {month_label}", body)

if __name__ == "__main__":
    main()
