from datetime import timedelta
from typing import Union

from aws_cdk import Duration
from aws_cdk.aws_cloudwatch import Metric, ComparisonOperator, TreatMissingData, GraphWidget
from aws_cdk.aws_lambda import Function
from aws_cdk.aws_logs import MetricFilter, FilterPattern

from infraflow.cdk.core.utils import to_duration
from infraflow.cdk.instrumentation.metrics import InfraflowMetric


class LambdaMetrics:
    def __init__(self, function: Function):
        self.function = function

    @property
    def duration(self) -> InfraflowMetric:
        return InfraflowMetric(self.function.metric_duration())


    @property
    def concurrent_executions(self) -> InfraflowMetric:
        return InfraflowMetric(self.function.metric_all_concurrent_executions())


    @property
    def invocations(self) -> InfraflowMetric:
        return InfraflowMetric(self.function.metric_invocations())


    @property
    def errors(self) -> InfraflowMetric:
        return InfraflowMetric(self.function.metric_errors())


    @property
    def throttles(self) -> InfraflowMetric:
        return InfraflowMetric(self.function.metric_throttles())

    def log_filter(self, id: str, metric_name: str, metric_value: str, filter_pattern: FilterPattern):
        return MetricFilter(
            self.function,
            id,
            log_group=self.function.log_group,
            metric_namespace=self.function.stack.stack_name,
            metric_name=metric_name,
            filter_pattern=filter_pattern,
            metric_value=metric_value
        )


class LambdaAlarms:
    def __init__(self, function: Function, reserved_concurrency: int):
        self.function = function
        self.metrics = LambdaMetrics(function)
        self.reserved_concurrency = reserved_concurrency

    def running_longer_than_expected(self, over_timespan: Union[int, timedelta, Duration], evaluation_periods: int, percent_of_timeout_threshold: float):
        return self.metrics.duration.max.over(over_timespan).create_alarm(
            alarm_name="LambdaRunningLongerThanExpected",
            alarm_description="Lambda running longer than expected",
            threshold=to_duration(round(self.function.timeout.to_seconds() * percent_of_timeout_threshold)),
            evaluation_periods=evaluation_periods,
            comparison_operator=ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=TreatMissingData.NOT_BREACHING,
        )

    def invocations_exceed_threshold(self, over_timespan: Union[int, timedelta, Duration], evaluation_periods: int, threshold: int):
        return self.metrics.invocations.average.over(over_timespan).create_alarm(
            alarm_name="LambdaInvocationsExceedThreshold",
            alarm_description="Lambda invocations exceed threshold",
            threshold=threshold,
            evaluation_periods=evaluation_periods,
            comparison_operator=ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=TreatMissingData.NOT_BREACHING,
        )

    def concurrency_exceed_threshold(self, over_timespan: Union[int, timedelta, Duration], evaluation_periods: int, percent_of_max_threshold: float):
        return self.metrics.concurrent_executions.average.over(over_timespan).create_alarm(
            alarm_name="LambdaConcurrencyExceedThreshold",
            alarm_description="Lambda concurrency exceed threshold",
            threshold=round(self.reserved_concurrency * percent_of_max_threshold),
            evaluation_periods=evaluation_periods,
            comparison_operator=ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=TreatMissingData.NOT_BREACHING,
        )

    def errors_exceed_threshold(self, over_timespan: Union[int, timedelta, Duration], evaluation_periods: int, threshold: float):
        return self.metrics.errors.average.over(over_timespan).create_alarm(
            alarm_name="LambdaErrorsExceedThreshold",
            alarm_description="Lambda errors exceed threshold",
            threshold=threshold,
            evaluation_periods=evaluation_periods,
            comparison_operator=ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=TreatMissingData.NOT_BREACHING,
        )



class LambdaWidgets:
    def __init__(self, function: Function):
        self.function = function
        self.metrics = LambdaMetrics(function)

    def errors_sum_widget(self, period: Union[int, timedelta, Duration], width: int, height: int):
        widget = GraphWidget(
            title=f"{self.function.function_name} - Total Errors",
            height=height,
            width=width,
        )
        widget.add_left_metric(self.metrics.errors.sum.over(period=period))
        return widget

    def concurrent_executions_widget(self, period: Union[int, timedelta, Duration], width: int, height: int):
        widget = GraphWidget(
            title=f"{self.function.function_name} - Concurrent Executions",
            height=height,
            width=width,
        )
        widget.add_left_metric(self.metrics.concurrent_executions.max.over(period=period))
        return widget

    def invocation_widget(self, period: Union[int, timedelta, Duration], width: int, height: int):
        widget = GraphWidget(
            title=f"{self.function.function_name} - Invocations",
            height=height,
            width=width,
        )
        widget.add_left_metric(self.metrics.invocations.sum.over(period=period))
        return widget

    def duration_widget(self, period: Union[int, timedelta, Duration], width: int, height: int):
        widget = GraphWidget(
            title=f"{self.function.function_name} - Duration",
            height=height,
            width=width,
        )
        widget.add_left_metric(self.metrics.duration.average.over(period=period))
        return widget

    def throttle_widget(self, period: Union[int, timedelta, Duration], width: int, height: int):
        widget = GraphWidget(
            title=f"{self.function.function_name} - Throttles",
            height=height,
            width=width,
        )
        widget.add_left_metric(self.metrics.throttles.sum.over(period=period))
        return widget


class LambdaInstrumentation:
    def __init__(self, function: Function, reserved_concurrency):
        self.metrics = LambdaMetrics(function)
        self.reserved_concurrency = reserved_concurrency
        self.function = function
        self.widgets = LambdaWidgets(function)
        self.alarms = LambdaAlarms(function)
        self.log_group = function.log_group

