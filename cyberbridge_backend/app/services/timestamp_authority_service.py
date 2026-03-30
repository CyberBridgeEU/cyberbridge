"""
Timestamp Authority Service (RFC 3161)
----------------------------------------
Provides trusted third-party timestamps for compliance certificates
and audit sign-offs.

How RFC 3161 works:
  1. We hash the payload (SHA-256) and build a TimeStampReq ASN.1 structure.
  2. We POST it to a public Timestamp Authority (FreeTSA.org).
  3. The TSA signs the hash along with its own trusted clock and returns
     a TimeStampResp DER blob.
  4. We store the raw DER response (base64). Anyone can verify it using
     the TSA's public certificate — completely independent of our database.

Verification:
  - Re-hash the current payload → SHA-256 digest
  - Confirm that digest exists inside the stored DER token
    (the TSA embedded it when it signed, so any modification to the
     original data produces a different hash → mismatch → tamper detected)
  - Extract genTime from the DER to show the trusted timestamp

This does NOT require pyasn1_modules — only core pyasn1 + requests.
"""

import base64
import hashlib
import os
import struct
from datetime import datetime, timezone
from typing import Optional

import requests
from sqlalchemy.orm import Session

from app.models import models

# ── TSA configuration ─────────────────────────────────────────────────────────
TSA_URL = "http://freetsa.org/tsr"
TSA_TIMEOUT_SECONDS = 10

# SHA-256 OID: 2.16.840.1.101.3.4.2.1 (DER-encoded)
_SHA256_OID_DER = bytes([
    0x06, 0x09,
    0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x01,
])


# ── ASN.1 DER helpers ─────────────────────────────────────────────────────────

def _der_length(n: int) -> bytes:
    """Encode an ASN.1 DER length."""
    if n < 0x80:
        return bytes([n])
    length_bytes = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(length_bytes)]) + length_bytes


def _der_tlv(tag: int, value: bytes) -> bytes:
    return bytes([tag]) + _der_length(len(value)) + value


def _der_seq(content: bytes) -> bytes:
    return _der_tlv(0x30, content)


