# Combined Argo Workflow templates (multi-step deployments)
WORKFLOWS = {
    "5gcore-sub-prov": {
        "type": "argo",
        "github_path": "5g/argo-workflows/5gcore-sub-prov-wf.yaml",
        "required_params": ["mcc", "mnc", "count"],
        "next_step": "ueransim"
    },
    "5g-solution": {
        "type": "argo",
        "github_path": "5g/argo-workflows/5g-solution-wf.yaml",
        "required_params": ["mcc", "mnc", "count"]
    },
    "sub-prov-ueransim": {
        "type": "argo",
        "github_path": "5g/argo-workflows/sub-prov-ueransim-wf.yaml",
        "required_params": ["mcc", "mnc", "count"]
    }
}

STEP_LABELS = {
    "sub-prov": "Provision subscribers",
    "ueransim": "Deploy RAN & UE simulation",
}
