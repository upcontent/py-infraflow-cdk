from typing import Union

from aws_cdk.aws_ec2 import Vpc
from constructs import IConstruct, Construct


class IEnv:
    @property
    def vpc(self) -> Vpc:
        raise NotImplemented()

    def subnets(self, subnet_type=None):
        raise NotImplemented()

    def get_secret(self, key) -> str:
        raise NotImplemented()

    def get_param(self, key) -> str:
        raise NotImplemented()

    @property
    def environment_vars(self) -> dict:
        raise NotImplemented()


class EnvConfig:
    def __init__(self, vpc_id: str):
        self.vpc_id = vpc_id


class Env(IEnv):
    def __init__(self, stage_name: str, scope: IConstruct, config: EnvConfig):
        self.stage_name = stage_name
        self.config = config
        self.scope = scope

    @property
    def vpc(self) -> Vpc:
        return Vpc.from_lookup(self.scope, "VPC", vpc_id=self.config.vpc_id)

    def subnets(self, subnet_type=None):
        return self.vpc.select_subnets(subnet_type)

    def get_secret(self, key):
        return ''

    def get_param(self, key):
        return ''

    @property
    def environment_vars(self):
        return {

        }