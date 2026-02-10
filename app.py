import streamlit as st
import pandas as pd
from data_manager import DataManager
from logic import Logic
from agent import Agent

st.set_page_config(page_title="Skylark Drones Agent", layout="wide")

@st.cache_resource
def get_system():
    dm = DataManager()
    logic = Logic(dm)
    agent = Agent(dm, logic)
    return dm, logic, agent

dm, logic, agent = get_system()

st.title("🚁 Skylark Drone Ops Coordinator")

# Sidebar for Data Preview
with st.sidebar:
    st.header("Data Check")
    if st.checkbox("Show Pilot Roster", value=True):
        st.dataframe(dm.pilots)
    if st.checkbox("Show Drone Fleet", value=False):
        st.dataframe(dm.drones)
    if st.checkbox("Show Missions", value=False):
        st.dataframe(dm.missions)
    
    st.header("Manual Actions")
    # Quick Status Update UI
    st.subheader("Update Pilot Status")
    p_id = st.selectbox("Pilot ID", dm.pilots['pilot_id'].unique())
    new_stat = st.selectbox("New Status", ["Available", "On Leave", "Unavailable", "Assigned"])
    if st.button("Update Status"):
        if dm.update_pilot_status(p_id, new_stat):
            st.success(f"Updated {p_id}")
            st.rerun()

# Main Chat Interface
st.header("💬 Operations Chat")
st.info("Try asking: 'Show available pilots', 'Assign P001 to PRJ001', 'Set P003 status to On Leave', 'Help with urgent PRJ002'")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("How can I help you?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = agent.process_query(prompt)
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

# Dashboard / Conflicts View
st.divider()
st.header("⚠️ Active Conflicts")
# Check all assignments?
# For now, just a button to scan all
if st.button("Scan All Assignments for Conflicts"):
    found_conflicts = []
    # Check all active missions
    for _, mission in dm.missions.iterrows():
        pid = mission['project_id']
        # Find who is assigned to this?
        # In our CSV, the link is ON the pilot/drone.
        assigned_pilots = dm.pilots[dm.pilots['current_assignment'] == pid]
        for _, p in assigned_pilots.iterrows():
            c = logic.check_conflicts(pid, pilot_id=p['pilot_id'])
            if c: found_conflicts.append(f"**{pid} / {p['pilot_id']}**: {', '.join(c)}")
            
        assigned_drones = dm.drones[dm.drones['current_assignment'] == pid]
        for _, d in assigned_drones.iterrows():
            c = logic.check_conflicts(pid, drone_id=d['drone_id'])
            if c: found_conflicts.append(f"**{pid} / {d['drone_id']}**: {', '.join(c)}")
            
    if found_conflicts:
        for fc in found_conflicts:
            st.error(fc)
    else:
        st.success("No conflicts found in current assignments.")
