from fastapi import FastAPI
from bedrock_client import call_bedrock
from workflow_executor import execute_workflow
from param_extractor import extract_params
from response_generator import generate_response
from status import free5gc_core_status, ueransim_status, subscriber_provisioning_stdout, run_latency_test

app = FastAPI()

STATE = {
    "workflow": None,
    "params": {},
    "missing": []
}


@app.post("/chat")
def chat(request: dict):

    user_message = request["message"]

    # 🛡️ Step 9 — safety check (prevents broken state)
    if STATE["workflow"] and not STATE["missing"]:
        STATE["workflow"] = None
        STATE["params"] = {}

    print("STATE BEFORE:", STATE)

# 🧠 Handle "what's next" type questions
    if "next step" in user_message or "what next" in user_message:

        if STATE["workflow"] is None:
            return {"message": "No active deployment. You can start by deploying a 5G core."}

        from workflows_registry import WORKFLOWS, STEP_LABELS

        next_step = WORKFLOWS[STATE["workflow"]].get("next_step")

        if not next_step:
            return {"message": "No further steps required."}

        label = STEP_LABELS.get(next_step, next_step)

        return {
            "message": f"The next step is: {label}"
        }

    # 🔁 CASE 1 — Continuation (missing params)
    if STATE["missing"]:

        # 🧠 Optional improvement: detect new intent (override state)
        if any(word in user_message.lower() for word in ["deploy", "start", "create"]):
            print("New intent detected → resetting state")
            STATE["workflow"] = None
            STATE["params"] = {}
            STATE["missing"] = []
        else:
            # continue normal param extraction
            extracted = extract_params(user_message, STATE["missing"])
            print("EXTRACTED PARAMS:", extracted)

            STATE["params"].update(extracted)

            result = execute_workflow(STATE["workflow"], STATE["params"])

            if result.get("status") == "missing_params":
                STATE["missing"] = result["missing"]
                print("STATE AFTER:", STATE)
                return {"message": generate_response(result)}

            response = {"message": generate_response(result)}
            if result.get("status") == "started":
                response["deployment_started"] = True
                response["workflow"] = STATE["workflow"]

            # ✅ success → reset state
            STATE["workflow"] = None
            STATE["params"] = {}
            STATE["missing"] = []

            print("STATE AFTER:", STATE)
            return response

    # 🆕 CASE 2 — New request
    result = call_bedrock(user_message)

    tool_call = None
    for item in result["content"]:
        if item["type"] == "tool_use":
            tool_call = item
            break

    if not tool_call:
        return {"message": "I couldn't understand your request."}

    workflow_name = tool_call["input"]["workflow"]
    params = tool_call["input"].get("parameters", {})

    exec_result = execute_workflow(workflow_name, params)

    # ❗ missing params → store in STATE
    if exec_result.get("status") == "missing_params":
        STATE["workflow"] = workflow_name
        STATE["params"] = params
        STATE["missing"] = exec_result["missing"]

    if exec_result.get("status") == "started" and workflow_name == "free5gc":
        cnf = free5gc_core_status()
        if "error" not in cnf:
            exec_result["cnf_status"] = cnf

    print("STATE AFTER:", STATE)

    response = {"message": generate_response(exec_result)}
    if exec_result.get("status") == "started":
        response["deployment_started"] = True
        response["workflow"] = workflow_name
    return response




@app.post("/reset")
def reset():
    STATE["workflow"] = None
    STATE["params"] = {}
    STATE["missing"] = []
    return {"message": "State reset"}


@app.get("/status")
def status():
    cnf_status = free5gc_core_status()

    if "error" in cnf_status:
        return {"message": f"⚠️ Could not retrieve status: {cnf_status['error']}"}

    lines = ["📡 **5G Core Network — Deployment Status**\n"]
    for nf, state in cnf_status.items():
        lines.append(f"  • {nf.upper()}: {state}")

    return {"message": "\n".join(lines)}


@app.get("/status/raw")
def status_raw():
    return free5gc_core_status()


@app.get("/status/ueransim/raw")
def status_ueransim_raw():
    return ueransim_status()


@app.get("/status/subscribers/raw")
def status_subscribers_raw():
    return subscriber_provisioning_stdout()


@app.post("/test/latency")
def test_latency():
    return run_latency_test()
