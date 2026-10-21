
import json
import os

os.environ["AWS_REGION"] = "ap-south-2"
os.environ["ORDERS_TABLE"] = "Orders"
os.environ["SNS_TOPIC_ARN"] = (
    "arn:aws:sns:ap-south-2:000000000000:test-topic"
)

from lambdas.process_order import lambda_function


def make_event(order=None, body=None, message_id="test-message-1"):
    if body is None:
        body = json.dumps({
            "event_type": "ORDER_CREATED",
            "order": order or {
                "order_id": "order-123",
                "customer_id": "CUST001",
                "product_id": "PROD001",
                "quantity": 2,
                "status": "CREATED",
            },
        })

    return {
        "Records": [{
            "eventSource": "aws:sqs",
            "messageId": message_id,
            "body": body,
        }]
    }


def test_process_order_success(monkeypatch):
    notifications = []
    updates = []

    monkeypatch.setattr(
        lambda_function.sns,
        "publish",
        lambda **kwargs: notifications.append(kwargs),
    )
    monkeypatch.setattr(
        lambda_function.orders_table,
        "update_item",
        lambda **kwargs: updates.append(kwargs),
    )

    result = lambda_function.lambda_handler(make_event(), None)

    assert result == {"batchItemFailures": []}
    assert len(notifications) == 1
    assert notifications[0]["Subject"] == "Order processed: order-123"
    assert len(updates) == 1
    assert updates[0]["Key"] == {"order_id": "order-123"}
    assert updates[0]["ExpressionAttributeValues"][":status"] == "PROCESSED"


def test_invalid_json_returns_partial_failure():
    event = make_event(body="{invalid-json")

    result = lambda_function.lambda_handler(event, None)

    assert result == {
        "batchItemFailures": [
            {"itemIdentifier": "test-message-1"}
        ]
    }


def test_unsupported_event_type_returns_partial_failure():
    event = make_event(body=json.dumps({
        "event_type": "UNKNOWN",
        "order": {"order_id": "order-123"},
    }))

    result = lambda_function.lambda_handler(event, None)

    assert result == {
        "batchItemFailures": [
            {"itemIdentifier": "test-message-1"}
        ]
    }


def test_sns_failure_returns_partial_failure(monkeypatch):
    updates = []

    def fail_publish(**kwargs):
        raise RuntimeError("Simulated SNS failure")

    monkeypatch.setattr(
        lambda_function.sns, "publish", fail_publish
    )
    monkeypatch.setattr(
        lambda_function.orders_table,
        "update_item",
        lambda **kwargs: updates.append(kwargs),
    )

    result = lambda_function.lambda_handler(make_event(), None)

    assert result == {
        "batchItemFailures": [
            {"itemIdentifier": "test-message-1"}
        ]
    }
    assert updates == []


def test_database_failure_returns_partial_failure(monkeypatch):
    notifications = []

    monkeypatch.setattr(
        lambda_function.sns,
        "publish",
        lambda **kwargs: notifications.append(kwargs),
    )

    def fail_update(**kwargs):
        raise RuntimeError("Simulated DynamoDB failure")

    monkeypatch.setattr(
        lambda_function.orders_table,
        "update_item",
        fail_update,
    )

    result = lambda_function.lambda_handler(make_event(), None)

    assert result == {
        "batchItemFailures": [
            {"itemIdentifier": "test-message-1"}
        ]
    }
    assert len(notifications) == 1
