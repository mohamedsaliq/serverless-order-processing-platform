
import json
import os
import logging

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

AWS_REGION = os.environ["AWS_REGION"]
ORDERS_TABLE = os.environ["ORDERS_TABLE"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
orders_table = dynamodb.Table(ORDERS_TABLE)
sns = boto3.client("sns", region_name=AWS_REGION)


def process_record(record):
    if record.get("eventSource") != "aws:sqs":
        raise ValueError("Unsupported event source")

    try:
        message = json.loads(record["body"])
    except (KeyError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid SQS message body") from exc

    if not isinstance(message, dict):
        raise ValueError("SQS message must be a JSON object")

    if message.get("event_type") != "ORDER_CREATED":
        raise ValueError("Unsupported order event type")

    order = message.get("order")
    if not isinstance(order, dict):
        raise ValueError("Order must be a JSON object")

    order_id = order.get("order_id")
    if not order_id:
        raise ValueError("Order is missing order_id")

    # SNS and DynamoDB cannot participate in one atomic transaction.
    # A retry after a successful publish may create a duplicate notice.
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=f"Order processed: {order_id}",
        Message=json.dumps({
            "event_type": "ORDER_PROCESSED",
            "order": order,
        }),
    )

    orders_table.update_item(
        Key={"order_id": order_id},
        UpdateExpression="SET #status = :status",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={":status": "PROCESSED"},
    )

    logger.info("Processed order %s", order_id)


def lambda_handler(event, context):
    batch_item_failures = []

    for record in event.get("Records", []):
        try:
            process_record(record)
        except Exception:
            logger.exception(
                "Failed to process SQS message %s",
                record.get("messageId", "unknown"),
            )

            message_id = record.get("messageId")
            if message_id:
                batch_item_failures.append({
                    "itemIdentifier": message_id
                })
            else:
                # Do not acknowledge a failed record if its ID is absent.
                raise

    return {"batchItemFailures": batch_item_failures}
