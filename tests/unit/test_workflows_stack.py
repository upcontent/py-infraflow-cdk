import aws_cdk as core
import aws_cdk.assertions as assertions
from aws_cdk import aws_events as events
import pytest_snapshot

from infraflow.cdk import ServiceStageStack
from infraflow.cdk import EnvConfig
import os.path
import json

from infraflow.cdk.events import EventBridgeEventBus
from infraflow.cdk.lambdas import LambdaContext
from tests.unit.lambda_test_code import my_test_function

script_path = os.path.realpath(__file__)
root_dir = os.path.dirname(script_path)

# example tests. To run these tests, uncomment this file along with the example
# resource in workflows/workflows_stack.py
def test_sqs_queue_created(snapshot):
    app = core.App()
    stack = ServiceStageStack(app, service_name='MyService', stage_name='QA', env=EnvConfig(vpc_id=""))
    bus_cdk = events.EventBus(stack, 'MyBus')
    bus = EventBridgeEventBus(stack, 'MyBus', bus_cdk)
    lambda_context = LambdaContext(stack, 'tests')

    added = bus.event('added')
    added.subscribe(lambda_context.queued_function(my_test_function, suffix='added').queue)

    amplify_express = bus.event('updated').with_true_prop('x').express_only()
    amplify_express.subscribe(lambda_context.queued_function(my_test_function, suffix='express').queue)

    amplify_default = bus.event('updated').with_true_prop('x').non_express()
    amplify_default.subscribe(lambda_context.queued_function(my_test_function, suffix='default').queue)

    bus.event('updated').with_true_prop('y').subscribe(
        lambda_context.queued_function(my_test_function, suffix='update-y').queue
    )

    template = assertions.Template.from_stack(stack)
    snapshot.assert_match(json.dumps(template.to_json(), indent=2), 'cloudformation.json')
#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
