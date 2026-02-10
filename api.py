from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from data_manager import DataManager
from logic import Logic

app = FastAPI()
dm = DataManager()
logic = Logic(dm)

# --- Schemas ---
class ConflictCheckRequest(BaseModel):
    project_id: str
    pilot_id: Optional[str] = None
    drone_id: Optional[str] = None

class AssignmentRequest(BaseModel):
    project_id: str
    resource_id: str # Pilot or Drone ID
    resource_type: str # "pilot" or "drone"
    confirm: bool = False
    override_soft_conflicts: bool = False

class ReassignmentRequest(BaseModel):
    project_id: str
    urgent: bool = False

# --- Endpoints ---

@app.get("/pilots/available")
def get_pilots(status: Optional[str] = "Available"):
    if status and status.lower() == "all":
        return dm.pilots.to_dict(orient='records')
    elif status and status.lower() == "unavailable":
         return dm.pilots[dm.pilots['status'] != 'Available'].to_dict(orient='records')
    elif status:
        return dm.pilots[dm.pilots['status'] == status].to_dict(orient='records')
    return dm.pilots.to_dict(orient='records')

class QueryPilotsRequest(BaseModel):
    filters: dict

@app.post("/pilots/query")
def query_pilots(req: QueryPilotsRequest):
    return dm.pilots.to_dict(orient='records') # Fallback if logic not called, but let's use logic
    # Actually, we should use logic.query_pilots
    return logic.query_pilots(req.filters)

@app.get("/project/{project_id}/matches")
def get_project_matches(project_id: str):
    return logic.find_matches(project_id)

class QueryDronesRequest(BaseModel):
    filters: dict

class QueryMissionsRequest(BaseModel):
    filters: dict

@app.post("/drones/query")
def query_drones(req: QueryDronesRequest):
    return logic.query_drones(req.filters)

@app.post("/missions/query")
def query_missions(req: QueryMissionsRequest):
    return logic.query_missions(req.filters)

@app.post("/conflicts/check")
def check_conflicts(req: ConflictCheckRequest):
    conflicts = logic.check_conflicts(req.project_id, req.pilot_id, req.drone_id)
    return {"conflicts": conflicts}

@app.post("/assign")
def assign_resource(req: AssignmentRequest):
    # 1. Check Conflicts
    if req.resource_type == "pilot":
        conflicts = logic.check_conflicts(req.project_id, pilot_id=req.resource_id)
    else:
        conflicts = logic.check_conflicts(req.project_id, drone_id=req.resource_id)
        
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
    if soft_conflicts and not req.override_soft_conflicts:
        return {
            "success": False,
            "message": "Soft conflicts detected. Confirmation required.",
            "conflicts": soft_conflicts,
            "requires_confirmation": True
        }
        
    # 4. Check for Explicit User Confirmation (Two-Step State Change)
    if not req.confirm:
         return {
            "success": False,
            "message": "Dry Run Successful. Please set confirm=True to execute.",
            "conflicts": soft_conflicts if soft_conflicts else []
        }

    # 5. Execute
    if req.resource_type == "pilot":
        if dm.assign_pilot_to_mission(req.resource_id, req.project_id):
            return {"success": True, "message": f"Assigned Pilot {req.resource_id} to {req.project_id}"}
    else:
        if dm.assign_drone_to_mission(req.resource_id, req.project_id):
            return {"success": True, "message": f"Assigned Drone {req.resource_id} to {req.project_id}"}
            
    return {"success": False, "message": "Database update failed."}

@app.post("/reassign/suggest")
def suggest_reassignments(req: ReassignmentRequest):
    suggestions = logic.suggest_reassignments(req.project_id, urgent_mode=req.urgent)
    return {"suggestions": suggestions}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
