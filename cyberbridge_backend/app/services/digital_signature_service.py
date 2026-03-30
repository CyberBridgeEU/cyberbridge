"""
Digital Signature Service
--------------------------
Provides RSA-2048 signing and verification for compliance certificates
and audit sign-offs.

Design:
  - One RSA-2048 key pair per organisation, generated on first use.
  - Private key is stored encrypted in the DB using Fernet (AES-128 + HMAC),
    derived from the org's UUID — the same pattern already used in backup_service.
  - Public key is stored as plain PEM (anyone can verify).
  - Signatures are PKCS#1v15 with SHA-256 and stored as hex strings.

What this gives you:
  - Authentication  — only the private key holder could have produced this signature
  - Integrity       — any change to the signed data invalidates the signature
  - Non-repudiation — the org cannot deny signing (private key is uniquely theirs)
"""

import hashlib
import base64
import os
from typing import Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy.orm import Session

from app.models import models


# ── Key derivation ────────────────────────────────────────────────────────────
# Salt read from environment — fall back to a default only in development.
# In production set SIGNING_KDF_SALT to a long random string.
_KDF_SALT = os.environ.get("SIGNING_KDF_SALT", "cyberbridge_signing_salt_2026").encode()
_KDF_ITERATIONS = 480_000


def _derive_fernet_key(org_id) -> bytes:
    """Derive a Fernet key from the org's UUID for private-key encryption."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_KDF_SALT,
        iterations=_KDF_ITERATIONS,
        backend=default_backend(),
    )
    return base64.urlsafe_b64encode(kdf.derive(str(org_id).encode()))


def _encrypt_private_key(private_pem: bytes, org_id) -> str:
    """Encrypt a PEM private key bytes with a Fernet key derived from org_id."""
    f = Fernet(_derive_fernet_key(org_id))
    return f.encrypt(private_pem).decode()


def _decrypt_private_key(encrypted: str, org_id) -> bytes:
    """Decrypt the stored private key PEM."""
    f = Fernet(_derive_fernet_key(org_id))
    return f.decrypt(encrypted.encode())


# ── Key pair management ───────────────────────────────────────────────────────

def get_or_create_org_key(db: Session, org_id) -> models.OrgSigningKey:
    """
    Return the org's signing key record, generating a fresh RSA-2048 pair
    if one does not yet exist.
    """
    key_record = db.query(models.OrgSigningKey).filter(
        models.OrgSigningKey.organisation_id == org_id,
        models.OrgSigningKey.revoked == False,
    ).first()

    if key_record:
        return key_record

    # Generate new RSA-2048 key pair
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    encrypted_private = _encrypt_private_key(private_pem, org_id)

    key_record = models.OrgSigningKey(
        organisation_id=org_id,
        public_key_pem=public_pem,
        encrypted_private_key=encrypted_private,
        algorithm="RSA-2048-PKCS1v15-SHA256",
        revoked=False,
    )
    db.add(key_record)
    db.commit()
    db.refresh(key_record)
    return key_record


def get_public_key_pem(db: Session, org_id) -> Optional[str]:
    """Return the organisation's current public key in PEM format."""
    record = db.query(models.OrgSigningKey).filter(
        models.OrgSigningKey.organisation_id == org_id,
        models.OrgSigningKey.revoked == False,
    ).first()
    return record.public_key_pem if record else None


# ── Sign / Verify ─────────────────────────────────────────────────────────────

def sign_payload(payload: str, org_id, db: Session) -> tuple[str, str]:
    """
    Sign a canonical string payload using the org's RSA private key.

    Returns:
        (signature_hex, signing_key_id_str)
    """
    key_record = get_or_create_org_key(db, org_id)
    private_pem = _decrypt_private_key(key_record.encrypted_private_key, org_id)

    private_key = serialization.load_pem_private_key(
        private_pem, password=None, backend=default_backend()
    )

    signature_bytes = private_key.sign(
        payload.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )

    return signature_bytes.hex(), str(key_record.id)


def verify_signature(payload: str, signature_hex: str, org_id, db: Session) -> dict:
    """
    Verify a hex-encoded RSA signature against a canonical payload.

    Returns a dict with:
        valid (bool), algorithm (str), key_id (str), detail (str)
    """
    key_record = db.query(models.OrgSigningKey).filter(
        models.OrgSigningKey.organisation_id == org_id,
        models.OrgSigningKey.revoked == False,
    ).first()

    if not key_record:
        return {
            "valid": False,
            "algorithm": None,
            "key_id": None,
            "detail": "No active signing key found for this organisation.",
        }

    try:
        public_key = serialization.load_pem_public_key(
            key_record.public_key_pem.encode(), backend=default_backend()
        )
        signature_bytes = bytes.fromhex(signature_hex)

        public_key.verify(
            signature_bytes,
            payload.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )

        return {
            "valid": True,
            "algorithm": key_record.algorithm,
            "key_id": str(key_record.id),
            "detail": "Signature is valid. Document has not been tampered with.",
        }
    except Exception as exc:
        return {
            "valid": False,
            "algorithm": key_record.algorithm if key_record else None,
            "key_id": str(key_record.id) if key_record else None,
            "detail": f"Signature verification failed: {str(exc)}",
        }


# ── Canonical payload builders ────────────────────────────────────────────────

def certificate_payload(cert: models.ComplianceCertificate) -> str:
    """
    Build the canonical string that is signed for a certificate.
    Covers every field that makes a certificate meaningful.
    """
    parts = [
        str(cert.certificate_number),
        str(cert.framework_id),
        str(cert.organisation_id),
        str(cert.issued_by_user_id),
        f"{cert.overall_score:.4f}",
        cert.issued_at.isoformat(),
        cert.expires_at.isoformat(),
        cert.verification_hash,
    ]
    return "|".join(parts)


def sign_off_payload(sign_off: models.AuditSignOff) -> str:
    """
    Build the canonical string that is signed for an audit sign-off.
    """
    parts = [
        str(sign_off.id),
        str(sign_off.engagement_id),
        str(sign_off.signer_auditor_id),
        sign_off.sign_off_type,
        str(sign_off.target_id) if sign_off.target_id else "",
        sign_off.status,
        sign_off.comments or "",
        sign_off.signed_at.isoformat(),
        sign_off.ip_address or "",
    ]
    return "|".join(parts)
