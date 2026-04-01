import logging
import os
import sys
import json
import time
from botocore.exceptions import ClientError, BotoCoreError

import boto3
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class MockTable:
    def __init__(self, table_name):
        self.table_name = table_name
        self.file_path = f"{table_name}_local_db.json"
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump({}, f)

    def _read_db(self):
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _write_db(self, data):
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _client_error(self, code, message):
        raise ClientError(
            {
                'Error': {
                    'Code': code,
                    'Message': message,
                }
            },
            'MockDynamoDBOperation'
        )

    def _extract_email_key(self, key_dict):
        if not isinstance(key_dict, dict) or 'email' not in key_dict:
            self._client_error('ValidationException', "Mock table requires Key with 'email'")
        email = key_dict.get('email')
        if not email:
            self._client_error('ValidationException', "Partition key 'email' must be non-empty")
        return str(email)

    def get_item(self, Key):
        db_data = self._read_db()
        key_val = self._extract_email_key(Key)
        item = db_data.get(key_val)
        if item:
            return {'Item': item}
        return {}

    def put_item(self, Item, ConditionExpression=None):
        db_data = self._read_db()
        key_val = Item.get('email')
        if not key_val:
            self._client_error('ValidationException', "Item must include 'email' partition key")

        key_val = str(key_val)
        if ConditionExpression == "attribute_not_exists(email)" and key_val in db_data:
            self._client_error('ConditionalCheckFailedException', 'The conditional request failed')

        db_data[key_val] = Item
        self._write_db(db_data)
        return {'ResponseMetadata': {'HTTPStatusCode': 200}}

    def update_item(
        self,
        Key,
        UpdateExpression,
        ExpressionAttributeNames=None,
        ExpressionAttributeValues=None,
        ConditionExpression=None,
        ReturnValues=None,
    ):
        db_data = self._read_db()
        key_val = self._extract_email_key(Key)

        if ConditionExpression == "attribute_exists(email)" and key_val not in db_data:
            self._client_error('ConditionalCheckFailedException', 'The conditional request failed')

        current = db_data.get(key_val)
        if not current:
            self._client_error('ResourceNotFoundException', 'Item not found')

        if not UpdateExpression or not UpdateExpression.startswith("SET "):
            self._client_error('ValidationException', 'Only SET UpdateExpression is supported in mock')

        expression_names = ExpressionAttributeNames or {}
        expression_values = ExpressionAttributeValues or {}

        assignments = UpdateExpression[4:].split(',')
        for assignment in assignments:
            left, right = assignment.strip().split('=', 1)
            left = left.strip()
            right = right.strip()

            attr_name = expression_names.get(left, left.lstrip('#'))
            if right not in expression_values:
                self._client_error('ValidationException', f'Missing value for token: {right}')
            current[attr_name] = expression_values[right]

        db_data[key_val] = current
        self._write_db(db_data)

        response = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        if ReturnValues == "ALL_NEW":
            response['Attributes'] = current
        return response


class FakeDynamoDB:
    def __init__(self):
        pass

    def Table(self, name):
        return MockTable(name)


def retry_dynamodb_operation(func, max_retries=3, base_delay=0.1):
    """Retry DynamoDB operations with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            # Don't retry on user errors
            if error_code in ['ValidationException', 'ResourceNotFoundException']:
                raise
            
            # Retry on throttling and server errors
            if error_code in ['ProvisionedThroughputExceededException', 'InternalServerError', 'ServiceUnavailable']:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"DynamoDB operation failed ({error_code}), retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
            raise
        except BotoCoreError as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(f"DynamoDB network error, retrying in {delay}s (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(delay)
                continue
            raise
    
    return None


def _connect_dynamodb():
    """Establish connection to DynamoDB."""
    # Check environment - use local DB if not in production
    if os.getenv("FLASK_ENV") != "production":
        logger.info("Using FakeDynamoDB for local/development mode (FLASK_ENV != production)")
        return FakeDynamoDB()
    
    # Check if running in test/local mode via command-line flags
    use_mock = any(arg in sys.argv for arg in ["--test", "--local"])
    
    if use_mock:
        logger.info("Using FakeDynamoDB for local/test mode")
        return FakeDynamoDB()
    
    region = os.getenv("AWS_REGION", "us-east-2")

    # boto3 is lazy — the actual connection is made on the first operation.
    # Do NOT fall back to FakeDynamoDB here: a silent fallback in production
    # would write data to the instance's ephemeral disk and lose it silently.
    logger.info(f"Using AWS DynamoDB in region {region}")
    return boto3.resource("dynamodb", region_name=region)

db = _connect_dynamodb()