from uuid import uuid4

import pytest

from pyzeebe import ZeebeClient
from pyzeebe.errors import DecisionNotFoundError, InvalidJSONError

pytestmark = [pytest.mark.e2e, pytest.mark.anyio]


@pytest.mark.parametrize(
    ["input", "output"],
    (
        pytest.param("1", "One"),
        pytest.param("2", {"foo": "bar"}),
        pytest.param("3", 3),
    ),
)
async def test_evaluate_decision_by_id(input, output, zeebe_client: ZeebeClient, decision_id: str):
    response = await zeebe_client.evaluate_decision(None, decision_id, {"input": input})

    assert response.decision_output == output
    assert response.evaluated_decisions[0].decision_output == output
    assert response.evaluated_decisions[0].matched_rules[0].evaluated_outputs[0].output_value == output


async def test_evaluate_decision_by_key(zeebe_client: ZeebeClient, decision_key: int):
    response = await zeebe_client.evaluate_decision(decision_key, None, {"input": "1"})

    assert response.decision_output == "One"


async def test_non_existent_decision(zeebe_client: ZeebeClient):
    with pytest.raises(DecisionNotFoundError):
        await zeebe_client.evaluate_decision(1, str(uuid4()))
