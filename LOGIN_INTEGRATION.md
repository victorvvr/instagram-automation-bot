# Login Bot Integration Documentation

This document describes the integrated login and appeal functionality that has been added to the Instagram automation bot.

## Overview

The bot now includes comprehensive login recovery and account appeal capabilities integrated from the standalone login bot. This allows the bot to:

1. **Automatically re-login** when accounts get logged out
2. **Handle 2FA authentication** automatically via AdsPower extension
3. **Appeal suspended accounts** through automated captcha solving, phone verification, and selfie upload
4. **Handle cookie consent** popups automatically

## New Features

### 1. Automatic Login Recovery

When the bot detects an account is logged out, it will:
- Attempt to handle cookie consent if needed
- Wait for AdsPower extension to fill credentials
- Click the login button
- Detect and handle 2FA if required
- Continue with automation if login succeeds
- Shut down gracefully if login fails

**File**: `src/app/instagram/login/login_manager.py`

### 2. Account Appeal System

When an account is suspended, the bot will:
- Detect the current appeal step (captcha, phone, or selfie)
- Automatically solve captchas using 2Captcha extension
- Request and enter phone verification codes via DaisySMS
- Upload verification selfie if required
- Submit the appeal

**File**: `src/app/instagram/login/appeal_handler.py`

### 3. Phone Verification

Handles phone verification during appeals:
- Rents phone numbers from DaisySMS API
- Supports multiple retry attempts (default: 5)
- Enters phone number and requests SMS code
- Waits for and enters verification code
- Manages phone number lifecycle (rent, complete, cancel)

**File**: `src/app/instagram/login/phone_verification.py`

### 4. Captcha Solving

Automatically solves captchas during appeal process:
- Detects captcha presence
- Configures 2Captcha browser extension
- Waits for automatic solving (up to 2 minutes)
- Verifies solution and proceeds

**File**: `src/app/instagram/login/captcha_solver.py`

## Setup Instructions

### 1. Install Dependencies

Make sure you have the `requests` library installed:

```bash
pip install requests
```

### 2. Configure API Keys

Update your `.env` file with the following new keys:

```bash
# DaisySMS Configuration
DAISYSMS_API_KEY=your_key_here
DAISYSMS_BASE_URL=https://daisysms.com/stubs/handler_api.php

# 2Captcha Configuration
CAPTCHA_API_KEY=your_key_here
```

**Getting API Keys:**
- DaisySMS: Sign up at https://daisysms.com/ and get your API key from the dashboard
- 2Captcha: Sign up at https://2captcha.com/ and get your API key from the dashboard

### 3. Install 2Captcha Browser Extension

For captcha solving to work, you need to install the 2Captcha extension in your AdsPower browser profiles:

1. Download the 2Captcha Solver extension from Chrome Web Store
2. Add it to your AdsPower browser profile template
3. The bot will automatically configure it with your API key when needed

**Extension ID**: `ifibfemgeogfhoebkmokieepdoobkbpo`

### 4. Add Verification Selfie (Optional)

If you want to handle appeal flows that require selfie verification, place a file named `verification_selfie.jpg` in the project root directory. This should be a clear photo showing a face.

## How It Works

### Login Flow

```
AccountLoggedOut detected
    ↓
LoginManager.handle_login_process()
    ↓
Wait for AdsPower to fill credentials (7 seconds)
    ↓
Click "Log in" button
    ↓
Check if 2FA required
    ├─ Yes → Wait for extension to fill code → Click "Confirm"
    └─ No → Continue
    ↓
Login successful → Continue automation
```

### Appeal Flow

```
AccountSuspended detected
    ↓
AppealHandler.handle_suspended_account()
    ↓
Click "Appeal" button if present
    ↓
Detect appeal step
    ├─ Captcha → CaptchaSolver.handle_captcha_step()
    ├─ Phone → PhoneVerification.handle_phone_verification()
    └─ Selfie → AppealHandler._handle_verification_selfie()
    ↓
Appeal submitted → Set status to "Waiting for Appeal"
```

## Checkpoint Handlers

The integration modifies two checkpoint handlers:

### AccountLoggedOutHandler

**Before**: Immediately shut down when logged out
**After**:
1. Attempt automatic re-login
2. If successful, continue automation
3. If failed, shut down with "Logged Out" status

**Location**: `src/app/instagram/handlers/checkpoint_handlers.py:102-132`

### AccountSuspendedHandler

