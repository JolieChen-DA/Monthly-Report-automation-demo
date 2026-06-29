# Marketing Automation Report Pipeline

Automated monthly report pipeline that pulls campaign journey metrics from a marketing automation platform API, writes results to Google Sheets, and sends email notifications — replacing manual monthly data retrieval.

## Overview

| Report | Brands | Description |
|--------|--------|-------------|
| Campaign_Type_1 | Brand_A & Brand_B | Monthly + cumulative entered count |
| Campaign_Type_1 | Brand_C | Fills into the same sheet as Brand_A&B |
| Campaign_Type_2 | Brand_A / Brand_B / Brand_C | Monthly entered count for all 3 brands |

## Architecture

```
GitHub Actions (scheduled trigger)
    ↓
Python (calls Marketing Platform API)
    ↓
Google Sheets (auto-write results)
    ↓
Gmail (email notification)
```

**Stack:** Python 3.11 · GitHub Actions · Google Sheets API · Marketing Platform API · Gmail SMTP

All credentials managed via GitHub Secrets — nothing hardcoded.

## File Structure

```
├── report.py            # Campaign_Type_1 Brand_A&B (runs on 6th)
├── report_care.py       # Campaign_Type_2 all brands (runs on 1st)
├── report_brand_c.py    # Campaign_Type_1 Brand_C (runs on 5th-7th)
└── .github/workflows/
    ├── monthly.yml
    ├── monthly_care.yml
    └── monthly_brand_c.yml
```

## Environment Variables (GitHub Secrets)

| Secret | Description |
|--------|-------------|
| `BRAND_A_API_KEY` | API key for Brand_A & Brand_B |
| `BRAND_C_API_KEY` | API key for Brand_C |
| `GOOGLE_SHEETS_ID` | Target spreadsheet ID |
| `GOOGLE_CREDENTIALS` | Google Service Account JSON |
| `GMAIL_USER` | Sender Gmail account |
| `GMAIL_PASSWORD` | Gmail App Password |
| `NOTIFY_EMAIL` | Notification recipient |
| `JOURNEY_ID_BRAND_A_CAMPAIGN1` | Journey ID for Brand_A Campaign_Type_1 |
| `JOURNEY_ID_BRAND_C_CAMPAIGN1` | Journey ID for Brand_C Campaign_Type_1 |
| `JOURNEY_ID_BRAND_A_CAMPAIGN2` | Journey ID for Brand_A Campaign_Type_2 |
| `JOURNEY_ID_BRAND_B_CAMPAIGN2` | Journey ID for Brand_B Campaign_Type_2 |
| `JOURNEY_ID_BRAND_C_CAMPAIGN2` | Journey ID for Brand_C Campaign_Type_2 |
| `JOURNEY_START_DATE_BRAND_A_CAMPAIGN1` | Cumulative start date (DD/MM/YYYY) |
| `JOURNEY_START_DATE_BRAND_C_CAMPAIGN1` | Cumulative start date (DD/MM/YYYY) |

## How It Works

1. GitHub Actions triggers on schedule
2. Script calculates the previous month's date range automatically
3. Calls the marketing platform API to fetch `entered` counts per journey
4. Inserts results into Google Sheets (latest month always on top)
5. Sends email notification confirming execution
