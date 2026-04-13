# Single-step ArgoCD Application deployments (kubectl apply)
ARGOCD_APPS = {
    "free5gc": {
        "type": "kubectl",
        "github_path": "5g/argocd-apps/free5gc-app/free5gc-app.yml",
        "required_params": ["mcc", "mnc"],
        "next_step": "sub-prov"
    },
    "sub-prov": {
        "type": "kubectl",
        "github_path": "5g/argocd-apps/sub-prov-app/sub-prov-app.yml",
        "required_params": ["mcc", "mnc", "count"],
        "next_step": "ueransim"
    },
    "ueransim": {
        "type": "kubectl",
        "github_path": "5g/argocd-apps/ueransim-app/ueransim-app.yml",
        "required_params": ["mcc", "mnc", "count"]
    }
}