**Before**: Immediately shut down with "Banned" status
**After**:
1. Attempt automatic appeal process
2. Set status to "Waiting for Appeal" if successful
3. Shut down (appeal runs once per suspension)

**Location**: `src/app/instagram/handlers/checkpoint_handlers.py:66-94`

## Configuration

All configuration is handled through `src/app/core/config.py`:

```python
cfg = {
    # ... existing config ...
    "daisysms": {
        "apiKey": os.getenv("DAISYSMS_API_KEY"),
        "baseUrl": os.getenv("DAISYSMS_BASE_URL", "https://daisysms.com/stubs/handler_api.php"),
    },
    "captcha": {
        "apiKey": os.getenv("CAPTCHA_API_KEY"),
    },
}
```

## Module Structure

```
src/app/instagram/login/
├── __init__.py              # Module exports
├── login_manager.py         # Login & 2FA handling
├── appeal_handler.py        # Appeal orchestration
├── phone_verification.py    # Phone verification via DaisySMS
└── captcha_solver.py        # Captcha solving via 2Captcha
```

## Error Handling

The integration includes comprehensive error handling:

- **Login failures**: Log errors, attempt once, then shut down gracefully
- **Phone verification failures**: Try up to 5 different phone numbers
- **Captcha solving failures**: Timeout after 2 minutes, log error
- **Appeal failures**: Log errors, set appropriate Airtable status

All errors are logged using the existing logger system.

## Airtable Status Mapping

New statuses used by the integration:

| Status | When Set | Meaning |
|--------|----------|---------|
| `Logged Out` | Login failed | Account couldn't be logged in automatically |
| `Waiting for Appeal` | Appeal submitted | Appeal has been submitted, awaiting Instagram review |
| `Banned 🔴` | Appeal failed | Account suspended and appeal couldn't be completed |

## Costs

### DaisySMS Pricing
- ~$0.10 - $0.50 per phone number
- Bot tries up to 5 numbers per appeal (max ~$2.50 per appeal)

### 2Captcha Pricing
- ~$0.001 - $0.003 per reCAPTCHA solve
- Usually 1 captcha per appeal

**Total cost per successful appeal**: ~$0.50 - $3.00

## Limitations

1. **Manual intervention required for**:
   - Email verification checkpoints
   - Manual image captchas (non-reCAPTCHA)

2. **One appeal attempt per suspension**:
   - The bot attempts the appeal once
   - If it fails, manual intervention is required

3. **2FA dependency**:
   - Requires AdsPower extension for automatic 2FA code entry
   - Without it, 2FA accounts will fail to login

4. **Selfie verification**:
   - Requires `verification_selfie.jpg` in project root
   - Uses same photo for all accounts

## Troubleshooting

### Login not working
- Check that AdsPower extension is installed and configured
- Verify credentials are saved in AdsPower profile
- Check logs for specific error messages

### Phone verification failing
- Verify DAISYSMS_API_KEY is correct and has balance
- Check DaisySMS account for available numbers
- Ensure country is set to USA (code 187)

### Captcha solving not working
- Verify CAPTCHA_API_KEY is correct and has balance
- Ensure 2Captcha extension is installed in AdsPower
- Check extension ID matches: `ifibfemgeogfhoebkmokieepdoobkbpo`

### Appeal submission failing
- Check all API keys are configured correctly
- Verify `verification_selfie.jpg` exists if needed
- Review logs for specific step that failed

## Testing

To test the integration:

1. **Login recovery**:
   - Manually log out an account in Instagram
   - Run the bot - it should automatically re-login

2. **Appeal process**:
   - Use an account that's already suspended
   - Run the bot - it should attempt the appeal

3. **Monitor logs**: All steps are logged with detailed information

## Future Enhancements

Potential improvements:

- [ ] Number pooling system (reuse phone numbers across multiple appeals)
- [ ] Support for different selfie photos per account
- [ ] Email verification handling
- [ ] Manual captcha OCR integration
- [ ] Retry logic for failed appeals
- [ ] Appeal status checking and notification

## Support

If you encounter issues with the integration:

1. Check the logs for detailed error messages
2. Verify all API keys are configured correctly
3. Ensure required services (DaisySMS, 2Captcha) have sufficient balance
4. Review this documentation for setup requirements

## Credits

This integration is based on the standalone login bot located at `/Users/victorv/PycharmProjects/loginbot`, adapted and integrated into the follow automation bot.
