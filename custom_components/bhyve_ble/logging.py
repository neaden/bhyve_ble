"""Optional debug logging for Orbit BLE plaintext and decoded payloads.

Enable in Home Assistant ``configuration.yaml``::

    logger:
      logs:
        custom_components.bhyve_ble.logging: debug

Lines are prefixed with ``[<MAC>]`` for easy grepping in **Settings → System → Logs**.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from .orbit_codec import decode_orbit_ble_plaintext

_LOG = logging.getLogger(__name__)

_MAX_JSON_CHARS = 12_000


def _debug(address: str, msg: str, *args: object) -> None:
    _LOG.debug("[%s] " + msg, address, *args)


def _oneof_from_plaintext(plaintext: bytes) -> str | None:
    try:
        decoded = decode_orbit_ble_plaintext(plaintext)
    except Exception:  # noqa: BLE001
        return None
    return (decoded.get("_framing") or {}).get("oneof")


def _format_json(obj: Any) -> str:
    text = json.dumps(obj, indent=2, sort_keys=True, default=str)
    if len(text) > _MAX_JSON_CHARS:
        return text[:_MAX_JSON_CHARS] + f"\n… ({len(text) - _MAX_JSON_CHARS} chars truncated)"
    return text


def _packet_summary(link_msg_type: int, plaintext: bytes, *, oneof: str | None = None) -> str:
    label = oneof if oneof is not None else _oneof_from_plaintext(plaintext) or "?"
    return (
        f"link_type=0x{link_msg_type:02x} oneof={label} "
        f"plaintext_len={len(plaintext)} plaintext_hex={plaintext.hex()}"
    )


def log_ble_tx(address: str, link_msg_type: int, plaintext: bytes) -> None:
    _debug(address, "TX %s", _packet_summary(link_msg_type, plaintext))


def log_ble_rx(
    address: str,
    link_msg_type: int,
    plaintext: bytes,
    decoded: dict[str, Any],
) -> None:
    oneof = (decoded.get("_framing") or {}).get("oneof")
    _debug(
        address,
        "RX %s decoded_json:\n%s",
        _packet_summary(link_msg_type, plaintext, oneof=oneof),
        _format_json(decoded),
    )


def log_ble_rx_decode_failed(address: str, link_msg_type: int, plaintext: bytes, err: Exception) -> None:
    _debug(address, "RX decode failed %s err=%s", _packet_summary(link_msg_type, plaintext), err)


def log_ble_merged(address: str, merged: dict[str, Any] | None) -> None:
    if not merged:
        _debug(address, "merged last_message empty")
        return
    msg = merged.get("message") or {}
    framing = merged.get("_framing") or {}
    _debug(
        address,
        "merged last_message oneof_last=%s message_keys=%s merged_json:\n%s",
        framing.get("oneof") or "?",
        sorted(msg.keys()),
        _format_json(merged),
    )
