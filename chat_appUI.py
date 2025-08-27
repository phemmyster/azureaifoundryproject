# chat_app.py
import streamlit as st
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# ---------- CONFIGURATION ----------
CONN_STR = (
    "eastus2.api.azureml.ms;"
    "36db2f46-6f76-4fca-9258-228ef9d252f0;"
    "femitask-rg;"
    "femitask-project1"
)
AGENT_NAME = "asst_A1RuEQwPrHeotekt1C6t1d0M"

# ---------- SESSION STATE ----------
# Streamlit reruns the script on every interaction, so we keep state in st.session_state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "project_client" not in st.session_state:
    st.session_state.project_client = AIProjectClient.from_connection_string(
        credential=DefaultAzureCredential(),
        conn_str=CONN_STR,
    )

if "agent" not in st.session_state:
    st.session_state.agent = st.session_state.project_client.agents.get_agent(AGENT_NAME)

if "thread" not in st.session_state:
    st.session_state.thread = st.session_state.project_client.agents.create_thread()

# ---------- UI ----------
st.title("💬 Orchestrator Agent Chat")
st.caption("Powered by Azure AI Foundry")

# Display chat history from session state
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input widget
if prompt := st.chat_input("Ask the agent..."):
    # 1. Add user message to UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Send to Azure agent
    with st.spinner("Agent is thinking…"):
        project_client = st.session_state.project_client
        thread = st.session_state.thread
        agent = st.session_state.agent

        project_client.agents.create_message(
            thread_id=thread.id, role="user", content=prompt
        )
        run = project_client.agents.create_and_process_run(
            thread_id=thread.id,
            agent_id=agent.id
        )

        # Retrieve assistant messages
        msgs = project_client.agents.list_messages(thread_id=thread.id)
        assistant_texts = [m.as_dict()["text"]["value"]
                           for m in msgs.text_messages
                           if m.as_dict()["role"] == "assistant"]
        assistant_reply = assistant_texts[-1] if assistant_texts else "*No reply*"

    # 3. Add assistant message to UI
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
    with st.chat_message("assistant"):
        st.markdown(assistant_reply)