# pip install azure-ai-projects==1.0.0b10
from azure.ai.projects import AIProjectClient
from azure.identity import AzureCliCredential

# -----------------------------------------------------------
# 1. Connect, get agent, create thread, send first message
# -----------------------------------------------------------
project_client = AIProjectClient.from_connection_string(
    credential=AzureCliCredential(),
    conn_str="eastus2.api.azureml.ms;36db2f46-6f76-4fca-9258-228ef9d252f0;femitask-rg;femitask-project1")

agent = project_client.agents.get_agent("asst_A1RuEQwPrHeotekt1C6t1d0M")

thread = project_client.agents.create_thread()

message = project_client.agents.create_message(
    thread_id=thread.id,
    role="user",
    content="Hi Orchestrator Agent"
)

run = project_client.agents.create_and_process_run(
    thread_id=thread.id,
    agent_id=agent.id)

messages = project_client.agents.list_messages(thread_id=thread.id)
for text_message in messages.text_messages:
    print(text_message.as_dict())

# -----------------------------------------------------------
# 2. Send a NEW prompt as the user and get the reply
# -----------------------------------------------------------
new_prompt = "I am having the issue with my Laptop, how can i apply for a new one"

new_message = project_client.agents.create_message(
    thread_id=thread.id,
    role="user",
    content=new_prompt
)

run2 = project_client.agents.create_and_process_run(
    thread_id=thread.id,
    agent_id=agent.id)

messages_after = project_client.agents.list_messages(thread_id=thread.id)
for text_message in messages_after.text_messages:
    print(text_message.as_dict())