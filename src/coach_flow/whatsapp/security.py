"""Security and HMAC signature verification for Meta WhatsApp Cloud API Webhooks."""

import hashlib
import hmac
import logging

logger = logging.getLogger(__name__)


def verify_webhook_signature(
    payload_bytes: bytes,
    signature_header: str,
    app_secret: str,
) -> bool:
    """
    Validate that incoming Meta WhatsApp Cloud API webhook request was signed
    with our META_WA_APP_SECRET using HMAC-SHA256.

    Header format: 'sha256=<hex_digest>'
    """
    if not signature_header or not app_secret:
        return False

    if not signature_header.startswith("sha256="):
        return False

    expected_signature = signature_header.split("sha256=")[-1]
    mac = hmac.new(app_secret.encode("utf-8"), msg=payload_bytes, digestmod=hashlib.sha256)
    computed_signature = mac.hexdigest()

    return hmac.compare_digest(expected_signature, computed_signature)
