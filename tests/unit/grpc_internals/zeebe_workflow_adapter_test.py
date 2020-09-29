from io import BytesIO
from random import randint
from unittest.mock import patch, MagicMock
from uuid import uuid4

from pyzeebe.exceptions import InvalidJSON, WorkflowNotFound, WorkflowInstanceNotFound, WorkflowHasNoStartEvent, \
    WorkflowInvalid
from pyzeebe.grpc_internals.zeebe_workflow_adapter import ZeebeWorkflowAdapter
from tests.unit.utils.grpc_utils import *
from tests.unit.utils.random_utils import RANDOM_RANGE

zeebe_workflow_adapter: ZeebeWorkflowAdapter


@pytest.fixture(autouse=True)
def run_around_tests(grpc_channel):
    global zeebe_workflow_adapter
    zeebe_workflow_adapter = ZeebeWorkflowAdapter(channel=grpc_channel)
    yield
    zeebe_workflow_adapter = ZeebeWorkflowAdapter(channel=grpc_channel)


def test_create_workflow_instance(grpc_servicer):
    bpmn_process_id = str(uuid4())
    version = randint(0, 10)
    grpc_servicer.mock_deploy_workflow(bpmn_process_id, version, [])
    response = zeebe_workflow_adapter.create_workflow_instance(bpmn_process_id=bpmn_process_id, variables={},
                                                               version=version)
    assert isinstance(response, int)


def test_create_workflow_instance_common_errors_called(grpc_servicer):
    zeebe_workflow_adapter._common_zeebe_grpc_errors = MagicMock()
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.INTERNAL)

    zeebe_workflow_adapter._gateway_stub.CreateWorkflowInstance = MagicMock(side_effect=error)

    zeebe_workflow_adapter.create_workflow_instance(bpmn_process_id=str(uuid4()), variables={},
                                                    version=randint(0, 10))

    zeebe_workflow_adapter._common_zeebe_grpc_errors.assert_called()


def test_create_workflow_instance_with_result(grpc_servicer):
    bpmn_process_id = str(uuid4())
    version = randint(0, 10)
    grpc_servicer.mock_deploy_workflow(bpmn_process_id, version, [])
    response = zeebe_workflow_adapter.create_workflow_instance_with_result(bpmn_process_id=bpmn_process_id,
                                                                           variables={},
                                                                           version=version, timeout=0,
                                                                           variables_to_fetch=[])
    assert isinstance(response, dict)


def test_create_workflow_instance_with_result_common_errors_called():
    zeebe_workflow_adapter._common_zeebe_grpc_errors = MagicMock()
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.INTERNAL)

    zeebe_workflow_adapter._gateway_stub.CreateWorkflowInstanceWithResult = MagicMock(side_effect=error)

    zeebe_workflow_adapter.create_workflow_instance_with_result(bpmn_process_id=str(uuid4()), variables={},
                                                                version=randint(0, 10), timeout=0,
                                                                variables_to_fetch=[])

    zeebe_workflow_adapter._common_zeebe_grpc_errors.assert_called()


def test_cancel_workflow(grpc_servicer):
    bpmn_process_id = str(uuid4())
    version = randint(0, 10)
    grpc_servicer.mock_deploy_workflow(bpmn_process_id, version, [])
    workflow_instance_key = zeebe_workflow_adapter.create_workflow_instance(bpmn_process_id=bpmn_process_id,
                                                                            variables={}, version=version)
    zeebe_workflow_adapter.cancel_workflow_instance(workflow_instance_key=workflow_instance_key)
    assert workflow_instance_key not in grpc_servicer.active_workflows.keys()


def test_cancel_workflow_instance_already_cancelled():
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.NOT_FOUND)

    zeebe_workflow_adapter._gateway_stub.CancelWorkflowInstance = MagicMock(side_effect=error)

    with pytest.raises(WorkflowInstanceNotFound):
        zeebe_workflow_adapter.cancel_workflow_instance(workflow_instance_key=randint(0, RANDOM_RANGE))


def test_cancel_workflow_instance_common_errors_called():
    zeebe_workflow_adapter._common_zeebe_grpc_errors = MagicMock()
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.INTERNAL)

    zeebe_workflow_adapter._gateway_stub.CancelWorkflowInstance = MagicMock(side_effect=error)

    zeebe_workflow_adapter.cancel_workflow_instance(workflow_instance_key=randint(0, RANDOM_RANGE))

    zeebe_workflow_adapter._common_zeebe_grpc_errors.assert_called()


def test_deploy_workflow_workflow_invalid(grpc_servicer):
    with patch("builtins.open") as mock_open:
        mock_open.return_value = BytesIO()

        error = grpc.RpcError()
        error._state = GRPCStatusCode(grpc.StatusCode.INVALID_ARGUMENT)

        zeebe_workflow_adapter._gateway_stub.DeployWorkflow = MagicMock(side_effect=error)

        with pytest.raises(WorkflowInvalid):
            zeebe_workflow_adapter.deploy_workflow()


def test_deploy_workflow_common_errors_called(grpc_servicer):
    with patch("builtins.open") as mock_open:
        mock_open.return_value = BytesIO()

        zeebe_workflow_adapter._common_zeebe_grpc_errors = MagicMock()
        error = grpc.RpcError()
        error._state = GRPCStatusCode(grpc.StatusCode.INTERNAL)

        zeebe_workflow_adapter._gateway_stub.DeployWorkflow = MagicMock(side_effect=error)

        zeebe_workflow_adapter.deploy_workflow()

        zeebe_workflow_adapter._common_zeebe_grpc_errors.assert_called()


def test_get_workflow_request_object():
    with patch("builtins.open") as mock_open:
        mock_open.return_value = BytesIO()
        file_path = str(uuid4())
        zeebe_workflow_adapter._get_workflow_request_object(file_path)
        mock_open.assert_called_with(file_path, "rb")


def test_create_workflow_errors_not_found():
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.NOT_FOUND)
    with pytest.raises(WorkflowNotFound):
        zeebe_workflow_adapter._create_workflow_errors(error, str(uuid4()), randint(0, 10, ), {})


def test_create_workflow_errors_invalid_json():
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.INVALID_ARGUMENT)
    with pytest.raises(InvalidJSON):
        zeebe_workflow_adapter._create_workflow_errors(error, str(uuid4()), randint(0, 10, ), {})


def test_create_workflow_errors_workflow_has_no_start_event():
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.FAILED_PRECONDITION)
    with pytest.raises(WorkflowHasNoStartEvent):
        zeebe_workflow_adapter._create_workflow_errors(error, str(uuid4()), randint(0, 10, ), {})


def test_create_workflow_errors_common_errors_called():
    zeebe_workflow_adapter._common_zeebe_grpc_errors = MagicMock()
    error = grpc.RpcError()
    error._state = GRPCStatusCode("test")
    zeebe_workflow_adapter._create_workflow_errors(error, str(uuid4()), randint(0, 10, ), {})

    zeebe_workflow_adapter._common_zeebe_grpc_errors.assert_called()
