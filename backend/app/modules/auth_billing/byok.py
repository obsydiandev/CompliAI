"""BYOK (Bring Your Own Key) encryption helpers (Phase 2, T18.2).

Supports envelope encryption via:
  - AWS KMS
  - Azure Key Vault
  - GCP Cloud KMS (Cloud Key Management Service)

For each organisation with BYOK configured:
  1. A Data Encryption Key (DEK) is generated per encrypt operation.
  2. The DEK is encrypted by the customer-managed Key Encryption Key (KEK) in their KMS.
  3. The encrypted DEK (eDEK) is stored alongside the ciphertext.
  4. On decryption, the eDEK is sent to the KMS to recover the DEK.

This means CompliAI never holds the plaintext DEK — the customer's KMS key is the root of trust.
"""

from __future__ import annotations

import base64
import logging
import os

logger = logging.getLogger(__name__)

# ── AWS KMS ────────────────────────────────────────────────────────────────────


def _aws_encrypt_dek(key_arn: str, plaintext_dek: bytes) -> bytes:
    import boto3

    kms = boto3.client("kms")
    resp = kms.encrypt(KeyId=key_arn, Plaintext=plaintext_dek)
    return resp["CiphertextBlob"]


def _aws_decrypt_dek(key_arn: str, encrypted_dek: bytes) -> bytes:
    import boto3

    kms = boto3.client("kms")
    resp = kms.decrypt(KeyId=key_arn, CiphertextBlob=encrypted_dek)
    return resp["Plaintext"]


# ── Azure Key Vault ────────────────────────────────────────────────────────────


def _azure_encrypt_dek(key_id: str, plaintext_dek: bytes) -> bytes:
    from azure.keyvault.keys.crypto import CryptographyClient, EncryptionAlgorithm  # type: ignore
    from azure.identity import DefaultAzureCredential  # type: ignore

    credential = DefaultAzureCredential()
    client = CryptographyClient(key_id, credential=credential)
    result = client.encrypt(EncryptionAlgorithm.rsa_oaep, plaintext_dek)
    return result.ciphertext


def _azure_decrypt_dek(key_id: str, encrypted_dek: bytes) -> bytes:
    from azure.keyvault.keys.crypto import CryptographyClient, EncryptionAlgorithm  # type: ignore
    from azure.identity import DefaultAzureCredential  # type: ignore

    credential = DefaultAzureCredential()
    client = CryptographyClient(key_id, credential=credential)
    result = client.decrypt(EncryptionAlgorithm.rsa_oaep, encrypted_dek)
    return result.plaintext


# ── GCP KMS ────────────────────────────────────────────────────────────────────


def _gcp_encrypt_dek(key_name: str, plaintext_dek: bytes) -> bytes:
    from google.cloud import kms as google_kms  # type: ignore

    client = google_kms.KeyManagementServiceClient()
    resp = client.encrypt(request={"name": key_name, "plaintext": plaintext_dek})
    return resp.ciphertext


def _gcp_decrypt_dek(key_name: str, encrypted_dek: bytes) -> bytes:
    from google.cloud import kms as google_kms  # type: ignore

    client = google_kms.KeyManagementServiceClient()
    resp = client.decrypt(request={"name": key_name, "ciphertext": encrypted_dek})
    return resp.plaintext


# ── Generic envelope encrypt / decrypt ────────────────────────────────────────


def encrypt_field(provider: str, key_arn: str, plaintext: str) -> str:
    """Encrypt a plaintext string using envelope encryption.

    Returns a base64-encoded payload: <b64(encrypted_dek)>:<b64(iv)>:<b64(ciphertext)>
    """
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    plaintext_dek = os.urandom(32)  # 256-bit DEK
    iv = os.urandom(12)  # 96-bit IV for AES-GCM

    aesgcm = AESGCM(plaintext_dek)
    ciphertext = aesgcm.encrypt(iv, plaintext.encode(), None)

    if provider == "aws":
        encrypted_dek = _aws_encrypt_dek(key_arn, plaintext_dek)
    elif provider == "azure":
        encrypted_dek = _azure_encrypt_dek(key_arn, plaintext_dek)
    elif provider == "gcp":
        encrypted_dek = _gcp_encrypt_dek(key_arn, plaintext_dek)
    else:
        raise ValueError(f"Unknown KMS provider: {provider}")

    return (
        base64.b64encode(encrypted_dek).decode()
        + ":"
        + base64.b64encode(iv).decode()
        + ":"
        + base64.b64encode(ciphertext).decode()
    )


def decrypt_field(provider: str, key_arn: str, encrypted_payload: str) -> str:
    """Decrypt a payload produced by encrypt_field."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    parts = encrypted_payload.split(":")
    if len(parts) != 3:
        raise ValueError("Invalid encrypted payload format")

    encrypted_dek = base64.b64decode(parts[0])
    iv = base64.b64decode(parts[1])
    ciphertext = base64.b64decode(parts[2])

    if provider == "aws":
        plaintext_dek = _aws_decrypt_dek(key_arn, encrypted_dek)
    elif provider == "azure":
        plaintext_dek = _azure_decrypt_dek(key_arn, encrypted_dek)
    elif provider == "gcp":
        plaintext_dek = _gcp_decrypt_dek(key_arn, ciphertext)
    else:
        raise ValueError(f"Unknown KMS provider: {provider}")

    aesgcm = AESGCM(plaintext_dek)
    return aesgcm.decrypt(iv, ciphertext, None).decode()


def test_kms_connectivity(provider: str, key_arn: str) -> bool:
    """Test that KMS connectivity works by encrypting and decrypting a test value."""
    try:
        payload = encrypt_field(provider, key_arn, "compliai-byok-test")
        result = decrypt_field(provider, key_arn, payload)
        return result == "compliai-byok-test"
    except Exception as exc:
        logger.error("KMS connectivity test failed: %s", exc)
        return False
