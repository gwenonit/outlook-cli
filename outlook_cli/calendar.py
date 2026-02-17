"""
Calendar client for Microsoft Graph API
"""

import requests
from datetime import datetime
from outlook_cli.auth import AuthManager

GRAPH_BASE = "https://graph.microsoft.com/v1.0"

class CalendarClient:
    def __init__(self, config_dir, account=None):
        self.auth = AuthManager(config_dir)
        self.account = account
        self.access_token = self.auth.get_access_token(account)
        
        if not self.access_token:
            raise Exception("Not authenticated")
    
    def _headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def list_events(self, start_time, end_time, calendar_id='primary'):
        """List calendar events in a date range"""
        if calendar_id == 'primary':
            url = f"{GRAPH_BASE}/me/calendarView"
        else:
            url = f"{GRAPH_BASE}/me/calendars/{calendar_id}/calendarView"
        
        # Format times
        if isinstance(start_time, datetime):
            start_str = start_time.isoformat()
        else:
            start_str = start_time
        
        if isinstance(end_time, datetime):
            end_str = end_time.isoformat()
        else:
            end_str = end_time
        
        params = {
            'startDateTime': start_str,
            'endDateTime': end_str,
            '$orderby': 'start/dateTime',
            '$select': 'id,subject,start,end,location,attendees,bodyPreview'
        }
        
        response = requests.get(url, headers=self._headers(), params=params)
        
        if response.status_code == 200:
            return response.json().get('value', [])
        else:
            raise Exception(f"Failed to list events: {response.text}")
    
    def create_event(self, summary, start_time, end_time, location=None, attendees=None):
        """Create a calendar event"""
        url = f"{GRAPH_BASE}/me/events"
        
        event = {
            'subject': summary,
            'start': {
                'dateTime': start_time,
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'UTC'
            }
        }
        
        if location:
            event['location'] = {'displayName': location}
        
        if attendees:
            event['attendees'] = attendees
        
        response = requests.post(url, headers=self._headers(), json=event)
        
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to create event: {response.text}")
    
    def update_event(self, event_id, **kwargs):
        """Update a calendar event"""
        url = f"{GRAPH_BASE}/me/events/{event_id}"
        
        event = {}
        if 'summary' in kwargs:
            event['subject'] = kwargs['summary']
        if 'start_time' in kwargs:
            event['start'] = {'dateTime': kwargs['start_time'], 'timeZone': 'UTC'}
        if 'end_time' in kwargs:
            event['end'] = {'dateTime': kwargs['end_time'], 'timeZone': 'UTC'}
        if 'location' in kwargs:
            event['location'] = {'displayName': kwargs['location']}
        
        response = requests.patch(url, headers=self._headers(), json=event)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to update event: {response.text}")
    
    def delete_event(self, event_id):
        """Delete a calendar event"""
        url = f"{GRAPH_BASE}/me/events/{event_id}"
        
        response = requests.delete(url, headers=self._headers())
        
        if response.status_code == 204:
            return {'success': True}
        else:
            raise Exception(f"Failed to delete event: {response.text}")
    
    def get_free_busy(self, start_time, end_time, attendees):
        """Get free/busy schedule"""
        url = f"{GRAPH_BASE}/me/calendar/getSchedule"
        
        data = {
            'schedules': attendees if isinstance(attendees, list) else [attendees],
            'startTime': {'dateTime': start_time, 'timeZone': 'UTC'},
            'endTime': {'dateTime': end_time, 'timeZone': 'UTC'},
            'availabilityViewInterval': 30
        }
        
        response = requests.post(url, headers=self._headers(), json=data)
        
        if response.status_code == 200:
            return response.json().get('value', [])
        else:
            raise Exception(f"Failed to get schedule: {response.text}")
