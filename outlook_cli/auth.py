"""
Authentication manager for Outlook CLI
Handles device code flow, token storage, and refresh
"""

import json
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta
import click

# Keyring is optional - falls back to file storage
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

KEYRING_SERVICE = "outlook-cli"
TOKEN_FILE = "tokens.json"

class AuthManager:
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.token_file = config_dir / TOKEN_FILE
        self.config_file = config_dir / "config.json"
    
    def _load_config(self):
        """Load configuration"""
        if self.config_file.exists():
            with open(self.config_file) as f:
                return json.load(f)
        return {}
    
    def _save_config(self, config):
        """Save configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def _load_tokens(self):
        """Load tokens from storage"""
        if self.token_file.exists():
            with open(self.token_file) as f:
                return json.load(f)
        return {}
    
    def _save_tokens(self, tokens):
        """Save tokens to storage"""
        with open(self.token_file, 'w') as f:
            json.dump(tokens, f, indent=2)
        # Restrict permissions
        self.token_file.chmod(0o600)
    
    def device_code_login(self, client_id: str, tenant: str = 'consumers'):
        """
        Authenticate using device code flow
        https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-device-code
        """
        device_code_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/devicecode"
        token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
        
        scopes = "Mail.Read Mail.Send Calendars.ReadWrite Tasks.ReadWrite User.Read offline_access"
        
        # Step 1: Request device code
        click.echo("Requesting device code...")
        response = requests.post(device_code_url, data={
            'client_id': client_id,
            'scope': scopes
        })
        
        if response.status_code != 200:
            click.echo(f"Error: {response.text}", err=True)
            return False
        
        device_data = response.json()
        device_code = device_data['device_code']
        user_code = device_data['user_code']
        verification_uri = device_data.get('verification_uri', 'https://microsoft.com/devicelogin')
        expires_in = device_data['expires_in']
        interval = device_data.get('interval', 5)
        
        click.echo("\n" + "="*50)
        click.echo(f"  CODE: {user_code}")
        click.echo("="*50)
        click.echo(f"  Go to: {verification_uri}")
        click.echo("="*50)
        click.echo("\nWaiting for authorization...")
        
        # Step 2: Poll for token
        start_time = time.time()
        while time.time() - start_time < expires_in:
            time.sleep(interval)
            
            token_response = requests.post(token_url, data={
                'client_id': client_id,
                'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
                'device_code': device_code
            })
            
            if token_response.status_code == 200:
                token_data = token_response.json()
                
                # Get user info
                access_token = token_data['access_token']
                user_info = self._get_user_info(access_token)
                email = user_info.get('mail') or user_info.get('userPrincipalName')
                
                # Store tokens
                tokens = self._load_tokens()
                tokens[email] = {
                    'client_id': client_id,
                    'tenant': tenant,
                    'access_token': access_token,
                    'refresh_token': token_data['refresh_token'],
                    'expires_at': time.time() + token_data['expires_in'],
                    'user_info': user_info
                }
                self._save_tokens(tokens)
                
                click.echo(f"\n✓ Successfully authenticated as {email}")
                return True
            
            error_data = token_response.json()
            if error_data.get('error') == 'authorization_pending':
                click.echo(".", nl=False)
            elif error_data.get('error') == 'authorization_declined':
                click.echo("\n✗ Authorization declined")
                return False
            elif error_data.get('error') == 'expired_token':
                click.echo("\n✗ Device code expired")
                return False
            else:
                click.echo(f"\nError: {error_data}", err=True)
                return False
        
        click.echo("\n✗ Timeout waiting for authorization")
        return False
    
    def _get_user_info(self, access_token: str):
        """Get user info from Microsoft Graph"""
        response = requests.get(
            'https://graph.microsoft.com/v1.0/me',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        if response.status_code == 200:
            return response.json()
        return {}
    
    def get_access_token(self, email: str = None):
        """Get valid access token, refreshing if necessary"""
        tokens = self._load_tokens()
        
        if not tokens:
            click.echo("Not authenticated. Run: outlook auth login", err=True)
            return None
        
        # Use specified account or default to first
        if email is None:
            email = list(tokens.keys())[0]
        
        if email not in tokens:
            click.echo(f"Account {email} not found. Run: outlook auth login", err=True)
            return None
        
        account_data = tokens[email]
        
        # Check if token needs refresh
        if time.time() >= account_data['expires_at'] - 300:  # Refresh 5 min early
            new_token = self._refresh_token(email, account_data)
            if new_token:
                return new_token
            return None
        
        return account_data['access_token']
    
    def _refresh_token(self, email: str, account_data: dict):
        """Refresh access token"""
        token_url = f"https://login.microsoftonline.com/{account_data['tenant']}/oauth2/v2.0/token"
        
        response = requests.post(token_url, data={
            'client_id': account_data['client_id'],
            'grant_type': 'refresh_token',
            'refresh_token': account_data['refresh_token']
        })
        
        if response.status_code == 200:
            token_data = response.json()
            
            tokens = self._load_tokens()
            tokens[email]['access_token'] = token_data['access_token']
            tokens[email]['expires_at'] = time.time() + token_data['expires_in']
            
            # Update refresh token if provided
            if 'refresh_token' in token_data:
                tokens[email]['refresh_token'] = token_data['refresh_token']
            
            self._save_tokens(tokens)
            return token_data['access_token']
        else:
            click.echo(f"Failed to refresh token: {response.text}", err=True)
            return None
    
    def logout(self):
        """Clear all stored credentials"""
        if self.token_file.exists():
            self.token_file.unlink()
            click.echo("✓ Logged out successfully")
        else:
            click.echo("No active session")
    
    def status(self):
        """Show authentication status"""
        tokens = self._load_tokens()
        
        if not tokens:
            click.echo("Not authenticated")
            return
        
        for email, data in tokens.items():
            expires = datetime.fromtimestamp(data['expires_at'])
            now = datetime.now()
            
            if expires > now:
                status = f"Valid (expires {expires.strftime('%Y-%m-%d %H:%M')})"
            else:
                status = "Expired"
            
            click.echo(f"{email}: {status}")
    
    def list_accounts(self):
        """List authenticated accounts"""
        tokens = self._load_tokens()
        
        if not tokens:
            click.echo("No accounts")
            return
        
        click.echo("Authenticated accounts:")
        for email in tokens.keys():
            click.echo(f"  - {email}")
