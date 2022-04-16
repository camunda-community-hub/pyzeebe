from uuid import uuid4

import pytest

from pyzeebe import ZeebeClient
from pyzeebe.errors import ProcessDefinitionNotFoundError


@pytest.mark.asyncio
async def test_run_process(zeebe_client: ZeebeClient):
    process_key = await zeebe_client.run_process("test", {"input": str(uuid4()), "should_throw": False})
    assert isinstance(process_key, int)


@pytest.mark.asyncio
async def test_non_existent_process(zeebe_client: ZeebeClient):
    with pytest.raises(ProcessDefinitionNotFoundError):
        await zeebe_client.run_process(str(uuid4()))


@pytest.mark.asyncio
async def test_run_process_with_result(zeebe_client: ZeebeClient):
    input = str(uuid4())
    process_instance_key, process_result = await zeebe_client.run_process_with_result(
        "test", {"input": input, "should_throw": False}
    )
    assert isinstance(process_instance_key, int)
    assert isinstance(process_result["output"], str)
    assert process_result["output"].startswith(input)


@pytest.mark.asyncio
async def test_cancel_process(zeebe_client: ZeebeClient):
    process_key = await zeebe_client.run_process("test", {"input": str(uuid4()), "should_throw": False})
    await zeebe_client.cancel_process_instance(process_key)
