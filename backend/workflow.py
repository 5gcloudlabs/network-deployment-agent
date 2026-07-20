import os
import httpx
import subprocess
from jinja2 import Template
import yaml

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass


def fetch_template(github_path):
    """Fetch a raw file from the platform repository via GITHUB_RAW_BASE.

    Public platform repos need no authentication. If GITHUB_TOKEN is set,
    it is sent as an optional Authorization header (for private platforms).
    """
    github_raw_base = os.getenv("GITHUB_RAW_BASE")
    if not github_raw_base:
        raise RuntimeError("GITHUB_RAW_BASE is not set")

    url = f"{github_raw_base.rstrip('/')}/{github_path.lstrip('/')}"
    headers = {}
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    response = httpx.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    return response.text


def render_envsubst(yaml_text, params):
    """
    Substitute ${ARGOCD_ENV_<PARAM>} placeholders with actual values.
    Used for single-step ArgoCD Application YAMLs.
    """
    for key, value in params.items():
        yaml_text = yaml_text.replace(f"${{ARGOCD_ENV_{key.upper()}}}", str(value))
    return yaml_text


def render_jinja(yaml_text, params):
    """
    Render Jinja2 {{ param }} placeholders.
    Used for Argo Workflow templates.
    """
    return Template(yaml_text).render(**params)


def kubectl_apply(yaml_text):
    """Apply a YAML manifest via kubectl."""
    result = subprocess.run(
        ["kubectl", "apply", "-f", "-"],
        input=yaml_text.encode(),
        capture_output=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"kubectl apply failed: {result.stderr.decode()}")
    print("kubectl apply output:", result.stdout.decode())


def generate_workflow(github_path, params, workflow_type="argo"):
    """
    Fetch and render a workflow template from GitHub.
    - argo type: Jinja2 rendering → returns parsed dict for Argo submission
    - kubectl type: envsubst rendering → returns rendered YAML string
    """
    raw = fetch_template(github_path)

    if workflow_type == "kubectl":
        return render_envsubst(raw, params)
    else:
        rendered = render_jinja(raw, params)
        return yaml.safe_load(rendered)


def submit_workflow(workflow):
    """Submit a parsed Argo Workflow dict to the cluster via kubectl."""
    yaml_text = yaml.dump(workflow, default_flow_style=False)
    kubectl_apply(yaml_text)