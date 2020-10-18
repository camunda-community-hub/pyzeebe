from random import randint
from unittest.mock import MagicMock
from uuid import uuid4

from zeebe_grpc.gateway_pb2 import *

from pyzeebe.exceptions import MessageAlreadyExists
from pyzeebe.grpc_internals.zeebe_message_adapter import ZeebeMessageAdapter
from tests.unit.utils.grpc_utils import *
from tests.unit.utils.random_utils import RANDOM_RANGE

zeebe_message_adapter: ZeebeMessageAdapter


@pytest.fixture(autouse=True)
def run_around_tests(grpc_channel):
    global zeebe_message_adapter
    zeebe_message_adapter = ZeebeMessageAdapter(channel=grpc_channel)
    yield
    zeebe_message_adapter = ZeebeMessageAdapter(channel=grpc_channel)


def test_publish_message():
    response = zeebe_message_adapter.publish_message(name=str(uuid4()), variables={}, correlation_key=str(uuid4()),
                                                     time_to_live_in_milliseconds=randint(0, RANDOM_RANGE))
    assert isinstance(response, PublishMessageResponse)


def test_punlish_message_invalid_name():
    with pytest.raises(TypeError):
        zeebe_message_adapter.publish_message(name=randint(0, RANDOM_RANGE), variables={}, correlation_key=str(uuid4()),
                                              time_to_live_in_milliseconds=randint(0, RANDOM_RANGE))


def test_publish_message_invalid_correlation_key():
    with pytest.raises(TypeError):
        zeebe_message_adapter.publish_message(name=str(uuid4()), variables={}, correlation_key=randint(0, RANDOM_RANGE),
                                              time_to_live_in_milliseconds=randint(0, RANDOM_RANGE))


def test_punlish_message_invalid_time_to_live():
    with pytest.raises(TypeError):
        zeebe_message_adapter.publish_message(name=str(uuid4()), variables={}, correlation_key=str(uuid4()),
                                              time_to_live_in_milliseconds=str(uuid4()))


def test_publish_message_already_exists():
    message_id = str(uuid4())
    with pytest.raises(MessageAlreadyExists):
        zeebe_message_adapter.publish_message(message_id=message_id, name=str(uuid4()), variables={},
                                              correlation_key=str(uuid4()),
                                              time_to_live_in_milliseconds=randint(0, RANDOM_RANGE))
        zeebe_message_adapter.publish_message(message_id=message_id, name=str(uuid4()), variables={},
                                              correlation_key=str(uuid4()),
                                              time_to_live_in_milliseconds=randint(0, RANDOM_RANGE))


def test_publish_message_common_errors_called():
    zeebe_message_adapter._common_zeebe_grpc_errors = MagicMock()
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.INTERNAL)

    zeebe_message_adapter._gateway_stub.PublishMessage = MagicMock(side_effect=error)
    zeebe_message_adapter.publish_message(name=str(uuid4()), variables={}, correlation_key=str(uuid4()),
                                          time_to_live_in_milliseconds=randint(0, RANDOM_RANGE))

    zeebe_message_adapter._common_zeebe_grpc_errors.assert_called()
