import logging
from botocore.exceptions import ClientError

from apps.database import db, retry_dynamodb_operation
from apps.utils import normalize_email, validate_email

logger = logging.getLogger(__name__)
users_table = db.Table("users")


def get_user(email):
    """Retrieve a user record by email.

    Args:
        email: The user's email address (partition key).

    Returns:
        A dict with user attributes, or None if not found.
    """
    normalized_email = normalize_email(email)
    if not normalized_email or not validate_email(normalized_email):
        logger.warning(f"Invalid email format for user lookup: {email}")
        return None

    try:
        def _get_operation():
            return users_table.get_item(Key={"email": normalized_email})
        
        response = retry_dynamodb_operation(_get_operation)
        item = response.get("Item") if response else None
        
        if item:
            logger.debug(f"User found: {normalized_email}")
        else:
            logger.debug(f"User not found: {normalized_email}")
        
        return item
        
    except ClientError as e:
        logger.error(f"DynamoDB error getting user {normalized_email}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting user {normalized_email}: {e}")
        return None


def add_user(data):
    """Create a new user record in DynamoDB.

    Args:
        data: A namespace/object with id, email, and password attributes.
        
    Returns:
        True if successful, False otherwise.
    """
    normalized_email = normalize_email(getattr(data, "email", ""))
    
    # Validate required fields
    if not normalized_email or not validate_email(normalized_email):
        logger.warning(f"Invalid email for new user: {getattr(data, 'email', '')}")
        return False
    
    if not getattr(data, "password", None):
        logger.warning("Missing password for new user")
        return False
        
    if not getattr(data, "id", None):
        logger.warning("Missing user ID for new user")
        return False
    
    # Check if user already exists
    existing_user = get_user(normalized_email) 
    if existing_user:
        logger.warning(f"User already exists: {normalized_email}")
        return False
    
    try:
        def _put_operation():
            return users_table.put_item(
                Item={
                    "id": data.id,
                    "email": normalized_email,
                    "password": data.password,
                    "first_name": getattr(data, "first_name", ""),
                    "last_name": getattr(data, "last_name", ""),
                    "date_of_birth": getattr(data, "date_of_birth", ""),
                    "phone": getattr(data, "phone", ""),
                    "user_type": "user",
                    "is_active": True,
                    "email_verified": False,
                }
            )
        
        response = retry_dynamodb_operation(_put_operation)
        
        if response and response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200:
            logger.info(f"User created successfully: {normalized_email}")
            return True
        else:
            logger.error(f"Failed to create user: {normalized_email}")
            return False
            
    except ClientError as e:
        logger.error(f"DynamoDB error creating user {normalized_email}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error creating user {normalized_email}: {e}")
        return False


def update_user(email, updates):
    """Update fields on an existing user record.

    Args:
        email: The user's email address (partition key).
        updates: A dict of field names to new values.
        
    Returns:
        Updated user dict if successful, None otherwise.
    """
    normalized_email = normalize_email(email)
    if not normalized_email or not validate_email(normalized_email):
        logger.warning(f"Invalid email for user update: {email}")
        return None

    if not updates:
        logger.warning("No updates provided")
        return None

    try:
        # Get current user first
        user = get_user(normalized_email)
        if not user:
            logger.warning(f"User not found for update: {normalized_email}")
            return None

        # Prepare safe updates
        safe_updates = dict(updates)
        if "email" in safe_updates:
            new_email = normalize_email(safe_updates["email"])
            if not validate_email(new_email):
                logger.warning(f"Invalid new email format: {safe_updates['email']}")
                return None
            safe_updates["email"] = new_email

        # Apply updates
        user.update(safe_updates)
        user["email"] = normalize_email(user.get("email", normalized_email))
        
        def _put_operation():
            return users_table.put_item(Item=user)
        
        response = retry_dynamodb_operation(_put_operation)
        
        if response and response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200:
            logger.info(f"User updated successfully: {normalized_email}")
            return user
        else:
            logger.error(f"Failed to update user: {normalized_email}")
            return None
            
    except ClientError as e:
        logger.error(f"DynamoDB error updating user {normalized_email}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error updating user {normalized_email}: {e}")
        return None
