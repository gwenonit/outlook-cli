# Outlook CLI Test Plan

## Azure App Registration Steps (Travis)

1. Go to https://portal.azure.com
2. Navigate to: Microsoft Entra ID → App registrations → New registration
3. **Name**: "Gwen Outlook CLI" (or similar)
4. **Supported account types**: "Personal Microsoft accounts only" (for outlook.com)
5. **Redirect URI**: None needed (we use device code flow)
6. Click **Register**
7. Copy the **Application (client) ID** — you'll need this for testing

## Add API Permissions

1. In your app → **API permissions** → **Add a permission**
2. Select **Microsoft Graph** → **Delegated permissions**
3. Add these permissions:
   - ✅ `Mail.Read` — Read emails
   - ✅ `Mail.Send` — Send emails
   - ✅ `Calendars.ReadWrite` — Read/write calendar events
   - ✅ `Tasks.ReadWrite` — Read/write tasks (todo)
   - ✅ `User.Read` — Read user profile
   - ✅ `offline_access` — Refresh tokens (already included by default)
4. Click **Grant admin consent** (for personal accounts, you'll consent during login)

---

## Test Execution (Gwen will run these)

### Test 1: Installation
```bash
cd /tmp
pip install git+https://github.com/gwenonit/outlook-cli.git
which outlook
outlook --help
```
**Expected**: Command installs successfully, help text displays

### Test 2: Authentication
```bash
outlook auth login --client-id YOUR_CLIENT_ID
```
**Expected**: 
- Shows device code
- Prompts to visit https://microsoft.com/devicelogin
- After you authorize, shows "✓ Successfully authenticated"

### Test 3: Verify Auth Status
```bash
outlook auth status
outlook auth list
```
**Expected**: Shows your email as authenticated with valid token

### Test 4: Email - List Messages
```bash
outlook email list --max 5
outlook email list --max 10 --folder inbox
```
**Expected**: Lists recent emails with date, sender, subject

### Test 5: Email - Search
```bash
outlook email search "subject:meeting" --max 5
outlook email search "from:travis" --max 5
```
**Expected**: Returns matching emails

### Test 6: Email - Get Message
```bash
# Get a message ID from Test 4, then:
outlook email get MESSAGE_ID
```
**Expected**: Shows full email details including body

### Test 7: Email - Send
```bash
outlook email send --to gwenonit@outlook.com --subject "Test from CLI" --body "This is a test email sent via outlook-cli"
```
**Expected**: "✓ Email sent successfully"

### Test 8: Calendar - List Events
```bash
outlook calendar list --today
outlook calendar list --days 7
```
**Expected**: Shows events for today/next 7 days

### Test 9: Calendar - Create Event
```bash
outlook calendar create --summary "CLI Test Meeting" --from "2026-02-17T15:00:00" --to "2026-02-17T16:00:00" --location "Virtual"
```
**Expected**: "✓ Event created: EVENT_ID"

### Test 10: Tasks - List
```bash
outlook tasks lists
```
**Expected**: Lists todo items (may be empty if no tasks)

### Test 11: Tasks - Create
```bash
outlook tasks create --title "Test task from CLI"
```
**Expected**: "✓ Task created: TASK_ID"

### Test 12: Tasks - List Again
```bash
outlook tasks lists
```
**Expected**: Shows the newly created task

### Test 13: JSON Output
```bash
outlook email list --max 3 --json-output
outlook calendar list --today --json-output
```
**Expected**: Valid JSON output for scripting

### Test 14: Token Refresh
```bash
# Wait 1+ hour (or manually expire token), then:
outlook email list --max 1
```
**Expected**: Automatically refreshes token, no re-login needed

### Test 15: Logout
```bash
outlook auth logout
outlook auth status
```
**Expected**: "Not authenticated" after logout

---

## Success Criteria

- ✅ All 15 tests pass
- ✅ No errors during authentication flow
- ✅ Email operations work (read, search, send)
- ✅ Calendar operations work (list, create)
- ✅ Tasks operations work (list, create)
- ✅ Token refresh works automatically
- ✅ JSON output is valid

## Notes

- Personal Microsoft accounts (outlook.com, hotmail.com, live.com) use `tenant: consumers`
- Work/school accounts would need different tenant ID
- Token stored in `~/.outlook-cli/tokens.json` (chmod 600)
- Device code flow is most secure for CLI tools (no secrets in code)

## Rollback

If issues arise:
```bash
pip uninstall outlook-cli
rm -rf ~/.outlook-cli
```
