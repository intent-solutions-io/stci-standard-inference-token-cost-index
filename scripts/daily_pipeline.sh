#!/bin/bash
#
# STCI Daily Pipeline Runner
# Runs the full collection and indexing pipeline
#
# Usage:
#   ./scripts/daily_pipeline.sh              # Run for today
#   ./scripts/daily_pipeline.sh 2026-01-01   # Run for specific date
#
# Cron example (run daily at 00:30 UTC):
#   30 0 * * * /path/to/stci/scripts/daily_pipeline.sh >> /var/log/stci/daily.log 2>&1
#

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="${PROJECT_ROOT}/venv"
LOG_DIR="${PROJECT_ROOT}/logs"
DATE="${1:-$(date -u +%Y-%m-%d)}"

# Colors (disabled if not interactive)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    NC=''
fi

log() {
    echo -e "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1"
}

log_success() {
    log "${GREEN}✓${NC} $1"
}

log_error() {
    log "${RED}✗${NC} $1"
}

log_warn() {
    log "${YELLOW}⚠${NC} $1"
}

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Log file for this run
RUN_LOG="${LOG_DIR}/run-${DATE}.log"

{
    log "=========================================="
    log "STCI Daily Pipeline"
    log "Date: ${DATE}"
    log "Project: ${PROJECT_ROOT}"
    log "=========================================="
    echo

    # Check virtual environment
    if [[ ! -d "$VENV_PATH" ]]; then
        log_error "Virtual environment not found at ${VENV_PATH}"
        log "Run: python3 -m venv venv && pip install -r requirements.txt"
        exit 1
    fi

    # Activate virtual environment
    source "${VENV_PATH}/bin/activate"
    log "Activated venv: $(which python)"

    # Change to project directory
    cd "$PROJECT_ROOT"

    # Step 1: Collection
    log ""
    log "Step 1: Collection"
    log "------------------"

    if python -m services.collector.pipeline --date "$DATE"; then
        log_success "Collection completed"
    else
        log_error "Collection failed"
        exit 1
    fi

    # Step 2: Indexing
    log ""
    log "Step 2: Indexing"
    log "----------------"

    if python -m services.indexer.pipeline --date "$DATE"; then
        log_success "Indexing completed"
    else
        log_error "Indexing failed"
        exit 1
    fi

    # Step 3: Verification
    log ""
    log "Step 3: Verification"
    log "--------------------"

    INDEX_FILE="${PROJECT_ROOT}/data/indices/${DATE}.json"
    OBS_FILE="${PROJECT_ROOT}/data/observations/${DATE}.jsonl"

    if [[ -f "$INDEX_FILE" ]]; then
        log_success "Index file exists: ${INDEX_FILE}"
        # Extract summary
        python3 -c "
import json
with open('${INDEX_FILE}') as f:
    d = json.load(f)
print(f\"  Date: {d['date']}\")
print(f\"  Observations: {d['observation_count']}\")
print(f\"  Indices: {len(d['indices'])}\")
for name, data in d['indices'].items():
    print(f\"    {name}: \${data['blended_rate']:.2f}/1M ({data['model_count']} models)\")
print(f\"  Hash: {d['verification_hash']}\")
"
    else
        log_error "Index file missing: ${INDEX_FILE}"
        exit 1
    fi

    if [[ -f "$OBS_FILE" ]]; then
        OBS_COUNT=$(wc -l < "$OBS_FILE")
        log_success "Observations file exists: ${OBS_COUNT} records"
    else
        log_error "Observations file missing: ${OBS_FILE}"
        exit 1
    fi

    # Summary
    log ""
    log "=========================================="
    log_success "Pipeline completed successfully"
    log "Index: ${INDEX_FILE}"
    log "Observations: ${OBS_FILE}"
    log "=========================================="

} 2>&1 | tee -a "$RUN_LOG"

exit 0
