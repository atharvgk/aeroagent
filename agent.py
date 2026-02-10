import re
import pandas as pd

class Agent:
    def __init__(self, data_manager, logic):
        self.dm = data_manager
        self.logic = logic

    def process_query(self, user_input):
        user_input = user_input.lower()
        
        # Intent: Show Available / Find Pilots
        if "available" in user_input and "pilot" in user_input:
            # simple filter extraction
            matches = self.dm.pilots[self.dm.pilots['status'] == 'Available']
            if "skill" in user_input or "mapping" in user_input or "thermal" in user_input:
                # TODO: extract specific skill
                pass
            return "Here are the available pilots:\n" + matches[['pilot_id', 'name', 'skills', 'location']].to_markdown(index=False)

        # Intent: Check Conflicts
        # Pattern: "Check conflicts for [ProjectID]"
        match = re.search(r"check conflicts for (prj\d+)", user_input)
        if match:
            pid = match.group(1).upper()
            conflicts = self.logic.check_conflicts(pid)
            if not conflicts:
                 # Check if anyone is actually assigned?
                 mission = self.dm.missions[self.dm.missions['project_id'] == pid]
                 if mission.empty: return "Project not found."
                 # We need to find WHO is assigned to check conflicts? 
                 # Wait, logic.check_conflicts takes pilot_id logic too.
                 # Let's assume the user wants to check if the CURRENT assignment is valid?
                 # Or are they asking "If I assign X...?"
                 pass 
            return f"Conflicts for {pid}: {conflicts}"

        # Intent: Assign
        # Pattern: "Assign [PilotID] to [ProjectID]"
        match = re.search(r"assign (p\d+) to (prj\d+)", user_input)
        if match:
            pilot_id = match.group(1).upper()
            proj_id = match.group(2).upper()
            
            # Check for conflicts FIRST
            conflicts = self.logic.check_conflicts(proj_id, pilot_id=pilot_id)
            if conflicts:
                return f"⚠️ Cannot assign {pilot_id} to {proj_id} due to conflicts:\n- " + "\n- ".join(conflicts)
            
            if self.dm.assign_pilot(pilot_id, proj_id):
                return f"✅ Successfully assigned Pilot {pilot_id} to {proj_id}."
            else:
                return "❌ Failed to assign. Check IDs."

        # Intent: Update Status
        # Pattern: "Set [PilotID] status to [Status]"
        match = re.search(r"set (p\d+) status to ([\w\s]+)", user_input)
        if match:
            pilot_id = match.group(1).upper()
            new_status = match.group(2).strip().title() # Capitalize first letters
            if self.dm.update_pilot_status(pilot_id, new_status):
                return f"✅ Updated {pilot_id} status to {new_status}."
            else:
                return "❌ Failed to update."

        # Intent: Urgent Reassignment
        # Pattern: "Help with urgent mission [ProjectID]"
        match = re.search(r"urgent.*(prj\d+)", user_input)
        if match:
            pid = match.group(1).upper()
            suggestions = self.logic.suggest_reassignments(pid)
            if suggestions:
                return f"🚑 Urgent Reassignment Suggestions for {pid}:\n- " + "\n- ".join(suggestions)
            else:
                return f"No reassignments needed or possible for {pid}."

        return "I didn't understand that. You can ask me to:\n- Show available pilots\n- Assign P001 to PRJ001\n- Set P001 status to On Leave\n- Check conflicts for PRJ001"
