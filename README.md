# Serverless Order Processing Platform

An AWS serverless application that accepts orders through an HTTP API, stores them in DynamoDB, processes them asynchronously using SQS and Lambda, and publishes notifications through SNS.

The project demonstrates serverless application development, event-driven architecture, error handling, monitoring, automated testing, and cloud infrastructure operations.

## Architecture

```text
                         Client
                           |
                           v
                    Amazon API Gateway
                           |
                           v
                 Create Order Lambda
                    (Python / Boto3)
                      /         \
                     v           v
                DynamoDB       Amazon SQS
                Orders Table      |
                                  v
                          Process Order Lambda
                              /         \
                             v           v
                        DynamoDB      Amazon SNS
                        Update Status  Notifications
                                           |
                                           v
                                      Subscribers

              SQS failure handling:
              Retry policy -> Dead-letter queue (DLQ)

              Observability:
              Amazon CloudWatch Logs, metrics and alarms
```

## Order Processing Workflow

1. A client submits an order through the API Gateway HTTP endpoint.
2. The create-order Lambda validates the request.
3. The order is stored in DynamoDB with an initial `CREATED` status.
4. An `ORDER_CREATED` event is published to the SQS queue.
5. The process-order Lambda consumes the event.
6. The Lambda publishes an order notification to SNS and updates the order status to `PROCESSED`.
7. Failed SQS message processing can be retried, with messages eventually routed to a configured dead-letter queue when its redrive conditions are met.
8. CloudWatch provides logs, metrics, and alarms for operational visibility.

## AWS Services

- **Amazon API Gateway:** HTTP API endpoint for order creation.
- **AWS Lambda:** Python functions for order creation and asynchronous processing.
- **Amazon DynamoDB:** Persistent order records and processing status.
- **Amazon SQS:** Asynchronous message delivery and buffering.
- **Amazon SNS:** Order-processing notifications.
- **Amazon CloudWatch:** Application logs, monitoring, and alarms.
- **AWS IAM:** Permissions for application components to interact with AWS services.

## Technology Stack

- Python
- Boto3
- AWS Lambda
- Amazon API Gateway
- Amazon DynamoDB
- Amazon SQS
- Amazon SNS
- Amazon CloudWatch
- pytest
- Git and GitHub

## Project Structure

```text
serverless-order-processing-platform/
├── lambdas/
│   ├── create_order/
│   │   ├── __init__.py
│   │   └── lambda_function.py
│   └── process_order/
│       ├── __init__.py
│       └── lambda_function.py
├── tests/
│   ├── test_create_order.py
│   └── test_process_order.py
├── docs/
├── .gitignore
└── README.md
```

## Testing

The project includes automated unit tests for both Lambda handlers.

The current local test suite contains nine tests covering:

- Successful order creation.
- Request validation.
- Invalid quantities.
- Queue publishing failures.
- Successful asynchronous order processing.
- Invalid event payloads.
- Unsupported event types.
- SNS publishing failures.
- DynamoDB processing failures.

Run the tests locally:

```bash
python -m pytest -v
```

**Latest verified local result:** 9 tests passed.

Local unit tests do not replace end-to-end testing against deployed AWS resources.

## Reliability and Error Handling

The application includes several mechanisms for handling failures:

- Request validation before order processing.
- Logging for operational troubleshooting.
- SQS-based asynchronous processing.
- Partial batch failure reporting from the processing Lambda.
- SQS retries and dead-letter queue configuration.
- CloudWatch monitoring and alarms.

### Known Limitations

This is a learning and portfolio project, not a production-ready order management system.

- An order may be saved in DynamoDB even if publishing its SQS message fails.
- Retrying an API request can create duplicate orders because idempotency is not implemented.
- SNS publication and DynamoDB status updates are separate operations, so retries can produce duplicate notifications.
- Partial batch failure reporting depends on the event source mapping being configured to report individual failed records.
- Production deployment would require further security, resilience, idempotency, and operational testing.

## CI/CD

The next development stage introduces GitHub-based version control and automated testing.

The planned pipeline will run automated tests when code is pushed to GitHub. Automated AWS deployment will be introduced separately after the testing workflow is verified.

## Cost Awareness

AWS resources may incur charges depending on usage, configuration, retention, and regional pricing.

Review AWS Billing and Cost Management after infrastructure changes. Avoid unnecessary always-on resources and clean up resources that are no longer required.

## Learning Objectives

This project demonstrates practical experience with:

- Building serverless APIs.
- Developing AWS Lambda functions in Python.
- Using DynamoDB for application data.
- Implementing asynchronous workflows with SQS.
- Publishing notifications with SNS.
- Handling failures and configuring dead-letter queues.
- Monitoring applications with CloudWatch.
- Writing automated unit tests.
- Building a GitHub-based CI/CD workflow.

## Disclaimer

This project is intended for educational and portfolio purposes. Resource names, configuration details, and deployment instructions should be adapted to the target AWS environment.