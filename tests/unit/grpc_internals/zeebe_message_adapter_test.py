from random import randint
from unittest.mock import MagicMock
from uuid import uuid4

import grpc
import pytest
from zeebe_grpc.gateway_pb2 import *

from pyzeebe.exceptions import MessageAlreadyExists
from tests.unit.utils.grpc_utils import GRPCStatusCode
from tests.unit.utils.random_utils import RANDOM_RANGE


def test_publish_message(zeebe_adapter):
    response = zeebe_adapter.publish_message(name=str(uuid4()), variables={}, correlation_key=str(uuid4()),
                                             time_to_live_in_milliseconds=randint(0, RANDOM_RANGE))
    assert isinstance(response, PublishMessageResponse)


def test_publish_message_invalid_name(zeebe_adapter):
    with pytest.raises(TypeError):
        zeebe_adapter.publish_message(name=randint(0, RANDOM_RANGE), variables={}, correlation_key=str(uuid4()),
                                      time_to_live_in_milliseconds=randint(0, RANDOM_RANGE))


def test_publish_message_invalid_correlation_key(zeebe_adapter):
    with pytest.raises(TypeError):
        zeebe_adapter.publish_message(name=str(uuid4()), variables={}, correlation_key=randint(0, RANDOM_RANGE),
                                      time_to_live_in_milliseconds=randint(0, RANDOM_RANGE))


def test_punlish_message_invalid_time_to_live(zeebe_adapter):
    with pytest.raises(TypeError):
        zeebe_adapter.publish_message(name=str(uuid4()), variables={}, correlation_key=str(uuid4()),
                                      time_to_live_in_milliseconds=str(uuid4()))


def test_publish_message_already_exists(zeebe_adapter):
    message_id = str(uuid4())
    with pytest.raises(MessageAlreadyExists):
        zeebe_adapter.publish_message(message_id=message_id, name=str(uuid4()), variables={},
                                      correlation_key=str(uuid4()),
                                      time_to_live_in_milliseconds=randint(0, RANDOM_RANGE))
        zeebe_adapter.publish_message(message_id=message_id, name=str(uuid4()), variables={},
                                      correlation_key=str(uuid4()),
                                      time_to_live_in_milliseconds=randint(0, RANDOM_RANGE))


def test_publish_message_common_errors_called(zeebe_adapter):
    zeebe_adapter._common_zeebe_grpc_errors = MagicMock()
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.INTERNAL)

    zeebe_adapter._gateway_stub.PublishMessage = MagicMock(side_effect=error)
    zeebe_adapter.publish_message(name=str(uuid4()), variables={}, correlation_key=str(uuid4()),
                                  time_to_live_in_milliseconds=randint(0, RANDOM_RANGE))

    zeebe_adapter._common_zeebe_grpc_errors.assert_called()
