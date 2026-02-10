# AeroAgent - AI Drone Operations Coordinator

AeroAgent is an intelligent agent designed to help operations teams manage drone fleets, pilots, and missions. It uses a **Hybrid AI Architecture** combining the natural language understanding of LLMs with the safety and precision of deterministic code.

## Features
- **Natural Language Command:** "Assign Pilot X to Project Y", "Show me available drones".
- **Conflict Detection:** Automatically checks for:
    - **Hard Conflicts:** Maintenance, Certifications, Double Booking (Blocks assignment).
    - **Soft Conflicts:** Location mismatch, Skill mismatch (Requires confirmation).
- **Google Sheets Integration:** 2-way sync. Edit your roster in Sheets, and the AI sees it instantly.
- **Urgent Reassignment:** Smart logic to suggest pulling pilots from lower-priority tasks for urgent missions.

## Architecture
The system follows a "Brain-Body" separation:
1.  **Frontend (Body):** Streamlit UI for chat and dashboard visualization.
2.  **Brain (AgentLLM):** 
    - **NLU:** Classifies user intent (e.g., `assign_pilot`, `check_conflicts`) using GPT-4o-mini / OpenRouter.
    - **NLG:** Generates human-friendly responses from data.
3.  **Logic Layer (Core):** Deterministic Python code (`logic.py`) that handles dates, boolean logic, and business rules.
4.  **Data Layer:** connectors for Google Sheets (`data_manager.py`) with CSV fallback.

## Quick Start

### 1. Prerequisites
- Python 3.9+
- A Google Cloud Project with Sheets API enabled (or use local CSVs).
- OpenRouter API Key.

### 2. Installation
```bash
git clone https://github.com/atharvgk/aeroagent.git
cd aeroagent
pip install -r requirements.txt
```

### 3. Setup Credentials (Google Sheets)
1.  Place your `gcp_service_account` credentials in `.streamlit/secrets.toml` (for Cloud) or `credentials.json` (for Local).
2.  Set `OPENROUTER_API_KEY` in `.env` or Secrets.

### 4. Run Locally
```bash
streamlit run ui.py
```

## Project Structure
- `ui.py`: Main entry point (Frontend).
- `agent_llm.py`: The AI Brain (NLU & Response).
- `logic.py`: Business rules (Conflict checking, Matching).
- `data_manager.py`: Handles CSV/Google Sheets I/O.
- `api.py`: Optional REST API (for headless usage).
- `sync_to_sheets.py`: Utility to upload local CSVs to Sheets.

