from pyzeebe.grpc_internals.zeebe_job_adapter import ZeebeJobAdapter
from pyzeebe.grpc_internals.zeebe_message_adapter import ZeebeMessageAdapter
from pyzeebe.grpc_internals.zeebe_workflow_adapter import ZeebeWorkflowAdapter


# Mixin class
class ZeebeAdapter(ZeebeWorkflowAdapter, ZeebeJobAdapter, ZeebeMessageAdapter):
    pass
