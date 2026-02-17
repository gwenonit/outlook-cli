# Outlook CLI

A CLI wrapper for Microsoft Graph API providing Outlook email, calendar, and tasks functionality.

Inspired by [gogcli](https://github.com/steipete/gogcli) but built for Outlook.com/Microsoft 365.

## Features

- **Email**: Search, read, send, draft, delete emails
- **Calendar**: List events, create/update, check free/busy
- **Tasks**: Manage todo items (Microsoft To Do)
- **Secure**: Device code auth, token refresh, secure storage
- **BYO App**: Use your own Azure AD app registration for security
- **JSON Output**: Script-friendly JSON output for automation

## Prerequisites

1. A Microsoft account (outlook.com, hotmail.com, live.com, or Microsoft 365)
2. An Azure AD app registration (see setup below)

## Azure AD App Registration (One-time Setup)

### Step 1: Register Your Application

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to: **Microsoft Entra ID** → **App registrations** → **New registration**
3. **Name**: Choose a name (e.g., "Outlook CLI")
4. **Supported account types**: 
   - Select "Personal Microsoft accounts only" for outlook.com accounts
   - Or "Accounts in any organizational directory and personal accounts" for work/school accounts
5. **Redirect URI**: Leave blank (we use device code flow)
6. Click **Register**

### Step 2: Configure Authentication

1. In your app → **Authentication** (left sidebar)
2. Scroll to **Advanced settings**
3. Set **"Allow public client flows"** → **Yes**
4. Click **Save**

### Step 3: Add API Permissions

1. Go to **API permissions** → **Add a permission**
2. Select **Microsoft Graph** → **Delegated permissions**
3. Add these permissions:
   - ✅ `Mail.Read` — Read emails
   - ✅ `Mail.Send` — Send emails
   - ✅ `Calendars.ReadWrite` — Read/write calendar events
   - ✅ `Tasks.ReadWrite` — Read/write tasks
   - ✅ `User.Read` — Read user profile
4. Click **Grant admin consent** (for personal accounts, you'll consent during login)

### Step 4: Copy Your Client ID

1. Go to **Overview** page
2. Copy the **Application (client) ID**
3. You'll use this for `outlook auth login --client-id YOUR_CLIENT_ID`

## Installation

### Using pipx (Recommended)

```bash
pipx install git+https://github.com/gwenonit/outlook-cli.git
```

### Using pip

```bash
pip install git+https://github.com/gwenonit/outlook-cli.git
```

### From Source

```bash
git clone https://github.com/gwenonit/outlook-cli.git
cd outlook-cli
pip install -e .
```

## Authentication

### Initial Login

```bash
outlook auth login --client-id YOUR_CLIENT_ID
```

This will:
1. Display a device code
2. Open https://www.microsoft.com/link in your browser
3. Enter the device code
4. Sign in with your Microsoft account
5. Accept the permissions

The CLI will receive an access token and refresh token, stored securely in `~/.outlook-cli/tokens.json`.

### Check Authentication Status

```bash
outlook auth status
outlook auth list
```

### Logout

```bash
outlook auth logout
```

## Usage

### Email Commands

```bash
# List recent emails
outlook email list --max 10

# List emails from a specific folder
outlook email list --folder inbox --max 20
outlook email list --folder sent --max 5

# Search emails
outlook email search "subject:meeting" --max 10
outlook email search "from:boss@company.com" --max 5

# Get full email details
outlook email get MESSAGE_ID

# Send an email
outlook email send --to recipient@example.com --subject "Hello" --body "Message content"

# Send from file
outlook email send --to recipient@example.com --subject "Report" --body-file ./message.txt

# JSON output for scripting
outlook --json-output email list --max 5
```

### Calendar Commands

```bash
# List today's events
outlook calendar list --today

# List events for next 7 days
outlook calendar list --days 7

# List events with JSON output
outlook --json-output calendar list --days 3

# Create an event
outlook calendar create \
  --summary "Team Meeting" \
  --from "2026-02-17T14:00:00" \
  --to "2026-02-17T15:00:00" \
  --location "Conference Room A"

# Create with attendees
outlook calendar create \
  --summary "Project Review" \
  --from "2026-02-17T10:00:00" \
  --to "2026-02-17T11:00:00" \
  --attendees "alice@example.com,bob@example.com"
```

### Tasks Commands

```bash
# List tasks
outlook tasks lists

# Create a task
outlook tasks create --title "Buy groceries"

# Create with due date
outlook tasks create --title "Submit report" --due-date "2026-02-18T17:00:00"

# List from specific task list
outlook tasks lists --list-name "Work"
```

## Global Options

- `-a, --account TEXT` — Specify account email (if multiple accounts)
- `-j, --json-output` — Output as JSON for scripting
- `--help` — Show help message

## Configuration

Configuration and tokens are stored in:
- **Config**: `~/.outlook-cli/config.json`
- **Tokens**: `~/.outlook-cli/tokens.json` (chmod 600)

## Security Notes

- **Device code flow** is used for authentication — your password never touches this CLI
- Tokens are stored securely with restricted permissions (600)
- Refresh tokens are used automatically — no need to re-authenticate frequently
- Use your own Azure AD app — you control the permissions and can revoke access anytime

## Troubleshooting

### "The provided client is not supported for this feature"

Your Azure app needs "Allow public client flows" enabled. See Step 2 in setup.

### "Not authenticated" error

Run `outlook auth login --client-id YOUR_CLIENT_ID` again.

### Token expired

The CLI automatically refreshes tokens. If it fails, just run login again.

### Permission denied

Check that you've granted admin consent for the API permissions in Azure portal.

## Development

### Setup Development Environment

```bash
git clone https://github.com/gwenonit/outlook-cli.git
cd outlook-cli
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Project Structure

```
outlook_cli/
├── __init__.py
├── main.py          # CLI entry point (Click commands)
├── auth.py          # Authentication manager
├── email.py         # Email client
├── calendar.py      # Calendar client
└── tasks.py         # Tasks client
```

## License

MIT

## Acknowledgments

- Inspired by [gogcli](https://github.com/steipete/gogcli) for Google Workspace
- Built on [Microsoft Graph API](https://docs.microsoft.com/en-us/graph/)
