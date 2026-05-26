import os
import boto3
import json

BEDROCK_REGION = os.environ.get("BEDROCK_REGION") or os.environ.get("AWS_DEFAULT_REGION")
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID")

session = boto3.Session(region_name=BEDROCK_REGION)
client = session.client("bedrock-runtime")

TOOLS = [
    {
        "name": "select_workflow",
        "description": "Select the appropriate 5G deployment option and extract ONLY explicitly stated parameters",
        "input_schema": {
            "type": "object",
            "properties": {
                "workflow": {
                    "type": "string",
                    "description": "The deployment option name"
                },
                "parameters": {
                    "type": "object",
                    "description": "ONLY include parameters explicitly stated by the user. NEVER invent or assume values for mcc, mnc, or count.",
                    "properties": {
                        "mcc": {
                            "type": "string",
                            "description": "Mobile Country Code — ONLY include if the user explicitly stated it"
                        },
                        "mnc": {
                            "type": "string",
                            "description": "Mobile Network Code — ONLY include if the user explicitly stated it"
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of subscribers — ONLY include if the user explicitly stated it"
                        }
                    }
                }
            },
            "required": ["workflow"]
        }
    }
]


def validate_params(user_message, parameters):
    """
    Strip any parameter whose value doesn't appear in the user's message.
    Guards against hallucinated MCC/MNC/count values from the LLM.
    """
    return {
        key: value
        for key, value in parameters.items()
        if str(value) in user_message
    }


def call_bedrock(user_message):

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 200,
        "system": """
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
""",
        "tools": TOOLS,
        "messages": [
            {
                "role": "user",
                "content": user_message
            }
        ]
    }

    response = client.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )

    response_body = json.loads(response["body"].read())

    # Strip any parameter values the LLM invented (not present in user message)
    for item in response_body.get("content", []):
        if item.get("type") == "tool_use" and "input" in item:
            raw_params = item["input"].get("parameters", {})
            item["input"]["parameters"] = validate_params(user_message, raw_params)

    print("BEDROCK RESPONSE:", response_body)

    return response_body