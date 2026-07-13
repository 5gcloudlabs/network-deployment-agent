import os
import boto3
import json

from backend.constants import ANTHROPIC_VERSION
from backend.deployment_catalog import get_catalog
from prompts import build_intent_system_prompt

BEDROCK_REGION = os.environ.get("BEDROCK_REGION") or os.environ.get("AWS_DEFAULT_REGION")
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID")

session = boto3.Session(region_name=BEDROCK_REGION)
client = session.client("bedrock-runtime")


def _build_tools(catalog):
    return [
        {
            "name": "select_workflow",
            "description": "Select the appropriate 5G deployment option and extract ONLY explicitly stated parameters",
            "input_schema": {
                "type": "object",
                "properties": {
                    "workflow": {
                        "type": "string",
                        "enum": catalog.option_ids(),
                        "description": "The deployment option name",
                    },
                    "parameters": {
                        "type": "object",
                        "description": "ONLY include parameters explicitly stated by the user. NEVER invent or assume values for mcc, mnc, or count.",
                        "properties": {
                            "mcc": {
                                "type": "string",
                                "description": "Mobile Country Code — ONLY include if the user explicitly stated it",
                            },
                            "mnc": {
                                "type": "string",
                                "description": "Mobile Network Code — ONLY include if the user explicitly stated it",
                            },
                            "count": {
                                "type": "integer",
                                "description": "Number of subscribers — ONLY include if the user explicitly stated it",
                            },
                        },
                    },
                },
                "required": ["workflow"],
            },
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
    catalog = get_catalog()

    body = {
        "anthropic_version": ANTHROPIC_VERSION,
        "max_tokens": 200,
        "system": build_intent_system_prompt(catalog),
        "tools": _build_tools(catalog),
        "messages": [
            {
                "role": "user",
                "content": user_message,
            }
        ],
    }

    response = client.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )

    response_body = json.loads(response["body"].read())

    # Strip any parameter values the LLM invented (not present in user message)
    for item in response_body.get("content", []):
        if item.get("type") == "tool_use" and "input" in item:
            raw_params = item["input"].get("parameters", {})
            item["input"]["parameters"] = validate_params(user_message, raw_params)

    print("BEDROCK RESPONSE:", response_body)

    return response_body
