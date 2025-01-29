import os
import json
import datetime
from fastapi import FastAPI, Request
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()

# Setup templates
templates = Jinja2Templates(directory="templates")

# Mount static files (for styling if needed)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Google Sheets API Credentials (Update with your own JSON file)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "credentials.json")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Google Sheet ID and Range (Replace with your Sheet ID and range)
SPREADSHEET_ID = "1yLEGtm2mxOuSaB4dBt7GQiw-C5Dlp7R2mMraI5U2tdY"
RANGE_NAME = "Sheet1!A:C"  # Adjusted range to include "Completed" column

# Storage for daily logs
progress_log = []


def get_google_sheet_data():
    """Fetch data from Google Sheets and count completed tasks."""
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()
    
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get("values", [])

    if not values:
        return 0, 0
    
    # Extracting data
    total_tasks = len(values) - 1  # Excluding headers
    completed_tasks = sum(1 for row in values[1:] if len(row) > 2 and row[2].strip().lower() in ["yes", "✔", "✅", "tick"])

    # Log progress daily (only keep last 10 records)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    progress_log.append((timestamp, completed_tasks))
    if len(progress_log) > 10:
        progress_log.pop(0)
    
    return completed_tasks, total_tasks

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    completed, total = get_google_sheet_data()
    progress = int((completed / total) * 100) if total > 0 else 0
    
    html_content = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Progress Tracker</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                text-align: center;
                margin: 20px;
            }}
            .progress-container {{
                width: 50%;
                background-color: #e0e0e0;
                border-radius: 10px;
                margin: 20px auto;
                padding: 10px;
                box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.2);
            }}
            .progress-bar {{
                height: 30px;
                width: {progress}%;
                background-color: #4caf50;
                border-radius: 10px;
                transition: width 0.5s;
                text-align: center;
                color: white;
                line-height: 30px;
                font-weight: bold;
            }}
            table {{
                width: 50%;
                margin: 20px auto;
                border-collapse: collapse;
            }}
            th, td {{
                border: 1px solid black;
                padding: 8px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <h1>Task Progress</h1>
        <div class="progress-container">
            <div class="progress-bar">{progress}%</div>
        </div>
        
        <h2>Progress Log</h2>
        <table>
            <tr>
                <th>Timestamp</th>
                <th>Completed Tasks</th>
            </tr>
            {''.join(f'<tr><td>{log[0]}</td><td>{log[1]}</td></tr>' for log in progress_log)}
        </table>
    </body>
    </html>
    '''
    
    return HTMLResponse(content=html_content)
