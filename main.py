import os
import json
import datetime
from fastapi import FastAPI, Request, HTTPException
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Google Sheets API Credentials via Environment Variable
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SPREADSHEET_ID = "1yLEGtm2mxOuSaB4dBt7GQiw-C5Dlp7R2mMraI5U2tdY"
RANGE_NAME = "Sheet1!A:C"  # Adjusted range to include "Completed" column

# Storage for daily logs
progress_log = []

def get_google_sheet_data():
    """Fetch data from Google Sheets and count completed tasks."""
    credentials_json = os.getenv("GOOGLE_CREDENTIALS")
    if not credentials_json:
        raise HTTPException(status_code=500, detail="Missing GOOGLE_CREDENTIALS environment variable")

    try:
        credentials_dict = json.loads(credentials_json)
        creds = Credentials.from_service_account_info(credentials_dict, scopes=SCOPES)
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()

        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get("values", [])

        if not values:
            return 0, 0

        total_tasks = len(values) - 1  # Exclude headers
        completed_tasks = sum(1 for row in values[1:] if len(row) > 2 and row[2].strip().lower() in ["yes", "✔", "✅", "tick"])

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        progress_log.append((timestamp, completed_tasks))
        if len(progress_log) > 10:
            progress_log.pop(0)

        return completed_tasks, total_tasks
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Sheets API Error: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    completed, total = get_google_sheet_data()
    progress = int((completed / total) * 100) if total > 0 else 0
    
    return templates.TemplateResponse("progress.html", {"request": request, "progress": progress, "progress_log": progress_log})
