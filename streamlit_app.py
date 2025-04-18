import streamlit as st
import requests
import time

# --- Configuration ---
BACKEND_URL = "http://127.0.0.1:8000"
FACT_CHECK_ENDPOINT = f"{BACKEND_URL}/fact-check"
FOLLOWUP_ENDPOINT = f"{BACKEND_URL}/followup-stream"
NEW_SESSION_ENDPOINT = f"{BACKEND_URL}/new-session"

# --- Helper Functions ---

def call_new_session():
    try:
        response = requests.post(NEW_SESSION_ENDPOINT)
        response.raise_for_status()
        return response.json().get("session_id")
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {e}")
        return None

def call_fact_check_stream(claim: str, backend_session_id: str):
    payload = {"claim": claim, "session_id": backend_session_id}
    try:
        response = requests.post(FACT_CHECK_ENDPOINT, json=payload, stream=True)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"Error during fact-check: {e}")
        return None

def call_followup_stream(backend_session_id: str, question: str):
    payload = {"session_id": backend_session_id, "question": question}
    try:
        response = requests.post(FOLLOWUP_ENDPOINT, json=payload, stream=True)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"Error asking follow-up: {e}")
        return None

# --- Streamlit App ---

st.set_page_config(page_title="FactChecker AI", layout="wide", page_icon="🧐")

st.title("🧐 FactChecker AI Assistant")
st.caption("Enter a claim to check its validity, then ask follow-up questions.")

# --- Session State Setup ---

if 'sessions' not in st.session_state:
    st.session_state.sessions = {}
if 'active_session_key' not in st.session_state:
    st.session_state.active_session_key = None
if 'next_session_index' not in st.session_state:
    st.session_state.next_session_index = 1

# --- Sidebar ---
with st.sidebar:
    st.header("Fact-Check Sessions")
    if st.button("➕ Start New Fact-Check", use_container_width=True):
        backend_session_id = call_new_session()
        if backend_session_id:
            session_key = f"session_{st.session_state.next_session_index}"
            st.session_state.next_session_index += 1
            st.session_state.sessions[session_key] = {
                "backend_session_id": backend_session_id,
                "claim": None,
                "initial_result": None,
                "history": [],
                "display_name": f"Check #{session_key.split('_')[1]}"
            }
            st.session_state.active_session_key = session_key
            st.rerun()

    st.write("---")
    st.write("Active Sessions:")

    for key in list(st.session_state.sessions.keys()):
        session_data = st.session_state.sessions[key]
        button_label = f"{session_data['display_name']}"
        is_active = (key == st.session_state.active_session_key)
        button_type = "primary" if is_active else "secondary"

        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            if st.button(button_label, key=f"switch_{key}", use_container_width=True, type=button_type):
                st.session_state.active_session_key = key
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"delete_{key}", help="Close this session"):
                del st.session_state.sessions[key]
                if st.session_state.active_session_key == key:
                    remaining = list(st.session_state.sessions.keys())
                    st.session_state.active_session_key = remaining[0] if remaining else None
                st.rerun()

# --- Main UI ---

active_key = st.session_state.active_session_key

if not active_key or active_key not in st.session_state.sessions:
    st.info("Click 'Start New Fact-Check' in the sidebar to begin.")
else:
    session_data = st.session_state.sessions[active_key]
    backend_session_id = session_data["backend_session_id"]

    if session_data["claim"] is None:
        st.subheader(f"New Fact-Check Session: {session_data['display_name']}")
        claim_input = st.text_area("Enter the claim you want to fact-check:", height=100, key=f"claim_input_{active_key}")
        if st.button("Check Claim", key=f"check_button_{active_key}", type="primary"):
            if claim_input:
                stream_response = call_fact_check_stream(claim_input, backend_session_id)
                if stream_response:
                    session_data["claim"] = claim_input
                    display_claim = (claim_input[:40] + '...') if len(claim_input) > 40 else claim_input
                    session_data["display_name"] = f"Check: {display_claim}"

                    # User message
                    with st.chat_message("user"):
                        st.markdown(f"Fact-check this claim: {claim_input}")
                    session_data["history"].append({"role": "user", "content": f"Fact-check this claim: {claim_input}"})

                    # Stream assistant message
                    with st.chat_message("assistant"):
                        placeholder = st.empty()
                        full_response = ""
                        for chunk in stream_response.iter_content(chunk_size=1024, decode_unicode=True):
                            if chunk:
                                for char in chunk:
                                    full_response += char
                                    placeholder.markdown(full_response.replace("\n", "<br>") + "▌", unsafe_allow_html=True)
                                    time.sleep(0.01)  # Typing speed
                        stream_response.close()


                    session_data["initial_result"] = full_response
                    session_data["history"].append({"role": "assistant", "content": full_response})
                    st.rerun()
                else:
                    st.error("Failed to get fact-check results from the backend.")
            else:
                st.warning("Please enter a claim to check.")
    else:
        st.subheader(f"Fact-Checking: {session_data['display_name']}")
        st.markdown(f"**Original Claim:** {session_data['claim']}")
        st.divider()

        # Show full chat history
        for message in session_data["history"]:
            with st.chat_message(message["role"]):
                if isinstance(message["content"], (dict, list)):
                    st.json(message["content"])
                else:
                    # Fix: keep line breaks in assistant messages
                    if message["role"] == "assistant":
                        st.markdown(message["content"].replace("\n", "<br>"), unsafe_allow_html=True)
                    else:
                        st.markdown(message["content"])

        # Follow-up question
        if prompt := st.chat_input("Ask a follow-up question...", key=f"followup_input_{active_key}"):
            session_data["history"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                placeholder = st.empty()
                placeholder.markdown("🤔 Thinking...")

                stream_response = call_followup_stream(backend_session_id, prompt)
                full_response = ""

                if stream_response:
                    try:
                        for chunk in stream_response.iter_content(chunk_size=1024, decode_unicode=True):
                            if chunk:
                                for char in chunk:
                                    full_response += char
                                    placeholder.markdown(full_response.replace("\n", "<br>") + "▌", unsafe_allow_html=True)
                                    time.sleep(0.01)  # Typing speed
                    except Exception as e:
                        st.error(f"Error processing stream: {e}")
                        full_response = "[Error receiving response]"
                    finally:
                        stream_response.close()
                else:
                    full_response = "Sorry, I encountered an error trying to answer."
                    placeholder.markdown(full_response)

            session_data["history"].append({"role": "assistant", "content": full_response})

# --- Footer ---
st.sidebar.write("---")
st.sidebar.caption("Powered by AI Agents & FastAPI")
