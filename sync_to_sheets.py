import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import os
import sys

# CONFIGURATION
SHEET_ID = "1MqW5St4MriQEAXZ7XjN-dWfHMk21jq-vITCEFnecGSU" # Provided by user
CREDENTIALS_FILE = "credentials.json"
CSVS = {
    "Pilots": "pilot_roster.csv",
    "Drones": "drone_fleet.csv",
    "Missions": "missions.csv"
}

def sync_data():
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"Error: {CREDENTIALS_FILE} not found. Please place it in the root directory.")
        return

    print("Authenticating with Google...")
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)

    print(f"Opening Sheet: {SHEET_ID}...")
    try:
        sheet = client.open_by_key(SHEET_ID)
    except Exception as e:
        print(f"Error opening sheet: {e}")
        print("Did you share the sheet with the Service Account email inside credentials.json?")
        return

    for tab_name, csv_file in CSVS.items():
        if not os.path.exists(csv_file):
            print(f"Skipping {tab_name}: {csv_file} not found locally.")
            continue

        print(f"Syncing {csv_file} -> Tab '{tab_name}'...")
        
        # Read CSV
        df = pd.read_csv(csv_file, dtype=str).fillna("")
        
        # Get or Create Worksheet
        try:
            worksheet = sheet.worksheet(tab_name)
        except gspread.WorksheetNotFound:
            print(f"Tab '{tab_name}' not found. Creating...")
            worksheet = sheet.add_worksheet(title=tab_name, rows=100, cols=20)
        
        # Clear and Update
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        print(f"✓ {tab_name} updated.")

    print("\nSync Complete! Your Google Sheet is ready.")

if __name__ == "__main__":
    sync_data()
