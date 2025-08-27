# chat_app.py
import streamlit as st
from azure.ai.projects import AIProjectClient
from azure.identity import AzureCliCredential
import json
import time

# ---------- CONFIGURATION ----------
CONN_STR = (
    "eastus2.api.azureml.ms;"
    "36db2f46-6f76-4fca-9258-228ef9d252f0;"
    "femitask-rg;"
    "femitask-project1"
)
AGENT_NAME = "asst_A1RuEQwPrHeotekt1C6t1d0M"

# ---------- SESSION STATE ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "debug_info" not in st.session_state:
    st.session_state.debug_info = []

# Initialize Azure clients
if "project_client" not in st.session_state:
    try:
        st.session_state.project_client = AIProjectClient.from_connection_string(
            credential=AzureCliCredential(),
            conn_str=CONN_STR,
        )
        st.session_state.debug_info.append("✅ AIProjectClient created successfully")
    except Exception as e:
        st.session_state.debug_info.append(f"❌ Failed to create AIProjectClient: {e}")
        st.error(f"Failed to create AIProjectClient: {e}")

if "agent" not in st.session_state and "project_client" in st.session_state:
    try:
        st.session_state.agent = st.session_state.project_client.agents.get_agent(AGENT_NAME)
        st.session_state.debug_info.append(f"✅ Agent '{AGENT_NAME}' retrieved successfully")
    except Exception as e:
        st.session_state.debug_info.append(f"❌ Failed to get agent: {e}")
        st.error(f"Failed to get agent: {e}")

if "thread" not in st.session_state and "project_client" in st.session_state:
    try:
        st.session_state.thread = st.session_state.project_client.agents.create_thread()
        st.session_state.debug_info.append("✅ Thread created successfully")
        
        # Add the initial assistant greeting to our chat UI
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Hello! How can I assist you today?"
        })
    except Exception as e:
        st.session_state.debug_info.append(f"❌ Failed to create thread: {e}")
        st.error(f"Failed to create thread: {e}")

# ---------- UI ----------
st.title("💬 Orchestrator Agent Chat")
st.caption("Powered by Azure AI Foundry")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Debug section (collapsible)
with st.expander("Debug Information"):
    st.write("Connection Details:")
    st.code(f"Connection String: {CONN_STR}\nAgent Name: {AGENT_NAME}")
    
    st.write("Session State:")
    st.json({k: str(type(v)) for k, v in st.session_state.items()})
    
    st.write("Debug Log:")
    for log_entry in st.session_state.debug_info:
        st.text(log_entry)

# Chat input
if prompt := st.chat_input("Ask the agent..."):
    # Add user message to UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Send to Azure agent
    with st.spinner("Agent is thinking…"):
        try:
            project_client = st.session_state.project_client
            thread = st.session_state.thread
            agent = st.session_state.agent
            
            # Log the request
            st.session_state.debug_info.append(f"📤 Sending message: {prompt}")
            
            # Create user message
            message_result = project_client.agents.create_message(
                thread_id=thread.id, 
                role="user", 
                content=prompt
            )
            st.session_state.debug_info.append(f"✅ User message created: {message_result.id if hasattr(message_result, 'id') else 'No ID'}")
            
            # Create and process run
            run = project_client.agents.create_and_process_run(
                thread_id=thread.id,
                agent_id=agent.id
            )
            st.session_state.debug_info.append(f"✅ Run created: {run.id if hasattr(run, 'id') else 'No ID'}")
            
            # Wait for the run to complete
            max_attempts = 10
            for attempt in range(max_attempts):
                run_status = project_client.agents.get_run(thread_id=thread.id, run_id=run.id)
                status = run_status.status if hasattr(run_status, 'status') else 'unknown'
                st.session_state.debug_info.append(f"🔄 Run status: {status} (attempt {attempt + 1})")
                
                if status in ['completed', 'failed', 'cancelled', 'expired']:
                    break
                    
                time.sleep(1)
            
            # Retrieve assistant messages
            msgs = project_client.agents.list_messages(thread_id=thread.id)
            
            # Debug: Let's examine the full structure of the messages
            all_messages = list(msgs.text_messages)
            st.session_state.debug_info.append(f"📥 Retrieved {len(all_messages)} messages")
            
            # Extract assistant responses - we need to identify which messages are from the assistant
            assistant_texts = []
            
            for msg in all_messages:
                msg_dict = msg.as_dict()
                
                # Check if this is an assistant message by looking at the content
                # Assistant messages typically come after user messages in the thread
                if "text" in msg_dict and "value" in msg_dict["text"]:
                    text_value = msg_dict["text"]["value"]
                    
                    # Check if this looks like an assistant response (not the user's message)
                    if text_value != prompt and not any(text_value == m["content"] for m in st.session_state.messages if m["role"] == "user"):
                        assistant_texts.append(text_value)
                        st.session_state.debug_info.append(f"💬 Potential assistant response: {text_value}")
            
            # If we didn't find any assistant responses, try a different approach
            if not assistant_texts and len(all_messages) > 0:
                # Get the last message that isn't the user's prompt
                for msg in reversed(all_messages):
                    msg_dict = msg.as_dict()
                    if "text" in msg_dict and "value" in msg_dict["text"]:
                        text_value = msg_dict["text"]["value"]
                        if text_value != prompt:
                            assistant_texts.append(text_value)
                            break
            
            st.session_state.debug_info.append(f"💬 Found {len(assistant_texts)} assistant responses")
            
            assistant_reply = assistant_texts[-1] if assistant_texts else "*No reply received*"
            
        except Exception as e:
            st.session_state.debug_info.append(f"❌ Error during processing: {str(e)}")
            import traceback
            st.session_state.debug_info.append(f"❌ Stack trace: {traceback.format_exc()}")
            assistant_reply = f"Error: {str(e)}"

    # Add assistant message to UI
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
    with st.chat_message("assistant"):
        st.markdown(assistant_reply)

# Add a button to clear chat history
if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.session_state.debug_info = []
    # Keep the thread but reset the UI
    st.rerun()

# Add a button to test connection
if st.sidebar.button("Test Connection"):
    try:
        if "project_client" in st.session_state:
            # Try to list agents to test connection
            agents = st.session_state.project_client.agents.list_agents()
            st.sidebar.success("✅ Connection test successful!")
            st.session_state.debug_info.append("✅ Connection test successful")
        else:
            st.sidebar.error("❌ Project client not initialized")
    except Exception as e:
        st.sidebar.error(f"❌ Connection test failed: {e}")
        st.session_state.debug_info.append(f"❌ Connection test failed: {e}")

# Add a button to inspect thread messages
if st.sidebar.button("Inspect Thread"):
    try:
        if "project_client" in st.session_state and "thread" in st.session_state:
            msgs = st.session_state.project_client.agents.list_messages(
                thread_id=st.session_state.thread.id
            )
            all_messages = list(msgs.text_messages)
            st.sidebar.write(f"Thread has {len(all_messages)} messages")
            
            for i, msg in enumerate(all_messages):
                msg_dict = msg.as_dict()
                st.sidebar.write(f"Message {i}:")
                st.sidebar.json(msg_dict)
        else:
            st.sidebar.error("❌ Project client or thread not initialized")
    except Exception as e:
        st.sidebar.error(f"❌ Inspection failed: {e}")