import logging
import os
import sys
import json

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

    def get_item(self, Key):
        db_data = self._read_db()
        # Assume single key for simple mock
        key_val = next(iter(Key.values()))
        item = db_data.get(str(key_val))
        if item:
            return {'Item': item}
        return {}

    def put_item(self, Item):
        db_data = self._read_db()
        # Find the primary key - we assume 'email' for users based on usage
        key_val = Item.get('email') or Item.get('id')
        if key_val:
            db_data[str(key_val)] = Item
            self._write_db(db_data)
        return {'ResponseMetadata': {'HTTPStatusCode': 200}}


class FakeDynamoDB:
    def __init__(self):
        pass

    def Table(self, name):
        return MockTable(name)


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