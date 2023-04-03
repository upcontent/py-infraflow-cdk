from aws_cdk import aws_lambda
from aws_cdk import aws_sqs
from aws_cdk import aws_lambda_event_sources as sources
from constructs import Construct, IConstruct

from infraflow.cdk.core.service_stage import ServiceStageStack

registry = []


class LambdaContext:
    def __init__(self, stage: ServiceStageStack, path: str, runtime: aws_lambda.Runtime = aws_lambda.Runtime.PYTHON_3_9):
        self.runtime = runtime
        self.path = path
        self.stage = stage

    # def to_cdk(self):
    #     return dict(
    #         scope=self.scope,
    #         code=aws_lambda.Code.from_asset(self.path),
    #         runtime=self.runtime
    #     )

    def function(self, handler: callable, name=None, suffix=None, scope_override: IConstruct = None):
        base_name = name or handler.__name__
        constructed_name = f"{base_name}_{suffix}" if suffix else base_name
        return aws_lambda.Function(
                id=constructed_name,
                handler=f"{handler.__module__}.{handler.__name__}",
                scope=scope_override or self.stage,
                code=aws_lambda.Code.from_asset(self.path),
                runtime=self.runtime
                # function_name=''
        )

    def queued_function(self, handler, name=None, suffix=None, **queue_config):
        base_name = name or handler.__name__
        constructed_name = f"{base_name}_{suffix}" if suffix else base_name
        queued_function = QueueFunctionConstruct(self.stage, constructed_name)
        queue = aws_sqs.Queue(queued_function, 'queue', **queue_config)
        func = self.function(handler, 'function', scope_override=queued_function)
        func.add_event_source(sources.SqsEventSource(queue))
        queued_function.queue = queue
        queued_function.function = func
        return queued_function


class QueueFunctionConstruct(Construct):
    function: aws_lambda.Function
    queue: aws_sqs.Queue

    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)
