import asyncio
import os
import chainlit as cl
import httpx

BACKEND_URL = os.environ.get("BACKEND_URL")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "1"))
DOMAIN_NAME = os.environ.get("DOMAIN_NAME")

STATUS_TRIGGERS = {"status", "check status", "deployment status", "show status"}
TEST_KEYWORDS = {"test", "validate", "ping", "latency"}
ALL_READY_STATES = {"✅ Available", "✅ Completed"}


def map_status(phase: str) -> str:
    mapping = {
        "Pending": "🔄 Starting",
        "Running": "✅ Available",
        "Succeeded": "✅ Completed",
        "Failed": "❌ Error",
        "Unknown": "❓ Unknown",
    }
    return mapping.get(phase, "⚙️ Initializing")


def all_cnfs_ready(cnf_status: dict) -> bool:
    """Return True only when every CNF reports a ready state."""
    return all(v in ALL_READY_STATES for v in cnf_status.values())


def format_cnf_status(cnf_status: dict) -> str:
    lines = ["📡 **5G Core Network — Deployment Status**\n"]
    for nf, state in cnf_status.items():
        lines.append(f"  • {nf.upper()}: {state}")
    return "\n".join(lines)


def format_ueransim_status(ueransim: dict) -> str:
    lines = ["📶 **UE & RAN Simulation — Deployment Status**\n"]
    lines.append(f"  • UE: {ueransim.get('ue', '❌ Not Deployed')}")
    lines.append(f"  • gNB: {ueransim.get('gnb', '❌ Not Deployed')}")
    return "\n".join(lines)


def is_ueransim_ready(ueransim: dict) -> bool:
    ue_state = ueransim.get("ue")
    gnb_state = ueransim.get("gnb")
    return ue_state in ALL_READY_STATES and gnb_state in ALL_READY_STATES


async def poll_full_solution_progress():
    """Walk user through full 5G solution phases sequentially."""

    # ── Phase 1: 5G Core CNF progression ─────────────────────────────────
    core_msg = cl.Message(content="📡 **Phase 1/3 — 5G Core Network Deployment**\n\nFetching status…")
    await core_msg.send()

    while True:
        await asyncio.sleep(POLL_INTERVAL)
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{BACKEND_URL}/status/raw", timeout=10)
                core_status = resp.json()
            except Exception as e:
                await cl.Message(content=f"⚠️ Could not fetch core status: {e}").send()
                return

        core_msg.content = "📡 **Phase 1/3 — 5G Core Network Deployment**\n\n" + "\n".join(
            f"  • {nf.upper()}: {state}" for nf, state in core_status.items()
        )
        await core_msg.update()

        if "error" not in core_status and all_cnfs_ready(core_status):
            break

    await cl.Message(content="✅ All 5G core network functions are up. Moving to subscriber provisioning…").send()

    # ── Phase 2: Subscriber Provisioning ─────────────────────────────────
    sub_msg = cl.Message(content="👥 **Phase 2/3 — Subscriber Provisioning**\n\nWaiting for job to start…")
    await sub_msg.send()

    while True:
        await asyncio.sleep(POLL_INTERVAL)
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{BACKEND_URL}/status/subscribers/raw", timeout=10)
                sub_status = resp.json()
            except Exception as e:
                await cl.Message(content=f"⚠️ Could not fetch subscriber status: {e}").send()
                return

        sub_phase = map_status(sub_status.get("phase", "Unknown"))
        sub_msg.content = (
            "👥 **Phase 2/3 — Subscriber Provisioning**\n\n"
            f"  • Status: {sub_phase}"
        )
        await sub_msg.update()

        if sub_status.get("phase") == "Succeeded":
            break

    stdout = sub_status.get("stdout", "(no output)").strip()[:3000]
    await cl.Message(
        content=f"📄 **Subscriber Provisioning Output**\n\n```text\n{stdout}\n```"
    ).send()

    await cl.Message(content="✅ Subscribers provisioned successfully. Moving to UE & RAN simulation deployment…").send()

    # ── Phase 3: UERANSIM ────────────────────────────────────────────────
    ue_msg = cl.Message(content="📶 **Phase 3/3 — UE & RAN Simulation Deployment**\n\nWaiting for gNB and UE pods…")
    await ue_msg.send()

    while True:
        await asyncio.sleep(POLL_INTERVAL)
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{BACKEND_URL}/status/ueransim/raw", timeout=10)
                ue_status = resp.json()
            except Exception as e:
                await cl.Message(content=f"⚠️ Could not fetch UERANSIM status: {e}").send()
                return

        ue_msg.content = "📶 **Phase 3/3 — UE & RAN Simulation Deployment**\n\n" + "\n".join([
            f"  • gNB: {ue_status.get('gnb', '❌ Not Deployed')}",
            f"  • UE: {ue_status.get('ue', '❌ Not Deployed')}",
        ])
        await ue_msg.update()

        if "error" not in ue_status and is_ueransim_ready(ue_status):
            break

    # ── Completion ────────────────────────────────────────────────────────
    await cl.Message(
        content=(
            "✅ **Everything is deployed and provisioned successfully!**\n\n"
            "Your 5G core network is running, subscribers are provisioned, "
            "and the UE & RAN simulation is active.\n\n"
            "Say *\"test network\"* to validate connectivity from the UE."
        )
    ).send()


