from workflows_registry import WORKFLOWS, STEP_LABELS
from argocd_registry import ARGOCD_APPS
from workflow import generate_workflow, submit_workflow, kubectl_apply


def lookup_workflow(workflow_name):
    """Check both registries and return (config, registry_type) or None."""
    if workflow_name in WORKFLOWS:
        return WORKFLOWS[workflow_name]
    if workflow_name in ARGOCD_APPS:
        return ARGOCD_APPS[workflow_name]
    return None


def validate_params(wf_config, params):
    required = wf_config["required_params"]
    return [p for p in required if p not in params]


def execute_workflow(workflow_name, params):
    wf_config = lookup_workflow(workflow_name)

    if wf_config is None:
        return {"message": f"Unknown workflow: {workflow_name}"}

    missing = validate_params(wf_config, params)
    if missing:
        return {
            "status": "missing_params",
            "missing": missing,
            "message": f"Missing parameters: {', '.join(missing)}"
        }

    github_path = wf_config["github_path"]
    workflow_type = wf_config["type"]

    # Support both next_step (string) and next_steps (list) key formats
    next_step_key = wf_config.get("next_step") or (wf_config.get("next_steps", [None])[0])
    next_step = STEP_LABELS.get(next_step_key, next_step_key) if next_step_key else None

    try:
        rendered = generate_workflow(github_path, params, workflow_type)

        if workflow_type == "kubectl":
            kubectl_apply(rendered)
        else:
            submit_workflow(rendered)

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

    return {
        "status": "started",
        "workflow": workflow_name,
        "type": workflow_type,
        "message": f"Workflow '{workflow_name}' started successfully",
        "next_step": next_step
    }
