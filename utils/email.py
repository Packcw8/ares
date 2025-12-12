import os
import requests

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
FROM_EMAIL = os.getenv("FROM_EMAIL", "onboarding@resend.dev")

def send_verification_email(to_email: str, token: str):
    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY is not set")

    verify_link = f"{FRONTEND_URL}/verify-email?email={to_email}&token={token}"

    payload = {
        "from": FROM_EMAIL,
        "to": [to_email],
        "subject": "Verify your email for ARES",
        "html": f"""
        <div style="font-family:Arial,sans-serif;line-height:1.5">
          <h2>Verify your email</h2>
          <p>Click the button below to verify your email for ARES.</p>
          <p><a href="{verify_link}" style="display:inline-block;padding:10px 16px;background:#1c2b4a;color:white;text-decoration:none;border-radius:6px;">Verify Email</a></p>
          <p>If the button doesn’t work, paste this link into your browser:</p>
          <p>{verify_link}</p>
        </div>
        """
    }

    r = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )
    r.raise_for_status()
    return r.json()
