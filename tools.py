from workflow import generate_workflow, submit_workflow


def deploy_core(mcc, mnc):

    workflow = generate_workflow(mcc, mnc)

    submit_workflow(workflow)

    return {
        "message": f"Starting deployment of 5G core with MCC {mcc} and MNC {mnc}"
    }