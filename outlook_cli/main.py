#!/usr/bin/env python3
"""
Outlook CLI - Microsoft Graph CLI for Outlook email, calendar, and tasks
"""

import click
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

from outlook_cli.auth import AuthManager
from outlook_cli.email import EmailClient
from outlook_cli.calendar import CalendarClient
from outlook_cli.tasks import TasksClient

CONFIG_DIR = Path.home() / ".outlook-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"

@click.group()
@click.option('--account', '-a', help='Account email to use')
@click.option('--json-output', '-j', is_flag=True, help='Output as JSON')
@click.pass_context
def cli(ctx, account, json_output):
    """Outlook CLI - Microsoft Graph API client for email, calendar, and tasks"""
    ctx.ensure_object(dict)
    ctx.obj['account'] = account
    ctx.obj['json_output'] = json_output
    
    # Ensure config directory exists
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

@cli.group()
def auth():
    """Authentication commands"""
    pass

@auth.command()
@click.option('--client-id', required=True, help='Azure AD Application Client ID')
@click.option('--tenant', default='consumers', help='Tenant ID (default: consumers for personal accounts)')
def login(client_id, tenant):
    """Authenticate using device code flow"""
    auth_manager = AuthManager(CONFIG_DIR)
    auth_manager.device_code_login(client_id, tenant)

@auth.command()
def logout():
    """Logout and clear stored credentials"""
    auth_manager = AuthManager(CONFIG_DIR)
    auth_manager.logout()

@auth.command()
def status():
    """Check authentication status"""
    auth_manager = AuthManager(CONFIG_DIR)
    auth_manager.status()

@auth.command()
def list():
    """List authenticated accounts"""
    auth_manager = AuthManager(CONFIG_DIR)
    auth_manager.list_accounts()

@cli.group()
@click.pass_context
def email(ctx):
    """Email commands"""
    pass

@email.command()
@click.option('--max', '-m', default=10, help='Maximum number of emails to list')
@click.option('--folder', '-f', default='inbox', help='Folder to list (default: inbox)')
@click.pass_context
def list(ctx, max, folder):
    """List emails"""
    client = EmailClient(CONFIG_DIR, ctx.obj.get('account'))
    emails = client.list_messages(max_results=max, folder=folder)
    
    if ctx.obj.get('json_output'):
        click.echo(json.dumps(emails, indent=2))
    else:
        for msg in emails:
            click.echo(f"[{msg['receivedDateTime']}] {msg['from']['emailAddress']['name']}: {msg['subject']}")

@email.command()
@click.argument('query')
@click.option('--max', '-m', default=10, help='Maximum results')
@click.pass_context
def search(ctx, query, max):
    """Search emails"""
    client = EmailClient(CONFIG_DIR, ctx.obj.get('account'))
    emails = client.search(query, max_results=max)
    
    if ctx.obj.get('json_output'):
        click.echo(json.dumps(emails, indent=2))
    else:
        for msg in emails:
            click.echo(f"[{msg['receivedDateTime']}] {msg['from']['emailAddress']['name']}: {msg['subject']}")

@email.command()
@click.option('--to', required=True, help='Recipient email')
@click.option('--subject', '-s', required=True, help='Email subject')
@click.option('--body', '-b', required=True, help='Email body')
@click.option('--body-file', '-f', type=click.File('r'), help='Read body from file')
@click.pass_context
def send(ctx, to, subject, body, body_file):
    """Send an email"""
    if body_file:
        body = body_file.read()
    
    client = EmailClient(CONFIG_DIR, ctx.obj.get('account'))
    result = client.send_message(to, subject, body)
    
    if ctx.obj.get('json_output'):
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo("✓ Email sent successfully")

@email.command()
@click.argument('message_id')
@click.pass_context
def get(ctx, message_id):
    """Get email details"""
    client = EmailClient(CONFIG_DIR, ctx.obj.get('account'))
    msg = client.get_message(message_id)
    
    if ctx.obj.get('json_output'):
        click.echo(json.dumps(msg, indent=2))
    else:
        click.echo(f"From: {msg['from']['emailAddress']['name']} <{msg['from']['emailAddress']['address']}>")
        click.echo(f"Subject: {msg['subject']}")
        click.echo(f"Date: {msg['receivedDateTime']}")
        click.echo(f"\n{msg.get('body', {}).get('content', 'No content')}")

@cli.group()
@click.pass_context
def calendar(ctx):
    """Calendar commands"""
    pass

@calendar.command()
@click.option('--today', is_flag=True, help='Show today\'s events')
@click.option('--days', '-d', default=7, help='Number of days to show')
@click.pass_context
def list(ctx, today, days):
    """List calendar events"""
    client = CalendarClient(CONFIG_DIR, ctx.obj.get('account'))
    
    if today:
        start = datetime.now().replace(hour=0, minute=0, second=0)
        end = start + timedelta(days=1)
    else:
        start = datetime.now()
        end = start + timedelta(days=days)
    
    events = client.list_events(start, end)
    
    if ctx.obj.get('json_output'):
        click.echo(json.dumps(events, indent=2))
    else:
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            click.echo(f"[{start}] {event['subject']}")

@calendar.command()
@click.option('--summary', '-s', required=True, help='Event title')
@click.option('--from', 'start_time', required=True, help='Start time (ISO 8601)')
@click.option('--to', 'end_time', required=True, help='End time (ISO 8601)')
@click.option('--location', '-l', help='Event location')
@click.option('--attendees', '-a', help='Comma-separated attendee emails')
@click.pass_context
def create(ctx, summary, start_time, end_time, location, attendees):
    """Create a calendar event"""
    client = CalendarClient(CONFIG_DIR, ctx.obj.get('account'))
    
    attendee_list = []
    if attendees:
        attendee_list = [{'emailAddress': {'address': email.strip()}, 'type': 'required'} 
                        for email in attendees.split(',')]
    
    result = client.create_event(summary, start_time, end_time, location, attendee_list)
    
    if ctx.obj.get('json_output'):
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"✓ Event created: {result['id']}")

@cli.group()
@click.pass_context
def tasks(ctx):
    """Tasks commands"""
    pass

@tasks.command()
@click.option('--list-name', default='Tasks', help='Task list name')
@click.pass_context
def lists(ctx, list_name):
    """List tasks"""
    client = TasksClient(CONFIG_DIR, ctx.obj.get('account'))
    items = client.list_tasks(list_name)
    
    if ctx.obj.get('json_output'):
        click.echo(json.dumps(items, indent=2))
    else:
        for item in items:
            status = "✓" if item['status'] == 'completed' else "○"
            click.echo(f"{status} {item['title']}")

@tasks.command()
@click.option('--title', '-t', required=True, help='Task title')
@click.option('--list-name', default='Tasks', help='Task list name')
@click.pass_context
def create(ctx, title, list_name):
    """Create a task"""
    client = TasksClient(CONFIG_DIR, ctx.obj.get('account'))
    result = client.create_task(title, list_name)
    
    if ctx.obj.get('json_output'):
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"✓ Task created: {result['id']}")

if __name__ == '__main__':
    cli()
