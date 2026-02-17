"""
Email client for Microsoft Graph API
"""

import requests
from outlook_cli.auth import AuthManager

GRAPH_BASE = "https://graph.microsoft.com/v1.0"

class EmailClient:
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
    
    def list_messages(self, max_results=10, folder='inbox'):
        """List emails from a folder"""
        folder_map = {
            'inbox': 'inbox',
            'sent': 'sentitems',
            'drafts': 'drafts',
            'deleted': 'deleteditems'
        }
        
        folder_id = folder_map.get(folder.lower(), folder)
        url = f"{GRAPH_BASE}/me/mailFolders/{folder_id}/messages"
        
        params = {
            '$top': max_results,
            '$orderby': 'receivedDateTime desc',
            '$select': 'id,subject,from,receivedDateTime,bodyPreview,isRead'
        }
        
        response = requests.get(url, headers=self._headers(), params=params)
        
        if response.status_code == 200:
            return response.json().get('value', [])
        else:
            raise Exception(f"Failed to list messages: {response.text}")
    
    def search(self, query, max_results=10):
        """Search emails"""
        url = f"{GRAPH_BASE}/me/messages"
        
        # Build search filter
        # Microsoft Graph supports $search parameter
        params = {
            '$top': max_results,
            '$orderby': 'receivedDateTime desc',
            '$select': 'id,subject,from,receivedDateTime,bodyPreview',
            '$search': f'"{query}"'
        }
        
        response = requests.get(url, headers=self._headers(), params=params)
        
        if response.status_code == 200:
            return response.json().get('value', [])
        else:
            raise Exception(f"Failed to search messages: {response.text}")
    
    def get_message(self, message_id):
        """Get full message details"""
        url = f"{GRAPH_BASE}/me/messages/{message_id}"
        
        response = requests.get(url, headers=self._headers())
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get message: {response.text}")
    
    def send_message(self, to_email, subject, body, body_type='Text'):
        """Send an email"""
        url = f"{GRAPH_BASE}/me/sendMail"
        
        message = {
            'message': {
                'subject': subject,
                'body': {
                    'contentType': body_type,
                    'content': body
                },
                'toRecipients': [
                    {
                        'emailAddress': {
                            'address': to_email
                        }
                    }
                ]
            }
        }
        
        response = requests.post(url, headers=self._headers(), json=message)
        
        if response.status_code == 202:
            return {'success': True}
        else:
            raise Exception(f"Failed to send message: {response.text}")
    
    def create_draft(self, to_email, subject, body, body_type='Text'):
        """Create a draft message"""
        url = f"{GRAPH_BASE}/me/messages"
        
        message = {
            'subject': subject,
            'body': {
                'contentType': body_type,
                'content': body
            },
            'toRecipients': [
                {
                    'emailAddress': {
                        'address': to_email
                    }
                }
            ]
        }
        
        response = requests.post(url, headers=self._headers(), json=message)
        
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to create draft: {response.text}")
    
    def delete_message(self, message_id):
        """Delete a message"""
        url = f"{GRAPH_BASE}/me/messages/{message_id}"
        
        response = requests.delete(url, headers=self._headers())
        
        if response.status_code == 204:
            return {'success': True}
        else:
            raise Exception(f"Failed to delete message: {response.text}")
