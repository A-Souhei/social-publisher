#!/usr/bin/env bash
# LinkedIn OAuth 2.0 token fetcher (standard authorization code flow)
# Usage: ./get_linkedin_token.sh
# Or:    LINKEDIN_CLIENT_ID=xxx LINKEDIN_CLIENT_SECRET=xxx ./get_linkedin_token.sh

set -euo pipefail

REDIRECT_URI="https://www.linkedin.com/developers/tools/oauth/redirect"
SCOPES="openid profile w_member_social"

# --- credentials ---
CLIENT_ID="${LINKEDIN_CLIENT_ID:-}"
CLIENT_SECRET="${LINKEDIN_CLIENT_SECRET:-}"

if [[ -z "$CLIENT_ID" ]]; then
  read -rp "Client ID: " CLIENT_ID
fi
if [[ -z "$CLIENT_SECRET" ]]; then
  read -rsp "Client Secret: " CLIENT_SECRET
  echo
fi


ENCODED_REDIRECT="https%3A%2F%2Fwww.linkedin.com%2Fdevelopers%2Ftools%2Foauth%2Fredirect"
ENCODED_SCOPES="openid%20profile%20w_member_social"

AUTH_URL="https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=${CLIENT_ID}&redirect_uri=${ENCODED_REDIRECT}&scope=${ENCODED_SCOPES}"

echo
echo "========================================="
echo " Step 1: Open this URL in your browser"
echo "========================================="
echo
echo "$AUTH_URL"
echo

# try to open automatically
if command -v xdg-open &>/dev/null; then
  xdg-open "$AUTH_URL" &>/dev/null || true
elif command -v open &>/dev/null; then
  open "$AUTH_URL" &>/dev/null || true
fi

echo "After authorizing, LinkedIn will show a 'code' on the page."
echo
read -rp "Paste the code here: " AUTH_CODE

echo
echo "Exchanging code for access token..."
echo

RESPONSE=$(curl -s -X POST https://www.linkedin.com/oauth/v2/accessToken \
  --data-urlencode "grant_type=authorization_code" \
  --data-urlencode "code=${AUTH_CODE}" \
  --data-urlencode "redirect_uri=${REDIRECT_URI}" \
  --data-urlencode "client_id=${CLIENT_ID}" \
  --data-urlencode "client_secret=${CLIENT_SECRET}")

if echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if 'access_token' in d else 1)" 2>/dev/null; then
  ACCESS_TOKEN=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
  EXPIRES_IN=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('expires_in','?'))")

  echo "========================================="
  echo " Success!"
  echo "========================================="
  echo
  if [[ "$EXPIRES_IN" =~ ^[0-9]+$ ]]; then
    EXPIRES_DAYS=$(( EXPIRES_IN / 86400 ))
    echo "Access token (expires in ${EXPIRES_IN}s / ~${EXPIRES_DAYS} days):"
  else
    echo "Access token:"
  fi
  echo
  echo "$ACCESS_TOKEN"
  echo
  echo "Add to Hermes .env:"
  echo "  LINKEDIN_ACCESS_TOKEN=$ACCESS_TOKEN"
else
  echo "Error response from LinkedIn:"
  echo "$RESPONSE"
  exit 1
fi
