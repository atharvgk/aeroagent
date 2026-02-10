# 🚁 Skylark Drone Operations Coordinator (SkyOps AI)

## Overview
SkyOps AI is a **Hybrid Agent** designed to assist drone operations managers. It combines:
1.  **Deterministic Logic (FastAPI)**: For strict safety checks, conflict detection, and roster management.
2.  **LLM Reasoning (OpenRouter)**: For natural language understanding and explaining operational trade-offs.
3.  **Interactive UI (Streamlit)**: A chat-based interface for easy interaction.

## Features
- **Roster Management**: Query pilot status, location, and skills.
- **Assignment**: Assign pilots/drones with automatic conflict checking.
- **Conflict Detection**: Detects double-booking, missing certs, and maintenance issues.
- **Urgent Reassignment**: AI-driven suggestions to move resources from lower-priority missions.

## Architecture
- **Backend**: Python, FastAPI (`api.py`)
- **Frontend**: Streamlit (`ui.py`)
- **AI**: OpenRouter API (`agent_llm.py`)
- **Data**: Local CSVs (`data_manager.py`)

## Setup & Installation

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configuration**:
    - The agent works in **Regex Fallback Mode** by default.
    - To enable AI reasoning, enter your **OpenRouter API Key** in the sidebar.

## How to Run

### Method 1: Automatic Script (Recommended)
Double-click `run_app.bat` or run it from the terminal:
```powershell
.\run_app.bat
```
This will launch both the backend server and the frontend UI automatically.

### Method 2: Manual Start
1.  **Start Backend** (Terminal 1):
    ```bash
    uvicorn api:app --reload --port 8000
    ```
2.  **Start Frontend** (Terminal 2):
    ```bash
    streamlit run ui.py
    ```

## Usage Guide
- **Ask**: "Who is available in Bangalore?"
- **Assign**: "Assign P001 to PRJ001"
- **Urgent**: "Help with urgent mission PRJ002"
- **Override**: If checking for soft conflicts (like location mismatch), type "Override" in your request to force it.
3.  The app will automatically detect the credentials and switch to Sheets mode.
4.  (Note: You may need to configure the specific Sheet names in `data_manager.py` depending on your setup).

## Features implemented

-   **Assignment**: Assign pilots to missions with conflict checks.
-   **Conflict Detection**: Auto-detects overlaps, skill mismatches, and maintenance issues.
-   **Urgent Reassignments**: Suggests "bumping" pilots from lower-priority missions for Urgent tasks.

## Files

-   `app.py`: Main application entry point.
-   `agent.py`: NLU and intent processing.
-   `logic.py`: Core business logic (conflicts, matching).
-   `data_manager.py`: Data persistence layer.
-   `decision_log.md`: Usage and design decisions.
