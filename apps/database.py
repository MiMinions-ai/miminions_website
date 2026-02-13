import logging
import os

import boto3
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def _connect_dynamodb():
    """Create a DynamoDB resource connection.

    Uses IAM role credentials automatically on AWS (EB/EC2).
    Falls back to environment variables for local development.
    """
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