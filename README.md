# Serverless Order Processing Platform

## Overview

A hands-on AWS serverless application demonstrating order creation, asynchronous event processing, and notifications.

## Architecture

1. Amazon API Gateway exposes the order creation HTTP endpoint.
2. The create_order Lambda validates requests, stores orders in DynamoDB, and sends events to SQS.
3. Amazon DynamoDB stores order records and processing status.
4. Amazon SQS buffers events for asynchronous processing.
5. The process_order Lambda consumes SQS events, updates order status, and publishes notifications.
6. Amazon SNS distributes order-processing notifications to subscribers.

## Technologies

- Python
- AWS Lambda
- Amazon API Gateway
- Amazon DynamoDB
- Amazon SQS
- Amazon SNS
- Boto3
- pytest

## Project Structure

    serverless-order-platform/
      lambdas/
        create_order/
          lambda_function.py
        process_order/
          lambda_function.py
      tests/
        test_create_order.py
        test_process_order.py
      .gitignore
      README.md

## Current Status

- Both Lambda handlers have been implemented.
- Nine local automated tests pass.
- AWS integration, event source mapping configuration, and end-to-end failure handling still require verification.

## Important Notes

This is a learning project and is not production-ready. Duplicate event handling, retries, failure recovery, permissions, and end-to-end AWS integration need further validation.

AWS resources may incur charges. Review AWS billing after infrastructure changes.
