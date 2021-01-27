from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
from datetime import datetime, timedelta
import os


class CalendarApi:
    TOKEN_JSON = 'credentials.json'
    TOKEN_PKL = os.path.abspath(os.path.join(os.path.dirname(__file__), 'token.pkl'))
    SCOPE = 'https://www.googleapis.com/auth/calendar'

    def __init__(self):
        with open(CalendarApi.TOKEN_PKL, 'rb') as token:
            creds = pickle.load(token)
        self.service = build('calendar', 'v3', credentials=creds)
        result = self.service.calendarList().list().execute()
        self.calendar_id = result['items'][0]['id']
        self.timeZone = 'Europe/Samara'

    @staticmethod
    def auth():
        scopes = [CalendarApi.SCOPE]
        flow = InstalledAppFlow.from_client_secrets_file(CalendarApi.TOKEN_JSON, scopes=scopes)
        credentials = flow.run_console()
        with open(CalendarApi.TOKEN_PKL, 'rb') as token:
            pickle.dump(credentials, token)

    def get_calendar_events(self) -> list:
        result = self.service.events().list(calendarId=self.calendar_id, timeZone=self.timeZone).execute()

        return result['items']

    def create_new_calendar_event(
            self,
            summary: str,
            description: str,
            duration=24,
            y=2021,
            m=1,
            d=20,
            h=0,
            minute=0
    ) -> None:  # todo добавить в значение по умолчаю сегодняшний день и время
        start_time = datetime(y, m, d, h, minute)
        end_time = start_time + timedelta(hours=duration)

        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                'timeZone': self.timeZone,
            },
            'end': {
                'dateTime': end_time.strftime("%Y-%m-%dT%H:%M:%S"),
                'timeZone': self.timeZone,
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 30},
                ],
            },
        }

        self.service.events().insert(calendarId=self.calendar_id, body=event).execute()

    def delete_event(self, event_summary: str):
        events = self.get_calendar_events()
        for event in events:
            if event['summary'].find(event_summary.strip()) != -1:
                self.service.events().delete(calendarId=self.calendar_id, eventId=event['id']).execute()


if __name__ == '__main__':
    CalendarApi.auth()
