from __future__ import annotations

from collections.abc import Iterable

import grpc

from pyzeebe.grpc_internals.types import (
    CancelProcessInstanceResponse,
    CreateProcessInstanceResponse,
    CreateProcessInstanceWithResultResponse,
    DeployResourceResponse,
    PublishMessageResponse,
)
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.types import Variables


class ZeebeClient:
    """A zeebe client that can connect to a zeebe instance and perform actions."""

    def __init__(self, grpc_channel: grpc.aio.Channel, max_connection_retries: int = 10) -> None:
        """
        Args:
            grpc_channel (grpc.aio.Channel): GRPC Channel connected to a Zeebe gateway
            max_connection_retries (int): Amount of connection retries before client gives up on connecting to zeebe. To setup with infinite retries use -1
        """

        self.zeebe_adapter = ZeebeAdapter(grpc_channel, max_connection_retries)

    async def run_process(
        self,
        bpmn_process_id: str,
        variables: Variables | None = None,
        version: int = -1,
        tenant_id: str | None = None,
    ) -> CreateProcessInstanceResponse:
        """
        Run process

        Args:
            bpmn_process_id (str): The unique process id of the process.
            variables (dict): A dictionary containing all the starting variables the process needs. Must be JSONable.
            version (int): The version of the process. Default: -1 (latest)
            tenant_id (str): The tenant ID of the process definition. New in Zeebe 8.3.

        Returns:
            CreateProcessInstanceResponse: response from Zeebe.

        Raises:
            ProcessDefinitionNotFoundError: No process with bpmn_process_id exists
            InvalidJSONError: variables is not JSONable
            ProcessDefinitionHasNoStartEventError: The specified process does not have a start event
            ZeebeBackPressureError: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailableError: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error
            UnknownGrpcStatusCodeError: If Zeebe returns an unexpected status code

        """
        return await self.zeebe_adapter.create_process_instance(
            bpmn_process_id=bpmn_process_id, variables=variables or {}, version=version, tenant_id=tenant_id
        )

    async def run_process_with_result(
        self,
        bpmn_process_id: str,
        variables: Variables | None = None,
        version: int = -1,
        timeout: int = 0,
        variables_to_fetch: Iterable[str] | None = None,
        tenant_id: str | None = None,
    ) -> CreateProcessInstanceWithResultResponse:
        """
        Run process and wait for the result.

        Args:
            bpmn_process_id (str): The unique process id of the process.
            variables (dict): A dictionary containing all the starting variables the process needs. Must be JSONable.
            version (int): The version of the process. Default: -1 (latest)
            timeout (int): How long to wait until a timeout occurs. Default: 0 (Zeebe default timeout)
            variables_to_fetch (List[str]): Which variables to get from the finished process
            tenant_id (str): The tenant ID of the process definition. New in Zeebe 8.3.

        Returns:
            CreateProcessInstanceWithResultResponse: response from Zeebe.

        Raises:
            ProcessDefinitionNotFoundError: No process with bpmn_process_id exists
            InvalidJSONError: variables is not JSONable
            ProcessDefinitionHasNoStartEventError: The specified process does not have a start event
            ProcessTimeoutError: The process was not finished within the set timeout
            ZeebeBackPressureError: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailableError: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error
            UnknownGrpcStatusCodeError: If Zeebe returns an unexpected status code

        """
        return await self.zeebe_adapter.create_process_instance_with_result(
            bpmn_process_id=bpmn_process_id,
            variables=variables or {},
            version=version,
            timeout=timeout,
            variables_to_fetch=variables_to_fetch or [],
            tenant_id=tenant_id,
        )

    async def cancel_process_instance(self, process_instance_key: int) -> CancelProcessInstanceResponse:
        """
        Cancel a running process instance

        Args:
            process_instance_key (int): The key of the running process to cancel

        Returns:
            CancelProcessInstanceResponse: response from Zeebe.

        Raises:
            ProcessInstanceNotFoundError: If no process instance with process_instance_key exists
            ZeebeBackPressureError: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailableError: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error
            UnknownGrpcStatusCodeError: If Zeebe returns an unexpected status code

        """
        return await self.zeebe_adapter.cancel_process_instance(process_instance_key=process_instance_key)

    async def deploy_resource(self, *resource_file_path: str, tenant_id: str | None = None) -> DeployResourceResponse:
        """
        Deploy one or more processes

        New in Zeebe 8.0.

        Args:
            resource_file_path (str): The file path to a resource definition file (bpmn/dmn/form)
            tenant_id (str): The tenant ID of the resources to deploy. New in Zeebe 8.3.

        Returns:
            DeployResourceResponse: response from Zeebe.

        Raises:
            ProcessInvalidError: If one of the process file definitions is invalid
            ZeebeBackPressureError: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailableError: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error
            UnknownGrpcStatusCodeError: If Zeebe returns an unexpected status code

        """
        return await self.zeebe_adapter.deploy_resource(*resource_file_path, tenant_id=tenant_id)

    async def publish_message(
        self,
        name: str,
        correlation_key: str,
        variables: Variables | None = None,
        time_to_live_in_milliseconds: int = 60000,
        message_id: str | None = None,
        tenant_id: str | None = None,
    ) -> PublishMessageResponse:
        """
        Publish a message

        Args:
            name (str): The message name
            correlation_key (str): The correlation key. For more info: https://docs.zeebe.io/glossary.html?highlight=correlation#correlation-key
            variables (dict): The variables the message should contain.
            time_to_live_in_milliseconds (int): How long this message should stay active. Default: 60000 ms (60 seconds)
            message_id (str): A unique message id. Useful for avoiding duplication. If a message with this id is still
                                active, a MessageAlreadyExists will be raised.
            tenant_id (str): The tenant ID of the message. New in Zeebe 8.3.

        Returns:
            PublishMessageResponse: response from Zeebe.

        Raises:
            MessageAlreadyExistsError: If a message with message_id already exists
            ZeebeBackPressureError: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailableError: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error
            UnknownGrpcStatusCodeError: If Zeebe returns an unexpected status code

        """
        return await self.zeebe_adapter.publish_message(
            name=name,
            correlation_key=correlation_key,
            time_to_live_in_milliseconds=time_to_live_in_milliseconds,
            variables=variables or {},
            message_id=message_id,
            tenant_id=tenant_id,
        )
