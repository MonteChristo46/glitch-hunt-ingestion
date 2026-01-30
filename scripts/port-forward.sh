#!/bin/bash

# Configuration
# Default values can be overridden by environment variables
NAMESPACE="${NAMESPACE:-glitch-hunt}"
# Release name assumption: glitch-hunt. If different, update these variables.
PG_CLUSTER_NAME="${PG_CLUSTER_NAME:-glitch-hunt-db}"
REDIS_SERVICE_NAME="${REDIS_SERVICE_NAME:-glitch-hunt-redis}"

# Local ports to avoid conflicts with local services
LOCAL_PG_PORT="${LOCAL_PG_PORT:-5433}"
LOCAL_REDIS_PORT="${LOCAL_REDIS_PORT:-6380}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

if ! command_exists kubectl; then
    log_error "kubectl is not installed."
    exit 1
fi

log_info "Fetching PostgreSQL credentials..."

# Get Postgres credentials from the CNPG app secret
PG_SECRET_NAME="${PG_CLUSTER_NAME}-app"

# Helper for base64 decoding that works on Mac and Linux
decode_base64() {
    if echo "$1" | base64 --decode >/dev/null 2>&1; then
        echo "$1" | base64 --decode
    elif echo "$1" | base64 -D >/dev/null 2>&1; then
        echo "$1" | base64 -D
    else
        echo "$1" | base64 -d
    fi
}

if kubectl get secret "$PG_SECRET_NAME" -n "$NAMESPACE" >/dev/null 2>&1; then
    # Fetch raw base64 values
    B64_USER=$(kubectl get secret "$PG_SECRET_NAME" -n "$NAMESPACE" -o jsonpath="{.data.username}")
    B64_PASS=$(kubectl get secret "$PG_SECRET_NAME" -n "$NAMESPACE" -o jsonpath="{.data.password}")
    B64_DB=$(kubectl get secret "$PG_SECRET_NAME" -n "$NAMESPACE" -o jsonpath="{.data.dbname}")
    
    # Decode
    PG_USER=$(decode_base64 "$B64_USER")
    PG_PASSWORD=$(decode_base64 "$B64_PASS")
    PG_DB=$(decode_base64 "$B64_DB")
    
    PG_HOST="localhost"
    PG_PORT="$LOCAL_PG_PORT"

    echo ""
    echo -e "${GREEN}PostgreSQL Credentials:${NC}"
    echo "----------------------------------------------------------------"
    echo "User:     $PG_USER"
    echo "Password: $PG_PASSWORD"
    echo "Database: $PG_DB"
    echo "Host:     $PG_HOST"
    echo "Port:     $PG_PORT"
    echo "----------------------------------------------------------------"
    echo ""
else
    log_error "PostgreSQL secret '$PG_SECRET_NAME' not found in namespace '$NAMESPACE'."
    log_error "Ensure the CloudNativePG cluster is running."
fi

echo -e "${GREEN}Redis Credentials:${NC}"
echo "----------------------------------------------------------------"
echo "Host:     localhost"
echo "Port:     $LOCAL_REDIS_PORT"
echo "Password: (none)"
echo "----------------------------------------------------------------"
echo ""

log_info "Starting Port Forwards..."

# Kill existing port-forwards if any
# Using simple pattern matching to avoid killing unrelated processes
pkill -f "kubectl port-forward.*$PG_CLUSTER_NAME" >/dev/null 2>&1
pkill -f "kubectl port-forward.*$REDIS_SERVICE_NAME" >/dev/null 2>&1

# Port forward Postgres
# Service is usually <cluster-name>-rw for read-write
PG_SERVICE_NAME="${PG_CLUSTER_NAME}-rw"
log_info "Forwarding PostgreSQL ($PG_SERVICE_NAME:5432 -> :$LOCAL_PG_PORT)..."
kubectl port-forward svc/"$PG_SERVICE_NAME" "$LOCAL_PG_PORT":5432 -n "$NAMESPACE" > /dev/null 2>&1 &
PG_PID=$!

# Port forward Redis
log_info "Forwarding Redis ($REDIS_SERVICE_NAME:6379 -> :$LOCAL_REDIS_PORT)..."
kubectl port-forward svc/"$REDIS_SERVICE_NAME" "$LOCAL_REDIS_PORT":6379 -n "$NAMESPACE" > /dev/null 2>&1 &
REDIS_PID=$!

log_success "Port forwarding started."
echo "Press Ctrl+C to stop."

# Trap Ctrl+C to kill the background processes
cleanup() {
    echo ""
    log_info "Stopping port forwards..."
    kill $PG_PID 2>/dev/null
    kill $REDIS_PID 2>/dev/null
    exit
}
trap cleanup INT

wait