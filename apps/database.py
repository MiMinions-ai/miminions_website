import logging
import os
import sys
import json
from types import SimpleNamespace

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


class MockDynamoDB:
    def __init__(self):
        pass

    def Table(self, name):
        return MockTable(name)


def _connect_dynamodb():
    """Establish connection to DynamoDB."""
    # Check for local testing flags
    if any(arg in sys.argv for arg in ["--local", "--test", "--deploy"]):
        logger.info("Using Local JSON Mock Database due to command line flag")
        return MockDynamoDB()

    region = os.getenv("AWS_REGION", "us-east-2")
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

    kwargs = {"region_name": region}
    if access_key and secret_key:
        kwargs["aws_access_key_id"] = access_key
        kwargs["aws_secret_access_key"] = secret_key

    try:
        resource = boto3.resource("dynamodb", **kwargs)
        # Verify connectivity by listing tables (lightweight call)
        list(resource.tables.limit(1))
        logger.info("DynamoDB connection established (region=%s)", region)
        return resource
    except Exception as exc:
        logger.error("Failed to connect to DynamoDB: %s", exc)
        raise RuntimeError(f"DynamoDB connection failed: {exc}") from exc


db = _connect_dynamodb()