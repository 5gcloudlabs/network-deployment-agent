import os
import boto3
import json

BEDROCK_REGION = os.environ.get("BEDROCK_REGION") or os.environ.get("AWS_DEFAULT_REGION")
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")

session = boto3.Session(region_name=BEDROCK_REGION)
client = session.client("bedrock-runtime")


def generate_response(data):

    prompt = f"""
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

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 150,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = client.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )

    result = json.loads(response["body"].read())

    return result["content"][0]["text"]