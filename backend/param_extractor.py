import os
import boto3
import json

from backend.constants import ANTHROPIC_VERSION
from prompts import build_extract_prompt

BEDROCK_REGION = os.environ.get("BEDROCK_REGION") or os.environ.get("AWS_DEFAULT_REGION")
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID")

session = boto3.Session(region_name=BEDROCK_REGION)
client = session.client("bedrock-runtime")


def _parse_json_response(text):
    """Extract JSON from model response, handling markdown code fences."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return {}


def extract_params(user_message, expected_params, current_params=None):

    prompt = build_extract_prompt(expected_params, user_message)

    body = {
        "anthropic_version": ANTHROPIC_VERSION,
        "max_tokens": 100,
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
    text = result["content"][0]["text"]
    return _parse_json_response(text)