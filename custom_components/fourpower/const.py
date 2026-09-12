"""Constants for the 4Power integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "fourpower"

# The public OAuth client. PKCE only — there is no secret, which is why this can
# live in a public repository at all (4PowerCloud sql/2026-09-11_oauth-pkce.sql).
CLIENT_ID = "4power-home-assistant"
OAUTH2_AUTHORIZE = "https://api.4power.dk/oauth/authorize"
OAUTH2_TOKEN = "https://api.4power.dk/oauth/token"

# Distinct from the Google Home account-linking scope: the cloud refuses /ha/*
# to a token without it, and refuses Google's fulfillment to a token with it.
OAUTH2_SCOPE = "ha"

API_DEVICES = "https://api.4power.dk/ha/devices"
API_COMMAND = "https://api.4power.dk/ha/command"

# The cloud documents its own floor in `minPollSeconds` and rate-limits per
# token; this is the fallback for a payload that omits it.
DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)
MIN_SCAN_SECONDS = 30

# A command's effect reaches the shadow in about a second, but the cloud masks
# the not-yet-applied value for only ~10 s (PENDING_DESIRED_MS). Polling inside
# that window shows the target; polling after it shows the old value again if
# the spa has not echoed. So refresh soon after commanding rather than waiting
# for the next scheduled poll.
POST_COMMAND_REFRESH = timedelta(seconds=3)

# Spa temperature range the cloud clamps to (device-output.mjs TEMP_MIN/MAX).
MIN_TEMP = 10.0
MAX_TEMP = 40.0
