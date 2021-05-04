from random import randint
from uuid import uuid4

import pytest
from zeebe_grpc.gateway_pb2 import PublishMessageResponse

from pyzeebe.errors import MessageAlreadyExistsError
from pyzeebe.grpc_internals.zeebe_message_adapter import ZeebeMessageAdapter
from tests.unit.utils.random_utils import RANDOM_RANGE


@pytest.mark.asyncio
class TestPublishMessage:
    zeebe_message_adapter: ZeebeMessageAdapter

    @pytest.fixture(autouse=True)
    def set_up(self, zeebe_adapter: ZeebeMessageAdapter):
        self.zeebe_message_adapter = zeebe_adapter

    async def publish_message(
        self,
        name=str(uuid4()),
        variables={},
        correlation_key=str(uuid4()),
        time_to_live_in_milliseconds=randint(0, RANDOM_RANGE),
        message_id=str(uuid4())
    ):
        return await self.zeebe_message_adapter.publish_message(name, correlation_key, time_to_live_in_milliseconds, variables, message_id)

    async def test_response_is_of_correct_type(self):
        response = await self.publish_message()

        assert isinstance(response, PublishMessageResponse)

    async def test_raises_on_invalid_name(self):
        with pytest.raises(TypeError):
            await self.publish_message(name=randint(0, RANDOM_RANGE))

    async def test_raises_on_invalid_correlation_key(self):
        with pytest.raises(TypeError):
            await self.publish_message(correlation_key=randint(0, RANDOM_RANGE))

    async def test_raises_on_invalid_time_to_live(self):
        with pytest.raises(TypeError):
            await self.publish_message(time_to_live_in_milliseconds=str(uuid4()))

    async def test_raises_on_duplicate_message(self):
        message_id = str(uuid4())

        with pytest.raises(MessageAlreadyExistsError):
            await self.publish_message(message_id=message_id)
            await self.publish_message(message_id=message_id)
