#!/bin/bash

# Test script to verify all autograder-critical endpoints
BASE_URL="https://xi43tvk341.execute-api.us-east-1.amazonaws.com"

echo "======================================"
echo "Testing Autograder-Critical Endpoints"
echo "======================================"
echo ""

# Test 1: Health check
echo "1. Testing /health..."
HEALTH=$(curl -s "$BASE_URL/health")
echo "Response: $HEALTH"
echo ""

# Test 2: Tracks endpoint  
echo "2. Testing /tracks..."
TRACKS=$(curl -s "$BASE_URL/tracks")
echo "Response: $TRACKS"
TRACK_COUNT=$(echo "$TRACKS" | jq -r '.planned_tracks | length')
echo "Track count: $TRACK_COUNT"
echo "Track name: $(echo "$TRACKS" | jq -r '.planned_tracks[0]')"
echo ""

# Test 3: Login (no credentials)
echo "3. Testing /login (no credentials)..."
LOGIN_NO_CREDS=$(curl -s -X POST "$BASE_URL/login" -H "Content-Type: application/json")
echo "Response: $LOGIN_NO_CREDS"
echo ""

# Test 4: Login (with credentials)
echo "4. Testing /login (with default admin credentials)..."
LOGIN_WITH_CREDS=$(curl -s -X POST "$BASE_URL/login" \
  -H "Content-Type: application/json" \
  -d '{
    "user": {"name": "ece30861defaultadminuser"},
    "secret": {"password": "correcthorsebatterystaple123(!__+@**(A;DROP TABLE packages"}
  }')
echo "Response: $LOGIN_WITH_CREDS"
TOKEN=$LOGIN_WITH_CREDS
echo ""

# Test 5: Authenticate endpoint
echo "5. Testing /authenticate..."
AUTH_RESPONSE=$(curl -s -X PUT "$BASE_URL/authenticate" \
  -H "Content-Type: application/json" \
  -d '{
    "user": {"name": "ece30861defaultadminuser"},
    "secret": {"password": "correcthorsebatterystaple123(!__+@**(A;DROP TABLE packages"}
  }')
echo "Response length: $(echo "$AUTH_RESPONSE" | wc -c)"
echo "Response starts with: $(echo "$AUTH_RESPONSE" | head -c 50)..."
echo ""

# Test 6: Reset (with auth)
echo "6. Testing /reset (DELETE with auth)..."
RESET_RESPONSE=$(curl -s -X DELETE "$BASE_URL/reset" \
  -H "Authorization: $TOKEN")
echo "Response: $RESET_RESPONSE"
echo ""

# Test 7: Tracks after reset
echo "7. Testing /tracks after reset..."
TRACKS_AFTER=$(curl -s "$BASE_URL/tracks")
echo "Response: $TRACKS_AFTER"
echo ""

# Test 8: Artifacts endpoint (should be empty after reset)
echo "8. Testing /artifacts (should be empty)..."
ARTIFACTS=$(curl -s "$BASE_URL/artifacts" -H "Authorization: $TOKEN")
echo "Response: $ARTIFACTS"
echo ""

echo "======================================"
echo "All tests complete!"
echo "======================================"
