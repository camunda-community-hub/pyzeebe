from pyzeebe.grpc_internals.zeebe_job_adapter import ZeebeJobAdapter
from pyzeebe.grpc_internals.zeebe_message_adapter import ZeebeMessageAdapter
from pyzeebe.grpc_internals.zeebe_process_adapter import ZeebeProcessAdapter


# Mixin class
class ZeebeAdapter(ZeebeProcessAdapter, ZeebeJobAdapter, ZeebeMessageAdapter):
    pass
