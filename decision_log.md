# AeroAgent - Decision Log

## 1. Key Assumptions

-   **Data Structure**: I assumed `current_assignment` in the CSVs is a single string referring to a `project_id`. In a real-world scenario, this would likely be a many-to-many relationship (Assignments table), but for this prototype, I treated it as 1:1.
-   **Date Parsing**: I assumed standard ISO or common date formats. I used `dateutil.parser` for robustness.
-   **Skill Matching**: I assumed simple case-insensitive substring matching. "Mapping" matches "Mapping, Survey".
-   **Location**: I assumed exact string matching for locations (e.g., "Bangalore" == "Bangalore").
-   **Sync**: I implemented a dual-mode system. If `credentials.json` is missing, it defaults to local CSV mode without error, ensuring the prototype is testable immediately.

## 2. Technical Decisions & Trade-offs

### Tech Stack: Streamlit + Python
-   **Decision**: Used Streamlit for the UI.
-   **Why**: It allows for extremely rapid development of data-centric applications. It handles the frontend reactive loop automatically, allowing me to focus on the Python logic (Agent/DB).
-   **Trade-off**: Less customization of the UI than React/Vue, but significantly faster time-to-delivery for a prototype.

### Architecture: Modular Python Files
-   **Decision**: Separated concerns into `data_manager.py`, `logic.py`, `agent.py`, `app.py`.
-   **Why**: Makes the code testable and maintainable. Logic can be tested without the UI.
-   **Trade-off**: Slightly more boilerplate than a single script, but essential for a "production-grade" prototype.

### Agent Logic: Regex/Rule-Based
-   **Decision**: Used robust Regex parsing instead of a pure LLM.
-   **Why**: For a control system, determinism is key. If a user says "Assign P1 to Prj1", I need 100% reliability, not a probabilistic response.
-   **Trade-off**: Less flexible conversationally. It won't understand "I think P1 is a good fit for that mapping job", but it will perfectly understand "Assign P001 to PRJ001".

## 3. "Urgent Reassignments" Interpretation

**Requirement**: "The agent should help coordinate urgent reassignments"

**My Interpretation**:
When an **Urgent** priority mission is blocked (no available pilots/drones), the agent should proactively suggest "bumping" resources from lower-priority tasks.

**Implementation**:
I added a `suggest_reassignments(project_id)` function in `Logic`.
1.  It checks if the target mission is strict `Urgent`.
2.  It scans all pilots who matches the skills but are currently assigned.
3.  It checks the priority of their *current* assignment.
4.  If their current assignment is `High` or `Standard` (lower than Urgent), it suggests them as a candidate for reassignment.

## 4. Future Improvements

-   **Real Database**: Migrate from CSV/Sheets to PostgreSQL.
-   **Route Optimization**: Use geospatial libraries to check distance between Pilot and Mission location, rather than string matching.
-   **Authentication**: Add user login levels (Admin vs Viewer).
-   **LLM Integration**: Use an LLM to parse complex natural language into the strict commands (e.g. "Draft a plan to move the team from Mumbai to Bangalore" -> converts to multiple `Assign` commands).
