from typing import Optional

from aws_cdk import App, aws_sns
import aws_cdk.aws_lambda as aws_lambda
import aws_cdk.aws_apigateway as apigateway
import aws_cdk.aws_events as aws_events
from aws_cdk.aws_ec2 import InterfaceVpcEndpointAwsService
from aws_cdk.aws_iam import IRole, Role, Policy, ManagedPolicy
from aws_cdk.aws_stepfunctions import IStateMachine

from infraflow.cdk import ServiceStageStack, EnvConfig
from infraflow.cdk.core.environment import DEFAULT_INTERFACE_SERVICES
from infraflow.cdk.docker import EcsCluster
from infraflow.cdk.events import EventBridgeEvents, InfraflowEventBus, SnsEvents
from infraflow.cdk.iam import PolicyBuilder, action_groups
from infraflow.cdk.lambdas import LambdaContext
from infraflow.cdk.sg.patterns import Tiered


class StandardServiceStage(ServiceStageStack):
    def __init__(self,
                 app: App,
                 service_name: str,
                 stage_name: str,
                 env: EnvConfig,
                 src_path: str = "src",
                 python_version: aws_lambda.Runtime = aws_lambda.Runtime.PYTHON_3_9,
                 vpc_endpoint_services: list[InterfaceVpcEndpointAwsService] = DEFAULT_INTERFACE_SERVICES,
                 **kwargs):
        super().__init__(app, service_name, stage_name, env, **kwargs)
        self.vpc_endpoint_services = vpc_endpoint_services
        self._app_role = None
        self._event_publish_policy = None
        self.python_version = python_version
        self.src_path = src_path
        self._lambda_context: Optional[LambdaContext] = None
        self._api:Optional[apigateway.IRestApi] = None
        self._event_bridge_bus_cdk: Optional[aws_events.IEventBus] = None
        self._events: Optional[EventBridgeEvents] = None
        self._ecs_cluster: Optional[EcsCluster] = None
        self.__sns_bus_ckd: Optional[aws_sns.Topic] = None
        self.security_groups: Tiered = Tiered(self)

    @property
    def api(self) -> apigateway.IRestApi:
        self.use_api()
        return self._api

    def use_api(self):
        self._api = self._api or apigateway.RestApi(self, "API")

    @property
    def events(self) -> InfraflowEventBus:
        self.use_bus()
        return self._events

    def use_events(self):
        if not self._event_bridge_bus_cdk and not self._sns_bus_ckd:
            self.use_event_bridge()

        self._events = self._events or (
            EventBridgeEvents(self, 'Events', self._event_bridge_bus_cdk) if self._event_bridge_bus_cdk else
            SnsEvents(self, 'Events', self._sns_bus_ckd) if self._sns_bus_ckd else
            None
        )

        if self._event_bridge_bus_cdk and self._app_role:
            self._event_bridge_bus_cdk.grant_put_events_to(self._app_role)

    @property
    def event_bridge_bus(self) -> aws_events.IEventBus:
        self.use_event_bridge()
        return self._event_bridge_bus_cdk

    def use_event_bridge(self):
        self._event_bridge_bus_cdk = self._event_bridge_bus_cdk or aws_events.EventBus(self, "Bus")

    @property
    def sns_bus(self) -> aws_events.IEventBus:
        self.use_sns()
        return self._sns_bus_ckd

    def use_sns(self):
        self._sns_bus_ckd = self._sns_bus_ckd or aws_sns.Topic(self, "SnsTopic")

    @property
    def default_lambda_context(self) -> LambdaContext:
        self.use_lambda()
        return self._lambda_context

    def use_lambda(self):
        self._lambda_context = self._lambda_context or LambdaContext(
            self,
            path=self.src_path,
            role=self.app_role,
            runtime=self.python_version
        )

    @property
    def ecs_cluster(self) -> EcsCluster:
        self.use_ecs()
        return self._ecs_cluster

    def use_ecs(self):
        self._ecs_cluster = self._ecs_cluster or EcsCluster(self, "EcsCluster")

    def use_monolith_lambda_api(self, handler):
        self._api = apigateway.LambdaRestApi(
            self, "API", handler=self.default_lambda_context.api_function(handler, "ApiHandler")
        )

    def use_monolith_step_function_api(self, state_machine: IStateMachine):
        self._api = apigateway.StepFunctionsRestApi(
            self, "API", state_machine=state_machine
        )

    def lambda_api_resource_handler(self, handler, name=None, suffix=None):
        return apigateway.LambdaIntegration(
            handler=self.default_lambda_context.api_function(handler, name=name, suffix=suffix)
        )

    def step_functions_api_resource_handler(self, state_machine: IStateMachine):
        integration = apigateway.StepFunctionsIntegration()
        integration.start_execution(state_machine)
        return integration

    @property
    def app_group(self):
        return self.security_groups.app

    @property
    def dbs_group(self):
        return self.security_groups.dbs

    @property
    def web_group(self):
        return self.security_groups.web

    @property
    def app_role(self) -> IRole:
        self._app_role = self._app_role or Role(self, 'Role')
        if self._event_bridge_bus_cdk:
            self._event_bridge_bus_cdk.grant_put_events_to(self._app_role)
        return self._app_role

    def setup_endpoint_access(self):
        interfaces = self.env.service_endpoints(self.vpc_endpoint_services)
        for x in interfaces:
            self.security_groups.app.connections.allow_to(x)
