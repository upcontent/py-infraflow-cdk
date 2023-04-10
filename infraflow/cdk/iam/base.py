from aws_cdk import IResource

from infraflow.cdk.arns import arn_for_resource, service_key_for_resource


class IamResource:
    def __init__(self, resource: IResource = None, service=None, pattern: str=None, all: bool=False):
        if (int(bool(resource)) + int(bool(pattern)) + int(all)) > 1:
            raise ValueError('Must only provide one parameter for: resource, pattern, or all')
        self.all = all
        self.resource = resource

        if pattern:
            if service:
                self.pattern = f"{service}:pattern"
            else:
                self.pattern = pattern
        elif all:
            self.pattern = f'{service}:*'
        elif resource:
            self.pattern = arn_for_resource(resource)

        if resource:
            self.service = service_key_for_resource(resource)
        else:
            self.service = service


class IamAction:
    def __init__(self, service: str, all: bool=False, pattern: str=None):
        """
        :param service: What AWS service this action is for
        :param all: whether to allow all actions for this service, can't be true/set if pattern is set
        :param pattern: the pattern to use for this service, can't be set if all is true
        """
        if all and pattern:
            raise ValueError('Must only provide one parameter for: pattern, or all')
        self.all = all
        if pattern:
            self.pattern = pattern
        elif all:
            self.pattern = '*'
        self.service = service
        self.key = f"{self.service}:{self.pattern}"



