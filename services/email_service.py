"""Email notification service using Resend."""

from typing import Optional
import resend

from config import settings


class EmailServiceError(Exception):
    """Raised when email sending fails."""
    pass


def is_configured() -> bool:
    """Check if email service is properly configured."""
    return (
        settings.email_provider == "resend"
        and settings.resend_api_key is not None
        and settings.email_from is not None
        and settings.email_to is not None
    )


def send_email(
    subject: str,
    body: str,
    to: Optional[str] = None,
    html: Optional[str] = None,
) -> str:
    """
    Send an email using Resend.

    Args:
        subject: Email subject line
        body: Plain text email body
        to: Recipient email (defaults to EMAIL_TO from settings)
        html: Optional HTML body (if provided, used instead of plain text)

    Returns:
        Email ID from Resend

    Raises:
        EmailServiceError: If email service is not configured or send fails
    """
    if not is_configured():
        raise EmailServiceError(
            "Email service not configured. Set EMAIL_PROVIDER=resend, "
            "RESEND_API_KEY, EMAIL_FROM, and EMAIL_TO in environment."
        )

    resend.api_key = settings.resend_api_key
    recipient = to or settings.email_to

    try:
        params = {
            "from": settings.email_from,
            "to": [recipient],
            "subject": subject,
            "text": body,
        }
        if html:
            params["html"] = html

        response = resend.Emails.send(params)
        return response.get("id", "unknown")

    except Exception as e:
        raise EmailServiceError(f"Failed to send email: {e}") from e


def send_test_email() -> str:
    """
    Send a test email to verify configuration.

    Returns:
        Email ID from Resend

    Raises:
        EmailServiceError: If send fails
    """
    subject = "[Ralph] Test Email - Configuration Verified"
    body = """This is a test email from Ralph Blog Content Generator.

If you received this, your email configuration is working correctly.

Configuration:
- Provider: Resend
- From: {from_addr}
- To: {to_addr}

-- Ralph
""".format(from_addr=settings.email_from, to_addr=settings.email_to)

    return send_email(subject, body)


def send_alert(
    alert_type: str,
    title: str,
    details: str,
    blog_post_id: Optional[str] = None,
) -> str:
    """
    Send an alert email for Ralph events.

    Args:
        alert_type: One of "ERROR", "FAILED", "SKIPPED"
        title: Brief description of the alert
        details: Full details of the event
        blog_post_id: Optional blog post ID for context

    Returns:
        Email ID from Resend

    Raises:
        EmailServiceError: If send fails
    """
    subject = f"[{alert_type}] Ralph: {title}"

    body = f"""Ralph Blog Content Generator Alert

Type: {alert_type}
Title: {title}

Details:
{details}
"""
    if blog_post_id:
        body += f"\nBlog Post ID: {blog_post_id}"

    body += "\n\n-- Ralph"

    return send_email(subject, body)
