import pandas as pd
import os

class DataManager:
    def __init__(self, pilot_file="pilot_roster.csv", drone_file="drone_fleet.csv", missions_file="missions.csv"):
        self.pilot_file = pilot_file
        self.drone_file = drone_file
        self.missions_file = missions_file
        self.load_data()

    def load_data(self):
        # Load Pilots
        try:
            self.pilots = pd.read_csv(self.pilot_file, dtype=str)
            # Ensure columns exist
            required_pilot_cols = ["pilot_id", "name", "skills", "certifications", "location", "status", "current_assignment", "available_from"]
            for col in required_pilot_cols:
                if col not in self.pilots.columns:
                    self.pilots[col] = ""
        except Exception:
            self.pilots = pd.DataFrame(columns=["pilot_id", "name", "skills", "certifications", "location", "status", "current_assignment", "available_from"], dtype=str)

        # Load Drones
        try:
            self.drones = pd.read_csv(self.drone_file, dtype=str)
            required_drone_cols = ["drone_id", "model", "capabilities", "status", "location", "current_assignment", "maintenance_due"]
            for col in required_drone_cols:
                if col not in self.drones.columns:
                    self.drones[col] = ""
        except Exception:
            self.drones = pd.DataFrame(columns=["drone_id", "model", "capabilities", "status", "location", "current_assignment", "maintenance_due"], dtype=str)

        # Load Missions
        try:
            self.missions = pd.read_csv(self.missions_file, dtype=str)
        except Exception:
            self.missions = pd.DataFrame(columns=["project_id", "client", "location", "required_skills", "required_certs", "start_date", "end_date", "priority"], dtype=str)

    def save_pilots(self):
        self.pilots.to_csv(self.pilot_file, index=False)

    def save_drones(self):
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
