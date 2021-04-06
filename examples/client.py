from pyzeebe import ZeebeClient, CamundaCloudCredentials

# Create a zeebe client without credentials
zeebe_client = ZeebeClient(hostname="localhost", port=26500)

# Create a zeebe client with TLS
zeebe_client = ZeebeClient(
    hostname="localhost", port=26500, secure_connection=True)

# Create a zeebe client for camunda cloud
camunda_cloud_credentials = CamundaCloudCredentials(client_id="<my_client_id>", client_secret="<my_client_secret>",
                                                    cluster_id="<my_cluster_id>")
zeebe_client = ZeebeClient(credentials=camunda_cloud_credentials)

# Run a Zeebe instance process
process_instance_key = zeebe_client.run_process(
    bpmn_process_id="My zeebe process", variables={})

# Run a Zeebe instance process and receive the result
process_instance_key, process_result = zeebe_client.run_process_with_result(
    bpmn_process_id="My zeebe process",
    timeout=10000
)  # Will wait 10000 milliseconds (10 seconds)

# Deploy a bpmn process definition
zeebe_client.deploy_process("process.bpmn")

# Cancel a running process
zeebe_client.cancel_process_instance(process_instance_key=12345)

# Publish message
zeebe_client.publish_message(name="message_name", correlation_key="some_id")
