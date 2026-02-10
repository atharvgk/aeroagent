import pandas as pd
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Sheet ID from env
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

class DataManager:
    def __init__(self, pilot_file="pilot_roster.csv", drone_file="drone_fleet.csv", missions_file="missions.csv"):
        self.pilot_file = pilot_file
        self.drone_file = drone_file
        self.missions_file = missions_file
        self.use_sheets = False
        self.sheet = None
        
        # Check if Sheet ID exists
        if not SHEET_ID:
            print("⚠️ GOOGLE_SHEET_ID not found in .env. Falling back to CSV.")
        
        # Try connecting to Google Sheets
        elif os.path.exists("credentials.json"):
            try:
                scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
                creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
                client = gspread.authorize(creds)
                self.sheet = client.open_by_key(SHEET_ID)
                self.use_sheets = True
                print("✅ Connected to Google Sheets (Local)")
            except Exception as e:
                print(f"⚠️ Google Sheets Connection Failed: {e}. Falling back to CSV.")
        
        # Streamlit Cloud Secrets Fallback
        else:
            try:
                import streamlit as st
                # Check for both common names
                secrets_key = None
                if "gcp_service_account" in st.secrets:
                    secrets_key = "gcp_service_account"
                elif "google_service_account" in st.secrets:
                    secrets_key = "google_service_account"
                
                if secrets_key:
                    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
                    creds_dict = st.secrets[secrets_key]
                    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
                    client = gspread.authorize(creds)
                    self.sheet = client.open_by_key(SHEET_ID)
                    self.use_sheets = True
                    print("✅ Connected to Google Sheets (Streamlit Secrets)")
            except Exception:
                print("⚠️ No credentials found (Local or Secrets). Falling back to CSV.")
        
        self.load_data()

    def _load_sheet_df(self, tab_name, required_cols):
        try:
            worksheet = self.sheet.worksheet(tab_name)
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            # Ensure all columns exist and are strings (to match CSV behavior)
            for col in required_cols:
                if col not in df.columns:
                    df[col] = ""
            return df.astype(str)
        except Exception as e:
            print(f"Error loading {tab_name} from Sheets: {e}")
            return pd.DataFrame(columns=required_cols, dtype=str)

    def load_data(self):
        # Define Columns
        cols_pilots = ["pilot_id", "name", "skills", "certifications", "location", "status", "current_assignment", "available_from"]
        cols_drones = ["drone_id", "model", "capabilities", "status", "location", "current_assignment", "maintenance_due"]
        cols_missions = ["project_id", "client", "location", "required_skills", "required_certs", "start_date", "end_date", "priority"]

        if self.use_sheets:
            print("Loading data from Google Sheets...")
            self.pilots = self._load_sheet_df("Pilots", cols_pilots)
            self.drones = self._load_sheet_df("Drones", cols_drones)
            self.missions = self._load_sheet_df("Missions", cols_missions)
        else:
            print("Loading data from local CSVs...")
            self.pilots = self._load_csv(self.pilot_file, cols_pilots)
            self.drones = self._load_csv(self.drone_file, cols_drones)
            self.missions = self._load_csv(self.missions_file, cols_missions)

    def _load_csv(self, filename, required_cols):
        try:
            df = pd.read_csv(filename, dtype=str).fillna("")
            for col in required_cols:
                if col not in df.columns:
                    df[col] = ""
            return df
        except Exception:
            return pd.DataFrame(columns=required_cols, dtype=str)

    def _save_to_sheet(self, tab_name, df):
        if not self.use_sheets: return
        try:
            worksheet = self.sheet.worksheet(tab_name)
            worksheet.clear()
            # method update requires [list of headers] + [list of rows]
            worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        except Exception as e:
            print(f"Error saving to {tab_name}: {e}")

    def save_pilots(self):
        if self.use_sheets:
            self._save_to_sheet("Pilots", self.pilots)
        else:
            self.pilots.to_csv(self.pilot_file, index=False)

    def save_drones(self):
        if self.use_sheets:
            self._save_to_sheet("Drones", self.drones)
        else:
            self.drones.to_csv(self.drone_file, index=False)

    def get_pilot(self, pilot_id):
        df = self.pilots[self.pilots['pilot_id'] == pilot_id]
        if df.empty: return None
        return df.iloc[0].to_dict()

    def get_drone(self, drone_id):
        df = self.drones[self.drones['drone_id'] == drone_id]
        if df.empty: return None
        return df.iloc[0].to_dict()

    def get_mission(self, project_id):
        df = self.missions[self.missions['project_id'] == project_id]
        if df.empty: return None
        return df.iloc[0].to_dict()
        
    def update_pilot_status(self, pilot_id, new_status):
        if pilot_id in self.pilots['pilot_id'].values:
            self.pilots.loc[self.pilots['pilot_id'] == pilot_id, 'status'] = new_status
            self.save_pilots()
            return True
        return False
    
    def update_drone_status(self, drone_id, new_status):
        if drone_id in self.drones['drone_id'].values:
            self.drones.loc[self.drones['drone_id'] == drone_id, 'status'] = new_status
            self.save_drones()
            return True
        return False

    def assign_pilot_to_mission(self, pilot_id, project_id):
        if pilot_id in self.pilots['pilot_id'].values:
            self.pilots.loc[self.pilots['pilot_id'] == pilot_id, 'current_assignment'] = project_id
            self.pilots.loc[self.pilots['pilot_id'] == pilot_id, 'status'] = 'Assigned'
            self.save_pilots()
            return True
        return False

    def assign_drone_to_mission(self, drone_id, project_id):
        if drone_id in self.drones['drone_id'].values:
            self.drones.loc[self.drones['drone_id'] == drone_id, 'current_assignment'] = project_id
            self.drones.loc[self.drones['drone_id'] == drone_id, 'status'] = 'Assigned'
            self.save_drones()
            return True
        return False
