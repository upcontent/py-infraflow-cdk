from aws_cdk import Stack, App

from infraflow.cdk.core.construct import HasEnv
from infraflow.cdk.core.environment import EnvConfig, Env


class ServiceStageStack(Stack, HasEnv):
    def __init__(self, app: App, service_name: str, stage_name: str, env: EnvConfig, **kwargs):
        super().__init__(app, f"{stage_name}-{service_name}", **kwargs)
        self.service_name = service_name
        self.stage_name = stage_name
        self.scope = app
        self.env = Env(stage_name, self, env)


