#!/usr/bin/env python3
"""CLI command to test email configuration.

Usage:
    python -m ralph.test_email
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.email_service import send_test_email, is_configured, EmailServiceError
from config import settings


def main():
    """Test email configuration by sending a test email."""
    print("Ralph Email Test")
    print("=" * 40)

    # Check configuration
    print(f"Provider: {settings.email_provider or 'Not set'}")
    print(f"From: {settings.email_from or 'Not set'}")
    print(f"To: {settings.email_to or 'Not set'}")
    print(f"API Key: {'Set' if settings.resend_api_key else 'Not set'}")
    print()

    if not is_configured():
        print("ERROR: Email service is not configured.")
        print("Please set the following environment variables:")
        print("  - EMAIL_PROVIDER=resend")
        print("  - RESEND_API_KEY=re_xxxxxxxxxx")
        print("  - EMAIL_FROM=sender@example.com")
        print("  - EMAIL_TO=recipient@example.com")
        sys.exit(1)

    print("Sending test email...")
    try:
        email_id = send_test_email()
        print(f"SUCCESS! Email sent with ID: {email_id}")
        print(f"Check your inbox at: {settings.email_to}")
        sys.exit(0)
    except EmailServiceError as e:
        print(f"FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
