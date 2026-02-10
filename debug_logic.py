from data_manager import DataManager
from logic import Logic
import sys

with open("debug_log.txt", "w") as f:
    sys.stdout = f
    
    dm = DataManager()
    print("Pilots Loaded:", len(dm.pilots))
    print("First Pilot:", dm.pilots.iloc[0].to_dict())

    logic = Logic(dm)
    print("\n--- FIND MATCHES FOR PRJ 001 (Space) ---")
    matches = logic.find_matches("PRJ 001")
    print("\nResult:", matches)
