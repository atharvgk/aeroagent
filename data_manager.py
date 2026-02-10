import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from datetime import datetime

class DataManager:
    def __init__(self, pilot_file="pilot_roster.csv", drone_file="drone_fleet.csv", missions_file="missions.csv"):
        self.pilot_file = pilot_file
        self.drone_file = drone_file
        self.missions_file = missions_file
        self.use_sheets = False
        self.gc = None
        self.sh_pilots = None
        self.sh_drones = None
        
        # Try to connect to Google Sheets if credentials exist
        if os.path.exists("credentials.json"):
            try:
                scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
                self.gc = gspread.authorize(creds)
                self.use_sheets = True
                # Try to open sheets
                try:
                    self.sh_pilots = self.gc.open("Pilot Roster").sheet1
                    self.sh_drones = self.gc.open("Drone Fleet").sheet1
                except Exception as sheet_err:
                    print(f"Error opening Sheets: {sheet_err}. specific sheets 'Pilot Roster' and 'Drone Fleet' must exist.")
                    self.use_sheets = False
            except Exception as e:
                print(f"Failed to connect to Sheets: {e}")
                self.use_sheets = False

        self.pilots = self.load_pilots()
        self.drones = self.load_drones()
        self.missions = self.load_missions()

    def load_pilots(self):
        try:
            return pd.read_csv(self.pilot_file)
        except Exception:
            return pd.DataFrame(columns=["pilot_id", "name", "skills", "certifications", "location", "status", "current_assignment", "available_from"])

    def load_drones(self):
        try:
            return pd.read_csv(self.drone_file)
        except Exception:
            return pd.DataFrame(columns=["drone_id", "model", "capabilities", "status", "location", "current_assignment", "maintenance_due"])

    def load_missions(self):
        try:
            return pd.read_csv(self.missions_file)
        except Exception:
            return pd.DataFrame(columns=["project_id", "client", "location", "required_skills", "required_certs", "start_date", "end_date", "priority"])

    def save_pilots(self):
        self.pilots.to_csv(self.pilot_file, index=False)
        if self.use_sheets and self.sh_pilots:
            try:
                # Update entire sheet content
                self.sh_pilots.clear()
                self.sh_pilots.update([self.pilots.columns.values.tolist()] + self.pilots.values.tolist())
            except Exception as e:
                print(f"Error syncing pilots to Sheets: {e}")

    def save_drones(self):
        self.drones.to_csv(self.drone_file, index=False)
        if self.use_sheets and self.sh_drones:
            try:
                self.sh_drones.clear()
                self.sh_drones.update([self.drones.columns.values.tolist()] + self.drones.values.tolist())
            except Exception as e:
                print(f"Error syncing drones to Sheets: {e}")
            
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

    def assign_pilot(self, pilot_id, project_id):
        if pilot_id in self.pilots['pilot_id'].values:
            self.pilots.loc[self.pilots['pilot_id'] == pilot_id, 'current_assignment'] = project_id
            self.pilots.loc[self.pilots['pilot_id'] == pilot_id, 'status'] = 'Assigned'
            self.save_pilots()
            return True
        return False
        
    def assign_drone(self, drone_id, project_id):
        if drone_id in self.drones['drone_id'].values:
            self.drones.loc[self.drones['drone_id'] == drone_id, 'current_assignment'] = project_id
            self.drones.loc[self.drones['drone_id'] == drone_id, 'status'] = 'Assigned'
            self.save_drones()
            return True
        return False
