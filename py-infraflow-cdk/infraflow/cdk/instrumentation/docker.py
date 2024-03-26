from datetime import timedelta
from typing import Union

from aws_cdk import Duration
from aws_cdk.aws_cloudwatch import ComparisonOperator, TreatMissingData, GraphWidget
from aws_cdk.aws_ecs import FargateService
from aws_cdk.aws_logs import MetricFilter, FilterPattern, LogGroup
from constructs import Construct

from infraflow.cdk.core.utils import to_duration
from infraflow.cdk.instrumentation.metrics import InfraflowMetric


class EcsServiceMetrics:
    def __init__(self, ecs_service: FargateService, log_group: LogGroup, scope: Construct=None):
        self.log_group = log_group
        self.ecs_service = ecs_service
        self.scope = ecs_service.stack if scope is None else scope

    @property
    def cpu(self) -> InfraflowMetric:
        return InfraflowMetric(self.ecs_service.metric_cpu_utilization())

    @property
    def memory(self) -> InfraflowMetric:
        return InfraflowMetric(self.ecs_service.metric_memory_utilization())

    def log_filter(self, id: str, metric_name: str, metric_value: str, filter_pattern: FilterPattern):
        return MetricFilter(
            self.ecs_service,
            id,
            log_group=self.log_group,
            metric_namespace=self.ecs_service.stack.stack_name,
            metric_name=metric_name,
            filter_pattern=filter_pattern,
            metric_value=metric_value
        )


class EcsServiceAlarms:
    def __init__(self, ecs_service: FargateService, scope: Construct=None):
        self.ecs_service = ecs_service
        self.metrics = EcsServiceMetrics(ecs_service)
        self.scope = ecs_service.stack if scope is None else scope

    def cpu_over_threshold(self, over_timespan: Union[int, timedelta, Duration], evaluation_periods: int, threshold: float):
        return self.metrics.cpu.average.over(period=over_timespan).create_alarm(
            id=f"{self.ecs_service}ContainerCPUOverThreshold",
            alarm_name=f"{self.ecs_service.service_name}ContainerCPUOverThreshold",
            scope=self.scope,
            alarm_description="Container CPU Over Threshold",
            evaluation_periods=evaluation_periods,
            threshold=threshold,
            comparison_operator=ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=TreatMissingData.NOT_BREACHING,
        )

    def cpu_under_threshold(self, over_timespan: Union[int, timedelta, Duration], evaluation_periods: int, threshold: float):
        return self.metrics.cpu.average.over(period=over_timespan).create_alarm(
            id=f"{self.ecs_service}ContainerCPUUnderThreshold",
            alarm_name=f"{self.ecs_service.service_name}ContainerCPUUnderThreshold",
            scope=self.scope,
            alarm_description="Container CPU Under Threshold",
            evaluation_periods=evaluation_periods,
            threshold=threshold,
            comparison_operator=ComparisonOperator.LESS_THAN_THRESHOLD,
            treat_missing_data=TreatMissingData.NOT_BREACHING,
        )

    def memory_over_threshold(self, over_timespan: Union[int, timedelta, Duration], evaluation_periods: int, threshold: float):
        return self.metrics.cpu.average.over(period=over_timespan).create_alarm(
            id=f"{self.ecs_service}ContainerMemoryOverThreshold",
            scope=self.scope,
            alarm_name=f"{self.ecs_service.service_name}ContainerMemoryOverThreshold",
            alarm_description="Container Memory Over Threshold",
            evaluation_periods=evaluation_periods,
            threshold=threshold,
            comparison_operator=ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=TreatMissingData.NOT_BREACHING,
        )

    def memory_under_threshold(self, over_timespan: Union[int, timedelta, Duration], evaluation_periods: int, threshold: float):
        return self.metrics.cpu.average.over(period=over_timespan).create_alarm(
            id=f"{self.ecs_service.service_name}ContainerMemoryUnderThreshold",
            alarm_name=f"{self.ecs_service.service_name}ContainerMemoryUnderThreshold",
            scope=self.scope,
            alarm_description="Container Memory Under Threshold",
            evaluation_periods=evaluation_periods,
            threshold=threshold,
            comparison_operator=ComparisonOperator.LESS_THAN_THRESHOLD,
            treat_missing_data=TreatMissingData.NOT_BREACHING,
        )


class EcsServiceWidgets:
    def __init__(self, ecs_service: FargateService, scope: Construct=None):
        self.ecs_service = ecs_service
        self.metrics = EcsServiceMetrics(ecs_service)
        self.scope = ecs_service.stack if scope is None else scope

    def combined_widget(self, period: Union[int, timedelta, Duration], width: int, height: int):
        widget = GraphWidget(
            title=f"{self.ecs_service.service_name} - CPU",
            height=height,
            width=width,
        )
        widget.add_left_metric(self.metrics.cpu.average.over(period=period))
        widget.add_right_metric(self.metrics.memory.average.over(period=period))
        return widget

    def cpu_widget(self, period: Union[int, timedelta, Duration], width: int, height: int):
        widget = GraphWidget(
            title=f"{self.ecs_service.service_name} - CPU",
            height=height,
            width=width,
        )
        widget.add_left_metric(self.metrics.cpu.average.over(period=period))
        return widget

    def memory_widget(self, period: Union[int, timedelta, Duration], width: int, height: int):
        widget = GraphWidget(
            title=f"{self.ecs_service.service_name} - Memory",
            height=height,
            width=width,
        )
        widget.add_left_metric(self.metrics.memory.average.over(period=period))
        return widget


class EcsServiceInstrumentation:
    def __init__(self, ecs_service: FargateService, log_group: LogGroup, scope: Construct=None):
        self.scope = ecs_service.stack if scope is None else scope
        self.log_group = log_group
        self.metrics = EcsServiceMetrics(ecs_service, log_group, scope=self.scope)
        self.ecs_service = ecs_service
        self.widgets = EcsServiceWidgets(ecs_service, scope=self.scope)
        self.alarms = EcsServiceAlarms(ecs_service, scope=self.scope)
