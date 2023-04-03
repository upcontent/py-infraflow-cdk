from constructs import Construct

from infraflow.cdk.core.construct import HasEnv, ConstructWithEnv


class ComponentService(Construct, HasEnv):
    def __init__(self, parent:  ConstructWithEnv, id: str, **kwargs):
        super().__init__(parent, id, **kwargs)
        self.env = parent.env
