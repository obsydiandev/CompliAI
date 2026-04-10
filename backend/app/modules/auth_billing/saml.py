"""SAML 2.0 SP-initiated SSO (T5.1).

Implements a minimal Service Provider (SP) using the ``python3-saml``
(onelogin) library.  If the library is not installed the module degrades
gracefully — all functions raise ``NotImplementedError`` with an
installation hint.

Required settings
-----------------
SAML_SP_ENTITY_ID        — SP entityID (e.g. https://app.compliai.io)
SAML_SP_ACS_URL          — Assertion Consumer Service URL
                           (e.g. https://app.compliai.io/api/v1/sso/saml/acs)
SAML_SP_SLO_URL          — Single Logout Service URL (optional)
SAML_SP_PRIVATE_KEY      — PEM-encoded SP private key (no headers)
SAML_SP_CERTIFICATE      — PEM-encoded SP certificate (no headers)
SAML_IDP_ENTITY_ID       — IdP entityID
SAML_IDP_SSO_URL         — IdP SSO redirect URL
SAML_IDP_SLO_URL         — IdP SLO URL (optional)
SAML_IDP_CERTIFICATE     — IdP X.509 certificate (no headers)

All settings default to empty strings so the application starts without
them; the endpoints return 503 if SAML is not configured.
"""

from __future__ import annotations

import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# Try to import python3-saml (onelogin)
try:
    from onelogin.saml2.auth import OneLogin_Saml2_Auth  # type: ignore[import-untyped]
    from onelogin.saml2.settings import OneLogin_Saml2_Settings  # type: ignore[import-untyped]

    _SAML_AVAILABLE = True
except ImportError:
    _SAML_AVAILABLE = False


def _is_configured() -> bool:
    return bool(
        getattr(settings, "SAML_IDP_ENTITY_ID", "")
        and getattr(settings, "SAML_IDP_SSO_URL", "")
        and getattr(settings, "SAML_IDP_CERTIFICATE", "")
        and getattr(settings, "SAML_SP_ENTITY_ID", "")
        and getattr(settings, "SAML_SP_ACS_URL", "")
    )


def _build_saml_settings() -> dict[str, Any]:
    """Build the python3-saml settings dict from application config."""
    sp_cert = getattr(settings, "SAML_SP_CERTIFICATE", "")
    sp_key = getattr(settings, "SAML_SP_PRIVATE_KEY", "")

    return {
        "strict": True,
        "debug": getattr(settings, "ENVIRONMENT", "production") != "production",
        "sp": {
            "entityId": getattr(settings, "SAML_SP_ENTITY_ID", ""),
            "assertionConsumerService": {
                "url": getattr(settings, "SAML_SP_ACS_URL", ""),
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
            },
            "singleLogoutService": {
                "url": getattr(settings, "SAML_SP_SLO_URL", ""),
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
            "x509cert": sp_cert,
            "privateKey": sp_key,
        },
        "idp": {
            "entityId": getattr(settings, "SAML_IDP_ENTITY_ID", ""),
            "singleSignOnService": {
                "url": getattr(settings, "SAML_IDP_SSO_URL", ""),
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "singleLogoutService": {
                "url": getattr(settings, "SAML_IDP_SLO_URL", ""),
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "x509cert": getattr(settings, "SAML_IDP_CERTIFICATE", ""),
        },
    }


def get_metadata_xml() -> str:
    """Return SP metadata XML string."""
    if not _SAML_AVAILABLE:
        raise NotImplementedError(
            "python3-saml is not installed. Run: pip install python3-saml"
        )
    if not _is_configured():
        raise ValueError("SAML is not configured (SAML_IDP_ENTITY_ID / SAML_SP_ENTITY_ID missing)")

    saml_settings = OneLogin_Saml2_Settings(settings=_build_saml_settings(), sp_validation_only=True)
    metadata = saml_settings.get_sp_metadata()
    errors = saml_settings.validate_metadata(metadata)
    if errors:
        raise ValueError(f"SAML metadata validation errors: {errors}")
    return metadata


def build_authn_request(request_data: dict[str, Any]) -> str:
    """Return the IdP redirect URL for an SP-initiated AuthnRequest.

    Parameters
    ----------
    request_data:
        Dict with keys ``http_host``, ``script_name``, ``get_data``,
        ``post_data``, ``https`` — as produced by the FastAPI SAML helper.

    Returns
    -------
    str — URL the browser should be redirected to.
    """
    if not _SAML_AVAILABLE:
        raise NotImplementedError(
            "python3-saml is not installed. Run: pip install python3-saml"
        )
    if not _is_configured():
        raise ValueError("SAML is not configured")

    auth = OneLogin_Saml2_Auth(request_data, old_settings=_build_saml_settings())
    return auth.login()


def process_acs_response(request_data: dict[str, Any]) -> dict[str, Any]:
    """Process the IdP's POST response at the Assertion Consumer Service URL.

    Parameters
    ----------
    request_data:
        Dict with ``post_data`` containing the SAMLResponse field.

    Returns
    -------
    dict with keys:
        ``email``      — user email from NameID / attributes
        ``name``       — display name (may be empty)
        ``attributes`` — raw SAML attributes dict
        ``session_index`` — SAML session index (for SLO)

    Raises
    ------
    ValueError if the response is invalid.
    """
    if not _SAML_AVAILABLE:
        raise NotImplementedError(
            "python3-saml is not installed. Run: pip install python3-saml"
        )
    if not _is_configured():
        raise ValueError("SAML is not configured")

    auth = OneLogin_Saml2_Auth(request_data, old_settings=_build_saml_settings())
    auth.process_response()
    errors = auth.get_errors()
    if errors:
        raise ValueError(f"SAML response errors: {errors}. {auth.get_last_error_reason()}")
    if not auth.is_authenticated():
        raise ValueError("SAML authentication failed")

    attrs = auth.get_attributes()
    name_id = auth.get_nameid()
    # Try common attribute names for display name
    name = (
        _first_attr(attrs, "displayName")
        or _first_attr(attrs, "cn")
        or f"{_first_attr(attrs, 'givenName', '')} {_first_attr(attrs, 'sn', '')}".strip()
        or ""
    )
    email = (
        _first_attr(attrs, "email")
        or _first_attr(attrs, "mail")
        or _first_attr(attrs, "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress")
        or name_id
        or ""
    )
    return {
        "email": email.lower(),
        "name": name,
        "attributes": {k: v for k, v in attrs.items()},
        "session_index": auth.get_session_index(),
        "name_id": name_id,
    }


def _first_attr(attrs: dict[str, list], key: str, default: str = "") -> str:
    val = attrs.get(key)
    if val and isinstance(val, list):
        return str(val[0])
    return default
