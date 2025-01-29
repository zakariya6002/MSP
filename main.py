import os
import json
from fastapi import FastAPI, Request
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Setup templates
templates = Jinja2Templates(directory="templates")

# Mount static files (for styling if needed)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Google Sheets API Credentials (Update with your own JSON file)
SERVICE_ACCOUNT_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Google Sheet ID and Range (Replace with your Sheet ID and range)
SPREADSHEET_ID = "your_google_sheet_id"
RANGE_NAME = "Sheet1!A:B"  # Assuming column B has checkmarks for completed tasks

def get_google_sheet_data():
    """Fetch data from Google Sheets and count completed tasks."""
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()
    
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get("values", [])

    if not values:
        return 0, 0

    total_tasks = len(values) - 1  # Excluding headers
    completed_tasks = sum(1 for row in values[1:] if row[1].strip().lower() in ["yes", "✔", "✅", "tick"])

    return completed_tasks, total_tasks

@app.get("/")
async def read_root(request: Request):
    completed, total = get_google_sheet_data()
    progress = int((completed / total) * 100) if total > 0 else 0
    return templates.TemplateResponse("index.html", {"request": request, "progress": progress})

