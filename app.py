import streamlit as st
import json
import os
from openai import OpenAI
from env import AMLEnvironment
from models import Action

# --- Page Config ---
st.set_page_config(page_title="Forensic AML Investigator", page_icon="🕵️‍♂️", layout="wide")

# --- Initialize OpenAI Client ---
api_base = os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1")
model_name = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
api_key = os.getenv("HF_TOKEN")

# Only initialize client if API key is present
client = OpenAI(base_url=api_base, api_key=api_key) if api_key else None

# --- Initialize Session State ---
if 'env' not in st.session_state:
    st.session_state.env = AMLEnvironment()
if 'terminal_history' not in st.session_state:
    st.session_state.terminal_history = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_task' not in st.session_state:
    st.session_state.current_task = "easy"
if 'is_done' not in st.session_state:
    st.session_state.is_done = False

def reset_environment(task_name):
    st.session_state.env.reset(task_name)
    st.session_state.terminal_history = [{"role": "system", "content": f"Environment Reset to {task_name.upper()} mode."}]
    
    # Reset chat history with a fresh greeting
    st.session_state.chat_history = [
        {"role": "assistant", "content": f"Hello Investigator! I am your AI Copilot for the **{task_name.upper()}** case. I have access to all background ledgers and emails. Ask me anything!"}
    ]
    st.session_state.current_task = task_name
    st.session_state.is_done = False

# --- UI Sidebar ---
with st.sidebar:
    st.title("🕵️‍♂️ AML Dashboard")
    st.markdown("Investigate financial crimes manually or chat with the AI Copilot.")
    
    st.subheader("1. Select Investigation")
    selected_task = st.selectbox("Task Difficulty", ["easy", "medium", "hard"])
    
    if st.button("Initialize Case", use_container_width=True):
        reset_environment(selected_task)
        st.rerun()

    st.divider()
    
    st.subheader("🔒 Active Freezes")
    frozen = st.session_state.env.state().frozen_accounts
    if frozen:
        for acc in frozen:
            st.error(f"❄️ {acc}")
    else:
        st.info("No accounts frozen yet.")

    st.divider()
    if not api_key:
        st.warning("⚠️ API Key not detected! Set HF_TOKEN in your terminal to enable the AI Chat Assistant.")

# --- Main UI Area ---
st.title("Financial Crime Investigation Platform")

if not st.session_state.terminal_history:
    reset_environment("easy")

# Create Tabs
tab1, tab2 = st.tabs(["💻 Manual Terminal", "🤖 AI Assistant Chat"])

# ==========================================
# TAB 1: MANUAL TERMINAL (Existing Logic)
# ==========================================
with tab1:
    # Display Terminal History
    for msg in st.session_state.terminal_history:
        if msg["role"] == "system":
            st.success(msg["content"])
        elif msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(f"**Action Executed:** `{msg['action']}` | **Target:** `{msg['target']}`")
        elif msg["role"] == "env":
            with st.chat_message("assistant", avatar="💻"):
                st.code(msg["content"], language="json")

    # Action Form
    if not st.session_state.is_done:
        st.markdown("### Execute Next Command")
        col1, col2, col3 = st.columns([2, 3, 1])
        
        with col1:
            action_type = st.selectbox("Action", ["read_sar", "query_ledger", "read_emails", "lookup_company", "freeze_account", "submit_report"], label_visibility="collapsed")
        with col2:
            target_val = st.text_input("Target (Account ID, Name, etc.)", placeholder="e.g. ACC-CHARLIE", label_visibility="collapsed")
        with col3:
            execute_btn = st.button("Execute", type="primary", use_container_width=True)

        if execute_btn:
            target = target_val if target_val else None
            try:
                act = Action(action_type=action_type, target=target)
                obs, reward, done, info = st.session_state.env.step(act)
                
                st.session_state.terminal_history.append({"role": "user", "action": action_type, "target": target})
                st.session_state.terminal_history.append({"role": "env", "content": obs.result})
                
                if done:
                    st.session_state.is_done = True
                    st.session_state.terminal_history.append({"role": "system", "content": f"Task Complete! Final Score: {info['task_score']} / 1.0"})
                
                st.rerun()
                
            except Exception as e:
                st.error(f"Validation Error: {e}")
    else:
        st.info("Investigation Closed. Initialize a new case from the sidebar.")

# ==========================================
# TAB 2: AI ASSISTANT CHAT (New Feature!)
# ==========================================
with tab2:
    st.markdown("### Case Copilot")
    st.markdown("Ask the AI about the current database. It has full knowledge of who is guilty and who is a decoy.")
    
    # Render chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input Box
    if prompt := st.chat_input("Ask about an account or employee..."):
        if not api_key:
            st.error("API Key missing! Please set HF_TOKEN environment variable.")
        else:
            # 1. Add user message to UI
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # 2. Get current database context to feed the AI
            current_task = st.session_state.current_task
            db_context = st.session_state.env.db[current_task]
            
            system_prompt = f"""
            You are an expert Anti-Money Laundering AI Copilot advising a human investigator.
            You have access to the absolute truth of the case database.
            Current Case Difficulty: {current_task.upper()}
            
            CASE DATABASE:
            {json.dumps(db_context, indent=2)}
            
            RULES:
            1. Answer the user's questions clearly and concisely.
            2. If they ask if someone is innocent or guilty, look at the "targets" list in the database. If an account is in the "targets" list, it is guilty. If it is NOT in the "targets" list, it is innocent/a decoy.
            3. Guide them on what actions to take in the Manual Terminal tab.
            """

            # 3. Call the LLM
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                
                messages_for_api = [{"role": "system", "content": system_prompt}]
                # Feed the last 5 chat messages for context
                for m in st.session_state.chat_history[-5:]:
                    messages_for_api.append({"role": m["role"], "content": m["content"]})
                
                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=messages_for_api,
                        temperature=0.3
                    )
                    full_response = response.choices[0].message.content
                    message_placeholder.markdown(full_response)
                    
                    # Add AI response to history
                    st.session_state.chat_history.append({"role": "assistant", "content": full_response})
                except Exception as e:
                    st.error(f"Error communicating with AI: {str(e)}")
                    
                    
                    