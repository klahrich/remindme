"""Google Calendar: OAuth + calendar/event fetching."""

import datetime as dt

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import config


def get_service():
    """Return an authenticated Calendar API service, refreshing/creating the token."""
    creds = None
    if config.TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(config.TOKEN_FILE, config.SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                config.GOOGLE_CREDENTIALS_FILE, config.SCOPES
            )
            creds = flow.run_local_server(port=0)
        config.TOKEN_FILE.write_text(creds.to_json())
    return build("calendar", "v3", credentials=creds)


def list_calendars(service) -> list[dict]:
    """All calendars on the account, minus blocklisted subscriptions."""
    items = service.calendarList().list().execute().get("items", [])
    kept = []
    for cal in items:
        summary = cal.get("summary", "").lower()
        cal_id = cal.get("id", "").lower()
        if any(kw in summary or kw in cal_id for kw in config.CALENDAR_BLOCKLIST):
            continue
        kept.append(cal)
    return kept


def get_events_in_window(service, calendar_id: str,
                         time_min: dt.datetime, time_max: dt.datetime) -> list[dict]:
    """Events starting within [time_min, time_max) (timezone-aware datetimes)."""
    result = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min.isoformat(),
        timeMax=time_max.isoformat(),
        singleEvents=True,   # expand recurring events into instances
        orderBy="startTime",
    ).execute()
    return result.get("items", [])


def skip_reason(event: dict) -> str | None:
    """Return why an event should be skipped, or None if it's callable."""
    if event.get("status") == "cancelled":
        return "cancelled"
    if not event["start"].get("dateTime"):
        return "all-day"
    if config.SKIP_FREE_EVENTS and event.get("transparency") == "transparent":
        return "marked free"
    for attendee in event.get("attendees", []):
        if attendee.get("self") and attendee.get("responseStatus") == "declined":
            return "declined"
    return None
