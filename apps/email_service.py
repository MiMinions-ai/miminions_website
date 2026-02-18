import logging
import jwt
from datetime import datetime, timezone, timedelta
from flask import current_app, url_for
import resend

logger = logging.getLogger(__name__)


def _get_resend_client():
    """Configure and return the Resend API key."""
    api_key = current_app.config.get("RESEND_API_KEY")
    if not api_key:
        logger.warning("RESEND_API_KEY is not set — emails will not be sent")
        return None
    resend.api_key = api_key
    return True


def generate_verification_token(email):
    """Generate a JWT token for email verification.

    Args:
        email: The user's email address to encode.

    Returns:
        A URL-safe JWT string valid for 24 hours.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "email": email,
        "purpose": "email_verification",
        "exp": now + timedelta(hours=24),
        "iat": now,
    }
    token = jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")
    return token


def verify_token(token):
    """Decode and validate a JWT verification token.

    Args:
        token: The JWT string to decode.

    Returns:
        The email address from the token, or None if invalid/expired.
    """
    try:
        payload = jwt.decode(
            token,
            current_app.config["JWT_SECRET_KEY"],
            algorithms=["HS256"],
        )
        if payload.get("purpose") != "email_verification":
            return None
        return payload.get("email")
    except jwt.ExpiredSignatureError:
        logger.warning("Verification token expired")
        return None
    except jwt.InvalidTokenError as exc:
        logger.warning(f"Invalid verification token: {exc}")
        return None


def send_verification_email(email):
    """Send an email-verification link to a new user.

    Args:
        email: The recipient's email address.

    Returns:
        True if the email was sent (or skipped in dev), False on error.
    """
    if not _get_resend_client():
        logger.info(f"[DEV] Skipping verification email to {email}")
        return True

    token = generate_verification_token(email)
    verification_url = url_for("auth.verify_email", token=token, _external=True)

    try:
        resend.Emails.send({
            "from": current_app.config["MAIL_FROM"],
            "to": [email],
            "subject": "Verify your email — miminions.ai",
            "html": (
                f"<h2>Welcome to miminions.ai!</h2>"
                f"<p>Thanks for signing up. Please verify your email address by clicking the link below:</p>"
                f'<p><a href="{verification_url}" '
                f'style="display:inline-block;padding:12px 24px;background:#0d6efd;color:#fff;'
                f'text-decoration:none;border-radius:6px;">Verify Email</a></p>'
                f"<p>This link will expire in 24 hours.</p>"
                f"<p>If you didn't create an account, you can safely ignore this email.</p>"
                f"<br><p>— The miminions.ai Team</p>"
            ),
        })
        logger.info(f"Verification email sent to {email}")
        return True
    except Exception as exc:
        logger.error(f"Failed to send verification email to {email}: {exc}")
        return False


def send_contact_email(name, email, phone, message):
    """Forward a contact-form submission to the team inbox.

    Args:
        name: Sender's full name.
        email: Sender's email address.
        phone: Sender's phone number (may be empty).
        message: The message body.

    Returns:
        True if the email was sent (or skipped in dev), False on error.
    """
    if not _get_resend_client():
        logger.info(f"[DEV] Skipping contact email from {email}")
        return True

    try:
        resend.Emails.send({
            "from": current_app.config["MAIL_FROM"],
            "to": [current_app.config["CONTACT_EMAIL"]],
            "reply_to": email,
            "subject": f"Contact Form — {name}",
            "html": (
                f"<h2>New Contact Form Submission</h2>"
                f"<p><strong>Name:</strong> {name}</p>"
                f"<p><strong>Email:</strong> {email}</p>"
                f"<p><strong>Phone:</strong> {phone or 'N/A'}</p>"
                f"<hr>"
                f"<p>{message}</p>"
            ),
        })
        logger.info(f"Contact email forwarded from {email}")
        return True
    except Exception as exc:
        logger.error(f"Failed to send contact email from {email}: {exc}")
        return False
