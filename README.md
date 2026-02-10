# Skylark Drone Operations Coordinator Agent

This is an AI agent designed to help Drone Operations Coordinators manage pilots, drones, and missions.

## Architecture

-   **Frontend**: Streamlit (Reactive UI).
-   **Backend**: Python.
-   **Data Layer**: Dual-mode (CSV default, Google Sheets optional).
-   **Agent Logic**: Regex-based intent parsing (Deterministic & Fast).

## Setup & Running

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Application**:
    ```bash
    streamlit run app.py
    ```

3.  **Access**: Open your browser at `http://localhost:8501`.

## Google Sheets Integration

To enable 2-way sync with Google Sheets:
1.  Place your `credentials.json` (Service Account key) in this directory.
2.  Ensure the service account has access to your sheets.
3.  The app will automatically detect the credentials and switch to Sheets mode.
4.  (Note: You may need to configure the specific Sheet names in `data_manager.py` depending on your setup).

## Features implemented

-   **Roster Management**: View & Update pilot status.
-   **Assignment**: Assign pilots to missions with conflict checks.
-   **Conflict Detection**: Auto-detects overlaps, skill mismatches, and maintenance issues.
-   **Urgent Reassignments**: Suggests "bumping" pilots from lower-priority missions for Urgent tasks.

## Files

-   `app.py`: Main application entry point.
-   `agent.py`: NLU and intent processing.
-   `logic.py`: Core business logic (conflicts, matching).
-   `data_manager.py`: Data persistence layer.
-   `decision_log.md`: Usage and design decisions.
