from datetime import datetime
import pandas as pd
from dateutil import parser

class Logic:
    def __init__(self, data_manager):
        self.dm = data_manager

    def parse_skills(self, skills_str):
        if pd.isna(skills_str):
            return []
        return [s.strip().lower() for s in str(skills_str).split(',')]

    def check_conflicts(self, project_id, pilot_id=None, drone_id=None):
        conflicts = []
        
        # Get Mission Details
        mission = self.dm.missions[self.dm.missions['project_id'] == project_id]
        if mission.empty:
            return ["Mission not found"]
        mission = mission.iloc[0]
        mission_start = parser.parse(str(mission['start_date']))
        mission_end = parser.parse(str(mission['end_date']))

        # Check Pilot Conflicts
        if pilot_id:
            pilot = self.dm.pilots[self.dm.pilots['pilot_id'] == pilot_id]
            if not pilot.empty:
                pilot = pilot.iloc[0]
                
                # Check 1: Status (if already assigned to ANOTHER project active at same time)
                # For simplicity in this CSV model, 'current_assignment' is a single field.
                # In a real DB, we'd check an 'assignments' table for overlaps.
                # Here we check if they are 'Available' or if their current assignment is not this one (reassignment context)
                if pilot['status'] == 'On Leave':
                    conflicts.append(f"Pilot {pilot['name']} is On Leave.")
                
                if pilot['current_assignment'] != '–' and pilot['current_assignment'] != project_id:
                    # Check overlap with existing assignment
                    # In this simple model (referenced CSVs), we assume 'current_assignment' implies active NOW or SOON.
                    # We should check the dates of the *other* project they are assigned to.
                    other_proj = self.dm.missions[self.dm.missions['project_id'] == pilot['current_assignment']]
                    if not other_proj.empty:
                        other_proj = other_proj.iloc[0]
                        other_start = parser.parse(str(other_proj['start_date']))
                        other_end = parser.parse(str(other_proj['end_date']))
                        
                        # Check Date Overlap
                        if (mission_start <= other_end) and (mission_end >= other_start):
                            conflicts.append(f"Pilot {pilot['name']} is already assigned to {pilot['current_assignment']} during these dates.")

                # Check 2: Skills & Certs
                req_skills = self.parse_skills(mission['required_skills'])
                pilot_skills = self.parse_skills(pilot['skills'])
                missing_skills = [s for s in req_skills if s not in pilot_skills]
                if missing_skills:
                    conflicts.append(f"Pilot {pilot['name']} missing skills: {', '.join(missing_skills)}")

                req_certs = self.parse_skills(mission['required_certs'])
                pilot_certs = self.parse_skills(pilot['certifications'])
                missing_certs = [c for c in req_certs if c not in pilot_certs]
                if missing_certs:
                    conflicts.append(f"Pilot {pilot['name']} missing certs: {', '.join(missing_certs)}")
                    
                # Check 3: Location (Warning only)
                if pilot['location'] != mission['location']:
                    conflicts.append(f"WARNING: Pilot {pilot['name']} is in {pilot['location']}, mission is in {mission['location']}.")

        # Check Drone Conflicts
        if drone_id:
            drone = self.dm.drones[self.dm.drones['drone_id'] == drone_id]
            if not drone.empty:
                drone = drone.iloc[0]
                
                if drone['status'] == 'Maintenance':
                    conflicts.append(f"Drone {drone['model']} is in Maintenance.")

                if drone['current_assignment'] != '–' and drone['current_assignment'] != project_id:
                     other_proj = self.dm.missions[self.dm.missions['project_id'] == drone['current_assignment']]
                     if not other_proj.empty:
                        other_proj = other_proj.iloc[0]
                        other_start = parser.parse(str(other_proj['start_date']))
                        other_end = parser.parse(str(other_proj['end_date']))
                        if (mission_start <= other_end) and (mission_end >= other_start):
                            conflicts.append(f"Drone {drone['model']} is already assigned to {drone['current_assignment']}.")
                            
                # Check Maintenance Date
                maint_date = parser.parse(str(drone['maintenance_due']))
                if maint_date < mission_end:
                     conflicts.append(f"WARNING: Drone {drone['model']} maintenance due ({drone['maintenance_due']}) before mission end.")

                # Check 4: Location (Warning only)
                if drone['location'] != mission['location']:
                    conflicts.append(f"WARNING: Drone {drone['model']} is in {drone['location']}, mission is in {mission['location']}.")
                
                # Check 5: Pilot-Drone Location Mismatch (if pilot is also assigned/checked)
                if pilot_id:
                    pilot = self.dm.pilots[self.dm.pilots['pilot_id'] == pilot_id].iloc[0]
                    if pilot['location'] != drone['location']:
                        conflicts.append(f"CRITICAL: Pilot {pilot['name']} ({pilot['location']}) and Drone {drone['model']} ({drone['location']}) are in different locations.")

        return conflicts

    def find_matches(self, project_id):
        mission = self.dm.missions[self.dm.missions['project_id'] == project_id]
        if mission.empty:
            return [], []
        
        mission = mission.iloc[0]
        req_skills = self.parse_skills(mission['required_skills'])
        req_certs = self.parse_skills(mission['required_certs'])
        
        # Find Pilots
        suitable_pilots = []
        for _, pilot in self.dm.pilots.iterrows():
            pilot_skills = self.parse_skills(pilot['skills'])
            pilot_certs = self.parse_skills(pilot['certifications'])
            
            # Basic skill check
            if all(s in pilot_skills for s in req_skills) and all(c in pilot_certs for c in req_certs):
                # Check availability (naive check for now, real check should verify dates)
                # We prioritize those Available
                suitable_pilots.append(pilot)
                
        # Find Drones
        suitable_drones = []
        # Logic for drones depends on capabilities. Assuming mission 'required_skills' maps to drone capabilities mostly for 'Thermal', 'Mapping' (LiDAR) etc.
        # This is an assumption. Let's map keywords.
        req_caps = []
        if 'thermal' in req_skills: req_caps.append('thermal')
        if 'mapping' in req_skills: req_caps.append('lidar') # Assuming Mapping -> LiDAR often? Or just RGB? Let's check fleet.
        
        for _, drone in self.dm.drones.iterrows():
            drone_caps = self.parse_skills(drone['capabilities'])
            if all(c in drone_caps for c in req_caps):
                 suitable_drones.append(drone)
                 
        return pd.DataFrame(suitable_pilots), pd.DataFrame(suitable_drones)

    def suggest_reassignments(self, project_id):
        """
        Suggests pilots/drones to reassign from lower priority missions
        if no one is available for this urgent mission.
        """
        mission = self.dm.missions[self.dm.missions['project_id'] == project_id]
        if mission.empty:
            return []
        
        mission = mission.iloc[0]
        if mission['priority'] != 'Urgent':
            return ["Mission is not Urgent. Use standard assignment."]

        req_skills = self.parse_skills(mission['required_skills'])
        req_certs = self.parse_skills(mission['required_certs'])

        suggestions = []
        
        # Look for pilots currently assigned to LOWER priority missions
        # We need to look at ALL pilots, check if they match skills, 
        # and if they are assigned, check the priority of that assignment.
        for _, pilot in self.dm.pilots.iterrows():
            # Check skills first
            pilot_skills = self.parse_skills(pilot['skills'])
            pilot_certs = self.parse_skills(pilot['certifications'])
            
            if not (all(s in pilot_skills for s in req_skills) and all(c in pilot_certs for c in req_certs)):
                continue

            # If available, we shouldn't be asking for reassignment (unless we missed them)
            if pilot['status'] == 'Available':
                continue
                
            # If assigned, check usage
            if pilot['current_assignment'] != '–':
                curr_proj_id = pilot['current_assignment']
                curr_proj = self.dm.missions[self.dm.missions['project_id'] == curr_proj_id]
                if not curr_proj.empty:
                    curr_proj = curr_proj.iloc[0]
                    # If current project is NOT Urgent (e.g. High or Standard), suggest pulling them
                    if curr_proj['priority'] != 'Urgent':
                        suggestions.append(f"Reassign Pilot {pilot['name']} ({pilot['pilot_id']}) from {curr_proj_id} ({curr_proj['priority']})")
        
        return suggestions