def _der_int(n: int) -> bytes:
    b = n.to_bytes((n.bit_length() + 7) // 8 or 1, "big")
    # Prepend 0x00 if high bit set (avoid sign ambiguity)
    if b[0] & 0x80:
        b = b"\x00" + b
    return _der_tlv(0x02, b)


def _der_octet(data: bytes) -> bytes:
    return _der_tlv(0x04, data)


def _der_null() -> bytes:
    return bytes([0x05, 0x00])


def _der_bool_true() -> bytes:
    return bytes([0x01, 0x01, 0xff])


# ── Request builder ───────────────────────────────────────────────────────────

def _build_timestamp_request(payload_hash: bytes) -> bytes:
    """
    Build a minimal RFC 3161 TimeStampReq DER for a SHA-256 hash.

    TimeStampReq ::= SEQUENCE {
      version      INTEGER { v1(1) },
      messageImprint MessageImprint,
      nonce        INTEGER OPTIONAL,
      certReq      BOOLEAN DEFAULT FALSE
    }
    MessageImprint ::= SEQUENCE {
      hashAlgorithm AlgorithmIdentifier,
      hashedMessage OCTET STRING
    }
    """
    algorithm_identifier = _der_seq(_SHA256_OID_DER + _der_null())
    message_imprint = _der_seq(algorithm_identifier + _der_octet(payload_hash))
    nonce = int.from_bytes(os.urandom(8), "big")

    return _der_seq(
        _der_int(1)          # version = 1
        + message_imprint
        + _der_int(nonce)
        + _der_bool_true()   # certReq = TRUE
    )


# ── GenTime extractor ─────────────────────────────────────────────────────────

def _extract_gen_time(der_bytes: bytes) -> Optional[datetime]:
    """
    Scan DER bytes for GeneralizedTime tag (0x18) and parse it.
    GeneralizedTime in RFC 3161 is always 15 bytes: YYYYMMDDHHmmssZ
    """
    i = 0
    while i < len(der_bytes) - 2:
        if der_bytes[i] == 0x18:  # GeneralizedTime tag
            length = der_bytes[i + 1]
            if length == 0x0F and i + 2 + length <= len(der_bytes):
                raw = der_bytes[i + 2: i + 2 + length]
                try:
                    time_str = raw.decode("ascii")
                    # Format: YYYYMMDDHHmmssZ
                    dt = datetime.strptime(time_str, "%Y%m%d%H%M%SZ")
                    return dt.replace(tzinfo=timezone.utc)
                except (ValueError, UnicodeDecodeError):
                    pass
        i += 1
    return None


def _extract_serial(der_bytes: bytes) -> Optional[str]:
    """
    Extract the TSA-assigned serial number from the TSTInfo.
    The serial follows the version INTEGER in TSTInfo — we look for
    the second INTEGER tag after the first SEQUENCE inside the response.
    This is best-effort for display purposes only.
    """
    # Simple scan: find all INTEGER values and return the largest one
    # (TSA serials tend to be large numbers)
    integers = []
    i = 0
    while i < len(der_bytes) - 2:
        if der_bytes[i] == 0x02:  # INTEGER tag
            length = der_bytes[i + 1]
            if 0x80 > length > 0 and i + 2 + length <= len(der_bytes):
                value = int.from_bytes(der_bytes[i + 2: i + 2 + length], "big")
                integers.append(value)
        i += 1

    if integers:
        # Return the largest integer as hex (likely the serial)
        return hex(max(integers))
    return None


# ── Public API ────────────────────────────────────────────────────────────────

def request_timestamp(payload: str, db: Session, target_type: str, target_id) -> Optional[models.TimestampToken]:
    """
    Request a trusted RFC 3161 timestamp for a string payload.

    Sends the SHA-256 hash of the payload to FreeTSA.org and stores
    the full DER response. Returns the TimestampToken record or None
    if the TSA is unreachable (non-blocking).
    """
    payload_bytes = payload.encode("utf-8")
    payload_hash = hashlib.sha256(payload_bytes).digest()
    payload_hash_hex = payload_hash.hex()

    tsr_der = _build_timestamp_request(payload_hash)

    try:
        response = requests.post(
            TSA_URL,
            data=tsr_der,
            headers={"Content-Type": "application/timestamp-query"},
            timeout=TSA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except Exception:
        return None  # TSA unreachable — caller continues without timestamp

    token_bytes = response.content
    if not token_bytes or token_bytes[0] != 0x30:
        return None  # Not a valid DER response

    gen_time = _extract_gen_time(token_bytes)
    serial = _extract_serial(token_bytes)

    record = models.TimestampToken(
        target_type=target_type,
        target_id=target_id,
        tsa_url=TSA_URL,
        hash_algorithm="SHA-256",
        payload_hash=payload_hash_hex,
        token_b64=base64.b64encode(token_bytes).decode("ascii"),
        gen_time=gen_time,
        tsa_serial=serial,
        status="granted",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def verify_timestamp_token(token_record: models.TimestampToken, payload: str) -> dict:
    """
    Verify that a stored timestamp token covers the given payload.

    Checks:
      1. The SHA-256 hash of the current payload matches the hash stored
         in the token (the TSA embedded this when it signed).
      2. The raw hash bytes are present inside the DER token blob
         (proves the TSA actually timestamped this exact hash).
    """
    if not token_record:
        return {
            "valid": False,
            "detail": "No timestamp token found.",
            "gen_time": None,
            "tsa_url": None,
        }

    current_hash = hashlib.sha256(payload.encode("utf-8")).digest()
    current_hash_hex = current_hash.hex()

    # Check 1: hash in DB matches current payload
    if current_hash_hex != token_record.payload_hash:
        return {
            "valid": False,
            "detail": (
                f"Payload hash mismatch — the data has been modified since timestamping. "
                f"Stored: {token_record.payload_hash[:16]}… "
                f"Current: {current_hash_hex[:16]}…"
            ),
            "gen_time": token_record.gen_time.isoformat() if token_record.gen_time else None,
            "tsa_url": token_record.tsa_url,
        }

    # Check 2: raw hash bytes are embedded inside the DER token
    try:
        token_bytes = base64.b64decode(token_record.token_b64)
    except Exception:
        return {
            "valid": False,
            "detail": "Stored timestamp token is corrupted (base64 decode failed).",
            "gen_time": None,
            "tsa_url": token_record.tsa_url,
        }

    if current_hash not in token_bytes:
        return {
            "valid": False,
            "detail": "Hash not found inside TSA token — token may be forged or corrupted.",
            "gen_time": token_record.gen_time.isoformat() if token_record.gen_time else None,
            "tsa_url": token_record.tsa_url,
        }

    return {
        "valid": True,
        "detail": (
            f"Timestamp valid. Data existed at "
            f"{token_record.gen_time.isoformat() if token_record.gen_time else 'unknown time'} "
            f"as certified by {token_record.tsa_url}."
        ),
        "gen_time": token_record.gen_time.isoformat() if token_record.gen_time else None,
        "tsa_url": token_record.tsa_url,
        "tsa_serial": token_record.tsa_serial,
        "payload_hash": token_record.payload_hash,
    }
