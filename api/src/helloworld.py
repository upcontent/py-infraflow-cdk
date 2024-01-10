import aws_cdk as core
import aws_cdk.assertions as assertions
from aws_cdk import aws_events as events
from aws_cdk import aws_rds as rds
from aws_cdk import aws_sns as sns
from aws_cdk import aws_ec2 as ec2

from infraflow.cdk import ServiceStageStack
from infraflow.cdk import EnvConfig
from infraflow.cdk.iam import actions
import os.path
import json

from infraflow.cdk.events import EventBridgeEventBus
from infraflow.cdk.iam import PolicyBuilder
from infraflow.cdk.lambdas import LambdaContext

script_path = os.path.realpath(__file__)
root_dir = os.path.dirname(script_path)

class ExternalResources:
    @staticmethod
    def db(stack):
        return rds.DatabaseInstance.from_database_instance_attributes(stack, 'id',
            instance_endpoint_address="instanceEndpointAddress",
            instance_identifier="instanceIdentifier",
            port=123,
            security_groups=[ec2.SecurityGroup.from_security_group_id(stack, 'test', 'test')]
        )

    @staticmethod
    def sns_topic(stack):
        return sns.Topic.from_topic_arn(stack, 'id', 'arn')

def hello_world():
    app = core.App()
    stack = ServiceStageStack(app, service_name='MyService', stage_name='QA', env=EnvConfig(vpc_id=""))
    bus_cdk = events.EventBus(stack, 'MyBus')
    bus = EventBridgeEventBus(stack, 'MyBus', bus_cdk)
    lambda_context = LambdaContext(stack, 'tests')

    # Create API lambda
    api_lamb = lambda_context.api_function()  # FIXME
    # Create scheduled lambda
    sched_lamb = lambda_context.scheduled_function()  # FIXME

    added = bus.event('added')
    added.subscribe(lambda_context.queued_function(api_lamb, suffix='added').queue)
    added.subscribe(lambda_context.queued_function(sched_lamb, suffix='added').queue)

    bus.event('updated').with_true_prop('y').subscribe(
        lambda_context.queued_function(api_lamb, suffix='update-y').queue
    )
    bus.event('updated').with_true_prop('y').subscribe(
        lambda_context.queued_function(sched_lamb, suffix='update-y').queue
    )

    # amplify_express = bus.event('updated').with_true_prop('x').express_only()
    # amplify_express.subscribe(lambda_context.queued_function(my_test_function, suffix='express').queue)

    # amplify_default = bus.event('updated').with_true_prop('x').non_express()
    # amplify_default.subscribe(lambda_context.queued_function(my_test_function, suffix='default').queue)


    # template = assertions.Template.from_stack(stack)
    # snapshot.assert_match(json.dumps(template.to_json(), indent=2), 'cloudformation.json')

    # internal_sg = ec2.SecurityGroup(stack, 'sg')
    # internal_policy = PolicyBuilder()
    # external_policy = PolicyBuilder()

    # db = ExternalResources.db(stack)
    # sns_topic = ExternalResources.sns_topic(stack)

    # internal_sg.connections.allow_to(db)
    # internal_sg.connections.allow_to(sns_topic)

    # internal_policy.allow_resource(sns_topic).for_actions(
    #     actions.Sns.Publish
    # )
    # ip = internal_policy.build_cdk_policy(stack, 'internal-policy')

    # external_policy.allow_resource(bus_cdk).for_actions(
    #     actions.Events.PutEvents
    # )
    # ep = external_policy.build_cdk_policy(stack, 'external-policy')
