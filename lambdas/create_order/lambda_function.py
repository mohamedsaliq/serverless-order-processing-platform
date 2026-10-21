
import json
import uuid
import boto3
import os
import logging
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

AWS_REGION = os.environ["AWS_REGION"]
ORDERS_TABLE = os.environ["ORDERS_TABLE"]

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
orders_table = dynamodb.Table(ORDERS_TABLE)
sqs = boto3.client("sqs", region_name=AWS_REGION)


def lambda_handler(event, context):
    try:
        body = event.get("body", {})

        if isinstance(body, str):
            body = json.loads(body)

        if not isinstance(body, dict):
            return response(400, {"error": "Request body must be a JSON object"})

        customer_id = body.get("customer_id")
        product_id = body.get("product_id")
        quantity = body.get("quantity")

        if not customer_id:
            return response(400, {"error": "customer_id is required"})

        if not product_id:
            return response(400, {"error": "product_id is required"})

        if type(quantity) is not int or quantity <= 0:
            return response(400, {
                "error": "quantity must be a positive integer"
            })

        order = {
            "order_id": str(uuid.uuid4()),
            "customer_id": customer_id,
            "product_id": product_id,
            "quantity": quantity,
            "status": "CREATED",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        orders_table.put_item(Item=order)

        queue_url = os.environ.get("ORDERS_QUEUE_URL")
        if not queue_url:
            logger.error(
                "ORDERS_QUEUE_URL is not configured for order %s",
                order["order_id"],
            )
            return response(500, {
                "error": "Order saved but event queue is not configured",
                "order_id": order["order_id"],
            })

        message = {
            "event_type": "ORDER_CREATED",
            "order": order,
        }

        try:
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(message),
            )
        except Exception:
            logger.exception(
                "Failed to enqueue order %s",
                order["order_id"],
            )
            return response(500, {
                "error": "Order saved but event could not be queued",
                "order_id": order["order_id"],
            })

        logger.info("Order created and queued: %s", order["order_id"])
        return response(201, order)

    except (json.JSONDecodeError, TypeError):
        return response(400, {"error": "Invalid request body"})


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body),
    }
