from pyzeebe import ZeebeClient


async def test_cancel_process(zeebe_client: ZeebeClient, process_name: str, process_variables: dict):
    response = await zeebe_client.run_process(process_name, process_variables)

    await zeebe_client.cancel_process_instance(response.process_instance_key)
