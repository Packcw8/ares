import os
import requests

# ======================================================
# Environment variables
# ======================================================

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
FROM_EMAIL = os.getenv("FROM_EMAIL", "support@aresjustice.com")

RESEND_API_URL = "https://api.resend.com/emails"


# ======================================================
# Email Verification
# ======================================================

def send_verification_email(to_email: str, token: str):
    """
    Sends a Constitution-themed email verification message via Resend.
    Includes both HTML and plain-text versions to improve deliverability.
    """

    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY is not set")

    verify_link = f"{FRONTEND_URL}/verify-email?email={to_email}&token={token}"

    payload = {
        "from": FROM_EMAIL,
        "to": [to_email],
        "subject": "Confirm your ARES account — Email Verification",

        # Plain-text version
        "text": (
            "ARES — Email Verification\n\n"
            "“We the People” depend on trusted identity to preserve the integrity "
            "of the public record.\n\n"
            "To confirm your email address for your ARES account, open the link below:\n\n"
            f"{verify_link}\n\n"
            "If you did not create an ARES account, you may safely ignore this email.\n"
            "This verification link expires automatically for your security."
        ),

        # HTML version
        "html": f"""
        <div style="font-family: Georgia, 'Times New Roman', serif; line-height: 1.7; color: #111;">
          <div style="
            max-width: 640px;
            margin: 0 auto;
            padding: 28px;
            border: 1px solid #e5e5e5;
            border-radius: 10px;
            background-color: #ffffff;
          ">

            <p style="
              margin: 0;
              font-size: 12px;
              letter-spacing: 0.08em;
              text-transform: uppercase;
              color: #555;
            ">
              ARES • Identity Confirmation
            </p>

            <h2 style="
              margin: 12px 0 10px;
              color: #0A2A42;
              font-weight: 700;
            ">
              Confirm your email
            </h2>

            <p>
              <em>“We the People…”</em> — ARES verifies email addresses to help protect
              the integrity of the public accountability record.
            </p>

            <p>
              To confirm this email address for your
              <strong>aresjustice.com</strong> account, click the button below:
            </p>

            <p style="margin: 24px 0;">
              <a href="{verify_link}"
                 style="
                   display: inline-block;
                   padding: 12px 20px;
                   background: #0A2A42;
                   color: #ffffff;
                   text-decoration: none;
                   border-radius: 6px;
                   font-weight: 700;
                   font-family: Arial, sans-serif;
                 ">
                Confirm Email
              </a>
            </p>

            <p>If the button does not work, copy and paste this link:</p>

            <p style="word-break: break-all; font-family: Arial, sans-serif;">
              {verify_link}
            </p>

            <hr style="margin: 26px 0; border-top: 1px solid #eee;" />

            <p style="font-size: 13px; color: #555; font-family: Arial, sans-serif;">
              If you did not request this, you may safely ignore this message.
            </p>

          </div>
        </div>
        """
    }

    response = requests.post(
        RESEND_API_URL,
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )

    response.raise_for_status()
    return response.json()


# ======================================================
# Password Reset
# ======================================================

def send_password_reset_email(to_email: str, token: str):
    """
    Sends a secure password reset email.
    Token is NEVER stored in plaintext — only sent to the user.
    """

    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY is not set")

    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"

    payload = {
        "from": FROM_EMAIL,
        "to": [to_email],
        "subject": "ARES Password Reset Request",

        # Plain-text version
        "text": (
            "ARES — Password Reset\n\n"
            "A request was made to reset the password for your ARES account.\n\n"
            "Use the link below to set a new password:\n\n"
            f"{reset_link}\n\n"
            "This link expires in 30 minutes.\n\n"
            "If you did not request this reset, you may safely ignore this email."
        ),

        # HTML version
        "html": f"""
        <div style="font-family: Georgia, 'Times New Roman', serif; line-height: 1.7; color: #111;">
          <div style="
            max-width: 640px;
            margin: 0 auto;
            padding: 28px;
            border: 1px solid #e5e5e5;
            border-radius: 10px;
            background-color: #ffffff;
          ">

            <p style="
              margin: 0;
              font-size: 12px;
              letter-spacing: 0.08em;
              text-transform: uppercase;
              color: #555;
            ">
              ARES • Account Security
            </p>

            <h2 style="color: #0A2A42;">
              Password Reset Requested
            </h2>

            <p>
              A request was made to reset the password for your
              <strong>aresjustice.com</strong> account.
            </p>

            <p>
              Click the button below to choose a new password.
              This link expires in <strong>30 minutes</strong>.
            </p>

            <p style="margin: 24px 0;">
              <a href="{reset_link}"
                 style="
                   display: inline-block;
                   padding: 12px 20px;
                   background: #8B1E1E;
                   color: #ffffff;
                   text-decoration: none;
                   border-radius: 6px;
                   font-weight: 700;
                   font-family: Arial, sans-serif;
                 ">
                Reset Password
              </a>
            </p>

            <p>If the button does not work, copy and paste this link:</p>

            <p style="word-break: break-all; font-family: Arial, sans-serif;">
              {reset_link}
            </p>

            <hr style="margin: 26px 0; border-top: 1px solid #eee;" />

            <p style="font-size: 13px; color: #555; font-family: Arial, sans-serif;">
              If you did not request a password reset, no action is required.
            </p>

          </div>
        </div>
        """
    }

    response = requests.post(
        RESEND_API_URL,
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )

    response.raise_for_status()
    return response.json()
# --------------------------------------------------
# 📧 ENTITY APPROVAL EMAIL
# --------------------------------------------------

# --------------------------------------------------
# 📧 ENTITY APPROVAL EMAIL
# --------------------------------------------------

def send_entity_approved_email(to_email: str, entity_name: str):
    """
    Sends an email notifying the user that their submitted entity was approved.
    """

    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY is not set")

    payload = {
        "from": FROM_EMAIL,
        "to": [to_email],
        "subject": "Your entity has been approved on ARES",

        # Plain-text version
        "text": (
            "ARES — Entity Approved\n\n"
            f"Your submitted entity '{entity_name}' has been reviewed and approved.\n\n"
            "It is now publicly visible on aresjustice.com and open for community accountability.\n\n"
            "Thank you for contributing to transparency.\n\n"
            "— ARES Team"
        ),

        # HTML version
        "html": f"""
        <div style="font-family: Georgia, 'Times New Roman', serif; line-height: 1.7; color: #111;">
          <div style="
            max-width: 640px;
            margin: 0 auto;
            padding: 28px;
            border: 1px solid #e5e5e5;
            border-radius: 10px;
            background-color: #ffffff;
          ">

            <p style="
              margin: 0;
              font-size: 12px;
              letter-spacing: 0.08em;
              text-transform: uppercase;
              color: #555;
            ">
              ARES • Entity Review
            </p>

            <h2 style="color: #0A2A42;">
              Entity Approved
            </h2>

            <p>
              Your submitted entity
              <strong>{entity_name}</strong>
              has been reviewed and approved by an administrator.
            </p>

            <p>
              It is now publicly visible on
              <strong>aresjustice.com</strong>
              and open for community accountability.
            </p>

            <hr style="margin: 26px 0; border-top: 1px solid #eee;" />

            <p style="font-size: 13px; color: #555;">
              Thank you for helping build a transparent public record.
            </p>

          </div>
        </div>
        """
    }

    response = requests.post(
        RESEND_API_URL,
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )

    response.raise_for_status()
    return response.json()
