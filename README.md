# Network Deployment Agent

**An AI-powered operational interface for deploying and provisioning cloud-native 5G network environments.**

Part of the **5G Cloud Labs** project.

This repository contains an **AI capability** that is developed independently and integrated into platform environments when ready for end-to-end evaluation.

For the project-wide contributor model and repository roles, see the [5G Cloud Labs organization profile](https://github.com/5gcloudlabs).

---

## Overview

The Network Deployment Agent provides a natural language interface for deploying and provisioning 5G network components on a running platform environment.

Users describe the desired outcome — for example deploying the 5G Core, provisioning subscribers, or deploying a complete end-to-end scenario. The agent interprets that intent, collects any required deployment parameters, and invokes the appropriate deployment action.

It is currently integrated into platform environments such as [`5g-platform-aws`](https://github.com/5gcloudlabs/5g-platform-aws), where network components are deployed on demand rather than during platform installation.

---

## Why This Use Case Exists

Deploying and provisioning a cloud-native 5G network involves multiple deployment paths, parameters, and operational steps. Manual execution through CLI commands and fixed scripts increases operational complexity and makes experimentation more difficult.

This use case explores how large language models (LLMs) can simplify deployment and provisioning workflows while remaining integrated with reproducible, GitOps-driven platform automation.

The agent is developed independently as a reusable capability and integrated into platform environments when ready for end-to-end evaluation.

---

## Current Capabilities

Current capabilities include:

- Natural language interaction at `https://console.<your-domain>`
- Guided parameter collection (MCC, MNC, subscriber count when required)
- Individual network component deployment via Argo CD Applications
- Multi-step deployment workflows via Argo Workflows
- Deployment progress reporting
- Connectivity validation through the user plane (when UERANSIM is deployed)

### Deployment Options

**Single-step deployment**

| Operation | Deploys | Parameters |
|-----------|---------|------------|
| 5G Core | Free5GC network functions | MCC, MNC |
| Subscriber provisioning | `sub-prov` Job | MCC, MNC, subscriber count |
| RAN / UE simulation | UERANSIM | MCC, MNC, subscriber count |

**Workflow-based deployment**

| Workflow | Deployment sequence | Parameters |
|----------|---------------------|------------|
| Core + Subscribers | Free5GC → Subscriber provisioning | MCC, MNC, subscriber count |
| Subscribers + Simulation | Subscriber provisioning → UERANSIM *(requires running Core)* | MCC, MNC, subscriber count |
| Complete 5G Environment | Free5GC → Subscriber provisioning → UERANSIM | MCC, MNC, subscriber count |

### Example Requests

```text
Deploy the 5G Core with MCC 602 and MNC 02
```

```text
Deploy the full 5G solution with MCC 602, MNC 02, and 10 subscribers
```

If required information is missing, the agent automatically requests the remaining parameters before executing any deployment.

---

## Operational Flow

```text
                 User
                   │
                   ▼
          Chainlit Web Interface
                   │
                   ▼
             FastAPI Backend
                   │
                   ▼
          Amazon Bedrock (Claude Haiku 4.5)
                   │
         Intent & Parameter Extraction
                   │
                   ▼
      Platform repository (manifest fetch)
                   │
           ┌───────┴────────┐
           ▼                ▼
      Argo CD Apps    Argo Workflows
           │                │
           └───────┬────────┘
                   ▼
         Network Components
      (Free5GC · sub-prov · UERANSIM)
```

| Component | Purpose |
|-----------|---------|
| Frontend | Natural language chat interface |
| Backend | Intent handling, parameter collection, orchestration |
| Amazon Bedrock | LLM inference for intent interpretation (default: Anthropic Claude Haiku 4.5) |
| Manifest retrieval | Reads deployment manifests from the platform repository (`GITHUB_RAW_BASE`) |
| Execution | Applies Argo CD Application manifests or submits Argo Workflows on the cluster |

On platform environments, the agent runs as the `network-deployment-agent` Kubernetes service (`network-deployment-agent-frontend` and `network-deployment-agent-backend` in the `network-deployment-agent` namespace), packaged from a **single container image** with different entrypoints per workload.

---

## How It Works

1. The user submits a request through the web interface.
2. Amazon Bedrock interprets the requested operation and selects exactly one deployment option.
3. The backend collects MCC, MNC, and subscriber count when explicitly provided or required.
4. Deployment manifests are fetched from the platform repository (`GITHUB_RAW_BASE`).
5. Single-step operations apply Argo CD Application manifests to the cluster; multi-step flows submit Argo Workflows.
6. Deployment progress and operational status are reported back to the user.

Platform administration, troubleshooting, and advanced validation remain available through standard Kubernetes and cloud tooling when required.

---

## Repository Layout

```text
.
├── frontend/              Chainlit web interface (frontend.py, chainlit.md)
├── backend/               FastAPI service (main.py and orchestration modules)
├── prompts/               LLM prompts and intent templates
├── tests/                 Unit and integration tests
├── docs/                  Use case documentation
├── Dockerfile             Single image for frontend and backend workloads
├── requirements.txt       Python dependencies
└── README.md
```

The container image is published as `ghcr.io/5gcloudlabs/network-deployment-agent`. Root-level `main.py` and `frontend.py` symlinks in the image preserve compatibility with the platform Helm chart entrypoints.

Platform packaging (Helm chart, Argo CD application, IAM) lives in the platform environment repository. For AWS:

```text
5g-platform-aws/
└── cluster-bootstrap/
    └── helm-charts/
        └── network-deployment-agent/
```

### Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.

# Backend API
uvicorn backend.main:app --reload --port 8000

# Frontend (separate terminal; set BACKEND_URL=http://localhost:8000)
chainlit run frontend/frontend.py --port 8080
```

---

## Development Workflow

Contributors do **not** require a deployed platform environment for all development activities.

| Stage | Location | Typical work |
|-------|----------|--------------|
| Develop | This repository or local workstation | Backend development, prompts, frontend, API behaviour |
| Integrate | Platform environment repository | Package and integrate into a platform environment |
| Evaluate | Running platform environment | End-to-end evaluation against live network components |

Most work can be completed locally. Platform deployment is primarily required when validating integrated behaviour.

---

## Integration

The Network Deployment Agent is integrated into platform environments during cluster bootstrap.

| Platform | Integration |
|----------|-------------|
| [`5g-platform-aws`](https://github.com/5gcloudlabs/5g-platform-aws) | Helm chart at `cluster-bootstrap/helm-charts/network-deployment-agent/`, synced by Argo CD as application `network-deployment-agent` |

Typical usage after platform provisioning:

1. Open `https://console.<your-domain>`.
2. Submit a deployment request through the agent.
3. Review deployment progress.
4. Validate network operation on the running platform.

Platform-specific operational guidance: [Network deployment](https://github.com/5gcloudlabs/5g-platform-aws/blob/5g-platform-aws/docs/installation-instructions/01%20network-deployment.md) in `5g-platform-aws`.

Bedrock access on the platform uses an IRSA role attached to the `network-deployment-agent` service account.

---

## Configuration

Key runtime configuration (provided by the platform Helm chart):

| Variable | Purpose |
|----------|---------|
| `DOMAIN_NAME` | Public platform domain |
| `AWS_DEFAULT_REGION` | AWS region for cluster and API calls |
| `BEDROCK_REGION` | AWS region for Amazon Bedrock |
| `BEDROCK_MODEL_ID` | LLM model or inference profile (default: Claude Haiku 4.5) |
| `GITHUB_RAW_BASE` | Base URL for fetching platform deployment manifests |
| `DEPLOYMENT_CATALOG_PATH` | Path to deployment catalog YAML in the platform repo (default: `5g/deployment-catalog.yaml`) |
| `ARGO_WF_BASE_PATH` | Argo Workflow manifest path under the platform repo |
| `ARGOCD_APPS_BASE_PATH` | Argo CD Application manifest path under the platform repo |
| `CORE_NAMESPACE` | Free5GC namespace (default: `free5gc`) |
| `UERANSIM_NAMESPACE` | UERANSIM namespace (default: `ueransim`) |
| `POLL_INTERVAL` | Status polling interval (seconds) |
| `PING_INTERFACE` / `PING_TARGET` / `PING_COUNT` | User-plane connectivity validation settings |

---

## Contributing

Contributions are welcome.

Typical contribution areas include:

- Agent orchestration logic
- Prompt engineering
- Frontend improvements
- Backend APIs
- Additional deployment capabilities

Platform-specific integration and packaging are maintained in the corresponding [platform environment](https://github.com/5gcloudlabs/5g-platform-aws) repository.

Open an issue or pull request to discuss changes, integration points, or new deployment capabilities.

---

## Related Repositories

| Repository | Role |
|------------|------|
| [`5g-platform-aws`](https://github.com/5gcloudlabs/5g-platform-aws) | AWS platform environment integrating this use case |
| `5g-platform-gcp` | Future platform environment *(planned)* |

---

## License

Apache License 2.0

---

## Maintainer

**5G Cloud Labs**

🌐 Website: https://5gcloudlabs.ai

📧 Contact: info@5gcloudlabs.ai
