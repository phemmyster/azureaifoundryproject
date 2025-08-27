# pip install azure-ai-projects==1.0.0b10
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
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