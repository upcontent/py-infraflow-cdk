from typing import Union
from enum import Enum
import boto3

from aws_cdk.aws_ec2 import Vpc, CfnInternetGateway, NatProvider, NatInstanceProvider, Subnet, IVpc, ISubnet, SubnetType
from constructs import IConstruct, Construct


class IEnv:
    @property
    def vpc(self) -> IVpc:
        raise NotImplemented()

    def subnets(self, subnet_type=None) -> list[ISubnet]:
        raise NotImplemented()

    def get_secret(self, key) -> str:
        raise NotImplemented()

    def get_param(self, key) -> str:
        raise NotImplemented()

    @property
    def environment_vars(self) -> dict:
        raise NotImplemented()


class EnvConfig:
    def __init__(
            self,
            vpc_id: str,
            subnet_map: dict[SubnetType, list[str]] = None,
            environment_variables: dict[str, str] = {}
    ):
        self.environment_variables = environment_variables
        self.vpc_id = vpc_id
        self.subnet_map = subnet_map


class Env(IEnv):
    def __init__(self, stage_name: str, scope: Construct, config: EnvConfig):
        self.stage_name = stage_name
        self.config = config
        self.scope = scope
        self.secrets_manager = boto3.client('secretsmanager')
        self.ssm = boto3.client('ssm')

    @property
    def vpc(self) -> IVpc:
        return Vpc.from_lookup(self.scope, "VPC", vpc_id=self.config.vpc_id)

    def vpc_subnets(self, subnet_type: SubnetType=None) -> list[ISubnet]:
        return self.vpc.select_subnets(subnet_type).subnets

    def service_subnets(self, subnet_type: SubnetType):
        vpc_subnets = self.vpc_subnets(subnet_type)
        if not self.config.subnet_map:
            return vpc_subnets

        subnet_ids = self.config.subnet_map[subnet_type]
        return [sn for sn in vpc_subnets for sni in subnet_ids if sni == sn.subnet_id]

    def secret(self, key):
        return self.secrets_manager.get_secret_value(key)

    def param(self, key):
        return self.ssm.get_parameter(key)

    @property
    def environment_vars(self):
        return self.config.environment_variables
