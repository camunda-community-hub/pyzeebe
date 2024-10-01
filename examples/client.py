from pyzeebe import (
    ZeebeClient,
    create_camunda_cloud_channel,
    create_insecure_channel,
    create_secure_channel,
)

# Create a zeebe client without credentials
grpc_channel = create_insecure_channel(grpc_address="localhost:26500")
zeebe_client = ZeebeClient(grpc_channel)

# Create a zeebe client with TLS
grpc_channel = create_secure_channel()
zeebe_client = ZeebeClient(grpc_channel)

# Create a zeebe client for camunda cloud
grpc_channel = create_camunda_cloud_channel(
    client_id="<my_client_id>",
    client_secret="<my_client_secret>",
    cluster_id="<my_cluster_id>",
    region="<region>",  # Default is bru-2
)
zeebe_client = ZeebeClient(grpc_channel)

# Run a Zeebe instance process
process_instance_key = await zeebe_client.run_process(bpmn_process_id="My zeebe process", variables={})

# Run a Zeebe process instance and receive the result
process_instance_key, process_result = await zeebe_client.run_process_with_result(
    bpmn_process_id="My zeebe process", timeout=10000
)  # Will wait 10000 milliseconds (10 seconds)

# Deploy a bpmn process definition
await zeebe_client.deploy_resource("process.bpmn")

# Cancel a running process
await zeebe_client.cancel_process_instance(process_instance_key=12345)

# Publish message
await zeebe_client.publish_message(name="message_name", correlation_key="some_id")