async def poll_until_ready():
    """Poll /status/raw, updating a live Chainlit message until all CNFs are up."""
    status_msg = cl.Message(content="📡 Fetching CNF deployment status…")
    await status_msg.send()

    while True:
        await asyncio.sleep(POLL_INTERVAL)
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{BACKEND_URL}/status/raw", timeout=10)
                cnf_status = resp.json()
            except Exception as e:
                status_msg.content = f"⚠️ Could not fetch status: {e}"
                await status_msg.update()
                return

        status_msg.content = format_cnf_status(cnf_status)
        await status_msg.update()

        if all_cnfs_ready(cnf_status):
            await cl.Message(
                content=(
                    "✅ **All network functions are up and running!**\n\n"
                    "👉 Ready for the next step: **Provision subscribers**\n"
                    "Just say *\"provision subscribers\"* to continue."
                )
            ).send()
            return


@cl.on_chat_start
async def on_chat_start():
    await cl.Message(
        content=(
            "👋 **Welcome to the 5G Deployment Agent**\n\n"
            "I can deploy and configure your entire 5G environment end-to-end:\n\n"
            "  - **5G Core Network** (AMF, SMF, UPF, and all network functions)\n"
            "  - **Subscriber Provisioning** (bulk provisioning of 5G-SA subscriber profiles)\n"
            "  - **UE & RAN Simulation** (gNB + UE for testing)\n\n"
            "Just tell me what you need in plain language, for example:\n\n"
            "  *\"Deploy a 5G core, provision 10 subscribers, and set up UE & RAN simulation\"*\n"
            "  *\"Deploy only the 5G core network\"*\n\n"
            "What would you like to set up?"
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    user_text = message.content.strip()

    # Status check shortcut
    if user_text.lower() in STATUS_TRIGGERS:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{BACKEND_URL}/status/raw", timeout=10)
                cnf_status = resp.json()
                content = format_cnf_status(cnf_status)

                if all_cnfs_ready(cnf_status):
                    content += (
                        "\n\n✅ **All CNFs are ready!**\n"
                        "👉 Say *\"provision subscribers\"* to continue."
                    )
            except Exception as e:
                content = f"⚠️ Could not reach backend: {e}"
        await cl.Message(content=content).send()
        return

    # Network test shortcut
    if any(kw in user_text.lower() for kw in TEST_KEYWORDS):
        test_msg = cl.Message(content="🧪 **Running network validation test…**\n\nPinging google.com from UE pod via uesimtun0 interface…")
        await test_msg.send()

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(f"{BACKEND_URL}/test/latency", timeout=35)
                result = resp.json()
                output = result.get("output", "No output received.")
                if result.get("status") == "ok":
                    test_msg.content = f"✅ **Network Validation — Passed**\n\n```text\n{output}\n```"
                else:
                    test_msg.content = f"❌ **Network Validation — Failed**\n\n```text\n{output}\n```"
            except Exception as e:
                test_msg.content = f"⚠️ Could not run test: {e}"
        await test_msg.update()

        await cl.Message(
            content=(
                "📊 **Further Validation**\n\n"
                "You can also inspect the network via these dashboards:\n\n"
                f"  - **Registration Dashboard:** [grafana.{DOMAIN_NAME}/d/reg](https://grafana.{DOMAIN_NAME}/d/reg/reg-dashboard)\n"
                f"  - **PDU Session Dashboard:** [grafana.{DOMAIN_NAME}/d/pdu](https://grafana.{DOMAIN_NAME}/d/pdu/pdu-dashboard)\n"
                f"  - **Registration & PDU Session Details:** [webui.free5gc.{DOMAIN_NAME}](https://webui.free5gc.{DOMAIN_NAME})\n"
            )
        ).send()
        return

    # Reset shortcut
    if user_text.lower() == "reset":
        async with httpx.AsyncClient() as client:
            try:
                await client.post(f"{BACKEND_URL}/reset", timeout=10)
                await cl.Message(content="🔄 Session has been reset. Ready for a new deployment!").send()
            except Exception as e:
                await cl.Message(content=f"⚠️ Could not reset: {e}").send()
        return

    # Regular chat → POST /chat
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{BACKEND_URL}/chat",
                json={"message": user_text},
                timeout=30,
            )
            data = resp.json()
            reply = data.get("message", "Sorry, I didn't get a response.")
            deployment_started = data.get("deployment_started", False)
        except Exception as e:
            reply = f"⚠️ Could not reach backend: {e}"
            deployment_started = False

    await cl.Message(content=reply).send()

    # Auto-poll CNF status after deployment is triggered
    if deployment_started:
        workflow_name = str(data.get("workflow", "")).strip().lower()
        combined_full_workflows = {"5g-solution", "5gcore-sub-prov", "sub-prov-ueransim"}

        should_track_full = workflow_name in combined_full_workflows
        # Fallback: if backend didn't send workflow, infer from user request wording.
        if not workflow_name:
            text = user_text.lower()
            should_track_full = any(k in text for k in ["subscriber", "simulation", "gnb", "ue", "ran"])

        if should_track_full:
            await cl.Message(
                content=(
                    f"🛰️ Auto progress tracker started for `{workflow_name or 'full 5G solution'}`."
                )
            ).send()
            asyncio.create_task(poll_full_solution_progress())
        else:
            await cl.Message(content="🛰️ Auto progress tracker started for 5G core phase.").send()
            asyncio.create_task(poll_until_ready())
