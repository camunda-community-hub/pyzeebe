from random import randint
from uuid import uuid4

import pytest


@pytest.fixture
def deployed_process(grpc_servicer):
    bpmn_process_id = str(uuid4())
    version = randint(0, 10)
    grpc_servicer.mock_deploy_process(bpmn_process_id, version, [])
    return bpmn_process_id, version
