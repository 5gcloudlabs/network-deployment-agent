from backend.deployment_catalog import get_catalog
from backend.workflow import generate_workflow, kubectl_apply, submit_workflow


def validate_params(wf_config, params):
    required = wf_config["required_params"]
    return [p for p in required if p not in params]


def execute_workflow(workflow_name, params):
    catalog = get_catalog()
    wf_config = catalog.get_option(workflow_name)

    if wf_config is None:
        return {"message": f"Unknown workflow: {workflow_name}"}

    missing = validate_params(wf_config, params)
    if missing:
        return {
            "status": "missing_params",
            "missing": missing,
            "message": f"Missing parameters: {', '.join(missing)}",
        }

    github_path = wf_config["github_path"]
    workflow_type = wf_config["type"]

    next_step_key = wf_config.get("next_step")
    next_step = (
        catalog.step_labels.get(next_step_key, next_step_key)
        if next_step_key
        else None
    )

    try:
        rendered = generate_workflow(github_path, params, workflow_type)

        if workflow_type == "kubectl":
            kubectl_apply(rendered)
        else:
            submit_workflow(rendered)

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }

    return {
        "status": "started",
        "workflow": workflow_name,
        "type": workflow_type,
        "message": f"Workflow '{workflow_name}' started successfully",
        "next_step": next_step,
    }
