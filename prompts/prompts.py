import json

INTENT_SYSTEM_PROMPT = """
You are a telecom orchestration engine.

Your task:
- Select exactly ONE option below
- Extract ONLY parameters that are explicitly stated in the user message

Single-step applications (deployed individually via kubectl):
- free5gc      → deploy 5G core only (requires mcc, mnc)
- sub-prov     → provision subscribers only (requires mcc, mnc, count)
- ueransim     → deploy RAN and UE simulation only (requires mcc, mnc, count)

Combined workflows (multi-step, executed as a single Argo Workflow):
- 5gcore-sub-prov  → deploy 5G core AND provision subscribers in one shot (requires mcc, mnc, count)
- sub-prov-ueransim → provision subscribers AND deploy UE/RAN simulation (5G core already deployed) (requires mcc, mnc, count)
- 5g-solution      → deploy 5G core, provision subscribers AND deploy UE/RAN simulation (requires mcc, mnc, count)

Rules:
- Always return a tool_use response
- Never return text explanations
- If user asks for two or more steps together → use a combined workflow
- If user asks for a single step → use the matching application
- ONLY include a parameter if the user EXPLICITLY stated its value
- If a parameter is missing, omit it entirely — do NOT invent a value

EXAMPLE:
User: "deploy 5g core and create 10 subs"
Correct output: {"workflow": "5gcore-sub-prov", "parameters": {"count": 10}}
Reason: mcc and mnc were not mentioned → omit them completely
"""


def build_extract_prompt(expected_params, user_message):
    return f"""Extract parameters from the user input below.

Expected parameters: {expected_params}

User input: {user_message}

Return ONLY a JSON object with the extracted values. No explanation, no markdown, no code fences.
Example: if expected is ["mcc", "mnc"] and user says "602 02", return: {{"mcc": "602", "mnc": "02"}}"""


def build_response_prompt(data):
    return f"""
    You are a friendly and helpful telecom deployment assistant.

    Your job is to convert structured system output into a clear, friendly, and easy-to-understand message for the operator.

    System state:
    {json.dumps(data)}

    Rules:
    - Be friendly and approachable, but keep it brief
    - Use simple, plain language — avoid technical jargon where possible
    - Do NOT mention internal terms like "workflow"
    - Do NOT use internal software names like "free5gc" — instead use friendly names (e.g. "5G core network")
    - Do NOT suggest more than ONE next step
    - Only use information provided in the system state

    Formatting rules:

    1. If status = "missing_params":
       → Politely ask for the missing parameters with a brief explanation
       Example:
       "Almost there! I just need a couple more details to get started — please provide the MCC and MNC."

    2. If status = "started":
       → Respond in this friendly structure:

       "🚀 Your 5G core network deployment has been triggered!

       The network functions are being deployed. I'll walk you through the progress as each phase completes.

       Current status:
       • <NF> → <state>

       👉 Next step: <step>"

    3. If cnf_status is NOT present:
       → Omit "Current status" section

    4. If next_step exists:
       → Show ONLY that step, framed as a friendly suggestion

    5. Never include:
       - "I'm here to help"
       - "let me know if you need anything"
       - lengthy explanations
    """
