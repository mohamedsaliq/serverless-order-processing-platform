
import json
import os

os.environ["AWS_REGION"] = "ap-south-2"
os.environ["ORDERS_TABLE"] = "Orders"
os.environ["ORDERS_QUEUE_URL"] = (
    "https://sqs.ap-south-2.amazonaws.com/000000000000/test-orders"
)

from lambdas.create_order import lambda_function


def valid_event():
    return {
        "body": json.dumps({
            "customer_id": "CUST001",
            "product_id": "PROD001",
            "quantity": 2,
        })
    }


def test_create_order_success(monkeypatch):
    written_items = []
    sent_messages = []

    def mock_put_item(**kwargs):
        written_items.append(kwargs["Item"])

    def mock_send_message(**kwargs):
        sent_messages.append(kwargs)
        return {"MessageId": "test-message-id"}

    monkeypatch.setattr(
        lambda_function.orders_table, "put_item", mock_put_item
    )
    monkeypatch.setattr(
        lambda_function.sqs, "send_message", mock_send_message
    )

    result = lambda_function.lambda_handler(valid_event(), None)
    body = json.loads(result["body"])

    assert result["statusCode"] == 201
    assert body["customer_id"] == "CUST001"
    assert body["product_id"] == "PROD001"
    assert body["quantity"] == 2
    assert body["status"] == "CREATED"
    assert body["order_id"]
    assert body["created_at"]

    assert len(written_items) == 1
    assert len(sent_messages) == 1

    message = json.loads(sent_messages[0]["MessageBody"])
    assert message["event_type"] == "ORDER_CREATED"
    assert message["order"]["order_id"] == body["order_id"]


def test_create_order_missing_customer_id():
    event = {
        "body": json.dumps({
            "product_id": "PROD001",
            "quantity": 2,
        })
    }

    result = lambda_function.lambda_handler(event, None)

    assert result["statusCode"] == 400
    assert json.loads(result["body"])["error"] == (
        "customer_id is required"
    )


def test_create_order_invalid_quantity():
    event = {
        "body": json.dumps({
            "customer_id": "CUST001",
            "product_id": "PROD001",
            "quantity": 0,
        })
    }

    result = lambda_function.lambda_handler(event, None)

    assert result["statusCode"] == 400
    assert json.loads(result["body"])["error"] == (
        "quantity must be a positive integer"
    )


def test_queue_failure_returns_error_and_preserves_order(monkeypatch):
    written_items = []

    monkeypatch.setattr(
        lambda_function.orders_table,
        "put_item",
        lambda **kwargs: written_items.append(kwargs["Item"]),
    )

    def fail_to_send(**kwargs):
        raise RuntimeError("Simulated SQS failure")

    monkeypatch.setattr(
        lambda_function.sqs, "send_message", fail_to_send
    )

    result = lambda_function.lambda_handler(valid_event(), None)
    body = json.loads(result["body"])

    assert result["statusCode"] == 500
    assert body["error"] == "Order saved but event could not be queued"
    assert len(written_items) == 1
    assert body["order_id"] == written_items[0]["order_id"]
