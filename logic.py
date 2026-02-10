from datetime import datetime
import pandas as pd
from dateutil import parser

class Logic:
    def __init__(self, data_manager):
        self.dm = data_manager

    def parse_skills(self, skills_str):
        if pd.isna(skills_str) or str(skills_str).strip() == "":
            return []
        return [s.strip().lower() for s in str(skills_str).split(',')]

    def check_conflicts(self, project_id, pilot_id=None, drone_id=None):
        """
        Returns a list of conflict dictionaries:
        {
            "type": str,
            "severity": "HARD" | "SOFT",
            "message": str,
            "can_override": bool
        }
        """
        conflicts = []
        
        # Get Mission Details
        mission = self.dm.get_mission(project_id)
        if not mission:
            return [{"type": "DATA_ERROR", "severity": "HARD", "message": f"Mission {project_id} not found", "can_override": False}]
            
        try:
            mission_start = parser.parse(str(mission.get('start_date', '')))
            mission_end = parser.parse(str(mission.get('end_date', '')))
        except:
             return [{"type": "DATA_ERROR", "severity": "HARD", "message": f"Invalid dates for Mission {project_id}", "can_override": False}]

        # --- PILOT CHECKS ---
        if pilot_id:
            pilot = self.dm.get_pilot(pilot_id)
            if not pilot:
                 conflicts.append({"type": "DATA_ERROR", "severity": "HARD", "message": f"Pilot {pilot_id} not found", "can_override": False})
            else:
                # 1. Status Check
                if pilot['status'] == 'On Leave':
                    conflicts.append({"type": "UNAVAILABLE", "severity": "HARD", "message": f"Pilot {pilot['name']} is On Leave.", "can_override": False})
                elif pilot['status'] == 'Unavailable':
                    conflicts.append({"type": "UNAVAILABLE", "severity": "HARD", "message": f"Pilot {pilot['name']} is Unavailable.", "can_override": False})

                # 2. Double Booking
                if pilot['current_assignment'] and pilot['current_assignment'] != '–' and pilot['current_assignment'] != project_id:
                     other_proj = self.dm.get_mission(pilot['current_assignment'])
                     if other_proj:
                        try:
                            other_start = parser.parse(str(other_proj['start_date']))
                            other_end = parser.parse(str(other_proj['end_date']))
                            if (mission_start <= other_end) and (mission_end >= other_start):
                                conflicts.append({
                                    "type": "DOUBLE_BOOKING", 
                                    "severity": "HARD", 
                                    "message": f"Pilot {pilot['name']} is assigned to {pilot['current_assignment']} during these dates.", 
                                    "can_override": False
                                })
                        except:
                            pass # Date error handled elsewhere

                # 3. Certification (HARD)
                req_certs = self.parse_skills(mission.get('required_certs', ''))
                pilot_certs = self.parse_skills(pilot.get('certifications', ''))
                missing_certs = [c for c in req_certs if c not in pilot_certs]
                if missing_certs:
                    conflicts.append({
                        "type": "CERTIFICATION_MISSING", 
                        "severity": "HARD", 
                        "message": f"Pilot {pilot['name']} missing required certs: {', '.join(missing_certs)}", 
                        "can_override": False
                    })

                # 4. Skills (SOFT - Explicit override required)
                req_skills = self.parse_skills(mission.get('required_skills', ''))
                pilot_skills = self.parse_skills(pilot.get('skills', ''))
                missing_skills = [s for s in req_skills if s not in pilot_skills]
                if missing_skills:
                    conflicts.append({
                        "type": "SKILL_MISMATCH", 
                        "severity": "SOFT", 
                        "message": f"Pilot {pilot['name']} missing preferred skills: {', '.join(missing_skills)}", 
                        "can_override": True
                    })

                # 5. Location (SOFT)
                if pilot['location'] != mission['location']:
                     conflicts.append({
                        "type": "LOCATION_MISMATCH", 
                        "severity": "SOFT", 
                        "message": f"Pilot {pilot['name']} is in {pilot['location']}, mission is in {mission['location']}.", 
                        "can_override": True
                    })

        # --- DRONE CHECKS ---
        if drone_id:
            drone = self.dm.get_drone(drone_id)
            if not drone:
                conflicts.append({"type": "DATA_ERROR", "severity": "HARD", "message": f"Drone {drone_id} not found", "can_override": False})
            else:
                # 1. Maintenance (HARD)
                if drone['status'] == 'Maintenance':
                    conflicts.append({"type": "MAINTENANCE", "severity": "HARD", "message": f"Drone {drone['model']} is in Maintenance.", "can_override": False})
                
                # Check Maintenance Due Date
                try:
                    maint_date = parser.parse(str(drone['maintenance_due']))
                    if maint_date < mission_end:
                        conflicts.append({"type": "MAINTENANCE_DUE", "severity": "HARD", "message": f"Drone {drone['model']} maintenance due ({drone['maintenance_due']}) before mission ends.", "can_override": False})
                except:
                    pass

                # 2. Double Booking (HARD)
                if drone['current_assignment'] and drone['current_assignment'] != '–' and drone['current_assignment'] != project_id:
                     other_proj = self.dm.get_mission(drone['current_assignment'])
                     if other_proj:
                        try:
                            other_start = parser.parse(str(other_proj['start_date']))
                            other_end = parser.parse(str(other_proj['end_date']))
                            if (mission_start <= other_end) and (mission_end >= other_start):
                                conflicts.append({
                                    "type": "DOUBLE_BOOKING", 
                                    "severity": "HARD", 
                                    "message": f"Drone {drone['model']} is assigned to {drone['current_assignment']}.", 
                                    "can_override": False
                                })
                        except: pass

                # 3. Location (SOFT)
                if drone['location'] != mission['location']:
                    conflicts.append({
                        "type": "LOCATION_MISMATCH", 
                        "severity": "SOFT", 
                        "message": f"Drone {drone['model']} is in {drone['location']}, mission is in {mission['location']}.", 
                        "can_override": True
                    })

                # 4. Pilot-Drone Mismatch (CRITICAL/HARD?) - Let's make it HARD for safety
                if pilot_id:
                     pilot = self.dm.get_pilot(pilot_id)
                     if pilot and pilot['location'] != drone['location']:
                         conflicts.append({
                            "type": "LOCATION_MISMATCH", 
                            "severity": "HARD", 
                            "message": f"Pilot ({pilot['location']}) and Drone ({drone['location']}) are in different locations.", 
                            "can_override": False
                        })

        return conflicts

    def query_pilots(self, filters):
        """
        Generic filter for pilots.
        filters: dict of {column: value}
        """
        df = self.dm.pilots.copy()
        
        for key, value in filters.items():
            if key not in df.columns:
                continue
                
            val_str = str(value).lower().strip()
            if not val_str: continue # Ignore empty filters
            
            # Special handling for list-like columns
            if key in ['skills', 'certifications']:
                # Partial match: checks if filter value is present in the comma-separated string
                df = df[df[key].str.lower().str.contains(val_str, na=False)]
            else:
                # Exact match (case-insensitive)
                df = df[df[key].str.lower() == val_str]
                
        return df.to_dict(orient='records')

    def query_drones(self, filters):
        """
        Generic filter for drones.
        filters: dict of {column: value}
        """
        df = self.dm.drones.copy()
        for key, value in filters.items():
            if key not in df.columns:
                continue
            val_str = str(value).lower().strip()
            if not val_str: continue # Ignore empty filters

            # Partial match for capabilities
            if key in ['capabilities']:
                df = df[df[key].str.lower().str.contains(val_str, na=False)]
            else:
                df = df[df[key].str.lower() == val_str]
        return df.to_dict(orient='records')

    def query_missions(self, filters):
        """
        Generic filter for missions.
        """
        df = self.dm.missions.copy()
        for key, value in filters.items():
             if key not in df.columns:
                continue
             val_str = str(value).lower().strip()
             if not val_str: continue # Ignore empty filters
             
             if key in ['required_skills', 'required_certs']:
                 df = df[df[key].str.lower().str.contains(val_str, na=False)]
             else:
                 df = df[df[key].str.lower() == val_str]
        return df.to_dict(orient='records')

    def find_matches(self, project_id):
        mission = self.dm.get_mission(project_id)
        if not mission: return {"pilots": [], "drones": []}
        
        req_skills = self.parse_skills(mission['required_skills'])
        req_certs = self.parse_skills(mission['required_certs'])
        
        candidates = []
        for _, pilot in self.dm.pilots.iterrows():
            pilot = pilot.to_dict()
            score = 0
            issues = []
            eligible = True
            
            # 1. Certifications Check (Critical)
            p_certs = self.parse_skills(pilot['certifications'])
            missing_certs = [c for c in req_certs if c not in p_certs]
            if missing_certs:
                eligible = False
                issues.append(f"Missing Certs: {', '.join(missing_certs)}")
                score -= 50
            else:
                score += 50
            
            # 2. Location Check (Important but maybe overrideable?)
            # Strictly speaking, for "Best Pilot", we prefer location match.
            if pilot['location'] != mission['location']:
                eligible = False # Mark ineligible for "perfect match", but keep in list
                issues.append(f"Location mismatch ({pilot['location']})")
                score -= 30
            else:
                score += 30
            
            # 3. Skills Check (Desirable)
            p_skills = self.parse_skills(pilot['skills'])
            missing_skills = [s for s in req_skills if s not in p_skills]
            if missing_skills:
                 score -= 10 * len(missing_skills)
                 issues.append(f"Missing Skills: {', '.join(missing_skills)}")
            else:
                 score += 20

            # 4. Status Check
            if pilot['status'] == 'Available':
                score += 20
            elif pilot['status'] == 'On Leave':
                eligible = False
                issues.append("Pilot On Leave")
                score -= 100
            elif pilot['status'] == 'Assigned':
                eligible = False
                issues.append(f"Already Assigned ({pilot.get('current_assignment', '')})")
                score -= 50

            candidates.append({
                "id": pilot['pilot_id'],
                "name": pilot['name'],
                "score": score,
                "location": pilot['location'],
                "status": pilot['status'],
                "eligible": eligible,
                "issues": issues,
                "certifications": pilot['certifications'],
                "skills": pilot['skills']
            })
            
        # Sort by Score (Higher is better)
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top 5, or more if needed
        return {"pilots": candidates[:5], "mission_id": project_id}

    def suggest_reassignments(self, project_id, urgent_mode=False):
        """
        Returns candidates for reassignment.
        Only returns if urgent_mode is True or priority matches.
        """
        mission = self.dm.get_mission(project_id)
        if not mission: return []
        
        if mission['priority'] != 'Urgent' and not urgent_mode:
            return []

        candidates = []
        req_skills = self.parse_skills(mission['required_skills'])
        req_certs = self.parse_skills(mission['required_certs'])
        
        for _, pilot in self.dm.pilots.iterrows():
            pilot = pilot.to_dict()
            
            # Only look at assigned pilots
            if pilot['current_assignment'] == '–': continue
            
            # Check basic qualifications (Hard constraints)
            p_certs = self.parse_skills(pilot['certifications'])
            if not all(c in p_certs for c in req_certs): continue
            
            curr_proj = self.dm.get_mission(pilot['current_assignment'])
            if not curr_proj: continue
            
            # Reassignment Logic
            # We can bump if current project priority is LOWER than new project priority
            # Urgent > High > Standard > Low
            priority_rank = {"Urgent": 4, "High": 3, "Standard": 2, "Low": 1}
            mys_prio = priority_rank.get(mission['priority'], 1)
            cur_prio = priority_rank.get(curr_proj['priority'], 1)
            
            if mys_prio > cur_prio:
                 candidates.append({
                     "pilot_id": pilot['pilot_id'],
                     "name": pilot['name'],
                     "current_assignment": pilot['current_assignment'],
                     "current_priority": curr_proj['priority'],
                     "location_match": pilot['location'] == mission['location']
                 })
                 
        return candidates

    def assign_resource(self, project_id, resource_id, resource_type, confirm=False, override_soft_conflicts=False):
        # 1. Check Conflicts
        if resource_type.lower() == "pilot":
            conflicts = self.check_conflicts(project_id, pilot_id=resource_id)
        else:
            conflicts = self.check_conflicts(project_id, drone_id=resource_id)
            
        hard_conflicts = [c for c in conflicts if c['severity'] == "HARD"]
        soft_conflicts = [c for c in conflicts if c['severity'] == "SOFT"]
        
        # 2. Block on Hard Conflicts
        if hard_conflicts:
            return {
                "success": False, 
                "message": "Assignment blocked by HARD conflicts.", 
                "conflicts": hard_conflicts
            }
        
        # 3. Warning on Soft Conflicts (unless overridden)
        if soft_conflicts and not override_soft_conflicts:
            return {
                "success": False,
                "message": "Soft conflicts detected. Confirmation required.",
                "conflicts": soft_conflicts,
                "requires_confirmation": True
            }
            
        # 4. Check for Explicit User Confirmation (Two-Step State Change)
        if not confirm:
             return {
                "success": False,
                "message": "Dry Run Successful. Please set confirm=True to execute.",
                "conflicts": soft_conflicts if soft_conflicts else []
            }

        # 5. Execute
        if resource_type.lower() == "pilot":
            if self.dm.assign_pilot_to_mission(resource_id, project_id):
                return {"success": True, "message": f"Assigned Pilot {resource_id} to {project_id}"}
        else:
            if self.dm.assign_drone_to_mission(resource_id, project_id):
                return {"success": True, "message": f"Assigned Drone {resource_id} to {project_id}"}
                
        return {"success": False, "message": "Database update failed."}
