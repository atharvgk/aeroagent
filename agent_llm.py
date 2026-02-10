import os
import re
import json
import logging
import requests
from openai import OpenAI

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AgentLLM:
    def __init__(self, api_url="http://127.0.0.1:8000", openrouter_key=None):
        self.api_url = api_url
        self.api_key = openrouter_key
        self.client = None
        
        if self.api_key:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
            )
        else:
            logging.warning("No OpenRouter API Key provided. Agent will run in Fallback Mode (Regex only).")

        self.system_prompt = """
        You are SkyOps AI, a Drone Operations Coordinator.
        Your goal is to help users manage pilots, drones, and missions.
        
        You have access to a deterministic operational system.
        When the user asks a question, your job is to:
        1. Understand their intent.
        2. output a JSON object representing the tool call you want to make.
        
        TOOLS:
        - QUERY_PILOTS: { "tool": "query_pilots", "filters": { "location": "...", "status": "...", "skills": "...", "certifications": "..." } }
        - QUERY_DRONES: { "tool": "query_drones", "filters": { "location": "...", "status": "...", "capabilities": "..." } }
        - QUERY_MISSIONS: { "tool": "query_missions", "filters": { "location": "...", "priority": "..." } }
        - CHECK_CONFLICTS: { "tool": "check_conflicts", "project_id": "PRJ...", "pilot_id": "P...", "drone_id": "D..." }
        - FIND_MATCHES: { "tool": "find_matches", "project_id": "PRJ..." }
        - ASSIGN_PILOT: { "tool": "assign_pilot", "project_id": "PRJ...", "pilot_id": "P...", "force": bool }
        - ASSIGN_DRONE: { "tool": "assign_drone", "project_id": "PRJ...", "drone_id": "D...", "force": bool }
        - SUGGEST_REASSIGNMENT: { "tool": "suggest_reassignment", "project_id": "PRJ...", "urgent": bool }
        - GENERAL_CHAT: { "tool": "general_chat", "reply": "Your response to the user..." } 
        
        OUTPUT FORMAT:
        Return ONLY the JSON object. Do not add markdown or explanation.
        """

    def process_message(self, user_message):
        """
        Main entry point.
        1. Try Regex NLU (Fast Path for Greetings)
        2. Try LLM NLU
        3. Fallback to Regex NLU
        4. Call API
        5. Generate AI Response (New!)
        """
        tool_call = self._nlu_layer(user_message)
        
        if not tool_call:
            return "I didn't understand that request. Try 'Assign P001 to PRJ001' or 'Check conflicts for PRJ001'."
            
        logging.info(f"NLU Identified Tool: {tool_call}")
        
        # Execute Tool
        result = self._execute_tool(tool_call)
        
        # Generate Response using LLM
        if self.client:
             return self._generate_ai_response(user_message, result)
        else:
             return self._generate_response_fallback(user_message, tool_call, result)

    def _nlu_layer(self, text):
        clean_text = text.lower().strip()
        
        # 1. Fast Path: General Chat (Strict Check)
        if re.search(r"\b(hello|hi|hey|greetings)\b", clean_text) and len(clean_text) < 20:
             return {"tool": "general_chat", "reply": "Hello! SkyOps AI online. How can I help?"}

        # 2. Try LLM
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="openai/gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.1
                )
                content = response.choices[0].message.content
                # Clean markdown code blocks if present
                content = content.replace("```json", "").replace("```", "").strip()
                return json.loads(content)
            except Exception as e:
                logging.error(f"LLM Error: {e}. Falling back to Regex.")
                
        # 3. Regex Fallback
        
        # Assign Pilot
        match = re.search(r"assign (p\d+) to (prj\d+)", clean_text)
        if match:
             return {"tool": "assign_pilot", "pilot_id": match.group(1).upper(), "project_id": match.group(2).upper(), "force": "override" in clean_text}

         # Assign Drone
        match = re.search(r"assign (d\d+) to (prj\d+)", clean_text)
        if match:
             return {"tool": "assign_drone", "drone_id": match.group(1).upper(), "project_id": match.group(2).upper(), "force": "override" in clean_text}

        # Check Conflicts
        match = re.search(r"check conflicts for (prj\d+)", clean_text)
        if match:
             return {"tool": "check_conflicts", "project_id": match.group(1).upper()}

        # Suggest Reassignment / Urgent
        match = re.search(r"urgent.*(prj\d+)", clean_text)
        if match:
             return {"tool": "suggest_reassignment", "project_id": match.group(1).upper(), "urgent": True}
        
        # Available (Regex fallback logic still needs to be manual since we don't have LLM here)
        # Query Pilots (Regex Fallback)
        # We rely on the LLM for specific fields. Regex is just a safety net for basic status.
        filters = {}
        
        # Query Drones (Regex Fallback - Basic generic detection only)
        if "drone" in clean_text:
             # We can't safely extract generic filters with regex without hardcoding.
             # So we just return an empty query (or basic status if obvious) and let the user handle it.
             filters = {}
             if "available" in clean_text: filters["status"] = "Available"
             return {"tool": "query_drones", "filters": filters}

        # Query Missions (Regex Fallback)
        if "mission" in clean_text or "project" in clean_text:
             return {"tool": "query_missions", "filters": {}}

        # Query Pilots (Regex Fallback - Default for "show available" etc if no other entity found)
        # We REMOVE hardcoded skill/city checks to comply with Agentic rules.
        if "available" in clean_text or "show" in clean_text or "list" in clean_text or "who" in clean_text or "give" in clean_text or "all" in clean_text or "pilot" in clean_text:
             filters = {}
             if "available" in clean_text: filters["status"] = "Available"
             # No more hardcoded "if 'bangalore': filters['location'] = 'Bangalore'"
             return {"tool": "query_pilots", "filters": filters}

        return None

        return None

    def _execute_tool(self, tool_call):
        try:
            tool = tool_call.get("tool")
            if tool == "general_chat":
                # Return the LLM's generated reply
                return {"message": tool_call.get("reply", "I am SkyOps AI.")}

            if tool == "check_conflicts":
                resp = requests.post(f"{self.api_url}/conflicts/check", json={
                    "project_id": tool_call.get("project_id"),
                    "pilot_id": tool_call.get("pilot_id"),
                    "drone_id": tool_call.get("drone_id")
                })
                return resp.json()

            elif tool == "find_matches":
                 project_id = tool_call.get("project_id", "").replace(" ", "").upper()
                 resp = requests.get(f"{self.api_url}/project/{project_id}/matches")
                 return resp.json()

            elif tool == "assign_pilot":
                 resp = requests.post(f"{self.api_url}/assign", json={
                    "project_id": tool_call.get("project_id"),
                    "resource_id": tool_call.get("pilot_id"),
                    "resource_type": "pilot",
                    "confirm": tool_call.get("force", False),
                    "override_soft_conflicts": tool_call.get("force", False) # Simplify logic for now
                })
                 return resp.json()

            elif tool == "assign_drone":
                 resp = requests.post(f"{self.api_url}/assign", json={
                    "project_id": tool_call.get("project_id"),
                    "resource_id": tool_call.get("drone_id"),
                    "resource_type": "drone",
                    "confirm": tool_call.get("force", False),
                    "override_soft_conflicts": tool_call.get("force", False)
                })
                 return resp.json()
            
            elif tool == "suggest_reassignment":
                resp = requests.post(f"{self.api_url}/reassign/suggest", json={
                     "project_id": tool_call.get("project_id"),
                     "urgent": tool_call.get("urgent", False)
                })
                return resp.json()
                
            elif tool == "query_pilots":
                 resp = requests.post(f"{self.api_url}/pilots/query", json={"filters": tool_call.get("filters", {})})
                 return resp.json()

            elif tool == "query_drones":
                 resp = requests.post(f"{self.api_url}/drones/query", json={"filters": tool_call.get("filters", {})})
                 return resp.json()

            elif tool == "query_missions":
                 resp = requests.post(f"{self.api_url}/missions/query", json={"filters": tool_call.get("filters", {})})
                 return resp.json()
                 
        except Exception as e:
            return {"error": str(e)}

    def _generate_ai_response(self, user_text, tool_result):
        """
        Uses the LLM to format the API result into a natural language response
        based on the user's original query.
        """
        try:
            system_msg = """
            You are SkyOps AI. You have just executed an operational tool based on the user's request.
            
            INPUT CONTEXT:
            1. User's Original Query
            2. Raw JSON Result from the Tool
            
            YOUR JOB:
            - Answer the user's question using the Tool Result.
            - Format the data exactly as requested (e.g. if they ask for "only names", list only names).
            - If the result contains a list of items, format them nicely (markdown table or list).
            - If the result indicates an error, explain it clearly.
            - Be concise professional.
            """
            
            response = self.client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": f"User Query: {user_text}\n\nTool Result: {json.dumps(tool_result, indent=2)}"}
                ],
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Response Gen Error: {e}")
            return f"Error generating response: {e}. Raw Result: {tool_result}"

    def _generate_response_fallback(self, user_text, tool_call, result):
        # ... (Old Code logic preserved as fallback) ...
        if "error" in result:
             return f"⚠️ **System Error**: {result['error']}"
             
        tool = tool_call.get("tool")
        
        if tool == "general_chat":
             return result.get("message")
        
        if tool == "check_conflicts":
             if not result.get("conflicts"):
                 return f"✅ **No conflicts found** for {tool_call.get('project_id')}."
             msg = f"⚠️ **Conflicts Detected for {tool_call.get('project_id')}**:\n"
             for c in result.get("conflicts"):
                 msg += f"- **{c['severity']}**: {c['message']}\n"
             return msg

        if tool == "find_matches":
             pilots = result.get("pilots", [])
             if not pilots:
                 return f"No pilots found for {tool_call.get('project_id')}."
             
             msg = f"**Matching Analysis for {tool_call.get('project_id')}**:\n\n"
             
             # Split into Eligible and Ineligible
             eligible = [p for p in pilots if p.get('eligible', True)]
             ineligible = [p for p in pilots if not p.get('eligible', True)]
             
             if eligible:
                 msg += "✅ **Suitable Candidates**:\n"
                 import pandas as pd
                 df = pd.DataFrame(eligible)
                 cols = ["id", "name", "score", "location", "status"]
                 msg += df[cols].to_markdown(index=False) + "\n\n"
             
             if ineligible:
                 if not eligible:
                     msg += "⚠️ **No fully qualified candidates found.**\n\n"
                 msg += "❌ **Partial Matches / Issues**:\n"
                 for p in ineligible[:3]: # Show top 3 partial matches
                     issues = ", ".join(p.get('issues', []))
                     msg += f"- **{p['name']}** ({p['location']}): {issues}\n"
             
             return msg
             
        if tool == "assign_pilot" or tool == "assign_drone":
             if result.get("success"):
                 return f"✅ {result.get('message')}"
             else:
                 msg = f"❌ **Assignment Failed**: {result.get('message')}\n"
                 if result.get("conflicts"):
                     for c in result.get("conflicts"):
                         msg += f"- {c['message']}\n"
                 if result.get("requires_confirmation"):
                     msg += "\nTo proceed, please type: **'Override and assign...'**"
                 return msg

        if tool == "suggest_reassignment":
             sugg = result.get("suggestions", [])
             if not sugg:
                 return "No reassignment options found."
             msg = "🚑 **Urgent Reassignment Options**:\n"
             for s in sugg:
                 msg += f"- {s}\n"
             return msg

        if tool == "query_pilots":
             # Format as a Markdown Table
             if not result:
                 return "No pilots found matching criteria."
             
             import pandas as pd
             df = pd.DataFrame(result)
             # Select relevant columns
             cols = ["pilot_id", "name", "location", "status", "skills", "certifications"] 
             if len(df) > 0:
                count_msg = f"**Found {len(df)} Pilots**"
                return f"{count_msg}:\n\n" + df[cols].to_markdown(index=False)
             else:
                 return "No pilots found."

        if tool == "query_drones":
             if not result: return "No drones found."
             import pandas as pd
             df = pd.DataFrame(result)
             cols = ["drone_id", "model", "location", "status", "capabilities"]
             return f"**Found {len(df)} Drones**:\n\n" + df[cols].to_markdown(index=False)

        if tool == "query_missions":
             if not result: return "No missions found."
             import pandas as pd
             df = pd.DataFrame(result)
             cols = ["project_id", "location", "priority", "required_skills", "start_date"]
             return f"**Found {len(df)} Missions**:\n\n" + df[cols].to_markdown(index=False)

        return str(result)
