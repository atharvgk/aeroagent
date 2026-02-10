from data_manager import DataManager

print("Initializing DataManager...")
dm = DataManager()

if dm.use_sheets:
    print("\nSUCCESS: System is using Google Sheets!")
    print(f"Sheet ID: {dm.sheet.id}")
    print(f"Sheet Title: {dm.sheet.title}")
    
    print("\n--- Sample Pilot Data (First 2) ---")
    print(dm.pilots.head(2))
else:
    print("\nFAILURE: System is using local CSV files.")
    print("Please check credentials.json and ensure it is valid.")
