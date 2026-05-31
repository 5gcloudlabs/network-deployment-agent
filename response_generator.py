import os
import boto3
import json

from prompts import build_response_prompt

BEDROCK_REGION = os.environ.get("BEDROCK_REGION") or os.environ.get("AWS_DEFAULT_REGION")
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID")

session = boto3.Session(region_name=BEDROCK_REGION)
client = session.client("bedrock-runtime")


def generate_response(data):

    prompt = build_response_prompt(data)

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