import os
import time
import asyncio
from typing import Any

import boto3

MAX_MESSAGES = 50


async def process_messages(processor: callable[Any, Any, Any]):
    queue_name = os.environ["SQS_QUEUE"]
    sqs = boto3.resource("sqs")
    queue = sqs.get_queue_by_name(QueueName=queue_name)

    class RunData:
        in_progress_count = 0

    async def process(message):
        try:
            await processor(event={"message": message}, context={})
        except Exception as e:
            # TODO: Log
            pass
        finally:
            RunData.in_progress_count -= 1

    while True:
        messages = queue.receive_messages(
            MaxNumberOfMessages=MAX_MESSAGES - RunData.in_progress_count,
            WaitTimeSeconds=1
        )
        RunData.in_progress_count += len(messages)
        for m in messages:
            process(m)

        await asyncio.sleep(0.2)

