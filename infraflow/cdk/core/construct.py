from typing import TypeVar

from constructs import Construct

from infraflow.cdk.core.environment import IEnv


class HasEnv:
    env: IEnv


ConstructWithEnv = TypeVar('ConstructWithEnv', Construct, HasEnv)
