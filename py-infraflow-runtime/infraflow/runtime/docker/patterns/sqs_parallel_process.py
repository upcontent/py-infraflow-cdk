import functools
import os
import time
import asyncio
import uuid
from datetime import timedelta
from typing import Any, Callable

import boto3
import structlog

from infraflow.runtime.docker.contracts.sqs import SqsBotoMessageRecord, SqsBotoResult

from infraflow.runtime.common.logging import get_logger

ENV_MAX_MESSAGES = int(os.environ.get("BATCH_SIZE") or 50)
ENV_MAX_RETRIES = int(os.environ.get("MAX_RETRIES") or 0)
ENV_QUEUE_NAME = os.environ.get("SQS_QUEUE") or None
ENV_RETRY_QUEUE_NAME = os.environ.get("SQS_RETRY_QUEUE") or None
ENV_DLQ_QUEUE_NAME = os.environ.get("SQS_DLQ_QUEUE") or None

logger = structlog.stdlib.BoundLogger()


def minutes_retry_scheme(retries: int = 1) -> timedelta:
    return timedelta(minutes=pow(2, retries - 1))


def async_message_processor(
        queue_name=ENV_QUEUE_NAME,
        max_messages=ENV_MAX_MESSAGES,
        retry_queue_name=ENV_QUEUE_NAME,
        max_retries=ENV_MAX_RETRIES,
        dead_letter_queue=ENV_DLQ_QUEUE_NAME
):
    def decorator(func: Callable):
        func.process_messages = lambda: process_messages(
            processor=func,
            queue_name=queue_name,
            max_messages=max_messages,
            retry_queue_name=retry_queue_name,
            max_retries=max_retries,
            dead_letter_queue_name=dead_letter_queue
        )
        return func
    return decorator


async def process_messages(
        processor: callable,
        queue_name=ENV_QUEUE_NAME,
        retry_queue_name=ENV_QUEUE_NAME,
        max_messages=ENV_MAX_MESSAGES,
        max_retries=ENV_MAX_RETRIES,
        dead_letter_queue_name=None
):
    sqs = boto3.resource("sqs")
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    retry_queue = sqs.get_queue_by_name(QueueName=retry_queue_name) if retry_queue_name else None
    dlq = sqs.get_queue_by_name(QueueName=dead_letter_queue_name) if dead_letter_queue_name else None


    class RunData:
        in_progress_tasks = []

    async def process_message(message: SqsBotoMessageRecord):
        task_id = uuid.uuid4()
        try:
            await processor(message=message)
            RunData.in_progress_tasks.append(task_id)
        except Exception as e:
            logger = get_logger('infraflow')
            logger.exception(e)
            retries = message.data.get('retries') or 0
            if retry_queue and retries < max_retries:
                message.data['retries'] = retries + 1
                # message.change_visibility(VisibilityTimeout=0)  # the ai added this but not sure why
                retry_queue.send_message(
                    MessageBody=message.body,
                    MessageAttributes=message.message_attributes,
                    DelaySeconds=minutes_retry_scheme(retries).total_seconds()
                )
            elif dlq:
                # message.change_visibility(VisibilityTimeout=0)  # the ai added this but not sure why
                dlq.send_message(MessageBody=message.body, MessageAttributes=message.message_attributes)
        finally:
            if task_id in RunData.in_progress_tasks:
                RunData.in_progress_tasks.remove(task_id)

    while True:
        if ENV_MAX_MESSAGES - len(RunData.in_progress_tasks):
            result: SqsBotoResult = queue.receive_messages(
                MaxNumberOfMessages=ENV_MAX_MESSAGES - len(RunData.in_progress_tasks),
                WaitTimeSeconds=1
            )
            for m in result.messages:
                while len(RunData.in_progress_tasks) > max_messages:
                    await asyncio.sleep(0.01)
                    process_message(m)

        await asyncio.sleep(0.01)

