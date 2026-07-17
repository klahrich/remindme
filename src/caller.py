"""Twilio outbound calling."""

import datetime as dt
import logging

from twilio.rest import Client

import config

log = logging.getLogger("remindme")

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        _client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
    return _client


def place_call(summary: str, start_time: dt.datetime) -> str | None:
    """Place the reminder call. Returns the call SID, or None on failure."""
    start_local = start_time.astimezone().strftime("%H:%M")
    twiml = (
        "<Response><Say voice=\"Polly.Joey\">"
        f"Hey! One minute warning. Your meeting, {summary}, starts at {start_local}."
        "</Say></Response>"
    )
    try:
        call = _get_client().calls.create(
            twiml=twiml,
            to=config.TWILIO_TO_NUMBER,
            from_=config.TWILIO_FROM_NUMBER,
        )
        log.info("Call placed for '%s' (SID: %s)", summary, call.sid)
        return call.sid
    except Exception:
        log.exception("Failed to place call for '%s'", summary)
        return None
