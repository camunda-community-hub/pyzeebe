from __future__ import annotations

import grpc
from grpc_health.v1.health_pb2 import HealthCheckRequest

from pyzeebe.grpc_internals.zeebe_adapter_base import ZeebeAdapterBase
from pyzeebe.proto.gateway_pb2 import TopologyRequest

from .types import HealthCheckResponse, TopologyResponse


class ZeebeClusterAdapter(ZeebeAdapterBase):
    async def topology(self) -> TopologyResponse:
        try:
            response = await self._gateway_stub.Topology(TopologyRequest())
        except grpc.aio.AioRpcError as grpc_error:
            await self._handle_grpc_error(grpc_error)

        return TopologyResponse(
            brokers=[
                TopologyResponse.BrokerInfo(
                    node_id=broker.nodeId,
                    host=broker.host,
                    port=broker.port,
                    partitions=[
                        TopologyResponse.BrokerInfo.Partition(
                            partition_id=partition.partitionId,
                            role=TopologyResponse.BrokerInfo.Partition.PartitionBrokerRole(partition.role),
                            health=TopologyResponse.BrokerInfo.Partition.PartitionBrokerHealth(partition.health),
                        )
                        for partition in broker.partitions
                    ],
                    version=broker.version,
                )
                for broker in response.brokers
            ],
            cluster_size=response.clusterSize,
            partitions_count=response.partitionsCount,
            replication_factor=response.replicationFactor,
            gateway_version=response.gatewayVersion,
        )

    async def healthcheck(self) -> HealthCheckResponse:
        try:
            response = await self._health_stub.Check(HealthCheckRequest(service="gateway_protocol.Gateway"))
        except grpc.aio.AioRpcError as grpc_error:
            pyzeebe_error = self._create_pyzeebe_error_from_grpc_error(grpc_error)
            raise pyzeebe_error from grpc_error

        return HealthCheckResponse(status=response.status)
