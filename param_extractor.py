import os
import boto3
import json

AWS_REGION = os.environ.get("AWS_DEFAULT_REGION")
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")

session = boto3.Session(region_name=AWS_REGION)
client = session.client("bedrock-runtime")


def extract_params(user_message, expected_params, current_params=None):

    prompt = f"""
Extract the following parameters from the user input.

Parameters: {expected_params}

Return JSON only.

User input:
{user_message}
"""

    body = {
        "anthropic_version": "bedrock-2023-05-31",
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

    try:
        return json.loads(text)
    except:
        return {}