import asyncio
import datetime
import uuid

import caldav


class CalendarService:
    def __init__(self, url: str, username: str, password: str):
        self.url = url
        self.username = username
        self.password = password

    def _create_event_sync(
        self,
        title: str,
        start: datetime.datetime,
        end: datetime.datetime,
        attendee_emails: list[str],
    ) -> str:
        client = caldav.DAVClient(url=self.url, username=self.username, password=self.password)
        principal = client.principal()
        calendars = principal.calendars()
        if not calendars:
            raise RuntimeError("No calendars found on CalDAV server")
        calendar = calendars[0]

        uid = str(uuid.uuid4())
        attendees = "\n".join(f"ATTENDEE;RSVP=TRUE:mailto:{email}" for email in attendee_emails)
        vcal = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Noetikon//EN
BEGIN:VEVENT
UID:{uid}
DTSTART:{start.strftime("%Y%m%dT%H%M%SZ")}
DTEND:{end.strftime("%Y%m%dT%H%M%SZ")}
SUMMARY:{title}
{attendees}
END:VEVENT
END:VCALENDAR"""

        calendar.save_event(vcal)
        return uid

    async def create_event(
        self,
        title: str,
        start: datetime.datetime,
        end: datetime.datetime,
        attendee_emails: list[str],
    ) -> str:
        return await asyncio.to_thread(self._create_event_sync, title, start, end, attendee_emails)
