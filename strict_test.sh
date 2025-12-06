
#!/bin/bash
set -euo pipefail

API="https://xi43tvk341.execute-api.us-east-1.amazonaws.com"   # base API URL
TOKEN=""
ARTIFACT_ID=""

RED="\033[0;31m"
GREEN="\033[0;32m"
NC="\033[0m"


fail() {
    echo -e "${RED}❌ TEST FAILED:${NC} $1"
    exit 1
}

pass() {
    echo -e "${GREEN}✔ PASS:${NC} $1"
}

###############################################
# FUNCTION: CHECK HTTP STATUS
###############################################
check_status() {
    STATUS=$1
    EXPECTED=$2
    MSG=$3

    if [ "$STATUS" -ne "$EXPECTED" ]; then
        fail "$MSG (expected $EXPECTED, got $STATUS)"
    fi
}

###############################################
# TEST 1 — HEALTH
###############################################
echo "TEST 1 — Health check"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/health")
check_status $STATUS 200 "Health endpoint failed"
pass "Health endpoint responds correctly"

###############################################
# TEST 2 — TRACKS
###############################################
echo "TEST 2 — Tracks"
TRACKS=$(curl -s "$API/tracks")
echo "$TRACKS" | jq . > /dev/null || fail "Tracks JSON invalid"
[[ "$TRACKS" == *"plannedTracks"* ]] || fail "Missing plannedTracks"
pass "Tracks endpoint valid"

###############################################
# TEST 3 — LOGIN
###############################################
echo "TEST 3 — Login"
LOGIN=$(curl -s -X POST "$API/login" \
    -H "Content-Type: application/json" \
    -d '{}')

TOKEN=$(echo "$LOGIN" | jq -r .token)
[[ "$TOKEN" != "null" && "$TOKEN" != "" ]] || fail "Login missing token"
pass "Login returned valid token ($TOKEN)"

###############################################
# TEST 4 — AUTHENTICATE
###############################################
echo "TEST 4 — Authenticate"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X PUT "$API/authenticate" \
    -H "Content-Type: application/json" \
    -d '{
        "user": { "name": "ece461", "is_admin": true },
        "secret": { "password": "password" }
    }')

check_status $STATUS 200 "Authenticate failed"
pass "Authenticate success"

###############################################
# TEST 5 — CREATE ARTIFACT
###############################################
echo "TEST 5 — Create Artifact"

