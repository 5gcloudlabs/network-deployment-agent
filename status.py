import subprocess
import json
from datetime import datetime

def map_status(phase):
    mapping = {
        "Pending": "🔄 Starting",
        "Running": "✅ Available",
        "Succeeded": "✅ Completed",
        "Failed": "❌ Error",
        "Unknown": "❓ Unknown"
    }
    return mapping.get(phase, "⚙️ Initializing")


def free5gc_core_status():

    try:
        output = subprocess.check_output([
            "kubectl", "-n", "free5gc", "get", "pods",
            "-l", "nf in (amf, ausf, nrf, nssf, smf, pcf, udm, udr, upf)",
            "-o", "json"
        ]).decode()

        pod_data = json.loads(output)

        summary = {nf: "❌ Not Deployed" for nf in [
            "amf", "ausf", "nrf", "nssf", "smf", "pcf", "udm", "udr", "upf"
        ]}

        for pod in pod_data.get("items", []):
            labels = pod.get("metadata", {}).get("labels", {})
            nf = labels.get("nf")

            if nf in summary:
                phase = pod.get("status", {}).get("phase", "Unknown")
                summary[nf] = map_status(phase)

        return summary

    except Exception as e:
        return {"error": str(e)}


def _parse_json_kubectl(args):
    output = subprocess.check_output(args).decode()
    return json.loads(output)


def _pick_latest_pod(items):
    def parse_ts(item):
        ts = item.get("metadata", {}).get("creationTimestamp", "")
        # Keep sorting resilient even with unexpected values.
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return datetime.min

    if not items:
        return None
    return sorted(items, key=parse_ts)[-1]


def ueransim_status():
    """Track UE and gNB pod readiness in ueransim namespace."""
    try:
        output = subprocess.check_output([
            "kubectl", "-n", "ueransim", "get", "pods",
            "-l", "component in (gnb, ue)",
            "-o", "json"
        ]).decode()

        pod_data = json.loads(output)

        summary = {c: "❌ Not Deployed" for c in ["gnb", "ue"]}

        for pod in pod_data.get("items", []):
            labels = pod.get("metadata", {}).get("labels", {})
            component = labels.get("component")

            if component in summary:
                phase = pod.get("status", {}).get("phase", "Unknown")
                summary[component] = map_status(phase)

        return summary
    except Exception as e:
        return {"error": str(e)}


def subscriber_provisioning_stdout(tail_lines=50):
    """
    Fetch latest subscriber-provisioning pod log tail from argo namespace.
    Returns pod status + stdout tail.
    """
    try:
        pods = _parse_json_kubectl([
            "kubectl", "-n", "free5gc", "get", "pods", "-o", "json"
        ])

        candidates = []
        for item in pods.get("items", []):
            name = item.get("metadata", {}).get("name", "").lower()
            if "sub" in name and "prov" in name:
                candidates.append(item)

        if not candidates:
            return {
                "status": "not_found",
                "phase": "Unknown",
                "pod": None,
                "stdout": "Subscriber provisioning pod not found yet.",
            }

        pod = _pick_latest_pod(candidates)
        pod_name = pod.get("metadata", {}).get("name")
        phase = pod.get("status", {}).get("phase", "Unknown")

        logs = subprocess.check_output([
            "kubectl", "-n", "free5gc", "logs", pod_name,
            "-c", "subscriber-provisioner", "--tail", str(tail_lines)
        ]).decode()

        return {
            "status": "ok",
            "phase": phase,
            "pod": pod_name,
            "stdout": logs.strip() or "(no logs yet)",
        }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "phase": "Unknown",
            "pod": None,
            "stdout": (e.stderr.decode() if e.stderr else str(e)).strip(),
        }
    except Exception as e:
        return {
            "status": "error",
            "phase": "Unknown",
            "pod": None,
            "stdout": str(e),
        }


def run_latency_test(count=10, target="google.com"):
    """Run a ping test from the UE pod's uesimtun0 interface."""
    try:
        pod_data = _parse_json_kubectl([
            "kubectl", "-n", "ueransim", "get", "pods",
            "-l", "component=ue",
            "-o", "json"
        ])

        items = pod_data.get("items", [])
        if not items:
            return {"status": "error", "output": "UE pod not found in ueransim namespace."}

        ue_pod = items[0]["metadata"]["name"]

        result = subprocess.run(
            [
                "kubectl", "-n", "ueransim", "exec", "-i", ue_pod, "--",
                "ping", "-c", str(count), "-I", "uesimtun0", target,
            ],
            capture_output=True,
            timeout=30,
        )

        output = result.stdout.decode() + result.stderr.decode()
        return {
            "status": "ok" if result.returncode == 0 else "error",
            "pod": ue_pod,
            "output": output.strip(),
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "output": "Ping timed out after 30 seconds."}
    except Exception as e:
        return {"status": "error", "output": str(e)}