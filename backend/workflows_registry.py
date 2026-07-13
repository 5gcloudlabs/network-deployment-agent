import os

ARGO_WF_BASE_PATH = os.environ.get("ARGO_WF_BASE_PATH")

WORKFLOWS = {
    "5gcore-sub-prov": {
        "type": "argo",
        "github_path": f"{ARGO_WF_BASE_PATH}/5gcore-sub-prov-wf.yaml",
        "required_params": ["mcc", "mnc", "count"],
        "next_step": "ueransim"
    },
    "5g-solution": {
        "type": "argo",
        "github_path": f"{ARGO_WF_BASE_PATH}/5g-solution-wf.yaml",
        "required_params": ["mcc", "mnc", "count"]
    },
    "sub-prov-ueransim": {
        "type": "argo",
        "github_path": f"{ARGO_WF_BASE_PATH}/sub-prov-ueransim-wf.yaml",
        "required_params": ["mcc", "mnc", "count"]
    }
}

STEP_LABELS = {
    "sub-prov": "Provision subscribers",
    "ueransim": "Deploy RAN & UE simulation",
}