CREATE=$(curl -s -w "\n%{http_code}" \
    -X POST "$API/artifact/model" \
    -H "Authorization: bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"url":"https://huggingface.co/bert-base-uncased"}')

BODY=$(echo "$CREATE" | head -n1)
STATUS=$(echo "$CREATE" | tail -n1)

check_status $STATUS 201 "Create artifact failed"

ARTIFACT_ID=$(echo "$BODY" | jq -r '.metadata.id')
[[ "$ARTIFACT_ID" != "null" ]] || fail "Missing artifact ID"

pass "Artifact created (ID=$ARTIFACT_ID)"

###############################################
# TEST 6 — GET ARTIFACT
###############################################
echo "TEST 6 — Get Artifact"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: bearer $TOKEN" \
    "$API/artifacts/model/$ARTIFACT_ID")
check_status $STATUS 200 "Get artifact failed"
pass "Get artifact works"

###############################################
# TEST 7 — RATE ARTIFACT
###############################################
echo "TEST 7 — Rate Artifact"
RATE=$(curl -s "$API/artifact/model/$ARTIFACT_ID/rate" -H "Authorization: bearer $TOKEN")
echo "$RATE" | jq . > /dev/null || fail "Invalid JSON"
[[ "$RATE" == *"net_score"* ]] || fail "Missing net_score"
pass "Rate OK"

###############################################
# TEST 8 — LIST ARTIFACTS
###############################################
echo "TEST 8 — List Artifacts"
LIST=$(curl -s "$API/artifacts" -H "Authorization: bearer $TOKEN")
echo "$LIST" | jq . > /dev/null || fail "Invalid JSON"
[[ "$LIST" == *"$ARTIFACT_ID"* ]] || fail "Artifact not listed"
pass "List OK"

###############################################
# TEST 9 — LICENSE CHECK
###############################################
echo "TEST 9 — License Check"
LICENSE=$(curl -s -X POST "$API/artifact/model/$ARTIFACT_ID/license-check" \
    -H "Authorization: bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"github_url":"https://github.com/huggingface/transformers"}')

echo "$LICENSE" | jq . > /dev/null || fail "Invalid JSON"
pass "License check OK"

###############################################
# TEST 10 — COST
###############################################
echo "TEST 10 — Cost"
COST=$(curl -s "$API/artifact/model/$ARTIFACT_ID/cost" \
    -H "Authorization: bearer $TOKEN")
echo "$COST" | jq . > /dev/null || fail "Invalid JSON"
pass "Cost OK"

###############################################
# TEST 11 — LINEAGE
###############################################
echo "TEST 11 — Lineage"
LINEAGE=$(curl -s "$API/artifact/model/$ARTIFACT_ID/lineage" \
    -H "Authorization: bearer $TOKEN")
echo "$LINEAGE" | jq . > /dev/null || fail "Invalid JSON"
pass "Lineage OK"

###############################################
# TEST 12 — SEARCH BY NAME
###############################################
echo "TEST 12 — Search by Name"
SEARCH_NAME=$(curl -s "$API/artifact/byName/bert" \
    -H "Authorization: bearer $TOKEN")
echo "$SEARCH_NAME" | jq . > /dev/null || fail "Invalid JSON"
pass "Search by name OK"

###############################################
# TEST 13 — SEARCH BY REGEX POST
###############################################
echo "TEST 13 — Search by Regex POST"
SEARCH_RGX=$(curl -s -X POST "$API/artifact/byRegEx" \
    -H "Authorization: bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"regex":"bert"}')
echo "$SEARCH_RGX" | jq . > /dev/null || fail "Invalid JSON"
pass "Regex search OK"

###############################################
# TEST 14 — RESET REGISTRY
###############################################
echo "TEST 14 — Reset Registry"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X DELETE "$API/reset" \
    -H "Authorization: bearer $TOKEN")

check_status $STATUS 200 "Reset failed"
pass "Reset OK"

echo -e "\n${GREEN}🎉 ALL STRICT TESTS PASSED SUCCESSFULLY${NC}\n"

###############################################
# TEST 16 — INGEST (SUCCESSFUL)
###############################################
echo "TEST 16 — Ingest Successful"

INGEST_OK=$(curl -s -w "\n%{http_code}" -X POST "$API/artifact/model/ingest" \
    -H "Authorization: bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"url": "https://huggingface.co/bert-base-uncased"}')

INGEST_BODY_OK=$(echo "$INGEST_OK" | head -n1)
INGEST_STATUS_OK=$(echo "$INGEST_OK" | tail -n1)

check_status $INGEST_STATUS_OK 201 "Ingest (success) should return 201"

ACCEPTED=$(echo "$INGEST_BODY_OK" | jq -r .accepted)
[[ "$ACCEPTED" == "true" ]] || fail "Ingest (success) did not return accepted=true"

INGEST_ID=$(echo "$INGEST_BODY_OK" | jq -r .metadata.id)
[[ "$INGEST_ID" != "null" ]] || fail "Ingest (success) missing metadata.id"

pass "Ingest success OK (ID=$INGEST_ID)"


###############################################
# TEST 17 — INGEST (REJECTED)
###############################################
echo "TEST 17 — Ingest Rejected"

# Use a bogus model URL (logic: we simulate rejection)
INGEST_FAIL=$(curl -s -w "\n%{http_code}" -X POST "$API/artifact/model/ingest" \
    -H "Authorization: bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"url": "https://huggingface.co/garbage-model-xyz"}')

INGEST_BODY_FAIL=$(echo "$INGEST_FAIL" | head -n1)
INGEST_STATUS_FAIL=$(echo "$INGEST_FAIL" | tail -n1)

check_status $INGEST_STATUS_FAIL 400 "Ingest (fail) should return 400"

ACCEPTED_FAIL=$(echo "$INGEST_BODY_FAIL" | jq -r .accepted)
[[ "$ACCEPTED_FAIL" == "false" ]] || fail "Ingest (fail) did not return accepted=false"

pass "Rejected ingest behaves correctly"
