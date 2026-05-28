import os

ARGOCD_APPS_BASE_PATH = os.environ.get("ARGOCD_APPS_BASE_PATH")

ARGOCD_APPS = {
    "free5gc": {
        "type": "kubectl",
        "github_path": f"{ARGOCD_APPS_BASE_PATH}/free5gc-app/free5gc-app.yml",
        "required_params": ["mcc", "mnc"],
        "next_step": "sub-prov"
    },
    "sub-prov": {
        "type": "kubectl",
        "github_path": f"{ARGOCD_APPS_BASE_PATH}/sub-prov-app/sub-prov-app.yml",
        "required_params": ["mcc", "mnc", "count"],
        "next_step": "ueransim"
    },
    "ueransim": {
        "type": "kubectl",
        "github_path": f"{ARGOCD_APPS_BASE_PATH}/ueransim-app/ueransim-app.yml",
        "required_params": ["mcc", "mnc", "count"]
    }
}
