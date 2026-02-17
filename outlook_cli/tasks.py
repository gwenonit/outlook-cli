"""
Tasks client for Microsoft Graph API
"""

import requests
from outlook_cli.auth import AuthManager

GRAPH_BASE = "https://graph.microsoft.com/v1.0"

class TasksClient:
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
    
    def _get_task_list_id(self, list_name='Tasks'):
        """Get task list ID by name"""
        url = f"{GRAPH_BASE}/me/todo/lists"
        
        response = requests.get(url, headers=self._headers())
        
        if response.status_code == 200:
            lists = response.json().get('value', [])
            for task_list in lists:
                if task_list['displayName'] == list_name:
                    return task_list['id']
            # Return first list if name not found
            if lists:
                return lists[0]['id']
        
        raise Exception(f"Task list '{list_name}' not found")
    
    def list_tasks(self, list_name='Tasks', include_completed=False):
        """List tasks from a task list"""
        list_id = self._get_task_list_id(list_name)
        url = f"{GRAPH_BASE}/me/todo/lists/{list_id}/tasks"
        
        params = {
            '$orderby': 'createdDateTime desc'
        }
        
        if not include_completed:
            params['$filter'] = "status ne 'completed'"
        
        response = requests.get(url, headers=self._headers(), params=params)
        
        if response.status_code == 200:
            return response.json().get('value', [])
        else:
            raise Exception(f"Failed to list tasks: {response.text}")
    
    def create_task(self, title, list_name='Tasks', due_date=None):
        """Create a task"""
        list_id = self._get_task_list_id(list_name)
        url = f"{GRAPH_BASE}/me/todo/lists/{list_id}/tasks"
        
        task = {
            'title': title
        }
        
        if due_date:
            task['dueDateTime'] = {
                'dateTime': due_date,
                'timeZone': 'UTC'
            }
        
        response = requests.post(url, headers=self._headers(), json=task)
        
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to create task: {response.text}")
    
    def update_task(self, task_id, list_name='Tasks', **kwargs):
        """Update a task"""
        list_id = self._get_task_list_id(list_name)
        url = f"{GRAPH_BASE}/me/todo/lists/{list_id}/tasks/{task_id}"
        
        task = {}
        if 'title' in kwargs:
            task['title'] = kwargs['title']
        if 'status' in kwargs:
            task['status'] = kwargs['status']
        if 'due_date' in kwargs:
            task['dueDateTime'] = {
                'dateTime': kwargs['due_date'],
                'timeZone': 'UTC'
            }
        
        response = requests.patch(url, headers=self._headers(), json=task)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to update task: {response.text}")
    
    def complete_task(self, task_id, list_name='Tasks'):
        """Mark a task as completed"""
        return self.update_task(task_id, list_name, status='completed')
    
    def delete_task(self, task_id, list_name='Tasks'):
        """Delete a task"""
        list_id = self._get_task_list_id(list_name)
        url = f"{GRAPH_BASE}/me/todo/lists/{list_id}/tasks/{task_id}"
        
        response = requests.delete(url, headers=self._headers())
        
        if response.status_code == 204:
            return {'success': True}
        else:
            raise Exception(f"Failed to delete task: {response.text}")
