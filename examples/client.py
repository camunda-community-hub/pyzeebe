from pyzeebe import ZeebeClient, CamundaCloudCredentials

# Create a zeebe client without credentials
zeebe_client = ZeebeClient(hostname='localhost', port=26500)

# Create a zeebe client for camunda cloud
camunda_cloud_credentials = CamundaCloudCredentials(client_id='<my_client_id>', client_secret='<my_client_secret>',
                                                    cluster_id='<my_cluster_id>')
zeebe_client = ZeebeClient(credentials=camunda_cloud_credentials)

# Run a workflow
workflow_instance_key = zeebe_client.run_workflow(bpmn_process_id='My zeebe workflow', variables={})

# Run a workflow and receive the result
workflow_result = zeebe_client.run_workflow_with_result(bpmn_process_id='My zeebe workflow',
                                                        timeout=10000)  # Will wait 10000 milliseconds (10 seconds)

# Deploy a bpmn workflow definition
zeebe_client.deploy_workflow('workflow.bpmn')

# Cancel a running workflow
zeebe_client.cancel_workflow_instance(workflow_instance_key=12345)

# Publish message
zeebe_client.publish_message(name='message_name', correlation_key='some_id')
