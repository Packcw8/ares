import os
import requests

# ======================================================
# Environment variables
# ======================================================

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
FROM_EMAIL = os.getenv("FROM_EMAIL", "no-reply@aresjustice.com")

RESEND_API_URL = "https://api.resend.com/emails"


def send_verification_email(to_email: str, token: str):
    """
    Sends a Constitution-themed email verification message via Resend.

    Includes both HTML and plain-text versions to improve
    deliverability and reduce spam/phishing warnings.
    """

    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY is not set")

    verify_link = f"{FRONTEND_URL}/verify-email?email={to_email}&token={token}"

    payload = {
        "from": FROM_EMAIL,
        "to": [to_email],

        # Subject: serious, non-phishy
        "subject": "Confirm your ARES account — Email Verification",

        # --------------------------------------------------
        # Plain-text version (VERY important for trust)
        # --------------------------------------------------
        "text": (
            "ARES — Email Verification\n\n"
            "“We the People” depend on trusted identity to preserve the integrity "
            "of the public record.\n\n"
            "To confirm your email address for your ARES account, open the link below:\n\n"
            f"{verify_link}\n\n"
            "If you did not create an ARES account, you may safely ignore this email.\n"
            "This verification link expires automatically for your security."
        ),

        # --------------------------------------------------
        # HTML version (Constitution-themed but professional)
        # --------------------------------------------------
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

            <p style="margin: 0 0 18px;">
              <em>“We the People…”</em> — ARES verifies email addresses to help protect
              the integrity of the public accountability record.
            </p>

            <p style="margin: 0 0 18px;">
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

            <p style="margin: 0 0 6px; color: #333;">
              If the button does not work, copy and paste this link into your browser:
            </p>

            <p style="
              margin: 0 0 20px;
              word-break: break-all;
              font-family: Arial, sans-serif;
              font-size: 14px;
            ">
              {verify_link}
            </p>

            <hr style="
              margin: 26px 0;
              border: 0;
              border-top: 1px solid #eee;
            " />

            <p style="
              margin: 0;
              font-size: 13px;
              color: #555;
              font-family: Arial, sans-serif;
            ">
              This email was sent because an account was created at
              <strong>aresjustice.com</strong>.
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
